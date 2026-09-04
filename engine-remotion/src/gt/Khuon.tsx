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
/* Bốn màu áo cho dàn nhân vật. Không lấy màu thương hiệu: màu ấy đã dùng cho đồ hoạ và
   con số, nên nhân vật mặc nó thì người và biểu đồ đọc ra cùng một lớp. Bốn tông trung
   tính đủ khác nhau ở cỡ nhỏ, và đều đủ sẫm để đường nét đen trên nền sáng vẫn nổi. */
const AO = ["#46505C", "#6E5A4A", "#4A6157", "#5B5470"];

export const BieuTuong: React.FC<{ ten: string; s: number; mau?: string; tu?: number; nv?: number }> =
({ ten, s, mau = "#2C2722", tu = 0, nv = 0 }) => {
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
    /* HƯƠU CAO CỔ — HÌNH KHỐI ĐẶC, KHÔNG PHẢI NÉT RỖNG.  (3/9/2026)
       Bản trước vẽ bằng ba đường nét không tô: thân là một khung chữ nhật hở, cổ là một đường
       cong, đầu là một tam giác. Ở cỡ đầy đủ còn đoán ra; ở bố cục SO SÁNH THEO TỈ LỆ vế nhỏ
       chỉ còn 34% cỡ, và soi khung HOW BIG (hươu 18 ft cạnh cây đỏ 350 ft) thì nó ra một cái
       móc câu — không ai đọc ra con hươu.
       Nét rỗng mất chữ tín khi thu nhỏ vì độ dày nét không co theo hình; **hình khối đặc thì
       co bao nhiêu vẫn giữ được bóng dáng**. Mọi biểu tượng dùng ở bố cục tỉ lệ phải là khối
       đặc — đó là ràng buộc của bố cục, không phải sở thích vẽ. */
    case "huou": return <g>
      <rect x={-k(0.20)} y={k(0.02)} width={k(0.40)} height={k(0.26)} rx={k(0.07)}
            fill="#D9A441" stroke={mau} strokeWidth={n} />
      {P(`M ${k(0.04)} ${k(0.06)} L ${k(0.20)} ${-k(0.40)} L ${k(0.34)} ${-k(0.36)} L ${k(0.17)} ${k(0.10)} Z`, "#D9A441")}
      {P(`M ${k(0.18)} ${-k(0.40)} L ${k(0.42)} ${-k(0.46)} L ${k(0.44)} ${-k(0.32)} L ${k(0.30)} ${-k(0.31)} Z`, "#D9A441")}
      {P(`M ${k(0.24)} ${-k(0.47)} l ${k(0.01)} ${-k(0.07)}`, "none", 1.2)}
      {P(`M ${k(0.33)} ${-k(0.49)} l ${k(0.01)} ${-k(0.07)}`, "none", 1.2)}
      {[-0.14, 0.02].map((dx) => (
        <rect key={dx} x={k(dx)} y={k(0.26)} width={k(0.055)} height={k(0.20)}
              fill="#D9A441" stroke={mau} strokeWidth={n} />
      ))}
      {[[-0.10, 0.08], [0.06, 0.14], [-0.02, 0.16]].map((q, qi) => (
        <circle key={qi} cx={k(q[0])} cy={k(q[1])} r={k(0.035)} fill="#8A5A2E" />
      ))}</g>;
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
    /* ── NGƯỜI  (vẽ lại 4/9/2026 theo ảnh tham chiếu anh gửi) ────────────────────────────
       Bản cũ: đầu tròn RỖNG · thân một nét thẳng · tay chữ V · hai nét chân. Anh xem khung
       và nói thẳng *"người que vẽ hơi xấu"* — đúng, và đọc mã thì thấy vì sao: nó có đủ bộ
       phận của một con người mà thiếu cả ba thứ làm nó thành một NHÂN VẬT.

       Đối chiếu ảnh tham chiếu, ba thứ ấy là:
         1. MẶT  — hai mắt bầu dục, hai lông mày, một miệng. Không có mặt thì hình chỉ nói
                   "có một người"; có mặt thì nó nói "người này đang thấy thế nào". Lông mày
                   làm phần lớn việc ấy.
         2. ÁO   — thân là một KHỐI đặc có viền, không phải một nét. Nét thì rỗng, và rỗng
                   thì ở cỡ nhỏ nó biến mất (§15.9 — nét rỗng chết khi thu nhỏ).
         3. KHỚP — tay chân gập ở khuỷu và gối. Bốn nét thẳng toả từ một điểm đọc ra ngôi
                   sao; gập một nhịp là đọc ra người đang đứng.

       Cỡ nhỏ vẫn phải đọc được: hình này còn dùng ở bố cục so sánh, thu còn 34% (§15.9).
       Nên mắt là KHỐI ĐẶC (co bao nhiêu vẫn thấy), lông mày dày gần bằng nét chính, và áo
       là mảng màu — ba thứ sống sót qua phép thu, khác hẳn nét mảnh. */
    case "nguoi": {
      /* ── NÉT RIÊNG, KHÔNG MƯỢN NÉT CHUNG  (đo lại sau khi soi ảnh cận) ────────────────
         Bản vẽ lại lần đầu dùng `n` (= 0,055·s) như mọi biểu tượng khác. Soi ảnh cận thì
         nét ấy NUỐT hết chi tiết: lông mày dính vào viền đầu, miệng thành một cục, hai
         tay thành hai khối đen. Đo trên ảnh tham chiếu anh gửi: viền khoảng **1,8% chiều
         cao hình**, tức chỉ bằng một phần ba `n`.
         `n` đúng cho biểu tượng đồ vật (ít chi tiết, cần dày để đọc ở cỡ nhỏ) và sai ở
         đây vì mặt người là chỗ chi tiết dày đặc nhất trong cả bảng hình. Đúng §6 —
         mượn một giá trị cho việc nó không sinh ra để làm. */
      const w = k(0.017);                 // nét thân/chi
      const wM = k(0.013);                // nét nét mặt — mảnh hơn, nhưng vẫn là KHỐI ĐẶC
      const N = (d: string, f = "none", ww = w) => (
        <path d={d} fill={f} stroke={mau} strokeWidth={ww}
              strokeLinejoin="round" strokeLinecap="round" />
      );
      const vaiY = -k(0.10);
      return (<g>
        {/* ÁO vẽ TRƯỚC đầu, để cổ áo chui xuống dưới cằm chứ không cắt ngang mặt */}
        {N(`M ${-k(0.105)} ${vaiY} Q 0 ${vaiY - k(0.030)} ${k(0.105)} ${vaiY}
            L ${k(0.092)} ${k(0.16)} L ${-k(0.092)} ${k(0.16)} Z`, AO[nv % AO.length])}
        {/* ── NĂM TƯ THẾ, KHÔNG PHẢI MỘT  (4/9/2026) ─────────────────────────────────────
            Sau khi buộc đồ vật phải lấy từ LỜI, `nguoi` chiếm 64% nhịp `canh` — và bốn nhịp
            người liên tiếp với MỘT tư thế đứng, MỘT nụ cười là đúng lời anh phê *"lặp đi lặp
            lại cùng một mô-típ"*. Đổi người thành cái đồng hồ để lấy đa dạng thì hỏng nghĩa,
            nên lối thoát duy nhất là để chính nhân vật DIỄN.
            Bốn ảnh anh gửi làm đúng thế: mọi khung đều có người, và cái đổi giữa khung này với
            khung kia là TƯ THẾ và BIỂU CẢM — ngồi cúi viết, nằm co bên lửa, đứng chỉ tay, đưa
            món đồ. Không khung nào đổi nhân vật thành một biểu tượng.
            Tay và chân vốn là bốn nét rời, nên tư thế chỉ là đổi toạ độ, không đổi kiến trúc. */}
        {tu === 1 ? (<>
          {/* chỉ tay lên — câu nêu một con số hoặc một sự thật */}
          {N(`M ${-k(0.105)} ${vaiY + k(0.045)} L ${-k(0.175)} ${k(0.060)} L ${-k(0.150)} ${k(0.16)}`)}
          {N(`M ${k(0.105)} ${vaiY + k(0.040)} L ${k(0.185)} ${-k(0.140)} L ${k(0.205)} ${-k(0.300)}`)}
        </>) : tu === 2 ? (<>
          {/* hai tay buông xuôi, vai chùng — mệt, chịu đựng */}
          {N(`M ${-k(0.100)} ${vaiY + k(0.060)} L ${-k(0.140)} ${k(0.080)} L ${-k(0.132)} ${k(0.215)}`)}
          {N(`M ${k(0.100)} ${vaiY + k(0.060)} L ${k(0.140)} ${k(0.080)} L ${k(0.132)} ${k(0.215)}`)}
        </>) : tu === 3 ? (<>
          {/* hai tay dang ra — câu hỏi, ngơ ngác */}
          {N(`M ${-k(0.105)} ${vaiY + k(0.045)} L ${-k(0.215)} ${-k(0.010)} L ${-k(0.255)} ${-k(0.090)}`)}
          {N(`M ${k(0.105)} ${vaiY + k(0.045)} L ${k(0.215)} ${-k(0.010)} L ${k(0.255)} ${-k(0.090)}`)}
        </>) : tu === 4 ? (<>
          {/* một tay đưa ra trước — trao, chỉ vào vật bên cạnh */}
          {N(`M ${-k(0.105)} ${vaiY + k(0.045)} L ${-k(0.165)} ${k(0.070)} L ${-k(0.148)} ${k(0.180)}`)}
          {N(`M ${k(0.105)} ${vaiY + k(0.050)} L ${k(0.230)} ${k(0.010)} L ${k(0.320)} ${k(0.020)}`)}
        </>) : (<>
          {N(`M ${-k(0.105)} ${vaiY + k(0.045)} L ${-k(0.185)} ${k(0.045)} L ${-k(0.155)} ${k(0.16)}`)}
          {N(`M ${k(0.105)} ${vaiY + k(0.045)} L ${k(0.195)} ${k(0.035)} L ${k(0.172)} ${k(0.145)}`)}
        </>)}
        {/* CHÂN gập ở gối, bàn chân bẻ ngang để nhân vật ĐỨNG chứ không lơ lửng.
            Tư thế 3 và 4 bước đi: một chân trước một chân sau. */}
        {tu === 3 || tu === 4 ? (<>
          {N(`M ${-k(0.050)} ${k(0.16)} L ${-k(0.135)} ${k(0.30)} L ${-k(0.150)} ${k(0.42)} L ${-k(0.215)} ${k(0.432)}`)}
          {N(`M ${k(0.050)} ${k(0.16)} L ${k(0.105)} ${k(0.30)} L ${k(0.075)} ${k(0.42)} L ${k(0.140)} ${k(0.432)}`)}
        </>) : (<>
          {N(`M ${-k(0.050)} ${k(0.16)} L ${-k(0.078)} ${k(0.30)} L ${-k(0.060)} ${k(0.42)} L ${-k(0.125)} ${k(0.432)}`)}
          {N(`M ${k(0.050)} ${k(0.16)} L ${k(0.078)} ${k(0.30)} L ${k(0.060)} ${k(0.42)} L ${k(0.125)} ${k(0.432)}`)}
        </>)}
        {/* ĐẦU chiếm khoảng một phần ba chiều cao — tỉ lệ ấy là thứ làm hình đọc ra nhân
            vật thay vì sơ đồ người. */}
        <circle cx="0" cy={-k(0.285)} r={k(0.150)} fill="#FFFFFF"
                stroke={mau} strokeWidth={k(0.019)} />
        {/* ── TÓC: BỐN KIỂU  (4/9/2026) ───────────────────────────────────────────────────
            Anh: *"lặp đi lặp lại 1 nhân vật, nhàm chán, không ra đâu cả"*. Tư thế thôi chưa
            đủ — bốn ảnh anh gửi có NHIỀU NGƯỜI KHÁC NHAU: người tóc bù, người tóc dài tết
            bím, người có râu. Cùng một khuôn mặt trắng, cái tách họ ra là TÓC và MÀU ÁO.
            Vẽ SAU vòng đầu để tóc đè lên đường viền trên, đúng cách ảnh tham chiếu làm —
            tóc mọc ra ngoài khối đầu chứ không nằm gọn bên trong. */}
        {nv % 4 === 1 ? (
          <path d={`M ${-k(0.150)} ${-k(0.300)} q ${k(0.030)} ${-k(0.140)} ${k(0.150)} ${-k(0.148)}
                    q ${k(0.122)} ${k(0.008)} ${k(0.150)} ${k(0.148)}
                    q ${-k(0.060)} ${-k(0.060)} ${-k(0.150)} ${-k(0.052)}
                    q ${-k(0.092)} ${-k(0.008)} ${-k(0.150)} ${k(0.052)} Z`} fill={mau} />
        ) : nv % 4 === 2 ? (
          <path d={`M ${-k(0.152)} ${-k(0.270)} q ${-k(0.010)} ${-k(0.190)} ${k(0.152)} ${-k(0.178)}
                    q ${k(0.162)} ${-k(0.012)} ${k(0.152)} ${k(0.178)}
                    l ${-k(0.038)} ${k(0.010)} q ${k(0.006)} ${-k(0.128)} ${-k(0.114)} ${-k(0.126)}
                    q ${-k(0.120)} ${-k(0.002)} ${-k(0.114)} ${k(0.126)} Z`} fill={mau} />
        ) : nv % 4 === 3 ? (
          <path d={`M ${-k(0.148)} ${-k(0.296)} q ${k(0.040)} ${-k(0.132)} ${k(0.148)} ${-k(0.140)}
                    q ${k(0.108)} ${k(0.008)} ${k(0.148)} ${k(0.140)}
                    l ${-k(0.052)} ${k(0.016)} q ${-k(0.030)} ${-k(0.072)} ${-k(0.096)} ${-k(0.070)}
                    q ${-k(0.066)} ${k(0.002)} ${-k(0.096)} ${k(0.070)} Z`} fill={mau} />
        ) : null}
        <ellipse cx={-k(0.050)} cy={-k(0.295)} rx={k(0.019)} ry={k(0.026)} fill={mau} />
        <ellipse cx={k(0.050)} cy={-k(0.295)} rx={k(0.019)} ry={k(0.026)} fill={mau} />
        {/* LÔNG MÀY + MIỆNG THEO TƯ THẾ. Ảnh tham khảo: người ngồi viết có lông mày XUÔI và
            miệng thẳng; người kể chuyện có miệng mở. Mặt bất động là thứ làm cả loạt khung
            đọc ra "cùng một hình dán", kể cả khi thân đã đổi tư thế. */}
        {tu === 2 ? (<>
          {/* MÀY XUÔI RA NGOÀI = MỆT. Bản trước cho đầu trong THẤP hơn đầu ngoài — đó là
              mày CHỤM VÀO GIỮA, tức nét giận dữ, và anh đọc ra đúng thế. Buồn/mệt thì
              ngược lại: đầu trong CAO, đuôi ngoài xuôi xuống. Một dấu trừ, hai cảm xúc
              trái ngược — và không có cách nào thấy ngoài việc nhìn khuôn mặt đã dựng. */}
          {N(`M ${-k(0.078)} ${-k(0.330)} L ${-k(0.026)} ${-k(0.356)}`, "none", wM)}
          {N(`M ${k(0.026)} ${-k(0.356)} L ${k(0.078)} ${-k(0.330)}`, "none", wM)}
        </>) : tu === 3 ? (<>
          {N(`M ${-k(0.082)} ${-k(0.386)} Q ${-k(0.052)} ${-k(0.408)} ${-k(0.022)} ${-k(0.390)}`, "none", wM)}
          {N(`M ${k(0.022)} ${-k(0.390)} Q ${k(0.052)} ${-k(0.408)} ${k(0.082)} ${-k(0.386)}`, "none", wM)}
        </>) : (<>
          {N(`M ${-k(0.078)} ${-k(0.358)} L ${-k(0.026)} ${-k(0.374)}`, "none", wM)}
          {N(`M ${k(0.026)} ${-k(0.374)} L ${k(0.078)} ${-k(0.358)}`, "none", wM)}
        </>)}
        {tu === 2
          ? N(`M ${-k(0.032)} ${-k(0.220)} L ${k(0.032)} ${-k(0.220)}`, "none", wM)
          : tu === 3
          ? <ellipse cx="0" cy={-k(0.216)} rx={k(0.026)} ry={k(0.032)} fill={mau} />
          : tu === 1 || tu === 4
          ? N(`M ${-k(0.044)} ${-k(0.234)} Q 0 ${-k(0.186)} ${k(0.044)} ${-k(0.234)}`, "none", wM)
          : N(`M ${-k(0.036)} ${-k(0.228)} Q 0 ${-k(0.202)} ${k(0.036)} ${-k(0.228)}`, "none", wM)}
      </g>);
    }
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
export const _pha = (h: string, t: number): string => {
  const m = /^#([0-9a-f]{6})$/i.exec((h || "").trim());
  if (!m) return h;
  return "#" + [0, 2, 4].map((i) => {
    const v = parseInt(m[1].slice(i, i + 2), 16);
    const r = t >= 0 ? v + (255 - v) * t : v * (1 + t);
    return Math.max(0, Math.min(255, Math.round(r))).toString(16).padStart(2, "0");
  }).join("");
};

/* Trộn hai mã màu theo tỉ lệ — dùng cho tường/sàn của `NenPhong`, xem chú thích tại chỗ. */
export const _tron = (a: string, b: string, t: number): string => {
  const ma = /^#([0-9a-f]{6})$/i.exec((a || "").trim());
  const mb = /^#([0-9a-f]{6})$/i.exec((b || "").trim());
  if (!ma || !mb) return a;
  return "#" + [0, 2, 4].map((i) => {
    const va = parseInt(ma[1].slice(i, i + 2), 16);
    const vb = parseInt(mb[1].slice(i, i + 2), 16);
    return Math.round(va + (vb - va) * t).toString(16).padStart(2, "0");
  }).join("");
};

/* ── MỘT NGUỒN SỰ THẬT CHO ĐƯỜNG CHÂN TRỜI  (4/9/2026) ──────────────────────────────────────
   Rà soát tìm ra **BỐN mặt sàn khác nhau cùng tồn tại trong một khung**, và mỗi lớp tự vẽ bóng
   tiếp đất của mình ở mặt sàn riêng ấy:

       NenPhong chân trời   0,730·H     (và đổi 0,66 / 0,73 / 0,80 theo `hat`)
       chủ thể `canh`       0,660·H     hằng `SAN` ghi cứng ở KichGiaiThich
       Chart yDay           0,640·H     (0,80 trong hệ H*0,80)
       ChiaDoi tỉ lệ        0,480·H     (0,60 trong hệ H*0,80)

   Hậu quả: cột biểu đồ lơ lửng 0,09·H TRÊN sàn phòng, khối so sánh lơ lửng 0,25·H, chủ thể
   `canh` lơ lửng 0,07·H — và cả bốn đều có bóng tiếp đất, nên mắt thấy bóng ở một chỗ và mặt
   sàn ở chỗ khác. Đây đúng họ lỗi §6: *chép hằng sang hệ quy chiếu khác* — 0,60 và 0,80 đo
   trong hệ `H*0,80`, còn 0,66 và 0,73 đo trong hệ khung đầy, và không ai quy đổi.

   Tệ hơn: chân trời của `NenPhong` ĐỔI THEO TẬP (`hat`), nên ba lớp kia lệch một lượng khác
   nhau ở mỗi tập — 5/6 số tập lệch, chỉ 1/6 trùng.

   Nay mọi lớp hỏi cùng một hàm. Ai nhận `H` khác thì tự quy đổi bằng tỉ lệ của mình. */
/* ── MẶT SÀN PHẢI NẰM TRÊN VÙNG CHỮ  (4/9/2026) ────────────────────────────────────────────
   Anh: *"tránh lỗi che khuất chồng chéo … người ko lơ lửng."* Hai câu ấy nghe như hai việc,
   nhưng ở đây chúng là MỘT: đo bằng pixel trên khung vừa dựng —

       dải nhãn trắng ("NOON — WORK")   0,72·H … 0,76·H
       dải phụ đề                        0,80·H … 0,85·H
       chân trời cũ                      0,66 · 0,73 · **0,80**·H

   Hai biến thể trong ba rơi thẳng vào vùng chữ. Nên vật ĐỨNG ĐÚNG trên mặt đất thì bị dải
   chữ cắt ngang bụng; còn muốn vật không bị cắt thì phải nhấc nó lên khỏi mặt đất — tức
   **lơ lửng**. Hai lời phê của anh là hai đầu của cùng một mâu thuẫn, và không bản vá nào ở
   phía vật giải được: chọn đằng nào cũng sai một đằng.

   Chữa ở chỗ sinh ra mâu thuẫn: kéo mặt sàn lên trên vùng chữ. Cả nền, cả vật, cả bóng đổ
   đều đọc hàm này nên chúng dịch cùng nhau — đó là lý do hàm này tồn tại (một nguồn sự thật).
   Và đây cũng chính là bố cục của mấy ảnh anh gửi: chân trời ở khoảng hai phần ba khung,
   nhân vật đứng trọn trên dải đất, chữ nằm hẳn dưới, không lớp nào chạm lớp nào.

   Ba biến thể vẫn giữ (nền đổi theo tập), chỉ hạ trần: cao nhất 0,70 để còn 0,02·H lề trước
   khi chạm mép dải nhãn. */
export const chanTroi = (H: number, hat: number = 0): number => {
  const k = Math.abs(hat) % 6;
  return H * (k === 1 ? 0.70 : k === 4 ? 0.60 : 0.66);
};

/* ── BỀ NGANG MỘT CHUỖI, ƯỚC LƯỢNG THEO TỪNG KÝ TỰ  (4/9/2026) ─────────────────────────────
   Cả hai chỗ ép cỡ chữ trong tệp này đều dùng `(W * k / s.length) * 1,6x` — tức giả định
   MỌI ký tự rộng như nhau, khoảng 0,61em. Với chữ số thì gần đúng; với CHỮ HOA thì sai hẳn:
   trong Poppins Black, `M`/`W` rộng ~0,95em còn `1`/`.`/`,` chỉ ~0,30–0,55em.

   Hậu quả soi được trên khung thật: SURVIVE hiện `PROBABLY` bị cắt cụt CẢ HAI mép, WHAT
   WEIGHS hiện `24,000` cũng cụt. Cùng một công thức, hai chuỗi khác loại ký tự.

   Đây là họ lỗi *"một kích thước chịu hai ràng buộc mà công thức chỉ mã hoá một"* (§6): cỡ
   chữ phụ thuộc CẢ số ký tự LẪN ký tự nào. Nay cộng bề ngang thật của từng ký tự.
   Số đo là ước lượng có chủ ý (không đo font lúc chạy được trong SVG tĩnh), và nó ước
   lượng THỪA — thà chữ nhỏ hơn một chút còn hơn tràn khỏi khung. */
/* ── ĐÁY CỦA MỘT BIỂU TƯỢNG  (4/9/2026) ────────────────────────────────────────────────────
   Mọi biểu tượng vẽ trong hộp tâm-ở-giữa cỡ `s`, nhưng KHÔNG hình nào chạm hết ±0,5·s: hình
   `nguoi` có bàn chân ở +0,432·s, mấy hình đồ vật quanh +0,43…+0,44.

   Nên khi đặt "tâm hình ở `san − 0,5·s`" thì đáy hình dừng ở `san − 0,068·s`: hình **treo trên
   mặt đất** một khoảng bằng 6,8% cỡ của nó, và bóng đổ vẽ ở `san + 0,03·s` lại nằm tách hẳn
   bên dưới. Hai thứ cùng nói "vật này không đứng trên nền".

   Đặt tên và dùng chung, thay vì để mỗi chỗ tự đoán một phân số — đó chính là cách hằng số
   0,5 lọt vào ba chỗ khác nhau mà không chỗ nào sai rõ ràng. */
export const DAY_HINH = 0.435;

/* ── VẬT NHỎ PHẢI VẼ NHỎ  (4/9/2026) ───────────────────────────────────────────────────────
   Sau khi phóng chủ thể lên 0,54·H (để nhân vật thôi bé như hình dán), soi khung DAY IN LIFE:
   **cái đồng hồ treo tường cao bằng nửa khung**, đè lên cả dãy nhà phía sau. Cùng một con số
   đúng cho người thì phi lý cho một vật cầm tay.

   Gốc: mọi biểu tượng dùng CHUNG một cỡ, tức mã đang giả định mọi vật to bằng nhau. Chữa
   không phải bằng cách hạ cỡ chung xuống — làm thế thì người lại bé như cũ.

   Phân loại theo KÍCH THƯỚC THẬT NGOÀI ĐỜI, không phải theo danh sách tuỳ ý:
     · vật to hơn người (xe buýt · máy bay · cá voi · nhà · Trái Đất) -> giữ nguyên, vì
       chính sự TO là thông điệp của mấy kênh ấy;
     · người -> 1,0, nó là thước đo;
     · vật cầm tay (đồng hồ · cốc · giấy · điện thoại · tiền · hộp) -> 0,58.
   Vật không khai thì mặc định 1,0: thà một vật hơi to còn hơn một vật biến mất, và danh sách
   này chỉ cần liệt kê ĐÚNG nhóm cầm tay. */
const _NHO = new Set(["dong_ho", "coc", "giay", "dien_thoai", "tien", "hop",
                      "nguyen_tu", "te_bao", "vi_khuan"]);
export const coHinh = (ten: string): number => (_NHO.has(ten) ? 0.58 : 1);

/* ══ TỈ LỆ THẬT CỦA HÌNH TRONG HỘP CỦA NÓ  (4/9/2026) ═══════════════════════════════════
   `BieuTuong` nhận một cỡ `s` và vẽ trong một hộp VUÔNG s×s. Nhưng không hình nào vuông, và
   hình người thì cao gấp ba lần rộng — đo trên chính toạ độ của `case "nguoi"`: đỉnh đầu ở
   −0,432·s, chân ở +0,435·s (= `DAY_HINH`), vai rộng ±0,105·s, kể cả tay dang thì ±0,15·s.
   Tức nó dùng **0,867 chiều cao hộp và 0,30 bề ngang hộp**.

   Hậu quả: chỗ gọi kẹp `s` bằng `min(trần_cao, trần_ngang)` như thể hình vuông, nên trần
   NGANG chặn trước và ghìm chiều cao xuống — nhân vật cao 30% khung trong khi chỉ rộng 19%.
   Đây là họ lỗi *một kích thước chịu hai ràng buộc mà công thức chỉ mã hoá một* đã ghi ở
   đầu tệp luật.

   Bảng này để chỗ gọi quy đổi được: cỡ hộp cần thiết để hình cao `h` là `h / cao`, và bề
   ngang hình khi ấy là `s × rong`. Chỉ khai hình đã ĐO; hình chưa đo mặc định 1,0×1,0 —
   tức giữ nguyên hành vi cũ, không đoán. Hình nào thấy còn nhỏ thì ĐO RỒI THÊM, đừng ước
   lượng: §13.7 đã trả giá sáu lần cho việc đoán một hằng số thay vì đo vật thật. */
export const TI_LE: Record<string, { cao: number; rong: number }> = {
  nguoi: { cao: 0.867, rong: 0.30 },
};
export const tiLe = (ten: string) => TI_LE[ten] || { cao: 1, rong: 1 };

export const _emChu = (s: string): number => {
  let e = 0;
  for (const c of s || "") {
    if (c === " ") e += 0.30;
    else if (".,:'’|".includes(c)) e += 0.30;
    else if (c === "1") e += 0.45;
    else if (c === "$") e += 0.60;
    else if (c >= "0" && c <= "9") e += 0.62;
    else if (c >= "a" && c <= "z") e += 0.60;
    else if ("MW".includes(c)) e += 0.95;
    else if ("IJ".includes(c)) e += 0.40;
    else if (c >= "A" && c <= "Z") e += 0.74;
    else e += 0.66;
  }
  return Math.max(e, 0.5);
};

export const NenPhong: React.FC<{ W: number; H: number; nen: string; mau: string;
                                  hat?: number; anTroi?: boolean; anCua?: boolean }> =
({ W, H, nen, mau, hat = 0, anTroi = false, anCua = false }) => {
  const k = Math.abs(hat) % 6;
  const yS = chanTroi(H, hat);            // nguồn sự thật duy nhất — xem `chanTroi`
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
  /* ── MÉP SÀN PHẢI ĐỦ SẪM CHO CHỮ TRẮNG ĐỌC ĐƯỢC  (3/9/2026) ─────────────────────────────
     Cổng `kiem_hinh` chấm bản dài HOW LOUD 84/100 với lý do *"tương phản phụ đề 2.6:1 < 4,5:1
     (chuẩn WCAG AA)"*. Đo pixel dải phụ đề ở năm mốc: sáng TB **133–184**, tương phản với chữ
     trắng **2,0–3,7:1** — dưới chuẩn ở MỌI mốc.

     Anh đã bảo bỏ tấm che đen (*"ko làm bóng mờ đen thế nha xấu"*), nên không đắp lại một lớp
     phủ. Thứ đúng là làm chính SÀN sẫm dần về mép dưới — sàn thật của một căn phòng vẫn sẫm ở
     mép gần, nên nó đọc ra bóng sàn chứ không ra tấm kính.

     Để đạt 4,5:1 với chữ trắng thì nền phải xuống dưới ~118/255. `-0.34` cho ra 133–184; cần
     sẫm hơn nữa ở ĐÁY, nên thêm một chặng thứ ba trong dải chuyển chỉ ở 18% cuối — phần trên
     của sàn giữ nguyên độ sáng để căn phòng không tối đi. */
  const sanD = _pha(_tron(nen, mau, 0.26), -0.34);
  // -0,70 và chặng bắt đầu ở 0,55: đo lần đầu (-0,62 / 0,62) cho 4,31–5,44:1, tức một
  // trong ba mốc vẫn hụt chuẩn 4,5. Hiệu chỉnh theo SỐ ĐO, không theo cảm giác (§13.7).
  // −0,70 → −0,22, cùng lý do và cùng lượt sửa với `CanhVe._bang.sanDay`: xem chú thích ở
  // đó. Hai nền phải đi CÙNG MỨC, nếu không thì một tập có hai độ sáng đáy khác nhau và
  // mắt đọc ra "chắp vá" ở đúng chỗ phụ đề đứng.
  const sanDay = _pha(_tron(nen, mau, 0.34), -0.22);
  const vach = _pha(mau, -0.55);
  const id = `np${Math.round(W)}_${k}`;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id={`${id}t`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={tuong} /><stop offset="1" stopColor={tuongD} />
        </linearGradient>
        <linearGradient id={`${id}s`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={san} />
          <stop offset="0.55" stopColor={sanD} />
          <stop offset="1" stopColor={sanDay} />
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

      {/* ── KHUNG CỬA SỔ PHẢI Ở SAU, KHÔNG Ở GIỮA  (3/9/2026) ─────────────────────────────
          Bản đầu vẽ khung cửa rộng 0,40·W đặt ngay tại nguồn sáng `xS`, độ mờ 0,30. Với nhịp
          `canh` (một chủ thể đứng giữa) thì nó đọc đúng là cửa sổ. Nhưng `NenPhong` là mặt sàn
          DÙNG CHUNG, nên nó cũng nằm dưới biểu đồ và khuôn so sánh — và ở đó soi lưới thấy
          **một hình chữ nhật rỗng lơ lửng** ôm lấy cột hoặc ôm lấy biểu tượng, đọc ra một cái
          hộp vô nghĩa chứ không ra cửa sổ.
          Đúng họ lỗi §12.5: một chi tiết đúng trong ngữ cảnh nó sinh ra, sai ở ngữ cảnh mới.
          Chữa: đẩy về GÓC đối diện nguồn sáng và làm mờ hẳn — đủ nói "trong nhà có ánh sáng
          ngoài", không đủ tranh chỗ với bất cứ thứ gì vẽ đè lên. */}
      {/* `!anCua`: khung đã có chủ thể toàn khung thì BỎ HẲN cửa sổ. Bản trước chỉ đẩy nó
          về góc và làm mờ — vẫn còn một hình chữ nhật đứng sau nhân vật, và nó không nói gì
          về câu đang kể vì `NenPhong` chạy cho 222/264 nhịp `canh` KHÔNG có nơi chốn nào.
          Một bối cảnh không liên quan thì không phải bối cảnh, nó là nhiễu. */}
      {(!anCua && (k === 0 || k === 5)) ? (() => {
        const xC = xS < W * 0.5 ? W * 0.62 : W * 0.08;   // luôn ở phía ĐỐI DIỆN quầng sáng
        const wC = W * 0.30, hC = yS * 0.34, yC = yS * 0.09;
        return (
          <g opacity={0.55}>
            {/* MẢNG SÁNG, KHÔNG PHẢI KHUNG VIỀN.
                Hai bản trước vẽ cửa sổ bằng nét viền rỗng. Soi lưới ba lần đều đọc ra **một
                hình chữ nhật trống** nằm sau đồ hoạ, không đọc ra cửa sổ — kể cả sau khi làm
                mờ và đẩy về góc. Vấn đề không phải độ mờ hay vị trí mà là CHẤT: trong tranh
                phẳng, cửa sổ nhận ra được nhờ mảng sáng KHÁC MÀU TƯỜNG, không nhờ đường bao.
                Mọi ảnh tham chiếu anh gửi đều vẽ cửa sổ như thế.
                Cùng bài học với con hươu (§15.9) và với số chương (§15.11): khi một hình sửa
                hai lần vẫn không đọc ra, thứ sai là CÁCH VẼ nó, không phải tham số. */}
            <rect x={xC} y={yC} width={wC} height={hC} rx={H * 0.008}
                  fill={_pha(tuong, 0.30)} />
            <line x1={xC + wC / 2} y1={yC} x2={xC + wC / 2} y2={yC + hC}
                  stroke={_pha(tuong, -0.10)} strokeWidth={Math.max(2, H * 0.004)} />
            <line x1={xC} y1={yC + hC * 0.5} x2={xC + wC} y2={yC + hC * 0.5}
                  stroke={_pha(tuong, -0.10)} strokeWidth={Math.max(2, H * 0.004)} />
          </g>
        );
      })() : null}

      {/* kiểu 2: đường gờ tường ngang — nhịp thị giác, không phải đồ đạc */}
      {k === 2 ? (
        <rect x={0} y={yS * 0.70} width={W} height={Math.max(2, H * 0.004)} fill={vach} opacity={0.22} />
      ) : null}

      <rect x={0} y={yS} width={W} height={H - yS} fill={`url(#${id}s)`} />
      {/* ── ẨN CHÂN TRỜI KHI KHUÔN CÓ TRỤC RIÊNG  (4/9/2026) ─────────────────────────────
          Rà soát tìm ra bốn "mặt sàn" cùng tồn tại: phòng 0,73·H · chủ thể 0,66·H · biểu đồ
          0,64·H · so sánh tỉ lệ 0,48·H. Phản xạ đầu là ép cả ba lớp kia xuống sàn phòng — em
          đã thử và SAI hai lần: phép quy đổi giữa hai hệ `H` và `H*0,80` nhầm, và quan trọng
          hơn là ép xuống thì **không còn chỗ cho nhãn dưới trục**.
          Gốc không phải mặt sàn lệch, mà là HAI ĐƯỜNG SÀN CÙNG HIỆN: biểu đồ đã có trục riêng
          làm mặt đất, phòng lại vẽ thêm một vạch chân trời ở độ cao khác. Mắt thấy hai đường
          ngang thì đọc ra "chắp vá", chứ không đọc ra vật lơ lửng.
          Nên: khuôn nào tự mang mặt đất (biểu đồ · so sánh · đếm) thì phòng chỉ giữ tường và
          quầng sáng, bỏ vạch chân trời và bỏ luôn mảng sàn sẫm. */}
      {anTroi ? null : (
        <rect x={0} y={yS} width={W} height={Math.max(2, H * 0.0035)} fill={vach} opacity={0.34} />
      )}

      {/* bóng tiếp đất mềm ngay dưới chân trời — đồ hoạ đè lên sẽ như đứng trên sàn, không lơ lửng */}
      <ellipse cx={W / 2} cy={yS + H * 0.012} rx={W * 0.40} ry={H * 0.022} fill="#000000" opacity={0.07} />
    </svg>
  );
};

export const ChiaDoi: React.FC<{
  W: number; H: number; trai: any; phai: any; mau: string; p: number;
  nen?: string; hat?: number; hatTap?: number;
}> = ({ W, H, trai, phai, mau, p, nen = "#F2F0EA", hat = 0, hatTap = 0 }) => {
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
  /* `kk` nuôi bo góc và độ đậm tấm nền — nó phải đổi theo TẬP, nên đọc `hatTap` chứ không đọc
     `hat` (chỗ gọi đang dùng `hat` để truyền CHỈ SỐ BỐ CỤC). Hai khái niệm khác hẳn nhau dùng
     chung một con số thì cả hai cùng sai: tấm nền hết đổi theo tập, và biến thể `rx` nhỏ nhất
     không bao giờ đạt tới vì nhánh dùng `kk` chỉ chạy khi bố cục thuộc {0, 2}. */
  const kk = Math.abs(hatTap) % 3;

  /* ── BA BỐ CỤC SO SÁNH  (3/9/2026) ──────────────────────────────────────────────────────
     Anh: *"2 loại này a thấy xấu nhàm chán mà nó cứ lặp đi lặp lại cùng 1 motip hoài."* Khuôn
     so sánh là loại thứ hai. Trước bản này nó luôn là: hai cột, một vạch đứt ở giữa, nhãn trên
     — hình đúng nhưng mọi tập của mọi kênh đều đúng một hình ấy.

       0  hai cột, vạch đứt         — bố cục gốc, mạnh và rõ, giữ làm mặc định
       1  trên/dưới                 — vạch nằm ngang; ở khung dọc 9:16 đây mới là bố cục tự
                                      nhiên, vì hai vế được cả bề ngang thay vì nửa
       2  THEO TỈ LỆ                — hai hình đứng chung một mặt sàn, CỠ TỈ LỆ VỚI SỐ, không
                                      có vạch ngăn. Đây là bố cục nói được điều mà hai cột bằng
                                      nhau không nói: sự chênh lệch thành thứ NHÌN THẤY được,
                                      không phải thứ đọc ra từ hai con số.

     Bố cục 2 cần số đọc được ở CẢ HAI vế và hai số phải khác nhau — không thì nó rơi về 0.
     Cấp một bố cục cho dữ liệu không đỡ nổi nó là cách chắc chắn để ra một khung vô nghĩa
     (đúng bài học biểu đồ bốn cột số 0 sáng nay). */
  const _num = (t: string): number | null => {
    const m = /(-?)\s*\$?\s*([\d][\d,\.]*)\s*([kK]|[mM]|[bB][nN]?)?(?![A-Za-z])/.exec(String(t || ""));
    if (!m) return null;
    const v = parseFloat(m[2].replace(/,/g, ""));
    if (!isFinite(v)) return null;
    const he: any = { k: 1e3, m: 1e6, b: 1e9, bn: 1e9 };
    return (m[1] ? -1 : 1) * v * (he[(m[3] || "").toLowerCase()] || 1);
  };
  const vT = _num(trai.so), vP = _num(phai.so);
  let k3 = Math.abs(hat) % 3;
  if (k3 === 2 && !(vT !== null && vP !== null && Math.abs(vT) !== Math.abs(vP)
                    && Math.abs(vT) > 0 && Math.abs(vP) > 0)) k3 = 0;

  if (k3 === 2) {
    const mx = Math.max(Math.abs(vT as number), Math.abs(vP as number));
    /* CĂN BẬC HAI, không tuyến tính: mắt so DIỆN TÍCH chứ không so chiều cao, nên tỉ lệ thẳng
       làm vế nhỏ biến mất khi chênh nhau trăm lần. Sàn 0,26 để vế nhỏ còn nhận ra được là cái
       gì — dưới mức ấy nó thành một chấm và người xem đọc ra "thiếu hình". */
    /* SÀN 0,34 chứ không 0,26. Soi khung HOW BIG (hươu 18 ft cạnh cây đỏ 350 ft): tỉ lệ căn
       bậc hai cho 0,23 nên rơi về sàn 0,26, và ở cỡ ấy con hươu ra một sợi không nhận ra là con
       gì. Sàn tồn tại để vế nhỏ còn ĐỌC ĐƯỢC là cái gì — 0,26 chưa đủ cho việc ấy.
       Đây vẫn là đánh đổi có ý thức: sàn càng cao thì chênh lệch càng bị nói dối bớt. 0,34 là
       mức thấp nhất mà biểu tượng còn nhận ra được ở khung điện thoại. */
    const co = (v: number) => Math.max(0.34, Math.sqrt(Math.abs(v) / mx));
    const sMax = Math.min(H * 0.46, W * 0.30);
    /* 0,60 chứ không 0,66: khối nhãn+số chiếm tới `san + 0,19·H`, và ở 0,66 nó rơi đúng vào
       đường chân trời của `NenPhong` (0,73·H khung đầy) — chữ nằm vắt ngang chỗ tường đổi sang
       sàn, nửa trên một nền nửa dưới một nền khác. Mặt sàn của bố cục này phải nằm CAO HƠN mặt
       sàn của căn phòng, không trùng nó. */
    const san = H * 0.60;
    const ve = (d: any, v: number, x: number, tre: number) => {
      const qq = Math.max(0, Math.min(1, (p - tre) / 0.3));
      const sz = sMax * co(v) * (0.90 + qq * 0.10);
      return (
        <g opacity={qq}>
          {/* ── CÙNG LỖI LƠ LỬNG, NHÁNH SONG SONG  (4/9/2026) ───────────────────────────
              Sáng nay em chữa "vật treo trên mặt đất" ở hai chỗ (`SoLieu` và lớp cảnh của
              `KichGiaiThich`) rồi dừng. Rà lại MỌI chỗ vẽ biểu tượng thì còn đúng chỗ này:
              cùng công thức `san − sz*0,5` (đáy hình thật ở 0,435 nên vật treo 0,068·sz) và
              cùng cái bóng đặt DƯỚI mặt sàn (`san + 0,035·sz`) — chân với bóng cách nhau
              0,103·sz.

              Hai chỗ còn lại (`ChiaDoi` bố cục căn giữa và `KinhLup`) KHÔNG có mặt sàn, nên
              `0,5` ở đó là phép căn giữa đúng, không phải cùng lỗi. Ghi ra để lần sau khỏi
              "sửa cho đều" rồi làm lệch hai khuôn đang đúng.

              Đây đúng họ lỗi §6 mà dự án vấp nhiều lần — và lần này người vá một nhánh rồi
              bỏ nhánh song song chính là em. */}
          <ellipse cx={x} cy={san} rx={sz * 0.40} ry={H * 0.014}
                   fill="#000000" opacity={0.13} />
          <g transform={`translate(${x} ${san - sz * DAY_HINH})`}><BieuTuong ten={d.bt || ""} s={sz} /></g>
          {/* KHOẢNG CÁCH TÍNH TỪ CỠ CHỮ, KHÔNG TỪ MỘT PHÂN SỐ CỐ ĐỊNH.
              Bản đầu đặt nhãn ở `san + 0,075·H` và số ở `san + 0,150·H` — nghe như cách nhau
              đủ, nhưng số cao tới 0,082·H nên đỉnh nó (0,150 − 0,082 = 0,068) nằm TRÊN chân
              nhãn (0,075). Hai dòng đè nhau, và chỉ soi khung mới thấy.
              Đúng họ lỗi đã trả giá ở `SoLieu` sáng nay: khoảng cách giữa hai dòng chữ phải
              suy ra từ CHIỀU CAO CHỮ, không phải từ hai phân số đặt tay cạnh nhau. */}
          {(() => {
            const cN = Math.min(H * 0.046, (W * 0.40 / Math.max(1, (d.nhan || "").length)) * 1.5);
            const cS = Math.min(H * 0.078, (W * 0.42 / Math.max(1, (d.so || "").length)) * 1.55);
            const yN = san + H * 0.070 + cN;
            return (
              <>
                <text x={x} y={yN} textAnchor="middle" fontFamily={F} fontWeight={900}
                      fontSize={cN} fill="#2C2722" letterSpacing={1}>{(d.nhan || "").toUpperCase()}</text>
                <text x={x} y={yN + cS * 1.18} textAnchor="middle" fontFamily={F} fontWeight={900}
                      fontSize={cS} fill={mau}>{d.so}</text>
              </>
            );
          })()}
        </g>
      );
    };
    return (
      <g>
        <line x1={W * 0.05} y1={san} x2={W * 0.95} y2={san}
              stroke={_pha(nen, -0.30)} strokeWidth={Math.max(2, H * 0.003)} />
        {ve(trai, vT as number, W * 0.27, 0)}
        {ve(phai, vP as number, W * 0.73, 0.16)}
      </g>
    );
  }

  if (k3 === 1) {
    /* TRÊN / DƯỚI — vạch nằm ngang. Mỗi vế được CẢ bề ngang, nên nhãn dài và số dài không còn
       phải thu nhỏ; đây là lý do thật để có bố cục này, không chỉ để đổi hình. */
    const ngan = (d: any, y: number, tre: number) => {
      const qq = Math.max(0, Math.min(1, (p - tre) / 0.3));
      const sz = Math.min(H * 0.20, W * 0.15);
      return (
        <g opacity={qq}>
          <text x={W * 0.09} y={y + H * 0.015} fontFamily={F} fontWeight={900}
                fontSize={Math.min(H * 0.052, (W * 0.34 / Math.max(1, (d.nhan || "").length)) * 1.5)}
                fill="#2C2722" letterSpacing={1}>{(d.nhan || "").toUpperCase()}</text>
          <g transform={`translate(${W * 0.50} ${y})`}><BieuTuong ten={d.bt || ""} s={sz} /></g>
          <text x={W * 0.91} y={y + H * 0.030} textAnchor="end" fontFamily={F} fontWeight={900}
                fontSize={Math.min(H * 0.095, (W * 0.34 / Math.max(1, (d.so || "").length)) * 1.55)}
                fill={mau}>{d.so}</text>
        </g>
      );
    };
    return (
      <g>
        {[0, 1].map((j) => (
          <rect key={`h${j}`} x={W * 0.03} y={H * (j ? 0.505 : 0.075)} width={W * 0.94} height={H * 0.40}
                rx={W * 0.010} fill={_tron(nen, mau, j ? 0.13 : 0.05)}
                opacity={0.86 * Math.min(1, p / 0.35)} />
        ))}
        {ngan(trai, H * 0.275, 0)}
        <line x1={W * 0.09} y1={H * 0.4875} x2={W * (0.09 + 0.82 * Math.min(1, p / 0.5))} y2={H * 0.4875}
              stroke="#2C2722" strokeWidth={Math.max(3, H * 0.005)}
              strokeDasharray={`${H * 0.03} ${H * 0.022}`} />
        {ngan(phai, H * 0.705, 0.16)}
      </g>
    );
  }

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
  tren_anh?: boolean; nen?: string; bo?: number; kieu?: number; san?: number;
}> = ({ W, H, so, don, chu, bt, mau, p, tren_anh = false, nen = "#EFE7D6", bo = 0, kieu = 0,
        san = 0 }) => {
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
  /* Bố cục DẢI MÀU: chú thích phải nằm HẲN DƯỚI dải, không nửa trong nửa ngoài. Dải cao
     0,25·H (0,30 ở khung ngang) và tâm ở `yCao`, nên mép dưới ở `yCao + 0,13`. Soi khung ODDS:
     dòng "trying once every day" rơi đúng mép dải — nửa trên nằm trên nền màu kênh, nửa dưới
     trên nền phòng, và cả hai nửa đều khó đọc vì màu chữ chỉ chọn được cho MỘT nền. */
  const yChuMin = ngang ? 0.33 : (tren_anh ? 0.37 : 0.44);
  const q = Math.min(1, p / 0.28);
  /* Cùng lỗi với `ChiaDoi`, và thêm một lỗi nữa: biểu tượng đặt ở `H*0.62` còn con số ở
     `H*0.30` với cỡ `H*0.20` — hai lớp cùng chọn chỗ theo H mà không biết nhau, nên số "9"
     nằm đè lên cái biểu tượng. Nay biểu tượng bám ĐÁY khung và số bám ĐỈNH, không gặp nhau. */
  /* ── BỐN BỐ CỤC, KHÔNG PHẢI BA LẦN DỊCH CHỖ  (3/9/2026) ────────────────────────────────
     Đo phân bố khuôn trên 18 kênh × 3 tập: `so_lieu` chiếm **29% tổng số nhịp** — gần một phần
     ba mọi video là khuôn này. Nó là khuôn xuất hiện nhiều nhất sau `canh`.

     Ba biến thể `bo` đang có chỉ đổi CỠ và CHỖ ĐẶT của cùng một bố cục: số ở giữa trên, đơn vị
     dưới số, hình dưới nữa. Người xem nhận ra BỐ CỤC (§15.1) — ba lần dịch chỗ vẫn đọc ra một
     mô-típ, đúng lời anh phê về thẻ chương.

       0  giữa           số canh giữa, hình bên dưới — mạnh nhất, mặc định
       1  canh trái      số canh trái, hình dạt sang phải — khuôn tạp chí; dùng được CẢ trên ảnh
       2  dải màu        số nằm trong dải màu kênh vắt ngang, hình đứng trên sàn bên dưới
       3  số làm nền     số khổng lồ mờ phía sau, hình đứng trước — trọng tâm là HÌNH, không số

     Kiểu 2 và 3 đổi hẳn nền nên chỉ dùng khi KHÔNG có ảnh; trên ảnh chúng sẽ đánh nhau với bức
     hình và với dải mờ. Kiểu 1 an toàn trên ảnh vì dải mờ vốn phủ hết bề ngang.
     Cấp một bố cục cho ngữ cảnh không đỡ nổi nó là cách chắc chắn ra khung hỏng — cùng bài học
     với biểu đồ bốn cột số 0. */
  const kA = tren_anh ? (Math.abs(kieu) % 4 === 1 ? 1 : 0) : (Math.abs(kieu) % 4);
  // Canh trái chỉ có 0,80·W cho chữ số (chừa chỗ cho hình bên phải); giữa thì được 0,88·W.
  const beNgang = kA === 1 ? 0.62 : kA === 3 ? 0.96 : 0.88;
  const cs = Math.min(H * cCao * (kA === 3 ? 1.35 : 1), (W * beNgang) / _emChu(so));
  // đáy dòng đơn vị = yCao·H + cs·0.56 ; chừa thêm 0,5·cs rồi mới đặt chú thích
  /* `cd` khai sau `yChu` trong bản cũ, nên `yChu` không thể cộng nó vào và đành dùng `cs*0.56`
     — chính con số vừa sai ở dòng đơn vị. Nâng khai báo `cd` lên đây để CẢ HAI chỗ dùng cùng
     một công thức; hai chỗ tính khoảng cách cho cùng một chồng chữ mà dùng hai công thức khác
     nhau thì sớm muộn chúng lệch nhau (§15.10, lần thứ tư). */
  const cd = Math.min(H * 0.055, (W * 0.80 / Math.max(1, (don || "").length)) * 1.7);
  const yDon = cs * 0.22 + cd * 1.05;                    // chân dòng đơn vị, so với chân số
  const cChu = Math.min(H * 0.042, (W * 0.90 / Math.max(1, (chu || "").length)) * 1.45);
  const yChu = Math.max(kA === 2 ? yCao + (ngang ? 0.16 : 0.14) + cChu / H : yChuMin,
                        (H * yCao + yDon + cChu * 1.15) / H);
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
      {/* Kiểu 2 — DẢI MÀU ôm lấy khối số. Căn phòng vẫn thấy trên và dưới dải, nên khuôn này
          là chỗ nghỉ mắt giữa những khuôn tràn nền. */}
      {kA === 2 ? (() => {
        /* ── DẢI PHẢI PHỦ TỚI DÒNG CHÚ THÍCH  (4/9/2026) ────────────────────────────────
           Chiều cao dải là một HẰNG SỐ (0,25·H), còn `yChu` thì tính ra — nên dòng chú
           thích rơi xuống DƯỚI mép dải bất cứ khi nào nó dài hoặc số cao. Soi khung
           REAL COST: *"assuming a 7% annual return"* chạy xuyên qua dãy nhà phía sau, đúng
           lời anh phê về chồng chéo.
           Đây là họ lỗi đã trả giá ba lần trong hai ngày: *hai phân số cố định đặt cạnh
           nhau không mã hoá được quan hệ "cái này nằm trong cái kia"* (§15.10). Nay đáy dải
           SUY TỪ `yChu` — dải luôn ôm trọn thứ nó phải ôm, dù số cao hay chú thích dài. */
        const dTren = yCao - (ngang ? 0.15 : 0.12);
        const dDuoi = (chu ? yChu + cChu / H * 0.55 : yCao + (ngang ? 0.15 : 0.13)) + 0.022;
        return (
          <rect x={0} y={H * dTren} width={W}
                height={H * Math.max(ngang ? 0.30 : 0.25, dDuoi - dTren)} fill={mau}
                opacity={0.94 * Math.min(1, p / 0.3)} />
        );
      })() : null}
      {/* Kiểu 3 — SỐ LÀM NỀN: chữ số chiếm gần hết khung ở độ mờ thấp, HÌNH đứng trước và là
          thứ mắt đọc trước. Đảo hẳn thứ bậc so với ba kiểu kia, nên nó là biến thể khác nhất. */}
      {kA === 3 ? (
        <text x={W / 2} y={H * (ngang ? 0.58 : 0.52)} textAnchor="middle" fontFamily={F}
              fontWeight={900}
              /* Số nền phải VỪA KHUNG. `cs*1,55` bỏ qua bề ngang, nên `100` của SPEED OF và
                 `360,000,000` của RIGHT NOW đều bị cắt mất mép phải — soi lưới thấy ngay.
                 `cs` vốn đã chịu ràng buộc bề ngang ở `beNgang`, nhưng nhân 1,55 thì phá mất
                 ràng buộc ấy. Ràng buộc phải áp SAU mọi phép nhân, không phải trước. */
              /* 4/9 — bề ngang đo theo TỪNG KÝ TỰ (`_emChu`), và trần 0,90·W chứ không 0,98:
                 chữ nền là thứ chạm mép đầu tiên nên nó cần lề, không cần sát mép. */
              fontSize={Math.min(cs * 1.55, (W * 0.90) / _emChu(soHien))}
              /* ĐỘ MỜ THEO CÁI NÓ NẰM TRÊN. 0,16 cố định là con số của một nền phẳng sáng;
                 đặt trên một ảnh CF nhiều chi tiết thì nó tan vào ảnh và đọc ra một VẾT BẨN,
                 không đọc ra một con số (§15.11 — phóng to hai lần vẫn không đọc được thì
                 thứ sai là VAI của nó, ở đây là độ tương phản). Trên ảnh thì đậm hơn. */
              fill={mau} opacity={(tren_anh ? 0.30 : 0.20) * q}>{soHien}</text>
      ) : null}
      {/* ── CHÂN PHẢI CHẠM SÀN, KHÔNG ĐỨNG Ở PHÂN SỐ CỐ ĐỊNH  (4/9/2026) ────────────────
          Anh: *"người ko lơ lửng nha."* Đo trên khung HOW LONG vừa dựng, bằng pixel:

              nét nhân vật  y = 0,407·H … 0,616·H
              mặt sàn       y = 0,727·H       -> **lơ lửng 0,111·H = 213 pixel**

          Gốc rễ không phải một con số sai mà là HAI HỆ QUY CHIẾU: `KichGiaiThich` dựng khuôn
          này bằng `<SoLieu H={H * 0.80}>`, nên mọi phân số bên trong đây tính trên 80% khung.
          `0,64` ở đây rơi vào `0,80 × 0,64 = 0,512·H` của khung thật — đúng chỗ đo được — còn
          `chanTroi()` trả `0,73·H` của khung THẬT. Hai lớp cùng chọn chỗ theo "H" mà "H" của
          chúng là hai thứ khác nhau, nên không ai lệch mà hình vẫn lơ lửng.

          Đúng họ lỗi §6 *chép hằng số sang hệ quy chiếu khác*: không báo lỗi, chỉ làm hình sai.

          Nay `KichGiaiThich` truyền THẲNG mặt sàn (đã quy đổi về hệ của khuôn này) và biểu
          tượng neo ĐÁY vào đó. Thiếu `san` thì giữ nguyên nếp cũ — khuôn này còn dùng ở chỗ
          không có mặt đất. */}
      {bt ? <g transform={`translate(${kA === 1 ? W * 0.76 : W / 2} ${
              san > 0 ? san - (tren_anh ? Math.min(H * 0.26, W * 0.28)
                               : (kA === 1 ? Math.min(H * 0.32, W * 0.42)
                                           : Math.min(H * 0.40, W * 0.66))) * DAY_HINH
                      : H * (ngang ? 0.62 : tren_anh ? 0.70 : 0.64)})`}
             opacity={tren_anh ? 0.92 : 1}>
        {/* CỠ BIỂU TƯỢNG THEO VAI TRÒ, không một cỡ cho hai vai trò khác nhau.
            Trên ảnh, biểu tượng chỉ là phụ chú -> nhỏ là đúng. KHÔNG có ảnh thì biểu tượng LÀ
            hình của cả khung, và cỡ 0,30 cho ra khung 60% trống (soi `howmuch` nhịp 0). Ảnh
            tham chiếu anh gửi đều có chủ thể chiếm quá nửa khung. */}
        {/* Bố cục canh trái đẩy hình sang x = 0,76·W, nên bề ngang còn lại chỉ 0,48·W. Giữ cỡ
            0,66·W thì hình TRÀN khỏi mép phải — soi khung WHAT IF thấy cái hộp bị cắt đôi.
            Cỡ biểu tượng phải theo CHỖ NÓ ĐỨNG, không phải theo cả khung. */}
        <BieuTuong ten={bt} s={(tren_anh ? Math.min(H * 0.26, W * 0.28)
                              : (kA === 1 ? Math.min(H * 0.32, W * 0.42)
                                          : Math.min(H * 0.40, W * 0.66))) * coHinh(bt)} /></g> : null}
      {/* Kiểu 3 vẽ số ở lớp NỀN phía trên rồi, nên ở đây bỏ khối số đi — vẽ hai lần thì con
          số đậm chồng lên chính bóng mờ của nó. */}
      <g transform={`translate(${kA === 1 ? W * 0.08 : W / 2} ${H * yCao}) scale(${0.86 + q * 0.14})`}
         opacity={kA === 3 ? 0 : q}>
        <text x="0" y="0" textAnchor={kA === 1 ? "start" : "middle"} fontFamily={F} fontWeight={900}
              fontSize={cs}
              fill={tren_anh ? "#FFFFFF" : (kA === 2 ? chuHopNen("#FFFFFF", mau) : "#2C2722")}
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
        {/* ── KHOẢNG CÁCH PHẢI CỘNG CỠ CỦA CHÍNH DÒNG DƯỚI  (3/9/2026) ─────────────────────
            `cs * 0.56` chỉ tính theo cỡ CON SỐ. Ở bố cục canh trái, bề ngang cho chữ số hẹp hơn
            (0,62·W thay vì 0,88·W) nên số dài làm `cs` co lại còn ~85px, trong khi dòng đơn vị
            `cd` vẫn ~69px — đỉnh nó ở 0,56·85 − 69 = **−21px**, tức NẰM TRÊN chân con số.
            Soi khung WHAT IF: `8,000,000,000` và `PEOPLE` đè lên nhau.

            Đây là lần thứ TƯ cùng một lỗi (§15.10): hai dòng chữ đặt cạnh nhau bằng một phân số
            của dòng TRÊN, mà quan hệ "dòng này nằm dưới dòng kia" cần cỡ của CẢ HAI. Nay cộng
            `cd` vào, nên công thức đúng ở mọi tổ hợp cỡ. */}
        {don ? <text x="0" y={yDon} textAnchor={kA === 1 ? "start" : "middle"} fontFamily={F} fontWeight={800}
                     fontSize={cd}
                     fill={tren_anh ? "#F2EFE9" : (kA === 2 ? chuHopNen("#F2EFE9", mau) : chuHopNen(mau, nen))}
                     letterSpacing={2}
                     style={{ filter: tren_anh
                       ? `drop-shadow(0 0 ${H * 0.016}px #000000ee) drop-shadow(0 ${H*0.004}px ${H*0.010}px #000000cc)`
                       : `drop-shadow(0 ${H*0.003}px ${H*0.009}px #00000099)` }}
                     >{don.toUpperCase()}</text> : null}
      </g>
      {chu ? <text x={kA === 1 ? W * 0.08 : W / 2} y={H * yChu}
                   textAnchor={kA === 1 ? "start" : "middle"} fontFamily={F} fontWeight={700}
                   fontSize={cChu}
                   fill={tren_anh ? "#EDE9E1" : chuHopNen("#3A342C", nen)}
                   /* BÓNG MỀM CẢ KHI KHÔNG NẰM TRÊN ẢNH. Nhánh `undefined` cũ giả định nền
                      dưới chú thích luôn phẳng — sai từ lúc có cảnh vẽ bằng code: dãy nhà,
                      cây, bàn ghế đều nằm ngay dưới dòng này. Bóng nhẹ hơn nhánh ảnh, đủ
                      tách chữ khỏi nét sau lưng mà không thành viền cứng (§12.12). */
                   style={{ filter: tren_anh
                     ? `drop-shadow(0 0 ${H * 0.015}px #000000ee) drop-shadow(0 ${H * 0.004}px ${H * 0.011}px #000000cc)`
                     : `drop-shadow(0 ${H * 0.003}px ${H * 0.009}px #00000088)` }}>{chu}</text> : null}
    </g>
  );
};

/* ── KHUÔN 4: TRỤC ────────────────────────────────────────────────────────────────────────
   Trục thời gian hoặc trục khoảng cách. Mũi tên chạy DẦN theo `p`, và cái chấm sáng dừng ở
   đúng chỗ lời kể đang nói. Không có cái chấm ấy thì trục chỉ là hình trang trí. */
/* ── TRỤC — NẰM NGANG Ở 16:9, ĐỨNG Ở 9:16  (nâng cấp 3/9/2026) ─────────────────────────────
   Soi khung WHERE GOES bản dọc: bốn mốc `bin · truck · sorting · end` với cỡ chữ ghi cứng
   `H·0,055`. Ở khung dọc, `H` của vùng vẽ là 1536 nên mỗi nhãn cao 84px và rộng tới ~340px,
   trong khi bề ngang chia đều chỉ cho mỗi mốc 270px. Kết quả: **`truck` và `sorting` dính vào
   nhau thành `trucksorting`**, và trục nằm ở một phần ba trên với 60% khung trống bên dưới.

   Hai lỗi, một gốc: **cỡ chữ tính theo `H` trong khi chỗ chứa nó là `W`.** Đúng họ lỗi *một
   kích thước chịu hai ràng buộc mà công thức chỉ mã hoá một* (§6) — lần thứ tư trong tệp này.

   Chữa hai tầng, vì hai tầng giải hai việc khác nhau:
     · cỡ chữ luôn phải chịu CẢ chiều cao lẫn bề rộng cột
     · khung DỌC thì xoay trục thành ĐỨNG — mỗi mốc được cả bề ngang, và trục dùng đúng cái
       chiều mà khung dọc đang thừa. Không phải để đổi hình cho vui: nó là hướng tự nhiên của
       một dòng thời gian trên điện thoại. */
export const Truc: React.FC<{
  W: number; H: number; moc: { nhan: string; phu?: string }[]; vt: number; mau: string; p: number;
}> = ({ W, H, moc, vt, mau, p }) => {
  /* Trục hiện xong trong 35% thời lượng cảnh, không phải 55%. Ở nhịp 1,6 giây thì 55% là
     0,9 giây — cảnh gần hết mà trục mới vẽ xong, người xem không kịp đọc mốc cuối. */
  const ch = Math.min(1, p / 0.35);
  const n = Math.max(3, Math.min(W, H) * 0.007);
  const doc = H > W * 1.2;
  const so = Math.max(1, moc.length);
  /* ── `vt` LÀ CHỈ SỐ, KHÔNG PHẢI PHÂN SỐ  (4/9/2026) ──────────────────────────────────
     Python ghi `vt = len(moc) - 1` — tức chỉ số của mốc đang nói tới. Engine dùng thẳng nó
     làm hệ số: `cy = y0 + (y1 - y0) * vt`. Với trục 3 mốc, `vt = 2` đẩy chấm xuống **gấp
     đôi chiều dài trục**, tức RA NGOÀI KHUNG — chấm nhấn biến mất hoàn toàn.
     Không lộ ra suốt vì trục cũ gần như luôn có ĐÚNG HAI mốc: `vt = 1` thì công thức sai
     ấy tình cờ cho ra đúng đáy trục. Sáng nay em hạ sàn xuống 3 mốc, và cùng lúc làm lộ
     lỗi này — mốc thứ ba không bao giờ được nhấn.
     Đúng họ lỗi *mượn giá trị cho việc nó không sinh ra để làm*: một chỉ số bị đọc thành
     một tỉ lệ, và hai thứ ấy trùng nhau đúng ở n = 2. */
  const fv = so > 1 ? Math.max(0, Math.min(1, vt / (so - 1))) : 0.5;

  if (doc) {
    /* ── TRỤC DỌC ĐANG BỎ TRỐNG BA PHẦN TƯ KHUNG  (4/9/2026) ──────────────────────────
       Đo tỉ lệ mực phủ vùng nội dung trên 90 khung của 6 clip: trung vị 26,8%, và **bốn
       trong sáu khung trống nhất đều là khuôn này**, thấp tới 3,9%. Đường trục nằm ở
       `W*0.26` với hai ba nhãn ngắn bên phải, còn lại là nền trơn.
       Ba việc, không việc nào đụng tới nghĩa của trục:
         · trục dịch sang trái (0,26 -> 0,18) để phần đọc được rộng ra
         · mỗi mốc kéo một ĐƯỜNG DẪN mảnh sang mép phải — vừa lấp dọc vừa giúp mắt bám
           mốc, đúng cách bảng số liệu in vẫn làm
         · cỡ chữ trần 0,042·H -> 0,058·H; nhãn hai ba chữ ở cỡ cũ đọc ra như chú thích
       Không thêm hình mới: `moc` không mang biểu tượng, bịa ra một cái là bịa dữ liệu. */
    const y0 = H * 0.10, y1 = H * 0.80, x = W * 0.18;
    const oCao = (y1 - y0) / Math.max(1, so - 1 || 1);
    const cN = (t: string) => Math.min(H * 0.058, oCao * 0.52,
                                       (W * 0.70 / Math.max(1, t.length)) * 1.55);
    return (
      <g>
        <line x1={x} y1={y0} x2={x} y2={y0 + (y1 - y0) * ch} stroke="#2C2722" strokeWidth={n} />
        <path d={`M ${x} ${y0 + (y1 - y0) * ch} l ${-W * 0.022} ${-W * 0.014} l ${W * 0.044} 0 Z`}
              fill="#2C2722" opacity={ch > 0.96 ? 1 : 0}
              transform={`rotate(180 ${x} ${y0 + (y1 - y0) * ch})`} />
        {moc.map((m, i) => {
          const f = so === 1 ? 0.5 : i / (so - 1);
          const y = y0 + (y1 - y0) * f;
          const c = cN(m.nhan || "");
          return (
            <g key={i} opacity={ch >= f - 0.02 ? 1 : 0}>
              {/* đường dẫn sang mép phải — lấp khoảng trống VÀ giúp mắt bám mốc */}
              <line x1={x + W * 0.034} y1={y} x2={W * 0.92} y2={y}
                    stroke="#2C2722" strokeWidth={Math.max(1, n * 0.18)} opacity={0.22} />
              <line x1={x - W * 0.030} y1={y} x2={x + W * 0.030} y2={y}
                    stroke="#2C2722" strokeWidth={n * 0.8} />
              <text x={x + W * 0.055} y={y - c * 0.22} fontFamily={F} fontWeight={900}
                    fontSize={c} fill="#2C2722">{m.nhan}</text>
              {m.phu ? (
                <text x={x + W * 0.055} y={y + c * 0.78} fontFamily={F} fontWeight={700}
                      fontSize={c * 0.66} fill="#5A544C">{m.phu}</text>
              ) : null}
            </g>
          );
        })}
        {vt >= 0 ? (
          <circle cx={x} cy={y0 + (y1 - y0) * fv} r={W * 0.026 * (1 + 0.18 * Math.sin(p * 12))}
                  fill={mau} stroke="#FFFFFF" strokeWidth={n} />
        ) : null}
      </g>
    );
  }

  const x0 = W * 0.10, x1 = W * 0.90, y = H * 0.52;
  const oRong = (x1 - x0) / Math.max(1, so);
  return (
    <g>
      <line x1={x0} y1={y} x2={x0 + (x1 - x0) * ch} y2={y} stroke="#2C2722" strokeWidth={n} />
      <path d={`M ${x0 + (x1 - x0) * ch} ${y} l ${-H * 0.028} ${-H * 0.018} l 0 ${H * 0.036} Z`}
            fill="#2C2722" opacity={ch > 0.96 ? 1 : 0} />
      {moc.map((m, i) => {
        const fx = so === 1 ? 0.5 : i / (so - 1);
        const x = x0 + (x1 - x0) * fx;
        const hien = ch >= fx - 0.02;
        // Cỡ chữ chịu CẢ hai ràng buộc: cao theo H, rộng theo ô mà mốc này được chia.
        const c = Math.min(H * 0.055, (oRong * 0.94 / Math.max(1, (m.nhan || "").length)) * 1.6);
        return (
          <g key={i} opacity={hien ? 1 : 0}>
            <line x1={x} y1={y - H * 0.035} x2={x} y2={y + H * 0.035} stroke="#2C2722" strokeWidth={n * 0.8} />
            <text x={x} y={y - H * 0.065} textAnchor="middle" fontFamily={F} fontWeight={900}
                  fontSize={c} fill="#2C2722">{m.nhan}</text>
            {m.phu ? <text x={x} y={y + H * 0.10} textAnchor="middle" fontFamily={F} fontWeight={700}
                           fontSize={c * 0.66} fill="#5A544C">{m.phu}</text> : null}
          </g>
        );
      })}
      {vt >= 0 ? (
        <circle cx={x0 + (x1 - x0) * fv} cy={y} r={H * 0.026 * (1 + 0.18 * Math.sin(p * 12))}
                fill={mau} stroke="#FFFFFF" strokeWidth={n} />
      ) : null}
    </g>
  );
};

export const KinhLup: React.FC<{
  W: number; H: number; x: number; y: number; nhan: string; mau: string; p: number;
  con: React.ReactNode; bt?: string;
}> = ({ W, H, x, y, nhan, mau, p, con, bt = "" }) => {
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
      {/* 3/9 — KHÔNG CÓ GÌ ĐỂ PHÓNG THÌ VẼ BIỂU TƯỢNG, ĐỪNG VẼ ĐĨA TRẮNG.
          Chú thích 1/9 ngay trên đã ghi đúng bệnh ("kính lúp đang phóng to chỗ trống") và chữa
          bằng cách nối ảnh nền vào `con`. Nhưng khi CẠN hồ ảnh CF thì `con` lại là `null`, và
          bệnh cũ quay lại y nguyên: soi khung THE RULES bản dọc ra một **đĩa trắng tinh** to
          bằng một phần ba khung.
          Đúng họ lỗi *vá một nhánh, để nguyên nhánh song song* — bản vá cũ chỉ chữa nhánh CÓ
          ảnh. Nhánh không ảnh cần một thứ khác hẳn: vẽ chính vật đang nói tới vào trong ống
          kính. Kính lúp phóng to một biểu tượng vẫn đúng nghĩa "nhìn kỹ vào chi tiết". */}
      {/* ── ỐNG KÍNH SOI CHÍNH VẬT, KHÔNG SOI MỘT LÁT ẢNH  (3/9/2026) ────────────────────
          Bản trước ưu tiên `con` (ảnh nền) và chỉ vẽ biểu tượng khi không có ảnh. Nhưng phóng
          to 2,2 lần một mảng bất kỳ của bức ảnh thì phần lớn trường hợp rơi vào nền trống —
          soi khung THE RULES ba lần đều ra **một đĩa trắng tinh**, kể cả sau khi dời điểm soi
          về giữa khung.
          Việc của kính lúp là nói *"nhìn kỹ vào THỨ NÀY"*. Một biểu tượng sạch nói điều ấy rõ
          hơn hẳn một lát ảnh phóng to — và nó không bao giờ rỗng. Nên đảo thứ tự ưu tiên:
          có `bt` thì vẽ `bt`; không có mới phóng ảnh. */}
      <circle cx={cx} cy={cy} r={r} fill={bt ? _pha(mau, 0.86) : "#FFFFFF"} />
      <g clipPath="url(#lup)">
        {bt
          ? <g transform={`translate(${cx} ${cy})`}><BieuTuong ten={bt} s={r * 1.35} /></g>
          : (con ? <g transform={`translate(${cx - x * 2.2} ${cy - y * 2.2}) scale(2.2)`}>{con}</g> : null)}
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
  /* ── VIÊN NHÃN GỌN, KHÔNG PHẢI THANH TRẮNG CẮT NGANG KHUNG  (4/9/2026) ─────────────────
     Anh gửi khung DAY IN LIFE: thanh trắng "4 AM — UP" **cắt ngang thân cô y tá**, và dưới
     nó phụ đề lại chồng lên tiếp. Bản cũ vẽ `<rect>` chạy HẾT bề ngang, tô đặc trắng 94% —
     nó không phải một nhãn, nó là một dải băng dán đè lên ảnh.

     Đây đúng dấu hiệu nghiệp dư số một ở §12.12 (*hộp nền bo góc quanh chữ — mặc định của
     trình tạo phụ đề điện thoại*), chỉ khác màu. Không ảnh tham chiếu nào của anh có một
     dải như vậy.

     Ba thay đổi, mỗi cái chữa một điều anh nêu:
       · bề ngang bằng ĐÚNG chữ + lề  -> hết cắt ngang khung, ảnh còn nguyên hai bên
       · nền là MỰC của khung (#2C2722), chữ sáng -> đọc được trên mọi ảnh, và cùng một
         thứ mực với nét vẽ nhân vật nên nó thuộc về khung thay vì dán lên khung
       · bo tròn hẳn thành viên thuốc, đặt cao hơn một chút để chừa chỗ cho phụ đề */
  const fs = Math.min(H * (W > H ? 0.048 : 0.060), (W * 0.62) / _emChu(chu));
  const rong = fs * _emChu(chu.toUpperCase()) + fs * 1.5;
  const cao = fs * 1.62;
  const y0 = H - cao - fs * 0.55;
  return (
    <g opacity={q}>
      <rect x={(W - rong) / 2} y={y0} width={rong} height={cao} rx={cao / 2}
            fill="#2C2722" opacity={0.90} />
      <text x={W / 2} y={y0 + cao * 0.68} textAnchor="middle" fontFamily={F} fontWeight={900}
            fontSize={fs} fill="#F6F1E7" letterSpacing={fs * 0.10}>{chu.toUpperCase()}</text>
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
/* ── ĐẾM VẬT — LƯỚI LẤP KHUNG, KHÔNG PHẢI MỘT HÀNG  (nâng cấp 3/9/2026) ────────────────────
   Quy tắc C (§12.11): *thời gian trôi vẽ bằng SỐ LƯỢNG biểu tượng để người xem ĐẾM*. Muốn đếm
   được thì biểu tượng phải đủ to để nhìn ra là cái gì.

   Bản cũ xếp tất cả trên MỘT HÀNG với `r = min(H·0,052, W·0,90/n/2,3)`. Ở khung dọc 9:16, mười
   tám biểu tượng chia bề ngang 1080 cho ra bán kính **26px** — soi khung YEARS OF thấy một dải
   mặt trời tí xíu nén ở đỉnh khung, và **90% khung còn lại TRỐNG**. Không ai đếm được, và cũng
   không ai nhận ra đó là mặt trời.

   Gốc: một hàng thì số lượng chỉ ăn vào BỀ NGANG, trong khi khung dọc thừa CHIỀU CAO. Lưới
   dùng được cả hai chiều, nên cùng số biểu tượng mà bán kính lớn gấp ba.

   Bỏ luôn dải trắng `#FFFFFF` phía sau: §12.12 xếp "dải nền dưới mọi khung" vào danh sách dấu
   hiệu nghiệp dư, và ở đây nó còn cắt ngang căn phòng thành hai mảnh. */
export const Dem: React.FC<{
  W: number; H: number; n: number; ngay: boolean; chu: string; p: number; mau: string;
}> = ({ W, H, n, ngay, chu, p, mau }) => {
  const so = Math.max(1, Math.min(20, n));
  const hien = Math.max(1, Math.round(so * Math.min(1, p / 0.55)));
  /* Số CỘT chọn sao cho ô gần vuông: `cot = round(sqrt(so · W / vùng cao))`. Không ghi cứng,
     vì cùng một `so` phải ra lưới khác nhau ở 16:9 và 9:16 — đúng chỗ bản cũ sai. */
  const vung = { x: W * 0.08, y: H * 0.10, w: W * 0.84, h: H * 0.62 };
  const cot = Math.max(1, Math.min(so, Math.round(Math.sqrt(so * vung.w / Math.max(1, vung.h)))));
  const hang = Math.ceil(so / cot);
  const bw = vung.w / cot, bh = vung.h / hang;
  const r = Math.min(bw, bh) * 0.40;
  return (
    <g>
      {Array.from({ length: so }).map((_, i) => {
        const c = i % cot, h = Math.floor(i / cot);
        // Hàng cuối thiếu ô thì căn giữa, không để lệch trái — lệch trái đọc ra "bị cắt mất".
        const trong = h === hang - 1 ? (cot * hang - so) : 0;
        const x = vung.x + bw * (c + 0.5) + trong * bw * 0.5;
        const y = vung.y + bh * (h + 0.5);
        const dem = ngay ? i % 2 === 1 : false;
        return (
          <g key={i} opacity={i < hien ? 1 : 0.13}>
            {/* ── KHÔNG có bóng tiếp đất ở đây  (bỏ 4/9/2026) ────────────────────────
                Luật "một khung có mặt sàn thì MỌI vật đứng trên sàn ấy phải để lại bóng"
                là luật đúng — và nó nói về vật ĐỨNG TRÊN SÀN. Lưới đếm này lơ lửng giữa
                khung theo hàng cột, nên một ellipse mờ ngay dưới mỗi biểu tượng đọc ra
                "hình dán đang bay", tức nó nói SAI đúng cái điều nó sinh ra để nói.
                Soi khung DAY IN LIFE thấy ngay: sáu mặt trời xếp lưới, mỗi cái một vệt
                bóng treo giữa trời.
                Đúng §12.5 — một luật đúng ở ngữ cảnh nó sinh ra, sai ở ngữ cảnh mới. Lưới
                đếm là một SƠ ĐỒ, không phải một cảnh; sơ đồ không có mặt sàn để mà đổ bóng. */}
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
        <text x={W / 2} y={vung.y + vung.h + H * 0.075} textAnchor="middle" fontFamily={F}
              fontWeight={900}
              fontSize={Math.min(H * 0.055, (W * 0.84 / Math.max(1, chu.length)) * 1.6)}
              fill={mau} letterSpacing={1}>{chu}</text>
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
        {/* ── TẤM MÀU PHỦ, KHÔNG PHẢI TẤM MÀU ĐẶC  (4/9/2026) ─────────────────────────
            Anh soi khung WHAT IF: *"Nothing at all."* trên một mảng cam kín khung, đọc ra
            một khung TRỐNG chứ không ra một câu khẳng định.
            Thẻ chữ là thiết bị đúng — §12.11 quy tắc E: lời chuyển sang khẳng định thì hình
            chuyển sang thẻ chữ. Cái sai là nó XOÁ SẠCH cảnh phía sau. `Nen` vẫn được dựng
            ngay dưới lớp này, nên chỉ cần hạ độ đục là cảnh hiện mờ trở lại: câu vẫn là thứ
            mắt đọc trước, mà khung không còn rỗng.
            0,80 đo bằng mắt: 0,94 vẫn đọc ra tấm đặc, dưới 0,70 thì chữ bắt đầu tranh chấp
            với nét sau lưng. */}
        <rect x={0} y={0} width={W} height={H} fill={mau} opacity={0.80} />
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
    /* ── KHOẢNG CÁCH SỐ / TIÊU ĐỀ TÍNH TỪ CỠ CHỮ  (4/9/2026) ────────────────────────────
       Bản trước đặt số ở `H*0,40` và khối tiêu đề ở `H*0,64` — hai phân số CỐ ĐỊNH cách nhau
       0,24·H. Nhưng khối tiêu đề neo ở TÂM, nên nửa trên của nó cao tới
       `(dòng/2)·fsz·1,16 + fsz·0,34`; với 4 dòng ở `fsz = 0,135·H` thì nửa trên là **0,36·H**,
       đỉnh khối chạm y = 0,28·H — trong khi chữ số chiếm 0,32–0,40·H, CÙNG `x = 0,08·W`.
       Đếm trên dữ liệu thật: **11 thẻ chương** rơi đúng tổ hợp (bố cục nêm chéo · có số · ≥4
       dòng), ví dụ `survive` chương 5 "Could you survive a night in the Everglades".

       Đây là lần thứ NĂM cùng một lỗi trong dự án (§15.10): hai phân số cố định không mã hoá
       được quan hệ "dòng này nằm dưới dòng kia". Nay suy từ chính cỡ chữ, và kẹp trần 0,80·H
       để khối không tụt xuống dải phụ đề. */
    const fsz = coChu(0.72, dongT.length);
    const nuaTren = (dongT.length / 2) * fsz * 1.16 + fsz * 0.34;
    const cSo = H * 0.085;
    const yTieu = Math.min(H * 0.80, Math.max(H * 0.52, H * 0.30 + cSo * 0.9 + nuaTren));
    return (
      <g opacity={q}>
        <rect x={0} y={0} width={W} height={H} fill={nen} />
        <path d={`M 0 ${H * 0.16} L ${W} ${H * -0.06} L ${W} ${H} L 0 ${H} Z`} fill={mau} />
        {soCh ? (
          <text x={W * 0.08} y={H * 0.30} fontFamily={F} fontWeight={900}
                fontSize={cSo} fill={chuSang} opacity={0.55}>{soCh}</text>
        ) : null}
        {khoi(W * 0.08, yTieu, "start", fsz, chuSang)}
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
  mau: string; mauPhu: string; p: number; nen?: string; hat?: number; kieu?: number;
}> = ({ W, H, cot, don, mau, mauPhu, p, nen = "#F2F0EA", hat = 0, kieu = 0 }) => {
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
  /* `bo` phải khai TRƯỚC nhánh cột ngang bên dưới. Bản đầu để nó ở dưới, và vì `const` có
     vùng chết tạm thời nên mọi biểu đồ kiểu 1/2 sẽ ném `ReferenceError` NGAY LÚC CHẠY — trong
     khi `esbuild` vẫn xanh, đúng bài học §12.2: bộ kiểm cú pháp không phải bộ dựng. */
  const bo = W * (kk === 1 ? 0.002 : kk === 2 ? 0.012 : 0.006);

  /* ── BA BỐ CỤC BIỂU ĐỒ  (3/9/2026) ──────────────────────────────────────────────────────
     Biểu đồ là nhịp CHỐT của gần như mọi kênh — chỗ người xem thấy toàn cảnh sau khi đã nghe
     từng phần. Nó chỉ chiếm 7% số nhịp nhưng đứng ở vị trí đắt nhất, và trước bản này mọi kênh
     mọi tập đều dùng đúng một hình: cột đứng, nhãn nằm dưới.

       0  CỘT ĐỨNG   — mặc định; mạnh khi nhãn ngắn và số ít
       1  CỘT NGANG  — nhãn nằm BÊN TRÁI nên chữ dài bao nhiêu cũng đủ chỗ; đây là lý do thật
                       để có nó, và cũng là bố cục hợp khung dọc 9:16 hơn hẳn
       2  CHẤM–GẬY   — một đường mảnh và một chấm đặc; ở khung điện thoại nó đọc nhanh hơn cột
                       vì mắt so VỊ TRÍ CHẤM thay vì so diện tích khối

     Cột ngang tự nhận việc khi nhãn dài: đo bề rộng nhãn dài nhất, quá ngưỡng thì ép về kiểu 1
     dù kênh khai kiểu khác. Bố cục là thứ phục vụ dữ liệu, không phải ngược lại. */
  const nhanDai = Math.max(...cot.map((c) => (c.nhan || "").length), 1);
  let kC = Math.abs(kieu) % 3;
  if (nhanDai * cot.length > 34 && kC === 0) kC = 1;   // nhãn không đủ chỗ ở cột đứng

  if (kC === 1 || kC === 2) {
    const xNhan = W * 0.30, x0 = W * 0.34;
    /* ── CHỪA CHỖ CHO THỨ VẼ SAU ĐẦU GẬY  (3/9/2026) ────────────────────────────────────
       `x1 = W*0.94` là chỗ đầu cột NGANG dừng lại — đúng cho cột, vì cột hết là hết. Chấm–gậy
       thì sau đầu gậy còn MỘT CHẤM (bán kính) và MỘT CON SỐ. Soi khung HOW MUCH: chấm của
       `billion` và số của nó chạy hẳn ra ngoài mép phải.
       Chép một hằng số sang bố cục khác mà không hỏi *"câu này còn đúng ở ngữ cảnh mới không"*
       — §12.5, lần thứ hai trong hàm này.

       ── VÀ TRẦN CHIỀU CAO MỖI DÒNG ──────────────────────────────────────────────────────
       Chia đều 0,62·H cho 2 dòng cho ra mỗi dòng 0,31·H, tức chấm bán kính 0,065·H — to bằng
       một nắm tay, và hai dòng cách nhau gần một phần ba khung. Số dòng ít thì phải THU LẠI và
       căn giữa, không phải giãn ra cho đầy. */
    const oCao = Math.min((H * 0.62) / Math.max(1, cot.length), H * 0.17);
    const rCham0 = oCao * 0.21;
    const cS = Math.min(oCao * 0.44, H * 0.040);
    /* ── CHỖ CHO CON SỐ PHẢI ĐO, KHÔNG ĐOÁN — VÀ PHẢI CHỪA Ở CẢ HAI KIỂU  (4/9/2026) ────
       Bản trước chỉ chừa cho kiểu 2 (chấm–gậy), và chừa bằng một hằng số đoán `W*0,13`.
       Kiểu 1 (cột ngang) để nguyên `x1 = W*0,94`, trong khi con số vẫn vẽ ở
       `x0 + dai + W*0,018` — tức cột dài nhất (theo định nghĩa `dai = x1 - x0`) đẩy số
       của nó ra **ngoài mép phải**. Và cột dài nhất luôn tồn tại: nó là cột `max`.
       Soi khung: HOW LONG hiện `77…` cụt, ODDS hiện `29…` cụt — cả hai đều là kiểu 1.

       Đúng họ lỗi §6 *vá một nhánh, để nguyên nhánh song song*, và chú thích ngay trên
       đây đã kể lại đúng họ lỗi ấy khi vá nhánh kia. Nay một phép chừa cho cả hai, và đo
       từ CHÍNH chuỗi sắp vẽ (`_bac`) thay vì từ một hằng số: `_bac(1.2e9)` ra `1.2B` (4
       ký tự) còn `_bac(30300)` ra `30.3K` (5) — chênh nhau đủ để một hằng số sai một bên. */
    const soDai = Math.max(...cot.map((c) => `${_bac(c.v)}`.length), 1);
    const chuaSo = W * 0.018 + cS * 0.60 * soDai + W * 0.012;
    const x1 = W * 0.94 - chuaSo - (kC === 2 ? rCham0 : 0);
    /* Căn khối vào GIỮA vùng vẽ, không dồn lên đầu một dải cố định. Với hai dòng thì công
       thức cũ đặt tâm khối ở 0,45·H — soi khung thấy đồ hoạ nằm hẳn nửa trên và nửa dưới trống
       trơn. Vùng vẽ đã trừ dải phụ đề rồi nên tâm của nó chính là tâm thị giác. */
    const yTop = Math.max(H * 0.14, H * 0.50 - (oCao * cot.length) / 2);
    const cN = Math.min(H * 0.040, oCao * 0.40, (xNhan * 0.88 / nhanDai) * 1.55);
    return (
      <g>
        {don ? (
          <text x={W / 2} y={H * 0.075} textAnchor="middle" fontFamily={F} fontWeight={800}
                fontSize={Math.min(H * 0.042, (W * 0.8 / Math.max(1, don.length)) * 1.7)}
                fill={mauPhu} letterSpacing={2}>{don.toUpperCase()}</text>
        ) : null}
        {cot.map((c, i) => {
          const qi = Math.max(0, Math.min(1, (q - i * 0.06) / 0.55));
          const y = yTop + oCao * (i + 0.5);
          /* SÀN CHIỀU DÀI phải đủ để CHẤM tách khỏi trục.  (3/9/2026)
             Soi khung HOW MUCH (million 1e6 cạnh billion 1e9): tỉ lệ 1/1000 nên gậy dài
             0,1% — chấm nằm chồng lên vạch trục và lên cả nhãn bên trái, còn số `1M` rơi vào
             giữa chấm. Ba thứ chồng nhau ở đúng một chỗ.
             Sàn cũ `W*0,006` (6px) viết cho CỘT, nơi bề rộng cột che phần lệch. Chấm–gậy cần
             sàn bằng ít nhất một đường kính chấm cộng khoảng thở — chép hằng số sang bố cục
             khác là lỗi §6 quen thuộc. */
          const rCham = rCham0;
          /* Sàn `W*0,006` (6px) chép từ bố cục CỘT ĐỨNG, nơi bề rộng cột đã đủ để mắt thấy
             có một cái cột. Ở cột NGANG thì 6px là một vạch không ai nhận ra — soi biểu đồ
             ODDS (36 cạnh 36 triệu) thấy hai cột nhỏ nhất biến mất hẳn, và người xem đọc ra
             "thiếu cột" chứ không đọc ra "cột này bé đến thế". Sàn tồn tại đúng để tránh cách
             đọc ấy, nên nó phải đủ lớn để NHÌN THẤY. */
          const dai = Math.max((x1 - x0) * (Math.abs(c.v) / max),
                               kC === 2 ? rCham * 2.4 : W * 0.018) * qi;
          const la = c === dinh;
          return (
            <g key={i}>
              <text x={xNhan - W * 0.015} y={y + cN * 0.34} textAnchor="end" fontFamily={F} fontWeight={800}
                    fontSize={cN} fill="#3A342C">{c.nhan}</text>
              {kC === 1 ? (
                <rect x={x0} y={y - oCao * 0.28} width={dai} height={oCao * 0.56} rx={bo}
                      fill={la ? mau : nhat} stroke="#2C2722" strokeWidth={Math.max(2, H * 0.003)} />
              ) : (
                <>
                  <line x1={x0} y1={y} x2={x0 + dai} y2={y}
                        stroke={la ? mau : nhat} strokeWidth={Math.max(3, oCao * 0.10)}
                        strokeLinecap="round" />
                  <circle cx={x0 + dai} cy={y} r={rCham}
                          fill={la ? mau : nhat} stroke="#2C2722" strokeWidth={Math.max(2, H * 0.003)} />
                </>
              )}
              {/* Số phải đứng SAU chấm, không phải sau đầu gậy — nếu không nó nằm trong chấm. */}
              <text x={x0 + dai + (kC === 2 ? rCham : 0) + W * 0.018} y={y + cS * 0.34}
                    fontFamily={F} fontWeight={900}
                    fontSize={cS} fill={la ? mau : _pha(mau, -0.34)} opacity={qi}>{_bac(c.v * qi)}</text>
            </g>
          );
        })}
        <line x1={x0} y1={yTop} x2={x0} y2={yTop + oCao * cot.length}
              stroke={_pha(nen, -0.30)} strokeWidth={Math.max(2, H * 0.003)} />
      </g>
    );
  }

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
