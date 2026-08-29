import React from "react";
import { CAM_XUC, CU_CHI, Kieu, TenCamXuc, TenCuChi, Tu, visemeTai } from "../v2/DienVien";

/**
 * DIỄN VIÊN HÀI — tạo hình hoạt hình Mỹ, riêng cho 10 kênh thế hệ 4 (30/8/2026).
 *
 * Anh: *"nhân vật cần chuẩn hoạt hình kiểu simpson hay phim hoạt hình mỹ ăn khách trước đó,
 * nhớ ko vi phạm bản quyền, nhưng vẫn đảm bảo được tính dễ thương hài hước đẹp, ko khô cứng
 * như hiện tại… nâng cấp sao cho mượt mà chuyển động, biểu cảm, lời nói"*.
 *
 * ── VÌ SAO LÀ TỆP MỚI, KHÔNG SỬA `v2/DienVien` ──────────────────────────────────────────
 * `v2/DienVien` đang chạy cho 10 kênh dữ liệu thế hệ 3. Sửa nó là sửa luôn mười kênh ấy trong
 * khi chúng đang đạt chuẩn — đúng thứ anh dặn tránh ("ko động vào channel đang ok"). Bộ hài
 * cần tạo hình khác hẳn, nên nó được một tệp riêng và mượn lại các bảng dữ liệu thuần
 * (cảm xúc, cử chỉ, khẩu hình) của tệp cũ.
 *
 * ── KHÁC BẢN CŨ Ở ĐÂU, VÀ VÌ SAO ────────────────────────────────────────────────────────
 * Bản cũ đọc ra "khô cứng" vì bốn thứ, không phải một:
 *
 *  1. **TỈ LỆ NGƯỜI THẬT.** Đầu bằng 1/6 thân. Hoạt hình Mỹ ăn khách để đầu 1/3,5 – 1/4: đầu
 *     to thì mắt to, mà mắt mới là chỗ khán giả đọc cảm xúc. Đây là thay đổi có tác dụng lớn
 *     nhất, và nó thuộc về TỈ LỆ — không sao chép nét vẽ của ai.
 *  2. **CHI THỂ LÀ QUE + KHỚP LÀ BI TRÔI.** Bàn tay là hình tròn rời khỏi cánh tay, nhìn ra
 *     ngay là hình ghép. Nay tay chân vẽ bằng nét dày bo tròn đầu (thành hình con nhộng liền
 *     mạch) và bàn tay là **găng bốn ngón** — ngôn ngữ tạo hình chung của hoạt hình phương
 *     Tây từ những năm 1930, không thuộc về một hãng nào.
 *  3. **KHÔNG CÓ NÉN – GIÃN.** Người thật không nén giãn, nhân vật hoạt hình thì có: mỗi nhịp
 *     thở và mỗi lần nhấn giọng, thân hơi lùn xuống rồi bật cao lên. Thiếu nó thì hình đứng
 *     yên như tượng dù mọi khớp đều động.
 *  4. **MỌI THỨ CHUYỂN ĐỘNG THEO ĐƯỜNG THẲNG.** Nay cử chỉ đi theo cung có gia tốc, và tóc,
 *     vạt áo, đuôi tóc trễ lại một nhịp so với đầu (`treo`).
 *
 * ── CHỖ CỐ Ý KHÔNG LÀM ──────────────────────────────────────────────────────────────────
 * Không da vàng, không răng vẩu, không mắt lồi có tròng đen bằng hạt đậu, không bốn ngón tay
 * vàng — đó là DẤU HIỆU NHẬN DẠNG của những bộ phim cụ thể và là chỗ bản quyền bám vào.
 * Thứ mượn được là NGUYÊN TẮC dựng hình (tỉ lệ đầu–thân, nét bao dày, găng tay, nén–giãn,
 * chuyển động thứ cấp) — những nguyên tắc ấy là kiến thức chung của ngành, không của ai cả.
 */

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const trn = (a: number, b: number, t: number) => a + (b - a) * kep(t);
const D = (deg: number) => (deg * Math.PI) / 180;
const P = (x: number, y: number, d: number, a: number): [number, number] =>
  [x + Math.cos(D(a)) * d, y + Math.sin(D(a)) * d];

