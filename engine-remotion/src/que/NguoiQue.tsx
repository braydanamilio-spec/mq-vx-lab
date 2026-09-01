import React from "react";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   NGƯỜI QUE — vẽ đúng ảnh mẫu anh gửi  (1/9/2026)

   Anh gửi ảnh tham chiếu và nói *"làm như e hiện xấu"*. Đúng: bản trước là HÀNG LAI — lấy rig
   cartoon (đầu tròn to r40, mắt anime có tròng và điểm sáng, thân khiên đặc) rồi bóp tay chân
   cho mảnh. Kết quả là cái đầu khổng lồ đặt trên que tăm, thêm một thanh ngang vai như bù nhìn.
   Không ra người que, cũng không ra cartoon.

   Ảnh mẫu cho thấy sáu điều, và cả sáu đều KHÁC bản cũ:
     1. đầu là VÒNG TRÒN VIỀN, ruột trắng — không phải khối màu da
     2. mặt: hai CHẤM mắt + một nét cười + hai nét mày — không phải mắt to có tròng
     3. thân: MỘT nét dọc mảnh — không phải khối đặc, và KHÔNG có thanh vai
     4. tay mọc từ gần ĐỈNH thân, không từ hai vai rộng
     5. nét tay chân ĐỀU NHAU, mảnh
     6. bàn tay nhỏ, bàn chân là ô van sẫm dẹt

   Nên viết riêng thay vì bẻ tiếp rig cũ: bẻ tiếp thì vẫn mang theo mọi giả định của cartoon.
   Chuyển động thì DÙNG LẠI `POSES` + `live()` của `StickAnim` — đó là phần hay thật (cẳng tay
   trễ pha so cánh tay, chân dồn trọng tâm so le), không việc gì phải viết lại.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

const RAD = Math.PI / 180;

/* SỐ ĐO XUẤT RA NGOÀI — để nơi dùng KHÔNG PHẢI ĐOÁN.
   Bản trước lơ lửng vì `KichQue` tự đoán "chân dài chừng 62 đơn vị" rồi trừ đi. Đoán sai 43
   đơn vị, nhân với tỉ lệ 4,9 thành 210px — mắt thấy ngay mà không ai biết sửa số nào.
   Nay chính tệp vẽ khai ra, và có cổng đo pixel đối chiếu (`kiem_san.py`). */
export const QUE_GOT = 105;   // gốc (hông) -> đáy gót
export const QUE_DINH = 210;  // gốc (hông) -> đỉnh đầu
export const QUE_CAO = QUE_GOT + QUE_DINH;   // tổng chiều cao rig
const PT = (x: number, y: number, len: number, deg: number): [number, number] =>
  [x + Math.cos(deg * RAD) * len, y + Math.sin(deg * RAD) * len];

/* XOÈ CHI RA KHỎI TRỤC THÂN.
   `POSES` viết cho rig cartoon: `idle` cho armL 100° / armR 80°, tức chỉ lệch 10° khỏi phương
   thẳng đứng. Ở rig ấy thân là một tấm khiên bề ngang ~70 đơn vị, nên cánh tay 10° vẫn nằm hẳn
   bên ngoài và nhìn thấy rõ. Ở đây thân là MỘT NÉT — nên cánh tay 10° nằm ĐÈ LÊN chính nét thân
   và biến mất. Soi khung ra đúng thế: nhân vật chỉ còn một tay, hai chân chập thành một que.

   KHÔNG sửa `POSES`: nó là của chung với `StickStory`, đụng vào là bộ kia lệch — đúng cái bẫy
   "vá một nhánh làm hỏng nhánh song song" đã ghi ở CLAUDE.md. Chỉ đổi ở nơi VẼ.

   Phép xoè giữ nguyên tư thế lớn (chỉ tay, giơ tay, nhún vai vẫn y nguyên vì biên độ đã lớn) và
   chỉ nống những góc quá sát trục — cái ngưỡng ấy mới là chỗ hỏng. */
const xoe = (g: number, ben: number, toi: number, them: number) => {
  const d = (g - 90) * ben;               // độ mở ra ngoài; âm = quặp vào trong
  return 90 + ben * (d < toi ? d + them : d);
};

export type Pose = {
  armL: number; foreL: number; armR: number; foreR: number;
  legL: number; shinL: number; legR: number; shinR: number;
  headTilt: number; lean: number;
};

/* Biểu cảm bằng BA số, đúng thứ nét vẽ này chở được: độ cong mày · độ mở mắt · độ cong miệng.
   Nét que không có má, không có nếp nhăn — thêm vào là quay lại lỗi cũ. */
