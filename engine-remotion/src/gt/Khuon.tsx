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
    case "hop":  return <g>{P(`M ${-k(0.4)} ${-k(0.2)} h ${k(0.8)} v ${k(0.56)} h ${-k(0.8)} Z`, "#C9A06A")}
      {P(`M ${-k(0.44)} ${-k(0.34)} h ${k(0.88)} v ${k(0.14)} h ${-k(0.88)} Z`, "#B08A56")}</g>;
    default:     return <circle cx="0" cy="0" r={k(0.36)} fill={mau} opacity={0.25} />;
  }
};

/* ── KHUÔN 2: CHIA ĐÔI ────────────────────────────────────────────────────────────────────
   Vạch dọc, hai nhãn hoa ở trên, hai biểu tượng, hai con số. Nhãn viết HOA và đặt SÁT TRÊN —
   người xem đọc nhãn trước, nhìn hình sau; ngược lại thì phải đoán mình đang so cái gì. */
export const ChiaDoi: React.FC<{
  W: number; H: number; trai: any; phai: any; mau: string; p: number;
}> = ({ W, H, trai, phai, mau, p }) => {
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
  return (
    <g>
      {ben(trai, W * 0.25, 0)}
      {/* Vạch giữa VẼ DẦN từ trên xuống: mắt bám theo nét đang chạy, nên nó dẫn người xem sang
          vế thứ hai đúng lúc lời kể nói tới vế thứ hai. */}
      <line x1={W / 2} y1={H * 0.10} x2={W / 2} y2={H * (0.10 + 0.80 * Math.min(1, p / 0.5))}
            stroke="#2C2722" strokeWidth={Math.max(3, H * 0.006)} strokeDasharray={`${H * 0.03} ${H * 0.022}`} />
      {ben(phai, W * 0.75, 0.35)}
    </g>
  );
};

/* ── KHUÔN 3: SỐ LIỆU ĐÈ HÌNH ─────────────────────────────────────────────────────────────
   Con số chiếm 1/5 chiều cao khung. To đến mức khó chịu là CỐ Ý: đây là khuôn dùng cho đúng
   một con số mà cả đoạn xoay quanh, và nó phải đọc được khi video chạy trong luồng cuộn. */
export const SoLieu: React.FC<{
  W: number; H: number; so: string; don: string; chu: string; bt: string; mau: string; p: number;
}> = ({ W, H, so, don, chu, bt, mau, p }) => {
  const q = Math.min(1, p / 0.28);
  /* Cùng lỗi với `ChiaDoi`, và thêm một lỗi nữa: biểu tượng đặt ở `H*0.62` còn con số ở
     `H*0.30` với cỡ `H*0.20` — hai lớp cùng chọn chỗ theo H mà không biết nhau, nên số "9"
     nằm đè lên cái biểu tượng. Nay biểu tượng bám ĐÁY khung và số bám ĐỈNH, không gặp nhau. */
  const cs = Math.min(H * 0.20, (W * 0.88 / Math.max(1, so.length)) * 1.65);
  const cd = Math.min(H * 0.055, (W * 0.80 / Math.max(1, (don || "").length)) * 1.7);
  return (
    <g>
      {bt ? <g transform={`translate(${W / 2} ${H * 0.70})`} opacity={0.92}>
        <BieuTuong ten={bt} s={Math.min(H * 0.30, W * 0.30)} /></g> : null}
      <g transform={`translate(${W / 2} ${H * 0.26}) scale(${0.86 + q * 0.14})`} opacity={q}>
        <text x="0" y="0" textAnchor="middle" fontFamily={F} fontWeight={900}
              fontSize={cs} fill="#2C2722"
              stroke="#FFFFFF" strokeWidth={H * 0.014} paintOrder="stroke">{so}</text>
        {don ? <text x="0" y={cs * 0.42} textAnchor="middle" fontFamily={F} fontWeight={800}
                     fontSize={cd} fill={mau} letterSpacing={2}>{don.toUpperCase()}</text> : null}
      </g>
      {chu ? <text x={W / 2} y={H * 0.94} textAnchor="middle" fontFamily={F} fontWeight={700}
                   fontSize={Math.min(H * 0.042, (W * 0.92 / Math.max(1, chu.length)) * 1.75)}
                   fill="#3A342C">{chu}</text> : null}
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
  const fs = Math.min(H * 0.075, (W * 0.80 / Math.max(1, chu.length)) * 1.5);
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
export const TheChu: React.FC<{ W: number; H: number; chu: string; p: number; mau: string }> =
({ W, H, chu, p, mau }) => {
  const q = Math.min(1, p / 0.2);
  const dong = chu.split("|");
  const dai = Math.max(...dong.map((d) => d.length), 1);
  const fs = Math.min(H * 0.115, (W * 0.74 / dai) * 1.62);
  return (
    <g opacity={q} transform={`translate(${W / 2} ${H / 2}) scale(${0.96 + q * 0.04})`}>
      <rect x={-W * 0.42} y={-fs * dong.length * 0.92} width={W * 0.84}
            height={fs * dong.length * 1.84} rx={H * 0.02}
            fill="#F2E7CE" stroke="#8A7550" strokeWidth={Math.max(3, H * 0.005)} />
      {dong.map((d, i) => (
        <text key={i} x="0" y={(i - (dong.length - 1) / 2) * fs * 1.22 + fs * 0.34}
              textAnchor="middle" fontFamily="Georgia, serif" fontWeight={700}
              fontSize={fs} fill="#2C2722">{d.trim()}</text>
      ))}
      <rect x={-W * 0.42} y={fs * dong.length * 0.92 - Math.max(3, H * 0.006)}
            width={W * 0.84} height={Math.max(3, H * 0.006)} fill={mau} />
    </g>
  );
};