/** Trễ pha + dao động tắt dần — cho tóc, đuôi tóc, vạt áo đi sau đầu một nhịp. */
const treo = (dich: number, t: number, tre = 0.13, bien = 1) =>
  dich + Math.sin((t - tre) * 7.5) * bien * 0.35 * Math.exp(-Math.abs(Math.sin(t * 1.1)) * 0.6);

export type PropsHai = {
  kieu: Kieu;
  camXuc: TenCamXuc;
  cuChi: TenCuChi;
  nhin: [number, number];
  noi: { w: number; h: number; tron: number };
  t: number;
  nhan?: number;                 // 0..1 — độ nhấn của lượt thoại này (dùng cho nén–giãn)
  nghieng?: number;              // độ ngả người về phía người đối thoại
  buoc?: number;                 // 0 = đứng yên; >0 = đang bước (biên độ sải chân)
  x?: number; y?: number; scale?: number; lat?: boolean;
};

// ══════════════════════════════════════════════════════════════════════════════════════════
// TỈ LỆ — đây là bảng quyết định "trông có ra hoạt hình không"
// ------------------------------------------------------------------------------------------
// Toàn thân cao 420 đơn vị, chân chạm y = 0, người mọc lên theo chiều âm.
// Đầu bán kính 58 nên đầu chiếm 116/420 ≈ 1/3,6 — đúng dải của hoạt hình truyền hình Mỹ.
// Chân CỐ Ý ngắn (150 trên tổng 420): chân ngắn + thân tròn là công thức "dễ thương", chân dài
// đọc ra là người lớn nghiêm nghị.
// ══════════════════════════════════════════════════════════════════════════════════════════
const Y_HONG = -168;
const Y_VAI = -262;
const R_DAU = 58;