export const NET_MAT: Record<string, { may: number; mat: number; mieng: number }> = {
  neutral:    { may: 0,    mat: 1,    mieng: 0.30 },
  curious:    { may: 0.55, mat: 1.12, mieng: 0.12 },
  shock:      { may: 0.95, mat: 1.45, mieng: -0.10 },
  annoyed:    { may: -0.7, mat: 0.80, mieng: -0.45 },
  happy:      { may: 0.25, mat: 1.05, mieng: 0.85 },
  suspicious: { may: -0.4, mat: 0.72, mieng: -0.15 },
  sad:        { may: 0.6,  mat: 0.92, mieng: -0.70 },
};

export const NguoiQue: React.FC<{
  x: number; y: number; scale?: number; flip?: boolean; pose: Pose;
  mouthOpen?: number; expr?: string; blink?: number; breath?: number;
  muc?: string;        // màu nét — mặc định đen mực
  toc?: string;        // kiểu tóc: "" | "re" | "bum" | "xoan" | "mu"
  nhan?: string;       // màu nhấn riêng của vai (mũ / nơ / khăn)
  dam?: number;        // độ dày nét
}> = ({ x, y, scale = 1, flip = false, pose, mouthOpen = 0, expr = "neutral",
        blink = 1, breath = 0, muc = "#14110F", toc = "re", nhan = "", dam = 7 }) => {
  const e = NET_MAT[expr] || NET_MAT.neutral;

  // ── KHUNG XƯƠNG ────────────────────────────────────────────────────────────────────────
  // GỐC TOẠ ĐỘ = HÔNG, y âm là lên. Cùng quy ước với `StickAnim` nên `POSES` dùng lại được
  // nguyên vẹn (góc thì không có đơn vị, đổi tỉ lệ chi không ảnh hưởng).
  // Tỉ lệ lấy từ ảnh mẫu: đầu ~1/4 chiều cao, thân ~1/3, chân ~2/5. KHÔNG chép số của rig
  // cartoon — số ấy sinh ra cho một hình có tỉ lệ khác hẳn (đó đúng là lỗi đã đẻ ra bản xấu).
  const R = 40;                                   // bán kính đầu (46 -> 40: soi khung ra đầu vẫn to hơn ảnh mẫu)
  const THAN = 132;                               // cổ -> hông
  const yCo = -THAN - breath * 0.25;
  const lean = pose.lean * 0.5;
  const co: [number, number] = [lean, yCo];
  const hong: [number, number] = [0, 0];
  const dauC: [number, number] = [lean + pose.headTilt * 0.5, yCo - R * 0.94];

  // Tay mọc từ gần ĐỈNH thân (ảnh mẫu: ngay dưới đầu), không từ hai vai rộng.
  const vai: [number, number] = [lean * (1 - 16 / THAN), yCo + 16];
  const DT = 46, DC = 44;                          // dài cánh tay / cẳng tay
  const gArmL = xoe(pose.armL, 1, 22, 18), gForeL = xoe(pose.foreL, 1, 22, 18);
  const gArmR = xoe(pose.armR, -1, 22, 18), gForeR = xoe(pose.foreR, -1, 22, 18);
  const aL = PT(vai[0], vai[1], DT, gArmL), fL = PT(aL[0], aL[1], DC, gForeL);
  const aR = PT(vai[0], vai[1], DT, gArmR), fR = PT(aR[0], aR[1], DC, gForeR);
  const DD = 50, DS = 48;                          // dài đùi / cẳng chân
  // Chân xoè ít hơn tay: dáng đứng, không phải dạng háng.
  const gLegL = xoe(pose.legL, 1, 13, 9), gShinL = xoe(pose.shinL, 1, 13, 9);
  const gLegR = xoe(pose.legR, -1, 13, 9), gShinR = xoe(pose.shinR, -1, 13, 9);
  const gL = PT(hong[0], hong[1], DD, gLegL), cL = PT(gL[0], gL[1], DS, gShinL);
  const gR = PT(hong[0], hong[1], DD, gLegR), cR = PT(gR[0], gR[1], DS, gShinR);

  const net = (a: number[], b: number[], w = dam) => (
    <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={muc} strokeWidth={w}
          strokeLinecap="round" />
  );
  // Bàn tay: ba ngón ngắn toè ra, đúng kiểu ảnh mẫu — không phải hình tròn đặc.
  const ban_tay = (p: number[], goc: number) => (
    <g>
      {[-26, 0, 26].map((d, i) => {
        const q = PT(p[0], p[1], 13, goc + d);
        return <line key={i} x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} stroke={muc}
                     strokeWidth={dam * 0.62} strokeLinecap="round" />;
      })}
    </g>
  );
  const ban_chan = (p: number[], huong: number) => (
    <ellipse cx={p[0] + huong * 11} cy={p[1] + 2} rx={17} ry={7} fill={muc}
             transform={`rotate(${huong * -6} ${p[0]} ${p[1]})`} />
  );

  const mo = Math.min(1, mouthOpen);
  const mm = e.mieng;

  return (
    <g transform={`translate(${x} ${y}) scale(${flip ? -scale : scale} ${scale})`}>
      {/* chân sau -> chân trước, tay sau -> tay trước: thứ tự vẽ cho ra chiều sâu */}
      {net(hong, gR)}{net(gR, cR)}{ban_chan(cR, 1)}
      {net(hong, gL)}{net(gL, cL)}{ban_chan(cL, -1)}
      {net(co, hong)}
      {net(vai, aR)}{net(aR, fR)}{ban_tay(fR, gForeR)}
      {net(vai, aL)}{net(aL, fL)}{ban_tay(fL, gForeL)}

      <g transform={`rotate(${pose.headTilt * 0.8} ${dauC[0]} ${dauC[1]})`}>
        {/* tóc: vài nét ngắn trên đỉnh — thứ duy nhất tách nhân vật này với nhân vật kia ở nét que */}
        {/* Tóc: vài nét NGẮN, VUỐT XUÔI một chiều. Bản trước để nét dài R*0,42 toả đúng phương
            bán kính, nên soi khung ra một vòng tia như mặt trời vẽ trẻ con, không ra tóc. */}
        {toc === "re" ? [-26, -9, 9, 26].map((d, i) => {
          const a = PT(dauC[0], dauC[1], R * 0.99, 270 + d), b = PT(a[0], a[1], R * 0.26, 300 + d * 0.5);
          return <line key={i} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={muc}
                       strokeWidth={dam * 0.7} strokeLinecap="round" />;
        }) : null}
        {toc === "bum" ? (
          <circle cx={dauC[0] + 2} cy={dauC[1] - R * 1.04} r={R * 0.32} fill="none"
                  stroke={muc} strokeWidth={dam * 0.8} />
        ) : null}
        {toc === "xoan" ? [-30, -10, 10, 30].map((d, i) => (
          <circle key={i} cx={PT(dauC[0], dauC[1], R * 0.95, 270 + d)[0]}
                  cy={PT(dauC[0], dauC[1], R * 0.95, 270 + d)[1]}
                  r={R * 0.24} fill="none" stroke={muc} strokeWidth={dam * 0.6} />
        )) : null}
        {toc === "mu" ? (
          <g>
            <path d={`M ${dauC[0] - R * 0.96} ${dauC[1] - R * 0.30}
                      a ${R} ${R} 0 0 1 ${R * 1.92} 0 z`}
                  fill={nhan || "#D9793C"} stroke={muc} strokeWidth={dam * 0.8} />
            <path d={`M ${dauC[0] + R * 0.5} ${dauC[1] - R * 0.30} l ${R * 0.72} 6`}
                  stroke={muc} strokeWidth={dam * 0.8} strokeLinecap="round" fill="none" />
          </g>
        ) : null}

        <circle cx={dauC[0]} cy={dauC[1]} r={R} fill="#FFFFFF" stroke={muc} strokeWidth={dam} />

        {/* mày: hai nét cong, độ cong = biểu cảm */}
        {[-1, 1].map((sg) => (
          <path key={`m${sg}`}
                d={`M ${dauC[0] + sg * R * 0.17} ${dauC[1] - R * 0.50 - e.may * 3}
                    q ${sg * R * 0.20} ${(-4 - e.may * 6)} ${sg * R * 0.42} ${1 - e.may * 2}`}
                fill="none" stroke={muc} strokeWidth={dam * 0.6} strokeLinecap="round" />
        ))}
        {/* mắt: hai CHẤM. Nhắm mắt thì bẹt lại thành nét ngang. */}
        {[-1, 1].map((sg) => (
          <ellipse key={`e${sg}`} cx={dauC[0] + sg * R * 0.33} cy={dauC[1] - R * 0.10}
                   rx={R * 0.115} ry={R * 0.115 * e.mat * blink} fill={muc} />
        ))}
        {/* miệng: một nét cong; nói thì há thành hình bầu dục */}
        {mo > 0.12 ? (
          <ellipse cx={dauC[0]} cy={dauC[1] + R * 0.44} rx={R * 0.20 + mo * R * 0.08}
                   ry={R * 0.09 + mo * R * 0.22} fill={muc} />
        ) : (
          <path d={`M ${dauC[0] - R * 0.36} ${dauC[1] + R * 0.36 - mm * 4}
                    q ${R * 0.36} ${mm * R * 0.46} ${R * 0.72} 0`}
                fill="none" stroke={muc} strokeWidth={dam * 0.78} strokeLinecap="round" />
        )}
      </g>
    </g>
  );
};
