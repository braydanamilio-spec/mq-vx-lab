import React from "react";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   NGƯỜI QUE — nét chung, người riêng  (1/9/2026)

   Hai ảnh anh gửi nói hai việc khác nhau, và phải làm cả hai:
     Ảnh 1 (người que trắng đen) — NGÔN NGỮ NÉT: đầu tròn viền ruột trắng, thân một nét, tay
       chân nét đều mảnh, bàn tay nhỏ, bàn chân ô van.
     Ảnh 2 (ba người trên sa mạc) — SỰ KHÁC NHAU: vẫn ngôn ngữ ấy, nhưng người tóc dài xoã,
       người tóc bù, người hói; ai cũng có áo riêng; mắt có mí nên đọc được cảm xúc.
   Anh chốt: *"nhân vật ko phải giống hết, đa nhân vật và đa dạng, có nét đặc trưng."*

   VÌ SAO BẢN TRƯỚC AI CŨNG NHƯ AI. Không phải vì thiếu ý tưởng, mà vì tôi đọc bản khoá nhân
   vật của gói rồi chỉ lấy ra hai màu áo/quần và vứt phần còn lại. Gói viết sẵn "short curly
   gray hair, purple glasses, floral blouse" cho từng vai — năm mươi vai khác nhau trên giấy,
   ra hình thành một người lặp lại năm mươi lần. Dữ liệu vẫn nằm đó suốt.

   ĐƠN VỊ. Gốc toạ độ = HÔNG, y âm là lên, cùng quy ước `StickAnim` nên `POSES` dùng lại nguyên
   vẹn. Mọi kích thước neo vào `R` (bán kính đầu) hoặc `THAN`, không có số rời.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

const RAD = Math.PI / 180;
const PT = (x: number, y: number, len: number, deg: number): [number, number] =>
  [x + Math.cos(deg * RAD) * len, y + Math.sin(deg * RAD) * len];

/* SỐ ĐO XUẤT RA NGOÀI — để nơi dùng KHÔNG PHẢI ĐOÁN.
   Bản đầu lơ lửng vì `KichQue` tự đoán "chân dài chừng 62 đơn vị" rồi trừ đi; đoán hụt 43 đơn
   vị, nhân tỉ lệ thành 210px. Mắt thấy ngay mà không ai biết sửa số nào. */
export const QUE_GOT = 105;                    // gốc (hông) -> đáy gót
export const QUE_DINH = 210;                   // gốc (hông) -> đỉnh đầu
export const QUE_CAO = QUE_GOT + QUE_DINH;     // 315

/* XOÈ CHI RA KHỎI TRỤC THÂN.
   `POSES` viết cho rig cartoon: `idle` cho armL 100° / armR 80°, chỉ lệch 10° khỏi phương thẳng
   đứng. Ở rig ấy thân là tấm khiên rộng ~70 đơn vị nên tay 10° vẫn nằm hẳn bên ngoài. Ở đây
   thân là MỘT NÉT, nên tay 10° nằm ĐÈ LÊN chính nét thân và biến mất — soi khung ra nhân vật
   một tay, hai chân chập thành một que.
   KHÔNG sửa `POSES`: dùng chung với `StickStory`, đụng vào là hỏng nhánh song song. */
const xoe = (g: number, ben: number, toi: number, them: number) => {
  const d = (g - 90) * ben;
  return 90 + ben * (d < toi ? d + them : d);
};

export type Pose = {
  armL: number; foreL: number; armR: number; foreR: number;
  legL: number; shinL: number; legR: number; shinR: number;
  headTilt: number; lean: number;
};

/* Biểu cảm bằng BỐN số — đúng thứ nét vẽ này chở được: độ cong mày · độ mở mắt · độ sụp mí ·
   độ cong miệng. Mí mắt là thứ ảnh 2 có mà bản trước không có, và nó gánh phần lớn cảm xúc:
   cùng một cặp mắt tròn, hạ mí xuống một nửa là ra ngay vẻ chán đời. */