export const DienVienHai: React.FC<PropsHai> = ({
  kieu, camXuc, cuChi, nhin, noi, t, nhan = 0, nghieng = 0, buoc = 0,
  x = 0, y = 0, scale = 1, lat = false,
}) => {
  const E = CAM_XUC[camXuc] || CAM_XUC.trung_tinh;
  const G = CU_CHI[cuChi] || CU_CHI.nghi;
  const cao = kieu.cao ?? 1;
  const ngang = kieu.beNgang ?? 1;
  const matTo = kieu.matTo ?? 1;
  const camV = kieu.cam ?? 0.4;

  // Nét bao dày là thứ đầu tiên mắt đọc ra "đây là phim hoạt hình". Giữ bề dày TRÊN MÀN HÌNH
  // không đổi bằng cách chia cho `scale` — không chia thì nhân vật càng xa nét càng mảnh và
  // hai người trong cùng khung trông như vẽ bằng hai cây bút khác nhau.
  const NG = 7.2 / scale;        // nét bao ngoài
  const NT = 3.4 / scale;        // nét chi tiết bên trong

  // ── NHỊP SỐNG ──────────────────────────────────────────────────────────────────────────
  const tho = Math.sin(t * 2.0);
  const dao = Math.sin(t * 0.6) * 1.6;
  // Dồn trọng tâm: người đứng lâu thì đổi chân trụ. Chu kỳ dài và lệch pha với nhịp thở nên
  // hai chuyển động không bao giờ trùng nhịp — trùng nhịp là dấu hiệu rõ nhất của hình máy.
  const trong = Math.sin(t * 0.41 + 1.2) * 3.2;

  // NÉN – GIÃN. Thân lùn xuống thì phình ngang ra, và ngược lại: giữ nguyên thể tích, nếu
  // không thì nhân vật đọc ra là bị kéo méo chứ không phải đang nhún.
  const nen = Math.sin(t * 2.0) * 0.012 + nhan * 0.03;
  const sy = 1 + nen;
  const sx = 1 - nen * 0.85;

  // Chớp mắt không đều nhịp — nhịp đều đọc ra ngay là máy.
  const cky = 3.3 + Math.sin(t * 0.37) * 1.5;
  const pc = (t % cky) / cky;
  const chop = pc > 0.962 ? Math.sin(((pc - 0.962) / 0.038) * Math.PI) : 0;

  // Đầu gật theo lời nói: miệng mở to thì đầu chúi xuống một chút. Đây là thứ làm lời thoại
  // "có người nói" thay vì "có cái miệng động".
  const gat = noi.h * 3.4;
  const nghiengDau = E.nghieng + dao * 0.6 + treo(0, t, 0.1, 0.6);

  // ── KHUNG XƯƠNG ────────────────────────────────────────────────────────────────────────
  const hong: [number, number] = [trong * 0.3, Y_HONG * cao + nhun];
  const vai: [number, number] = [trong * 0.6 + nghieng * 1.6, Y_VAI * cao + tho * 1.2 + nhun];
  const co: [number, number] = [vai[0] + dao * 0.4, vai[1] - 14 * cao];
  const dau: [number, number] = [co[0] + dao * 0.9, co[1] - 52 * cao + gat];

  const rongVai = 44 * ngang;
  const vaiT: [number, number] = [vai[0] - rongVai, vai[1] + 4];
  const vaiP: [number, number] = [vai[0] + rongVai, vai[1] + 4];
  const dtay = 74 * cao, dcang = 70 * cao;

  // Cử chỉ đi theo CUNG CÓ GIA TỐC, không đi thẳng: `muot` làm góc rời khỏi tư thế nghỉ chậm,
  // giữa nhanh, rồi dừng chậm. Tay người thật không quay đều tốc độ.
  const muot = (v: number) => v * v * (3 - 2 * v);
  const mo = muot(kep(t / 0.45));
  // Khi ĐI, tay vung NGƯỢC PHA với chân cùng bên — đó là cách người thật giữ thăng bằng, và
  // là chi tiết làm dáng đi đọc ra là đi chứ không phải trượt ngang.
  const vungT = buoc > 0 ? Math.sin(t * 7.4 + Math.PI) * buoc * 26 : 0;
  const vungP = buoc > 0 ? Math.sin(t * 7.4) * buoc * 26 : 0;
  const gocVT = trn(100, G.vaiT, mo) + Math.sin(t * 1.7) * 2.2 + vungT;
  const gocKT = trn(-8, G.khuyuT, mo);
  const gocVP = trn(80, G.vaiP, mo) + Math.sin(t * 1.7 + 1) * 2.2 + vungP;
  const gocKP = trn(8, G.khuyuP, mo);

  const khuyuT = P(vaiT[0], vaiT[1], dtay, gocVT);
  const tayT = P(khuyuT[0], khuyuT[1], dcang, gocVT + gocKT);
  const khuyuP = P(vaiP[0], vaiP[1], dtay, gocVP);
  const tayP = P(khuyuP[0], khuyuP[1], dcang, gocVP + gocKP);

  // ── DÁNG ĐI ────────────────────────────────────────────────────────────────────────────
  // Bước chân là chuyển động tuần hoàn: hai chân LỆCH PHA NỬA CHU KỲ, và bàn chân nhấc lên
  // theo nửa trên của hình sin (nửa dưới là lúc chân chạm đất nên phải giữ y = 0, không thì
  // chân lún xuống dưới sàn — lỗi vật lý mắt bắt được ngay).
  // `nhun` là nhịp thân nhấp nhô hai lần mỗi chu kỳ bước: người đi thì trọng tâm lên xuống,
  // đứng yên mà tay chân vung là thứ đọc ra là hình máy.
  const bPha = t * 7.4;
  const sai = buoc * 30;
  const dapT = Math.sin(bPha), dapP = Math.sin(bPha + Math.PI);
  const nhacT = buoc > 0 ? Math.max(0, dapT) * 20 : 0;
  const nhacP = buoc > 0 ? Math.max(0, dapP) * 20 : 0;
  const nhun = buoc > 0 ? Math.abs(Math.cos(bPha)) * 5 : 0;

  const rongHong = 30 * ngang;
  const goiT: [number, number] = [hong[0] - rongHong + dapT * sai * 0.5, hong[1] + 82 * cao - nhacT * 0.5];
  const goiP: [number, number] = [hong[0] + rongHong + dapP * sai * 0.5, hong[1] + 82 * cao - nhacP * 0.5];
  const chanT: [number, number] = [hong[0] - rongHong - 2 + dapT * sai, -4 - nhacT];
  const chanP: [number, number] = [hong[0] + rongHong + 2 + dapP * sai, -4 - nhacP];

  // ── MÀU ────────────────────────────────────────────────────────────────────────────────
  const V = kieu.net || "#20222B";
  const da = kieu.da, ao = kieu.ao, quan = kieu.quan;

  /** Chi thể: một nét bao dày rồi một nét màu mỏng hơn đè lên — ra hình con nhộng có viền. */
  const chi = (d: string, mau: string, day: number, key: string) => (
    <g key={key}>
      <path d={d} stroke={V} strokeWidth={day + NG} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} stroke={mau} strokeWidth={day} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </g>
  );

  /**
   * BÀN TAY GĂNG BỐN NGÓN — ngôn ngữ tạo hình chung của hoạt hình phương Tây từ thập niên 1930
   * (bốn ngón vẽ nhanh hơn năm, và đọc rõ hơn ở cỡ nhỏ). Không thuộc về hãng nào.
   * `goc` = hướng cẳng tay, để bàn tay nối liền chứ không trôi lơ lửng như bản cũ.
   */
  const ban = (p: [number, number], goc: number, key: string) => {
    const r = 17;
    const n = (i: number) => P(p[0], p[1], r * 0.98, goc - 34 + i * 22);
    return (
      <g key={key} transform={`rotate(${goc - 90} ${p[0]} ${p[1]})`}>
        <circle cx={p[0]} cy={p[1]} r={r} fill={da} stroke={V} strokeWidth={NG * 0.8} />
        {[0, 1, 2].map((i) => {
          const q = n(i);
          return <circle key={i} cx={q[0]} cy={q[1]} r={r * 0.44} fill={da} stroke={V} strokeWidth={NT} />;
        })}
        <circle cx={p[0] - r * 0.72} cy={p[1] + r * 0.34} r={r * 0.42} fill={da} stroke={V} strokeWidth={NT} />
      </g>
    );
  };

  /** Giày: khối bo tròn có gót — chân trần hình que là thứ làm bản cũ đọc ra là hình que. */
  const giay = (p: [number, number], huong: number, key: string) => (
    <g key={key}>
      <path d={`M ${p[0] - 15} ${p[1]} q -12 0 -12 -11 q 0 -12 13 -12 l 30 0 q 13 0 13 12 q 0 11 -13 11 z`}
            transform={`translate(${huong > 0 ? 6 : -20} 6)`}
            fill={V} stroke={V} strokeWidth={NG * 0.6} strokeLinejoin="round" />
    </g>
  );

  // ── MẶT ────────────────────────────────────────────────────────────────────────────────
  const mx = kep(nhin[0], -1, 1) * 7;
  const my = kep(nhin[1], -1, 1) * 5;
  const rMat = 15.5 * matTo;
  const rTrong = 7.4 * matTo;
  const mm = 1 - chop;
  const cachMat = 21 * matTo;
  const yMat = -8;
  const yMay = yMat - 20 - E.mayCao;

  // Miệng: bề ngang và bề cao lấy thẳng từ khẩu hình, cộng độ cong khoé môi theo cảm xúc.
  const mW = trn(26, 46, noi.w) * (1 + camV * 0.05);
  const mH = trn(2.5, 34, noi.h);
  const khoe = E.khoe * 9;
  const yMieng = 26;

  return (
    <g transform={`translate(${x} ${y}) rotate(${lat ? -nghieng * 0.4 : nghieng * 0.4} 0 0) scale(${(lat ? -scale : scale) * sx} ${scale * sy})`}>
      {/* BÓNG TIẾP ĐẤT — thiếu nó thì nhân vật lơ lửng dù đứng đúng chỗ. Bóng co giãn ngược
          chiều nén–giãn: người nhún xuống thì bóng loe ra. */}
      <ellipse cx={0} cy={2} rx={62 * ngang * (1 + nen * 2)} ry={11} fill="#00000026" />

      {/* CHÂN — vẽ trước thân để thân che chỗ nối ở hông */}
      {chi(`M ${hong[0] - rongHong} ${hong[1]} Q ${goiT[0] - 4} ${goiT[1]} ${chanT[0]} ${chanT[1]}`, quan, 27 * ngang, "cT")}
      {chi(`M ${hong[0] + rongHong} ${hong[1]} Q ${goiP[0] + 4} ${goiP[1]} ${chanP[0]} ${chanP[1]}`, quan, 27 * ngang, "cP")}
      {giay(chanT, -1, "gT")}
      {giay(chanP, 1, "gP")}

      {/* TAY SAU (bên trái) — vẽ trước thân, nên nó nằm sau lưng: ra chiều sâu mà không cần đổ bóng */}
      {chi(`M ${vaiT[0]} ${vaiT[1]} Q ${khuyuT[0]} ${khuyuT[1]} ${tayT[0]} ${tayT[1]}`, ao, 23 * ngang, "tT")}
      {ban(tayT, gocVT + gocKT, "bT")}

      {/* THÂN — hình hạt đậu, KHÔNG phải hình chữ nhật. Vai tròn và eo hơi thóp là thứ làm
          nhân vật đọc ra là dễ thương thay vì cứng đờ. */}
      <path
        d={`M ${vai[0] - rongVai - 6} ${vai[1] + 6}
            C ${vai[0] - rongVai - 16} ${vai[1] + 40}, ${hong[0] - rongHong - 20} ${hong[1] - 34}, ${hong[0] - rongHong - 12} ${hong[1] + 8}
            Q ${hong[0]} ${hong[1] + 26} ${hong[0] + rongHong + 12} ${hong[1] + 8}
            C ${hong[0] + rongHong + 20} ${hong[1] - 34}, ${vai[0] + rongVai + 16} ${vai[1] + 40}, ${vai[0] + rongVai + 6} ${vai[1] + 6}
            Q ${vai[0]} ${vai[1] - 14} ${vai[0] - rongVai - 6} ${vai[1] + 6} Z`}
        fill={ao} stroke={V} strokeWidth={NG} strokeLinejoin="round"
      />
      {/* Cổ áo chữ V + áo trong: một mảng sáng giữa ngực để thân không phẳng lì */}
      <path d={`M ${vai[0] - 20} ${vai[1] + 2} L ${vai[0]} ${vai[1] + 36} L ${vai[0] + 20} ${vai[1] + 2} Z`}
            fill={kieu.aoTrong} stroke={V} strokeWidth={NT} strokeLinejoin="round" />
      {kieu.caVat ? (
        <path d={`M ${vai[0] - 8} ${vai[1] + 26} L ${vai[0] + 8} ${vai[1] + 26} L ${vai[0] + 5} ${vai[1] + 78} L ${vai[0]} ${vai[1] + 86} L ${vai[0] - 5} ${vai[1] + 78} Z`}
              fill={kieu.caVat} stroke={V} strokeWidth={NT} strokeLinejoin="round" />
      ) : null}
      {kieu.phuKien === "the_deo" ? (
        <g>
          <path d={`M ${vai[0] - 16} ${vai[1] + 6} Q ${vai[0]} ${vai[1] + 52} ${vai[0] + 16} ${vai[1] + 6}`}
                stroke={V} strokeWidth={NT * 1.3} fill="none" />
          <rect x={vai[0] - 11} y={vai[1] + 46} width={22} height={28} rx={4}
                fill="#F4F7FC" stroke={V} strokeWidth={NT} />
        </g>
      ) : null}

      {/* TAY TRƯỚC (bên phải) — vẽ sau thân nên nằm trước ngực */}
      {chi(`M ${vaiP[0]} ${vaiP[1]} Q ${khuyuP[0]} ${khuyuP[1]} ${tayP[0]} ${tayP[1]}`, ao, 23 * ngang, "tP")}
      {ban(tayP, gocVP + gocKP, "bP")}

      {/* CỔ */}
      {chi(`M ${co[0]} ${co[1] + 16} L ${dau[0]} ${dau[1] + R_DAU * 0.62}`, da, 26, "co")}

      {/* ── ĐẦU ───────────────────────────────────────────────────────────────────────── */}
      <g transform={`rotate(${nghiengDau} ${dau[0]} ${dau[1] + R_DAU})`}>
        {/* Tai */}
        <ellipse cx={dau[0] - R_DAU * 0.94} cy={dau[1] + 6} rx={11} ry={15} fill={da} stroke={V} strokeWidth={NT * 1.2} />
        <ellipse cx={dau[0] + R_DAU * 0.94} cy={dau[1] + 6} rx={11} ry={15} fill={da} stroke={V} strokeWidth={NT * 1.2} />

        {/* SỌ — không phải hình tròn. Trán rộng, hàm thóp lại theo `cam`: 0 = mặt tròn trẻ con,
            1 = hàm vuông vức. Một trục này đủ tách "đứa trẻ" khỏi "ông chú" mà không cần thêm nét nào. */}
        <path
          d={`M ${dau[0] - R_DAU} ${dau[1] - 4}
              C ${dau[0] - R_DAU} ${dau[1] - R_DAU * 1.12}, ${dau[0] + R_DAU} ${dau[1] - R_DAU * 1.12}, ${dau[0] + R_DAU} ${dau[1] - 4}
              C ${dau[0] + R_DAU} ${dau[1] + R_DAU * (0.5 + camV * 0.34)}, ${dau[0] + R_DAU * (0.42 + camV * 0.4)} ${dau[1] + R_DAU * 0.98}, ${dau[0]} ${dau[1] + R_DAU * 0.98}
              C ${dau[0] - R_DAU * (0.42 + camV * 0.4)} ${dau[1] + R_DAU * 0.98}, ${dau[0] - R_DAU} ${dau[1] + R_DAU * (0.5 + camV * 0.34)}, ${dau[0] - R_DAU} ${dau[1] - 4} Z`}
          fill={da} stroke={V} strokeWidth={NG} strokeLinejoin="round"
        />

        {/* MẮT — tròng trắng to, con ngươi nhỏ và ĐI THEO HƯỚNG NHÌN. Mắt to là chỗ khán giả
            đọc cảm xúc; đây là lý do chính khiến đầu phải to. */}
        {[-1, 1].map((s) => (
          <g key={s}>
            <ellipse cx={dau[0] + s * cachMat} cy={dau[1] + yMat} rx={rMat} ry={rMat * (0.24 + 0.86 * mm)}
                     fill="#FFFFFF" stroke={V} strokeWidth={NT * 1.25} />
            {mm > 0.22 ? (
              <>
                <circle cx={dau[0] + s * cachMat + mx} cy={dau[1] + yMat + my} r={rTrong} fill="#1B1D25" />
                <circle cx={dau[0] + s * cachMat + mx - rTrong * 0.34} cy={dau[1] + yMat + my - rTrong * 0.4}
                        r={rTrong * 0.32} fill="#FFFFFF" />
              </>
            ) : null}
          </g>
        ))}

        {/* LÔNG MÀY — vẽ như một nét cong dày, không phải một gạch thẳng. Độ nghiêng lấy từ
            bảng cảm xúc; đây là chỗ đọc ra "đang bực" hay "đang ngơ" trước cả miệng. */}
        {[-1, 1].map((s) => {
          const bx = dau[0] + s * cachMat;
          const by = dau[1] + yMay;
          const ng = E.may * s * -1;
          return (
            <path key={s}
              d={`M ${bx - 16} ${by + ng * 0.34} Q ${bx} ${by - 7 - ng * 0.2} ${bx + 16} ${by - ng * 0.34}`}
              stroke={kieu.toc} strokeWidth={7.5} fill="none" strokeLinecap="round" />
          );
        })}

        {/* MÁ HỒNG — hai chấm mờ. Rẻ tiền về mặt kỹ thuật mà đổi hẳn cảm giác: có má hồng thì
            nhân vật đọc ra là dễ thương, không có thì đọc ra là hình minh hoạ. */}
        <ellipse cx={dau[0] - cachMat - 8} cy={dau[1] + 16} rx={12} ry={7} fill="#E8836F" opacity={0.3} />
        <ellipse cx={dau[0] + cachMat + 8} cy={dau[1] + 16} rx={12} ry={7} fill="#E8836F" opacity={0.3} />

        {/* MŨI — một nét cong nhỏ, không vẽ lỗ mũi (lỗ mũi ở cỡ này đọc ra là vết bẩn) */}
        <path d={`M ${dau[0] - 4} ${dau[1] + 11} q 5 7 9 0`} stroke={V} strokeWidth={NT * 1.25} fill="none" strokeLinecap="round" />

        {/* MIỆNG — mở theo khẩu hình. Có lưỡi và răng khi mở to, vì một cái lỗ đen thui đọc ra
            là thủng mặt chứ không phải đang nói. */}
        <g>
          <path
            d={`M ${dau[0] - mW / 2} ${dau[1] + yMieng - khoe * 0.5}
                Q ${dau[0]} ${dau[1] + yMieng - khoe} ${dau[0] + mW / 2} ${dau[1] + yMieng - khoe * 0.5}
                Q ${dau[0] + mW * (0.24 + noi.tron * 0.16)} ${dau[1] + yMieng + mH}
                  ${dau[0]} ${dau[1] + yMieng + mH}
                Q ${dau[0] - mW * (0.24 + noi.tron * 0.16)} ${dau[1] + yMieng + mH}
                  ${dau[0] - mW / 2} ${dau[1] + yMieng - khoe * 0.5} Z`}
            fill="#6E2A2E" stroke={V} strokeWidth={NT * 1.4} strokeLinejoin="round"
          />
          {mH > 12 ? (
            <>
              <path d={`M ${dau[0] - mW / 2 + 3} ${dau[1] + yMieng - khoe * 0.5 + 1}
                        L ${dau[0] + mW / 2 - 3} ${dau[1] + yMieng - khoe * 0.5 + 1}
                        L ${dau[0] + mW / 2 - 6} ${dau[1] + yMieng - khoe * 0.5 + 7}
                        L ${dau[0] - mW / 2 + 6} ${dau[1] + yMieng - khoe * 0.5 + 7} Z`}
                    fill="#FFFFFF" />
              <ellipse cx={dau[0]} cy={dau[1] + yMieng + mH * 0.62} rx={mW * 0.26} ry={mH * 0.28} fill="#C4636B" />
            </>
          ) : null}
        </g>

        {/* RÂU — vẽ SAU miệng thì nó phủ mất miệng; vẽ trước thì miệng nằm trên. Đây là bẫy đã
            gặp một lần ở bản cũ. */}
        {kieu.rau === "ria" ? (
          <path d={`M ${dau[0] - 20} ${dau[1] + yMieng - 9} q 20 -9 40 0 q -8 8 -20 8 q -12 0 -20 -8 Z`}
                fill={kieu.toc} stroke={V} strokeWidth={NT} strokeLinejoin="round" />
        ) : null}
        {kieu.rau === "de" ? (
          <path d={`M ${dau[0] - 13} ${dau[1] + yMieng + mH + 3} q 13 16 26 0 q -4 20 -13 20 q -9 0 -13 -20 Z`}
                fill={kieu.toc} stroke={V} strokeWidth={NT} strokeLinejoin="round" />
        ) : null}
        {kieu.rau === "quai" ? (
          <path d={`M ${dau[0] - R_DAU * 0.96} ${dau[1] - 6}
                    Q ${dau[0] - R_DAU * 0.8} ${dau[1] + R_DAU * 0.92} ${dau[0]} ${dau[1] + R_DAU * 1.02}
                    Q ${dau[0] + R_DAU * 0.8} ${dau[1] + R_DAU * 0.92} ${dau[0] + R_DAU * 0.96} ${dau[1] - 6}
                    q -12 26 -24 22 q -18 -6 -34 -6 q -16 0 -34 6 q -12 4 -24 -22 Z`}
                fill={kieu.toc} stroke={V} strokeWidth={NT} strokeLinejoin="round" opacity={0.96} />
        ) : null}

        {kieu.kinh ? (
          <g stroke={V} strokeWidth={NT * 1.5} fill="none">
            <circle cx={dau[0] - cachMat} cy={dau[1] + yMat} r={rMat + 6} fill="#FFFFFF" fillOpacity={0.13} />
            <circle cx={dau[0] + cachMat} cy={dau[1] + yMat} r={rMat + 6} fill="#FFFFFF" fillOpacity={0.13} />
            <line x1={dau[0] - cachMat + rMat + 6} y1={dau[1] + yMat} x2={dau[0] + cachMat - rMat - 6} y2={dau[1] + yMat} />
          </g>
        ) : null}

        {/* TÓC — đặt CUỐI cùng để nó phủ lên mép sọ, đúng như tóc thật phủ lên trán. */}
        <Toc kieu={kieu} dau={dau} R={R_DAU} V={V} NG={NG} t={t} />
      </g>
    </g>
  );
};

