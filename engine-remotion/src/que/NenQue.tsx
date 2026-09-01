import React from "react";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   NỀN CHO BỘ NGƯỜI QUE — mọi kích thước neo vào CHIỀU CAO NGƯỜI  (1/9/2026)

   Anh: *"nhân vật quá to so với bối cảnh, tỉ lệ chưa đúng"* và *"bối cảnh phải đúng, thay đổi
   đúng như trong prompt kịch bản 15s."*

   ĐO TRƯỚC KHI SỬA. Con mắt bảo "người quá to", nhưng đo ra thì ngược hẳn:
     người / trần phòng    = 1 : 1,32   (đời thật 1 : 1,41)  -> gần đúng
     người / lưng ghế sofa = 6,4 lần    (đời thật 2,0 lần)   -> ĐỒ ĐẠC NHỎ GẤP 3,2 LẦN
     người / cửa sổ        = 3,4 lần    (đời thật 1,4 lần)
   Người không hề to so với phòng; ĐỒ ĐẠC bị vẽ bé lại. `SceneBG` là tấm áp-phích phẳng: mỗi
   món được cho một con số chọn theo mắt (`height="150"` cho sofa) không neo vào thứ gì. Một
   hình chỉ có đồ đạc thì vẫn trông ổn — sai tỉ lệ chỉ lộ ra lúc đặt người vào cạnh.

   Không sửa `SceneBG`: `StickStory` dùng chung, ở đó cỡ người khác nên số ấy có thể đang đúng.
   Sửa tại chỗ là hỏng nhánh song song — họ lỗi đã trả giá nhiều lần.

   NGUYÊN TẮC Ở ĐÂY: không có một con số tuyệt đối nào. Mọi thứ viết bằng ĐƠN VỊ NGƯỜI, lấy từ
   đời thật:
     mặt bếp 0,53 (90cm/170cm) · lưng sofa 0,50 · cửa 1,20 · tủ lạnh 1,05 · máy giặt 0,53
     mặt bàn 0,44 · mặt giường 0,30 · bồn tắm 0,33 · tủ khoá 1,15 · kệ hàng 1,30
   Đổi cỡ người thì cả căn phòng đổi theo. Không còn chỗ nào để lệch.

   VÀ: đồ đạc chỉ được kê ở HAI DẢI MÉP, khoảng giữa để trống cho người diễn — đúng luật anh
   đặt cho ảnh AI, nay áp luôn cho nền vẽ tay.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

export type PropsNen = { noi: string; W: number; H: number; san: number; nguoi: number; t: number };

/* Mười một nơi — đúng bằng những nơi gói 15 giây THẬT SỰ nhắc tới, đếm trên cả 25.000 prompt:
   couch 1863 · kitchen 1149 · living room 700 · laundry 700 · hallway 313 · school 301 ·
   bedroom 200 · yard/street/store/bathroom 50 mỗi thứ.
   Bản trước ánh xạ vào 11 cảnh có sẵn của `SceneBG` (office/bank/city/hospital/lab/gym…) —
   mà bốn nơi hay gặp nhất lại không nằm trong đó, nên chúng rơi hết về "home". Đó là vì sao
   mọi tập đều diễn ở cùng một phòng khách. */