export const NET_MAT: Record<string, { may: number; mat: number; mi: number; mieng: number }> = {
  neutral:    { may: 0,    mat: 1,    mi: 0.10, mieng: 0.30 },
  curious:    { may: 0.55, mat: 1.12, mi: 0,    mieng: 0.12 },
  shock:      { may: 0.95, mat: 1.45, mi: 0,    mieng: -0.10 },
  annoyed:    { may: -0.7, mat: 0.95, mi: 0.52, mieng: -0.45 },
  happy:      { may: 0.25, mat: 1.05, mi: 0.05, mieng: 0.85 },
  suspicious: { may: -0.4, mat: 0.90, mi: 0.60, mieng: -0.15 },
  sad:        { may: 0.6,  mat: 0.92, mi: 0.34, mieng: -0.70 },
  deadpan:    { may: -0.1, mat: 1.0,  mi: 0.55, mieng: 0.02 },
};

export type Vai = {
  gioi: string;      // nam | nu
  tuoi: string;      // tre_con | tre | trung | gia
  toc: string;       // ngan | dai | song | xoan | bu | duoi_ngua | bum | troc
  mauToc: string;
  ao: string;
  quan: string;
  pk: string[];      // kinh | rau | mu | khan | day_deo | tap_de | hoodie | vay
};