/** Tóc — chín kiểu, vẽ bám theo vòm sọ. Đuôi tóc và búi có trễ pha nên đầu quay thì tóc theo sau. */
const Toc: React.FC<{ kieu: Kieu; dau: [number, number]; R: number; V: string; NG: number; t: number }> =
({ kieu, dau, R, V, NG, t }) => {
  const c = kieu.toc, k = kieu.kieuToc;
  const [x, y] = dau;
  const s = { fill: c, stroke: V, strokeWidth: NG * 0.82, strokeLinejoin: "round" as const };
  const tre = treo(0, t, 0.16, 2.2);
  if (k === "trocs") {
    return <path d={`M ${x - R} ${y - 6} C ${x - R} ${y - R * 0.9}, ${x + R} ${y - R * 0.9}, ${x + R} ${y - 6}
                     q -14 -16 -${R * 0.9} -16 q -${R * 0.7} 0 -${R * 0.2} 16 Z`} {...s} opacity={0.001} />;
  }
  const vom = `M ${x - R - 2} ${y - 2}
               C ${x - R - 2} ${y - R * 1.2}, ${x + R + 2} ${y - R * 1.2}, ${x + R + 2} ${y - 2}`;
  return (
    <g>
      {/* Vòm tóc chung cho mọi kiểu — khác nhau ở phần rủ xuống bên dưới */}
      <path d={`${vom} C ${x + R} ${y - R * 0.42}, ${x + R * 0.3} ${y - R * 0.6}, ${x} ${y - R * 0.58}
                C ${x - R * 0.3} ${y - R * 0.6}, ${x - R} ${y - R * 0.42}, ${x - R - 2} ${y - 2} Z`} {...s} />
      {k === "bui" ? <circle cx={x + tre * 0.5} cy={y - R * 1.22} r={22} {...s} /> : null}
      {k === "duoi_ngua" ? (
        <path d={`M ${x + R * 0.8} ${y - R * 0.5} q ${26 + tre} ${18} ${16 + tre} ${58} q -12 -22 -26 -34 Z`} {...s} />
      ) : null}
      {k === "bob" ? (
        <path d={`M ${x - R - 2} ${y - 6} q -4 ${R * 0.9} 6 ${R * 1.05} l 12 -6 q -8 -${R * 0.62} -6 -${R * 0.92} Z
                  M ${x + R + 2} ${y - 6} q 4 ${R * 0.9} -6 ${R * 1.05} l -12 -6 q 8 -${R * 0.62} 6 -${R * 0.92} Z`} {...s} />
      ) : null}
      {k === "xoan" ? (
        <g>{[-1, -0.45, 0.45, 1].map((p, i) => (
          <circle key={i} cx={x + p * R * 0.84} cy={y - R * (0.78 + Math.abs(p) * 0.12)} r={19} {...s} />
        ))}</g>
      ) : null}
      {k === "roi" || k === "hoi" ? (
        <path d={`M ${x - R * 0.7} ${y - R * 0.72} l 10 -22 l 8 18 l 12 -26 l 10 24 l 14 -20 l 6 22 Z`} {...s} />
      ) : null}
      {k === "re_ngoi" ? (
        <path d={`M ${x - R * 0.16} ${y - R * 0.95} l 4 26 l -10 -4 Z`} fill={V} opacity={0.5} />
      ) : null}
    </g>
  );
};

export { visemeTai };
export type { Tu };