const MAU: Record<string, { tuong: [string, string]; san: string; nhan: string }> = {
  bep:         { tuong: ["#F5EDDD", "#E8DAC1"], san: "#C8A87C", nhan: "#D8734F" },
  phong_khach: { tuong: ["#F6EEE0", "#EADAC4"], san: "#C9A87D", nhan: "#E07A52" },
  giat:        { tuong: ["#E6EFF4", "#D1E1EA"], san: "#AEB8BE", nhan: "#4F87AC" },
  tam:         { tuong: ["#E9F2F4", "#D4E6EA"], san: "#DCE6E8", nhan: "#5FA3B0" },
  phong_ngu:   { tuong: ["#F0E8F3", "#DDD0E4"], san: "#B99B78", nhan: "#7C68A4" },
  hanh_lang:   { tuong: ["#F1ECE2", "#DED5C6"], san: "#B08F68", nhan: "#9A8060" },
  truong:      { tuong: ["#EBF0E8", "#D6E0D2"], san: "#B6BCAE", nhan: "#4E7C4A" },
  cua_hang:    { tuong: ["#EFF1F3", "#DBDFE4"], san: "#C6CBD0", nhan: "#3E7FB0" },
  an:          { tuong: ["#F5EDDC", "#E7D7BA"], san: "#B98F63", nhan: "#C0724A" },
  san_vuon:    { tuong: ["#BFE2FA", "#EAF6FF"], san: "#7FA85C", nhan: "#4E7C3E" },
  duong:       { tuong: ["#BFE0FA", "#E8F4FF"], san: "#9AA0A6", nhan: "#5C6268" },
};