export const NguoiQue: React.FC<{
  x: number; y: number; scale?: number; flip?: boolean; pose: Pose; vai: Vai;
  mouthOpen?: number; expr?: string; blink?: number; breath?: number;
  mo?: number;       // độ đậm: 1 = người đang nói, <1 = người đứng nghe
}> = ({ x, y, scale = 1, flip = false, pose, vai, mouthOpen = 0, expr = "neutral",
        blink = 1, breath = 0, mo: doDam = 1 }) => {
  const e = NET_MAT[expr] || NET_MAT.neutral;
  const muc = "#1A1613";
  const treCon = vai.tuoi === "tre_con";
  const gia = vai.tuoi === "gia";

  // ── KHUNG XƯƠNG ────────────────────────────────────────────────────────────────────────
  // Trẻ con KHÔNG phải người lớn thu nhỏ: đầu chiếm tỉ lệ lớn hơn, thân ngắn hơn. Thu nhỏ đều
  // thì ra người lùn chứ không ra trẻ con — cùng lỗi "con cao bằng bố" đã ghi cho bộ truyện
  // tranh, nay không lặp lại nữa vì chiều cao đọc từ TUỔI THẬT trong gói.
  const R = treCon ? 42 : 40;
  const THAN = treCon ? 108 : 132;
  const dam = 7;
  const yCo = -THAN - breath * 0.25;
  const lean = pose.lean * 0.5 + (gia ? 5 : 0);   // người già hơi khom về trước
  const co: [number, number] = [lean, yCo];
  const hong: [number, number] = [0, 0];
  const dauC: [number, number] = [lean + pose.headTilt * 0.5, yCo - R * 0.94];

  /* VAI ÁO là nơi tay mọc ra, KHÔNG phải trục giữa thân.
     Bản trước cho cả hai tay mọc từ đúng một điểm trên trục giữa. Khi thân là một nét trần thì
     không sao. Nhưng vừa mặc áo vào là cả cánh tay nằm LỌT TRONG áo, chỉ còn mẩu cẳng tay thò
     ra — soi khung thấy bốn người cụt tay. Đây là họ lỗi quen: thêm một lớp mới mà không rà
     lại những chỗ lớp cũ đang dựa vào một giả định giờ đã sai. */
  const vaiW = R * 0.72;                       // nửa bề ngang vai áo
  const yVai = yCo + 14;
  const vaiL: [number, number] = [lean * 0.9 - vaiW, yVai];
  const vaiR: [number, number] = [lean * 0.9 + vaiW, yVai];
  const DT = treCon ? 38 : 46, DC = treCon ? 36 : 44;
  const gArmL = xoe(pose.armL, 1, 22, 18), gForeL = xoe(pose.foreL, 1, 22, 18);
  const gArmR = xoe(pose.armR, -1, 22, 18), gForeR = xoe(pose.foreR, -1, 22, 18);
  const aL = PT(vaiL[0], vaiL[1], DT, gArmL), fL = PT(aL[0], aL[1], DC, gForeL);
  const aR = PT(vaiR[0], vaiR[1], DT, gArmR), fR = PT(aR[0], aR[1], DC, gForeR);
  const DD = treCon ? 38 : 50, DS = treCon ? 36 : 48;
  const gLegL = xoe(pose.legL, 1, 13, 9), gShinL = xoe(pose.shinL, 1, 13, 9);
  const gLegR = xoe(pose.legR, -1, 13, 9), gShinR = xoe(pose.shinR, -1, 13, 9);
  const gL = PT(hong[0], hong[1], DD, gLegL), cL = PT(gL[0], gL[1], DS, gShinL);
  const gR = PT(hong[0], hong[1], DD, gLegR), cR = PT(gR[0], gR[1], DS, gShinR);

  const net = (a: number[], b: number[], w = dam) => (
    <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={muc} strokeWidth={w} strokeLinecap="round" />
  );
  const banTay = (p: number[], goc: number) => (
    <g>{[-26, 0, 26].map((d, i) => {
      const q = PT(p[0], p[1], 13, goc + d);
      return <line key={i} x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} stroke={muc}
                   strokeWidth={dam * 0.62} strokeLinecap="round" />;
    })}</g>
  );
  const banChan = (p: number[], h: number) => (
    <ellipse cx={p[0] + h * 11} cy={p[1] + 2} rx={17} ry={7} fill={muc}
             transform={`rotate(${h * -6} ${p[0]} ${p[1]})`} />
  );

  // ── ÁO QUẦN — vẽ ĐÈ lên nét thân, tay chân vẫn để trần đúng như ảnh 2 ───────────────────
  const coVay = vai.pk.includes("vay") || vai.gioi === "nu";
  /* Áo HẸP HƠN ĐẦU. Bản trước lấy `THAN*0.30` = 40 nửa-rộng, tức áo rộng bằng đúng đường kính
     đầu — cộng thêm nét viền dày thành một tấm bảng che kín người. Ở ngôn ngữ que, áo chỉ là
     một vệt màu gợi ý quần áo; hẹp hơn đầu thì mắt vẫn đọc ra "cái áo" mà không mất dáng que. */
  /* Áo hẹp hơn ĐẦU và viền NHẸ hơn chi. Bản trước dùng cùng độ đậm viền với tay chân, nên khối
     áo đen kịt hút hết mắt và người biến thành tấm biển quảng cáo. Trong ngôn ngữ que, chi là
     nét CHÍNH, áo chỉ là mảng màu phụ — độ đậm viền phải nói đúng thứ bậc đó. */
  const rongVai = R * 0.62, rongEo = R * 0.54, netAo = dam * 0.45;
    // Gấu váy tới NỬA TRÊN ống chân, không tới mắt cá: che hết chân là mất luôn dáng đi và
  // mất cả cái duyên của nét que — chân que động đậy chính là thứ anh nhớ về loại hoạt hình này.
  const yAo = yCo + 8, yGauAo = coVay ? THAN * 0.24 : THAN * 0.06;
  const AoTren = (
    <g>
      {coVay ? (
        // Váy chữ A: loe từ eo xuống, đây là dấu hiệu giới đọc được từ xa nhất ở nét que
        <path d={`M ${lean - rongVai} ${yAo} L ${lean + rongVai} ${yAo}
                  L ${rongEo * 1.9} ${yGauAo} L ${-rongEo * 1.9} ${yGauAo} Z`}
              fill={vai.ao} stroke={muc} strokeWidth={netAo} strokeLinejoin="round" />
      ) : (
        <path d={`M ${lean - rongVai} ${yAo} L ${lean + rongVai} ${yAo}
                  L ${rongEo} ${yGauAo} L ${-rongEo} ${yGauAo} Z`}
              fill={vai.ao} stroke={muc} strokeWidth={netAo} strokeLinejoin="round" />
      )}
      {/* Cổ áo: một nét chữ V nhỏ. Không có nó thì mảng màu chạm thẳng vào cằm và trông như
          cái yếm; có nó là mắt đọc ra ngay "áo mặc trên người". */}
      <path d={`M ${lean - rongVai * 0.42} ${yAo} L ${lean} ${yAo + R * 0.30} L ${lean + rongVai * 0.42} ${yAo}`}
            fill="none" stroke={muc} strokeWidth={netAo * 1.3} strokeLinejoin="round" />
      {vai.pk.includes("hoodie") ? (
        <path d={`M ${lean - rongVai * 0.9} ${yAo + 2} q ${rongVai * 0.9} ${R * 0.6} ${rongVai * 1.8} 0`}
              fill={vai.ao} stroke={muc} strokeWidth={dam * 0.7} />
      ) : null}
      {vai.pk.includes("day_deo") ? [-1, 1].map((s) => (
        <line key={s} x1={lean + s * rongVai * 0.55} y1={yAo} x2={s * rongEo * 0.6} y2={yGauAo}
              stroke="#B33A32" strokeWidth={dam * 0.7} />
      )) : null}
      {vai.pk.includes("khan") ? (
        <path d={`M ${lean - rongVai} ${yAo + 4} q ${rongVai} ${R * 0.5} ${rongVai * 2} 0
                  l ${-rongVai * 0.3} ${THAN * 0.22} l ${-rongVai * 1.4} 0 Z`}
              fill="#D98BA6" stroke={muc} strokeWidth={dam * 0.6} opacity={0.92} />
      ) : null}
      {vai.pk.includes("tap_de") ? (
        <rect x={-rongEo * 0.7} y={yAo + THAN * 0.18} width={rongEo * 1.4} height={THAN * 0.4}
              fill="#EDE3CE" stroke={muc} strokeWidth={dam * 0.6} />
      ) : null}
    </g>
  );
  // Quần: hai ống ngắn phủ nửa trên đùi. Váy thì không có ống.
  const Quan = coVay ? null : (
    <g>
      {[[gL, gLegL], [gR, gLegR]].map(([g, goc]: any, i) => {
        const m = PT(0, 0, DD * 0.62, goc);
        return <line key={i} x1={0} y1={0} x2={m[0]} y2={m[1]} stroke={vai.quan}
                     strokeWidth={dam * 2.1} strokeLinecap="round" />;
      })}
    </g>
  );

  // ── TÓC — nét nhận dạng mạnh nhất ở khoảng cách xa ─────────────────────────────────────
  const T = vai.mauToc;
  /* TÓC HAI LỚP — `TocSau` vẽ TRƯỚC cái đầu (nên nằm dưới), `TocTren` vẽ SAU (nên nằm trên).
     Bản trước gộp làm một và vẽ hết sau cái đầu: mảng tóc dài đè thẳng lên khuôn mặt, ra một
     cục đen che nửa mặt. Tóc dài mọc từ SAU GÁY — thứ tự vẽ phải nói đúng điều đó. */
  const TocSau = () => {
    const beHong = (rong: number, sau: number) => (
      <path d={`M ${dauC[0] - R * rong} ${dauC[1] - R * 0.2}
                q ${-R * 0.16} ${R * sau} ${R * 0.30} ${R * sau}
                l ${R * (rong * 2 - 0.6)} 0
                q ${R * 0.46} 0 ${R * 0.30} ${-R * sau} Z`}
            fill={T} stroke={muc} strokeWidth={dam * 0.6} strokeLinejoin="round" />
    );
    switch (vai.toc) {
      case "dai":  return beHong(1.02, 1.75);
      case "song": return beHong(1.06, 1.35);
      case "xoan": return beHong(1.10, 0.55);
      case "duoi_ngua": return (
        <path d={`M ${dauC[0] + R * 0.5} ${dauC[1] - R * 0.9}
                  q ${R * 1.15} ${R * 0.35} ${R * 0.78} ${R * 1.75}
                  q ${-R * 0.12} ${R * 0.28} ${-R * 0.5} ${R * 0.06}
                  q ${R * 0.34} ${-R * 1.15} ${-R * 0.58} ${-R * 1.62} Z`}
              fill={T} stroke={muc} strokeWidth={dam * 0.6} />);
      case "bum": return (
        <circle cx={dauC[0] - R * 0.05} cy={dauC[1] - R * 1.18} r={R * 0.36}
                fill={T} stroke={muc} strokeWidth={dam * 0.7} />);
      default: return null;
    }
  };

  /* Phần trên: chỏm tóc ôm sọ. Đây là nét phân biệt mạnh nhất ở khoảng cách xa — trên khung
     dọc điện thoại, người xem nhận ra ai là ai bằng KHỐI TÓC chứ không bằng khuôn mặt. */
  const TocTren = () => {
    /* CHÂN TÓC ở khoảng 35° trên đường ngang, không phải ở giữa đầu.
       Bản trước bắt đầu vòng cung từ y = tâm − 0,20R và quét hết nửa trên: ra một cái mũ bảo
       hiểm đen trùm kín sọ, che luôn viền mặt — soi khung thấy cả nhà đội mũ len. Tóc thật chỉ
       phủ khoảng một phần ba trên của khuôn mặt nhìn thẳng.
       `sau` = tóc dày tới đâu (rẽ ngôi thì mỏng, tóc bù thì dày). */
    const chom = (sau: number) => {
      const gx = R * 0.82, gy = -R * 0.57;          // hai chân tóc hai bên thái dương
      return (
        <path d={`M ${dauC[0] - gx} ${dauC[1] + gy}
                  A ${R} ${R} 0 0 1 ${dauC[0] + gx} ${dauC[1] + gy}
                  q ${-R * 0.30} ${R * sau} ${-R * 0.80} ${R * sau * 0.62}
                  q ${-R * 0.42} ${-R * sau * 0.30} ${-R * 0.84} ${-R * sau * 0.62} Z`}
              fill={T} stroke={muc} strokeWidth={dam * 0.6} strokeLinejoin="round" />
      );
    };
    switch (vai.toc) {
      case "troc":
        return gia ? (
          <path d={`M ${dauC[0] - R * 1.0} ${dauC[1] - R * 0.1}
                    a ${R} ${R} 0 0 1 ${R * 0.44} ${-R * 0.78}`}
                fill="none" stroke={T} strokeWidth={dam * 1.4} strokeLinecap="round" />) : null;
      case "xoan": return (
        <g>{[-64, -38, -13, 13, 38, 64].map((d, i) => {
          const q = PT(dauC[0], dauC[1], R * 0.94, 270 + d);
          return <circle key={i} cx={q[0]} cy={q[1]} r={R * 0.27} fill={T} stroke={muc}
                         strokeWidth={dam * 0.5} />;
        })}</g>);
      case "bu": return (
        <g>
          {chom(0.34)}
          {[-56, -32, -10, 12, 34, 58].map((d, i) => {
            const q = PT(dauC[0], dauC[1], R * 0.95, 270 + d);
            const r2 = PT(q[0], q[1], R * (0.30 + (i % 3) * 0.12), 270 + d * 1.7 - 12);
            return <line key={i} x1={q[0]} y1={q[1]} x2={r2[0]} y2={r2[1]} stroke={T}
                         strokeWidth={dam * 1.1} strokeLinecap="round" />;
          })}
        </g>);
      case "dai": case "song": case "duoi_ngua": case "bum": return chom(0.30);
      default: return chom(0.22);   // ngan
    }
  };

  const m = Math.min(1, mouthOpen);
  const mm = e.mieng;
  const rMat = R * 0.115;
  const mi = e.mi > 0.25 && blink > 0.5;   // chỉ vẽ mắt có mí khi biểu cảm THẬT SỰ cần nó

  return (
    <g transform={`translate(${x} ${y}) scale(${flip ? -scale : scale} ${scale})`} opacity={doDam}>
      {net(hong, gR)}{net(gR, cR)}{banChan(cR, 1)}
      {net(hong, gL)}{net(gL, cL)}{banChan(cL, -1)}
      {Quan}
      {net(co, hong)}
      {AoTren}
      {net(vaiR, aR)}{net(aR, fR)}{banTay(fR, gForeR)}
      {net(vaiL, aL)}{net(aL, fL)}{banTay(fL, gForeL)}

      <g transform={`rotate(${pose.headTilt * 0.8} ${dauC[0]} ${dauC[1]})`}>
        {/* TÓC HAI LỚP. Bản trước vẽ cả mảng tóc SAU cái đầu, nên phần dài đè thẳng lên mặt —
            tóc dài ra một cục đen che nửa khuôn mặt. Tóc dài mọc từ SAU gáy: phần buông xuống
            phải nằm DƯỚI cái đầu theo thứ tự vẽ, phần đỉnh mới nằm trên. */}
        <TocSau />
        <circle cx={dauC[0]} cy={dauC[1]} r={R} fill="#FFFFFF" stroke={muc} strokeWidth={dam} />
        <TocTren />
        {[-1, 1].map((sg) => (
          <path key={`m${sg}`}
                d={`M ${dauC[0] + sg * R * 0.17} ${dauC[1] - R * 0.50 - e.may * 3}
                    q ${sg * R * 0.20} ${-4 - e.may * 6} ${sg * R * 0.42} ${1 - e.may * 2}`}
                fill="none" stroke={muc} strokeWidth={dam * 0.6} strokeLinecap="round" />
        ))}
        {[-1, 1].map((sg) => (
          <g key={`e${sg}`}>
            {/* MẮT CÓ TRÒNG TRẮNG + MÍ ĐÈ LÊN TRÊN.
                Bản trước vẽ mí bằng một nét dày `rMat*1.5` gạch ngang qua tròng — soi khung ra
                hai vệt đen như băng bịt mắt, người già thì như đeo kính râm. Mí không phải một
                cái gạch: nó là mép da CHE BỚT phần trên của con mắt. Nên vẽ đúng như thế —
                tròng trắng, con ngươi đen, rồi một vòng cung màu da phủ từ trên xuống. */}
            {mi ? (
              <g>
                <circle cx={dauC[0] + sg * R * 0.33} cy={dauC[1] - R * 0.10} r={rMat * 1.7}
                        fill="#FFFFFF" stroke={muc} strokeWidth={dam * 0.5} />
                <circle cx={dauC[0] + sg * R * 0.33} cy={dauC[1] - R * 0.10 + rMat * 0.35}
                        r={rMat * 0.85} fill={muc} />
                <path d={`M ${dauC[0] + sg * R * 0.33 - rMat * 1.7} ${dauC[1] - R * 0.10}
                          a ${rMat * 1.7} ${rMat * 1.7} 0 0 1 ${rMat * 3.4} 0
                          l 0 ${-rMat * 1.7 + rMat * 3.4 * e.mi} l ${-rMat * 3.4} 0 Z`}
                      fill="#FFFFFF" />
                <path d={`M ${dauC[0] + sg * R * 0.33 - rMat * 1.7} ${dauC[1] - R * 0.10 - rMat * 1.7 + rMat * 3.4 * e.mi}
                          h ${rMat * 3.4}`} stroke={muc} strokeWidth={dam * 0.6} strokeLinecap="round" />
              </g>
            ) : (
              <ellipse cx={dauC[0] + sg * R * 0.33} cy={dauC[1] - R * 0.10}
                       rx={rMat} ry={rMat * e.mat * blink} fill={muc} />
            )}
          </g>
        ))}
        {vai.pk.includes("kinh") ? (
          <g fill="none" stroke={muc} strokeWidth={dam * 0.55}>
            <circle cx={dauC[0] - R * 0.33} cy={dauC[1] - R * 0.10} r={R * 0.26} />
            <circle cx={dauC[0] + R * 0.33} cy={dauC[1] - R * 0.10} r={R * 0.26} />
            <line x1={dauC[0] - R * 0.07} y1={dauC[1] - R * 0.10} x2={dauC[0] + R * 0.07} y2={dauC[1] - R * 0.10} />
          </g>
        ) : null}
        {m > 0.12 ? (
          <ellipse cx={dauC[0]} cy={dauC[1] + R * 0.44} rx={R * 0.20 + m * R * 0.08}
                   ry={R * 0.09 + m * R * 0.22} fill={muc} />
        ) : (
          <path d={`M ${dauC[0] - R * 0.36} ${dauC[1] + R * 0.36 - mm * 4}
                    q ${R * 0.36} ${mm * R * 0.46} ${R * 0.72} 0`}
                fill="none" stroke={muc} strokeWidth={dam * 0.78} strokeLinecap="round" />
        )}
        {vai.pk.includes("rau") ? (
          <path d={`M ${dauC[0] - R * 0.42} ${dauC[1] + R * 0.24}
                    q ${R * 0.42} ${R * 0.26} ${R * 0.84} 0
                    q ${-R * 0.42} ${R * 0.16} ${-R * 0.84} 0 Z`}
                fill={T} stroke={muc} strokeWidth={dam * 0.5} />
        ) : null}
        {vai.pk.includes("mu") ? (
          <g>
            <path d={`M ${dauC[0] - R * 1.0} ${dauC[1] - R * 0.30}
                      a ${R} ${R} 0 0 1 ${R * 2.0} 0 Z`}
                  fill={vai.ao} stroke={muc} strokeWidth={dam * 0.8} />
            <path d={`M ${dauC[0] + R * 0.55} ${dauC[1] - R * 0.30} l ${R * 0.75} ${R * 0.1}`}
                  stroke={muc} strokeWidth={dam * 0.8} strokeLinecap="round" fill="none" />
          </g>
        ) : null}
      </g>
    </g>
  );
};