export const NenQue: React.FC<PropsNen> = ({ noi, W, H, san, nguoi, t }) => {
  const c = MAU[noi] || MAU.phong_khach;
  const u = (v: number) => v * nguoi;        // ĐƠN VỊ NGƯỜI — nguồn duy nhất của mọi kích thước
  const ink = "#2C2722";
  const nd = Math.max(3, u(0.013));          // độ dày nét cũng theo cỡ người
  const ngoai = noi === "san_vuon" || noi === "duong";
  const sway = Math.sin(t * 0.7);

  // Hai dải mép được phép kê đồ. Mọi món phải nằm gọn trong một trong hai dải.
  const T = W * 0.015, P = W * 0.985;        // mép trái / mép phải của khung

  /* `hop` nhận Y ĐÁY chứ không nhận y đỉnh: đồ đạc đứng TRÊN SÀN, nên thứ cố định là chân nó.
     Nhận y đỉnh thì mỗi lần đổi chiều cao lại phải sửa kèm toạ độ — đúng kiểu sai lặp đi lặp
     lại đã sinh ra cả mớ đồ đạc lơ lửng ở bản trước. */
  const hop = (x: number, yDay: number, w: number, h: number, mau: string, r = 0.012) => (
    <rect x={x} y={yDay - h} width={w} height={h} rx={u(r)} fill={mau}
          stroke={ink} strokeWidth={nd} strokeLinejoin="round" />
  );
  const net = (x1: number, y1: number, x2: number, y2: number, w = 1) => (
    <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={ink} strokeWidth={nd * w} strokeLinecap="round" />
  );

  /* CỬA RA VÀO — 1,20 người. Đây là món dễ kiểm tỉ lệ nhất bằng mắt: người đứng cạnh mà đầu
     vượt quá khung cửa thì tỉ lệ sai, khỏi cần đo. Nên mọi phòng trong nhà đều có một cái. */
  const Cua = ({ x }: { x: number }) => (
    <g>
      {hop(x, san, u(0.52), u(1.2), "#B98A5E", 0.01)}
      {hop(x + u(0.05), san - u(0.09), u(0.42), u(1.02), "#C89A6E", 0.008)}
      <circle cx={x + u(0.44)} cy={san - u(0.55)} r={u(0.022)} fill="#E8C36A" stroke={ink} strokeWidth={nd * 0.7} />
    </g>
  );
  /* CỬA SỔ — bậu ở 0,55 người, cao 0,72. Cạnh dưới ngang hông, cạnh trên trên đầu một chút. */
  const CuaSo = ({ x, w = 0.86 }: { x: number; w?: number }) => (
    <g>
      {hop(x, san - u(0.55), u(w), u(0.72), "#FFFFFF", 0.01)}
      <rect x={x + nd * 2} y={san - u(1.27) + nd * 2} width={u(w) - nd * 4} height={u(0.72) - nd * 4}
            fill="#AFD9F5" />
      {net(x + u(w) / 2, san - u(1.27), x + u(w) / 2, san - u(0.55), 0.7)}
      {net(x, san - u(0.91), x + u(w), san - u(0.91), 0.7)}
      <circle cx={x + u(w * 0.24)} cy={san - u(1.12)} r={u(0.06)} fill="#FFE79A" />
    </g>
  );
  const Khung = ({ x, y, w = 0.3, h = 0.24 }: { x: number; y: number; w?: number; h?: number }) => (
    <g>{hop(x, y, u(w), u(h), "#FFFFFF", 0.006)}
       <rect x={x + nd * 2} y={y - u(h) + nd * 2} width={u(w) - nd * 4} height={u(h) - nd * 4} fill={c.nhan} opacity={0.5} /></g>
  );
  /* ĐÈN TRẦN treo giữa: nằm trên đầu người nên KHÔNG vi phạm luật "giữa để trống" — luật ấy
     nói về khoảng ĐỨNG DIỄN, tức dải sàn và tầm thân người. */
  const Den = () => (
    <g>
      {net(W / 2, 0, W / 2, u(0.16), 0.6)}
      <path d={`M ${W / 2 - u(0.13)} ${u(0.30)} Q ${W / 2} ${u(0.13)} ${W / 2 + u(0.13)} ${u(0.30)} Z`}
            fill="#F0D98A" stroke={ink} strokeWidth={nd} />
    </g>
  );

  const noiDung = () => {
    switch (noi) {
      /* ── BẾP: mặt bếp 0,53 · tủ trên từ 0,95 tới 1,45 · tủ lạnh 1,05 ────────────────── */
      case "bep": return (<g>
        {/* Tủ bếp: KHÔNG phải một khối phẳng. Soi khung bản trước ra một mảng nhạt trông như
            bức tường lửng. Cái làm mắt đọc ra "tủ bếp" là ĐƯỜNG CHIA CÁNH và TAY NẮM — hai nét
            rẻ tiền mà thiếu chúng thì bao nhiêu màu cũng vô ích. */}
        {hop(T, san, u(1.5), u(0.53), "#D3BF9C")}
        {[0, 1, 2].map((i) => (
          <g key={`d${i}`}>
            {net(T + u(0.5 * i), san - u(0.5), T + u(0.5 * i), san, 0.55)}
            {hop(T + u(0.5 * i) + u(0.36), san - u(0.34), u(0.09), u(0.022), "#6E6257", 0.01)}
          </g>))}
        {hop(T, san, u(1.5), u(0.06), "#3F3A34")}
        {hop(T, san - u(0.95), u(1.5), u(0.5), "#C6B18C")}
        {[0, 1, 2].map((i) => (
          <g key={`u${i}`}>
            {net(T + u(0.5 * i), san - u(1.45), T + u(0.5 * i), san - u(0.95), 0.55)}
            {hop(T + u(0.5 * i) + u(0.36), san - u(1.0), u(0.09), u(0.022), "#6E6257", 0.01)}
          </g>))}
        {hop(T + u(0.22), san - u(0.53), u(0.55), u(0.035), "#8E9BA5")}
        <ellipse cx={T + u(0.5)} cy={san - u(0.60)} rx={u(0.16)} ry={u(0.05)} fill="#5A6068" stroke={ink} strokeWidth={nd * 0.7} />
        <path d={`M ${T + u(0.44)} ${san - u(0.66)} q ${u(0.05)} ${-u(0.14) - sway * u(0.02)} ${u(0.12)} ${-u(0.22)}`}
              fill="none" stroke="#B9B9B9" strokeWidth={nd * 1.2} opacity={0.55} />
        {hop(P - u(0.62), san, u(0.62), u(1.05), "#D8DCE0")}
        {net(P - u(0.62), san - u(0.62), P, san - u(0.62), 0.8)}
        {net(P - u(0.10), san - u(0.55), P - u(0.10), san - u(0.72), 0.8)}
        <CuaSo x={W * 0.42} w={0.5} />
        <Den />
      </g>);

      /* ── PHÒNG KHÁCH: lưng sofa 0,50 · TV chéo 0,38 ─────────────────────────────────── */
      case "phong_khach": return (<g>
        {hop(T, san, u(1.55), u(0.5), c.nhan)}
        {hop(T, san, u(0.22), u(0.62), c.nhan, 0.03)}
        {hop(T + u(1.33), san, u(0.22), u(0.62), c.nhan, 0.03)}
        {hop(T + u(0.24), san - u(0.30), u(1.07), u(0.2), "#FFFFFF33", 0.02)}
        {hop(P - u(0.78), san - u(0.42), u(0.78), u(0.44), "#20262E", 0.008)}
        {hop(P - u(0.5), san, u(0.22), u(0.42), "#8A6842", 0.006)}
        <rect x={P - u(0.75)} y={san - u(0.83)} width={u(0.72)} height={u(0.38)} fill="#63B3E6" />
        <ellipse cx={W * 0.5} cy={san + (H - san) * 0.42} rx={W * 0.30} ry={(H - san) * 0.3}
                 fill="#00000018" />
        <Khung x={W * 0.40} y={san - u(1.30)} />
        <Den />
      </g>);

      /* ── PHÒNG GIẶT: máy giặt 0,53 · kệ trên 1,25 ───────────────────────────────────── */
      case "giat": return (<g>
        {hop(T, san, u(0.6), u(0.53), "#EDF2F5")}
        {hop(T + u(0.66), san, u(0.6), u(0.53), "#EDF2F5")}
        <circle cx={T + u(0.3)} cy={san - u(0.3)} r={u(0.17)} fill="#AFC7D4" stroke={ink} strokeWidth={nd} />
        <circle cx={T + u(0.96)} cy={san - u(0.3)} r={u(0.17)} fill="#AFC7D4" stroke={ink} strokeWidth={nd} />
        {hop(T, san - u(1.25), u(1.26), u(0.06), "#C9B896")}
        {hop(T + u(0.12), san - u(1.31), u(0.26), u(0.16), c.nhan, 0.01)}
        {hop(P - u(0.5), san, u(0.5), u(0.4), "#D8C39A", 0.04)}
        {hop(P - u(0.42), san - u(0.36), u(0.34), u(0.14), "#E8E2D2", 0.02)}
        <Cua x={W * 0.40} />
      </g>);

      /* ── PHÒNG TẮM: bồn rửa 0,52 · bồn tắm 0,33 ─────────────────────────────────────── */
      case "tam": return (<g>
        {hop(T, san, u(0.62), u(0.52), "#EDF3F5")}
        <ellipse cx={T + u(0.31)} cy={san - u(0.53)} rx={u(0.2)} ry={u(0.07)} fill="#FFFFFF" stroke={ink} strokeWidth={nd} />
        {hop(T + u(0.06), san - u(0.72), u(0.5), u(0.44), "#CFE6EC", 0.02)}
        {hop(P - u(0.95), san, u(0.95), u(0.33), "#FFFFFF", 0.03)}
        {net(P - u(0.95), san - u(0.33), P, san - u(0.33), 0.7)}
        {net(P - u(0.12), san - u(0.33), P - u(0.12), san - u(1.35), 0.7)}
        <path d={`M ${P - u(0.12)} ${san - u(1.35)} q ${-u(0.18)} 0 ${-u(0.2)} ${u(0.1)}`}
              fill="none" stroke={ink} strokeWidth={nd} />
        <rect x="0" y={san - u(0.62)} width={W} height={nd} fill="#00000018" />
        <Cua x={W * 0.41} />
      </g>);

      /* ── PHÒNG NGỦ: mặt giường 0,30 · đầu giường 0,62 ───────────────────────────────── */
      case "phong_ngu": return (<g>
        {hop(T, san, u(1.5), u(0.3), "#8E7355", 0.02)}
        {hop(T, san - u(0.3), u(1.5), u(0.16), "#EDE4F0", 0.03)}
        {hop(T, san, u(0.1), u(0.62), "#8E7355", 0.01)}
        {hop(T + u(0.1), san - u(0.4), u(0.42), u(0.14), "#FFFFFF", 0.04)}
        {hop(P - u(0.34), san, u(0.34), u(0.46), "#A08663", 0.01)}
        {hop(P - u(0.28), san - u(0.46), u(0.1), u(0.24), "#F2E8C8", 0.05)}
        <CuaSo x={W * 0.40} w={0.52} />
        <Khung x={T + u(0.5)} y={san - u(1.28)} w={0.34} h={0.26} />
      </g>);

      /* ── HÀNH LANG: cửa 1,20 hai bên, thảm chạy giữa ────────────────────────────────── */
      case "hanh_lang": return (<g>
        <Cua x={T} /><Cua x={P - u(0.52)} />
        <Khung x={T + u(0.66)} y={san - u(1.22)} w={0.26} h={0.32} />
        <Khung x={P - u(0.94)} y={san - u(1.22)} w={0.26} h={0.32} />
        {hop(T + u(0.62), san, u(0.36), u(0.5), "#9A8060", 0.01)}
        <ellipse cx={W * 0.5} cy={san + (H - san) * 0.45} rx={W * 0.22} ry={(H - san) * 0.32}
                 fill={c.nhan} opacity={0.28} />
        <Den />
      </g>);

      /* ── TRƯỜNG: tủ khoá 1,15 ───────────────────────────────────────────────────────── */
      case "truong": return (<g>
        {[0, 1, 2].map((i) => (
          <g key={`l${i}`}>{hop(T + u(0.38 * i), san, u(0.36), u(1.15), i % 2 ? "#5E8C5A" : "#6C9A66", 0.01)}
            {net(T + u(0.38 * i), san - u(0.62), T + u(0.38 * i) + u(0.36), san - u(0.62), 0.6)}
            <circle cx={T + u(0.38 * i) + u(0.29)} cy={san - u(0.72)} r={u(0.018)} fill="#E8E2D2" /></g>))}
        {[0, 1].map((i) => (
          <g key={`r${i}`}>{hop(P - u(0.36) - u(0.38 * i), san, u(0.36), u(1.15), i % 2 ? "#6C9A66" : "#5E8C5A", 0.01)}
            {net(P - u(0.36) - u(0.38 * i), san - u(0.62), P - u(0.38 * i), san - u(0.62), 0.6)}</g>))}
        <Den />
      </g>);

      /* ── CỬA HÀNG: kệ 1,30 ──────────────────────────────────────────────────────────── */
      case "cua_hang": return (<g>
        {[0, 1].map((s) => {
          const x = s ? P - u(0.72) : T;
          return (<g key={s}>
            {hop(x, san, u(0.72), u(1.3), "#D6DBE0", 0.008)}
            {[0.34, 0.66, 0.98, 1.26].map((h, i) => (
              <g key={i}>{net(x, san - u(h), x + u(0.72), san - u(h), 0.6)}
                {[0, 1, 2].map((j) => hop(x + u(0.06 + j * 0.22), san - u(h), u(0.16), u(0.16),
                  [c.nhan, "#E2A84E", "#7FB56A"][(i + j) % 3], 0.01))}</g>))}
          </g>);
        })}
        <Den />
      </g>);

      /* ── PHÒNG ĂN: mặt bàn 0,44 · lưng ghế 0,55 ─────────────────────────────────────── */
      case "an": return (<g>
        {hop(T, san, u(1.4), u(0.05), "#9A6B40")}
        {hop(T + u(0.08), san, u(0.07), u(0.44), "#8A5F38", 0.006)}
        {hop(T + u(1.25), san, u(0.07), u(0.44), "#8A5F38", 0.006)}
        {hop(T + u(0.3), san, u(0.06), u(0.55), c.nhan, 0.006)}
        {hop(T + u(0.3), san - u(0.42), u(0.3), u(0.05), c.nhan, 0.01)}
        {hop(P - u(0.42), san, u(0.42), u(0.9), "#A0774C", 0.01)}
        <CuaSo x={W * 0.44} w={0.46} />
        <Den />
      </g>);

      /* ── SÂN VƯỜN: hàng rào 0,60 ────────────────────────────────────────────────────── */
      case "san_vuon": return (<g>
        <rect x="0" y={san - u(0.6)} width={W} height={u(0.06)} fill="#E8E2D2" stroke={ink} strokeWidth={nd} />
        {Array.from({ length: 16 }).map((_, i) => hop(W * (i / 16) + u(0.02), san - u(0.44), u(0.05), u(0.16), "#E8E2D2", 0.004))}
        <g transform={`translate(${T + u(0.35)} ${san}) rotate(${sway * 0.8})`}>
          {hop(-u(0.05), 0, u(0.1), u(0.75), "#8A6A46", 0.01)}
          <circle cx="0" cy={-u(0.9)} r={u(0.42)} fill={c.nhan} stroke={ink} strokeWidth={nd} />
        </g>
        {hop(P - u(0.44), san, u(0.44), u(0.5), "#5C6268", 0.02)}
        {hop(P - u(0.4), san - u(0.5), u(0.36), u(0.06), "#3E4348", 0.01)}
      </g>);

      /* ── ĐƯỜNG PHỐ: nhà 2,4 người · thùng thư 0,72 ──────────────────────────────────── */
      default: return (<g>
        {hop(T, san - u(0.1), u(1.2), u(1.5), "#E3D6C0", 0.01)}
        <path d={`M ${T - u(0.06)} ${san - u(1.6)} L ${T + u(0.6)} ${san - u(2.05)} L ${T + u(1.26)} ${san - u(1.6)} Z`}
              fill="#A8593F" stroke={ink} strokeWidth={nd} />
        {hop(T + u(0.44), san - u(0.1), u(0.34), u(0.78), "#8A5F38", 0.01)}
        {hop(P - u(1.1), san - u(0.1), u(1.1), u(1.2), "#D8DCE0", 0.01)}
        <path d={`M ${P - u(1.16)} ${san - u(1.3)} L ${P - u(0.55)} ${san - u(1.68)} L ${P + u(0.06)} ${san - u(1.3)} Z`}
              fill="#6C7278" stroke={ink} strokeWidth={nd} />
        {hop(P - u(0.32), san, u(0.07), u(0.72), "#5C6268", 0.006)}
        {hop(P - u(0.44), san - u(0.72), u(0.3), u(0.18), c.nhan, 0.02)}
        <rect x="0" y={san - u(0.1)} width={W} height={u(0.1)} fill="#BFC4C9" stroke={ink} strokeWidth={nd} />
      </g>);
    }
  };

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width: W, height: H }}>
      <defs>
        <linearGradient id="nqt" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={c.tuong[0]} /><stop offset="1" stopColor={c.tuong[1]} />
        </linearGradient>
      </defs>

      {/* TƯỜNG (hoặc bầu trời khi ở ngoài) */}
      <rect x="0" y="0" width={W} height={san} fill="url(#nqt)" />
      {ngoai ? (
        <g opacity={0.9}>
          <ellipse cx={W * 0.22 + sway * u(0.05)} cy={u(0.30)} rx={u(0.34)} ry={u(0.14)} fill="#FFFFFF" />
          <ellipse cx={W * 0.78 - sway * u(0.04)} cy={u(0.52)} rx={u(0.28)} ry={u(0.11)} fill="#FFFFFF" />
        </g>
      ) : null}

      {/* SÀN — trọn phần ba dưới, liền một mạch từ mép trái sang mép phải. */}
      <rect x="0" y={san} width={W} height={H - san} fill={c.san} />
      <rect x="0" y={san} width={W} height={Math.max(3, nd * 1.4)} fill="#00000026" />
      {!ngoai ? <rect x="0" y={san - u(0.07)} width={W} height={u(0.07)} fill="#00000010" /> : null}

      {noiDung()}
    </svg>
  );
};