/* THÚ CƯNG — mọi gói đều có một con. Bốn chân, thân ngang, đuôi cong: ở nét que thì chỉ cần
   thân NẰM NGANG là mắt đọc ra ngay "không phải người", không cần vẽ chi tiết. */
export const ThuQue: React.FC<{ x: number; y: number; scale?: number; mau?: string; t?: number }> =
({ x, y, scale = 1, mau = "#8C9095", t = 0 }) => {
  const muc = "#1A1613", d = 6;
  const duoi = Math.sin(t * 2.2) * 12;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <ellipse cx="0" cy="-26" rx="46" ry="24" fill={mau} stroke={muc} strokeWidth={d} />
      {[-30, -8, 12, 34].map((px, i) => (
        <line key={i} x1={px} y1="-14" x2={px + (i % 2 ? 4 : -4)} y2="0" stroke={muc}
              strokeWidth={d} strokeLinecap="round" />
      ))}
      <path d={`M 44 -34 q 26 ${-10 + duoi} 16 ${-34 + duoi}`} fill="none" stroke={muc}
            strokeWidth={d} strokeLinecap="round" />
      <circle cx="-46" cy="-44" r="24" fill={mau} stroke={muc} strokeWidth={d} />
      <path d="M -62 -62 l 6 -16 l 12 10 Z" fill={mau} stroke={muc} strokeWidth={d * 0.8} />
      <path d="M -34 -62 l 6 -16 l 10 12 Z" fill={mau} stroke={muc} strokeWidth={d * 0.8} />
      <ellipse cx="-54" cy="-46" rx="4" ry="5" fill={muc} />
      <ellipse cx="-38" cy="-46" rx="4" ry="5" fill={muc} />
    </g>
  );
};
