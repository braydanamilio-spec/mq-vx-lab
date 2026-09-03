import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, Img } from "remotion";
import { NenQue } from "../que/NenQue";
import { ChiaDoi, SoLieu, Truc, KinhLup, DaiChu, Dem, TheChu, Chart, BieuTuong } from "./Khuon";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   PHIM GIẢI THÍCH — bảy khuôn hình, nhịp cắt 2,1 giây  (1/9/2026)

   Dựng từ số đo hai video anh gửi, không dựng từ ấn tượng:
     · 244 và 290 nhát cắt · trung vị 2,1 s · không cảnh nào quá 7 s · ≈26 cắt/phút
     · tiếng −14,0 LUFS, dải động nén còn 2,5–3,9 LU
     · KHÔNG phụ đề · chữ chỉ làm nhãn
     · bảy khuôn xoay vòng, bốn khuôn dựng thuần bằng code

   BA CHỖ CỐ Ý LÀM KHÁC ĐỂ HƠN HỌ
   1. CÓ PHỤ ĐỀ chạy theo mốc từ. Facebook và Instagram đa số xem không tiếng; video tham chiếu
      lên đó là mất trắng. Bộ `tts_karaoke` vốn đã trả về mốc từng từ nên chỗ này gần như free.
   2. CHỪA KHOẢNG LẶNG ở cú chốt. Họ không có lấy một quãng lặng nào dài quá 0,25 giây trong
      suốt 11 phút. Đổi lấy chỉ số giữ chân 30 giây đầu, nhưng cũng có nghĩa là không câu nào
      kịp ngấm. Mình chừa 0,8 giây ở các nhịp đỉnh.
   3. CỔNG ĐO NHỊP (`kiem_nhip.py`). Cổng chấm điểm cũ không đo nhịp cắt, mà nhịp mới là thứ
      quyết định người xem ở lại hay lướt.

   SHORT CẮT RA TỪ LONG — anh: *"mỗi long chọn ra tổng hợp 2-3 cái hay nhất dựng làm short."*
   Nên mỗi nhịp tự khai `dinh` (có đứng một mình được không). Bộ cắt short chỉ việc lấy các
   dải nhịp đỉnh liền nhau. Không dựng lại từ đầu, không sinh thêm tiếng.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const F = "Poppins, Arial Black, sans-serif";

export type NhipGT = {
  s: number; e: number;
  khuon: string;               // canh | chia_doi | so_lieu | truc | kinh_lup | nhom | dem | the_chu | chart | anh
  ve?: string;                 // PROMPT VẼ CẢNH — kịch bản viết kèm, khớp đúng lời của nhịp
  tam_trang?: string;          // kho | ngay | dem | lanh — đổi bảng màu cả khung
  cot?: { nhan: string; v: number }[];   // khuôn `chart`
  loi: string;                 // lời kể của nhịp — nền phải vẽ ĐÚNG theo câu này
  noi?: string;                // bối cảnh, đọc ra từ chính `loi`
  nenAnh?: string;             // ảnh nền AI (nếu có); không có thì vẽ bằng code
  dinh?: boolean;              // nhịp "đỉnh" — ứng viên cắt short
  pose?: string; expr?: string; n?: number;
  dai_chu?: string;            // dải chữ dưới — xương sống của BỘ CẢNH SONG SONG (quy tắc B)
  ngay?: boolean;              // khuôn `dem`: xen mặt trăng để thành "ngày", không thì đếm vật
  the?: string;                // khuôn `the_chu`: dùng "|" tách dòng
  ke_thua?: number;            // quy tắc D: cảnh này là cảnh thứ mấy trong một mạch liên tục
  trai?: any; phai?: any;
  so?: string; don?: string; chu?: string; bt?: string;
  moc?: { nhan: string; phu?: string }[]; vt?: number;
  x?: number; y?: number; nhan?: string;
  tep?: string;
};

export type PropsGT = {
  nhip?: NhipGT[];
  tu?: { t: number; d: number; w: string }[];
  voMp3?: string; nhac?: string; nhacVol?: number;
  tieuDe?: string; handle?: string; mau?: string; mauPhu?: string;
  dai?: number; doc?: boolean; hat?: number;
  /* TÔNG MÀU RIÊNG TỪNG NICHE — anh: *"xây dựng tông màu cho niche, phong cách dựng ảnh sao
     cho đẹp chuẩn USA như một channel top đầu."*
     Nền trơn và chữ không được dùng chung một bảng màu cho cả mười kênh: kênh tài chính cần
     tông lạnh trầm để đọc ra "đáng tin", kênh lịch sử cần tông ấm ngả giấy cũ. Bảng màu là
     thứ người xem nhận ra kênh TRƯỚC KHI đọc chữ đầu tiên. */
  nenTrang?: string; chuTrang?: string;
};

export const calcGT = async ({ props }: { props: PropsGT }) => ({
  durationInFrames: Math.max(90, Math.round((props.dai || 60) * 30)), fps: 30,
});

/* ── PHỤ ĐỀ KARAOKE ───────────────────────────────────────────────────────────────────────
   Từ đang đọc đổi màu. Không phải trang trí: mắt bám được dòng chữ khi tiếng tắt, và đây đúng
   là thứ video tham chiếu thiếu.
   Chỉ hiện CỬA SỔ 7 từ quanh từ đang đọc — hiện cả câu dài thì chữ phải nhỏ lại và mất tác dụng. */
const PhuDe: React.FC<{ tu: any[]; t: number; W: number; H: number; mau: string }> =
({ tu, t, W, H, mau }) => {
  /* Tính TRONG `PhuDe`, không tính ở component cha: chỗ dùng nằm trong hàm này, và khai ở ngoài
     thì render ném `ReferenceError: mauNhan is not defined` — cùng họ lỗi vùng phạm vi đã vấp
     với `_samMau` nửa giờ trước. Biến phải khai trong phạm vi nhìn thấy nó. */
  const mauNhan = nhanDocDuoc(mau);
  let i = -1;
  for (let k = 0; k < tu.length; k++) if (t >= tu[k].t - 0.06) i = k;
  if (i < 0) return null;
  /* CỬA SỔ THEO CÂU, không theo số từ cố định.
     Bản đầu lấy 7 từ quanh từ đang đọc. Soi khung ra "distance to the Moon. That is the" — nửa
     câu này dính nửa câu kia, đọc ra vô nghĩa. Người ta đọc phụ đề theo MỆNH ĐỀ; cắt giữa
     mệnh đề thì mắt phải ghép lại, và ở nhịp 2 giây một cảnh thì không kịp.
     Ranh giới câu đã nằm sẵn trong chính chuỗi từ (dấu chấm, hỏi, than) — chỉ việc dùng. */
  const het = (w: string) => /[.!?]$/.test(w || "");
  let a = 0;
  for (let k = i - 1; k >= 0; k--) if (het(tu[k].w)) { a = k + 1; break; }
  let b = tu.length;
  for (let k = i; k < tu.length; k++) if (het(tu[k].w)) { b = k + 1; break; }
  const cua = tu.slice(a, Math.min(b, a + 14));
  /* ── PHỤ ĐỀ: BỎ HỘP ĐEN ──────────────────────────────────────────────────────────────
     Anh: *"nâng cấp sao cho chuyên nghiệp chất lượng top 1, không rẻ tiền, nghiệp dư xấu."*

     Hộp đen bo góc là mặc định của trình tạo phụ đề trên điện thoại — ai xem cũng nhận ra ngay
     đó là bản làm nhanh. Nó tồn tại để giải một bài toán thật (chữ trắng trên nền sáng thì mất
     hút), nhưng nó giải bằng cách dán một khối lạ vào giữa khung.
     Cách phim làm: chữ trắng, đổ bóng MỀM và RỘNG. Bóng mềm tách chữ khỏi mọi nền mà không tạo
     ra hình khối nào — mắt không thấy có gì được thêm vào, chỉ thấy chữ đọc được.
     Cộng thêm một dải tối RẤT NHẸ chuyển dần ở đáy khung, không có cạnh. */
  /* ── PHỤ ĐỀ KARAOKE CHÁY: BỎ DẢI ĐEN, TỪ ĐANG NÓI TÔ VÀNG  (3/9/2026) ──────────────────
     Anh: *"làm sub cháy, karaoke, ko làm bóng mờ đen thế nha xấu, chữ karaoke màu vàng chạy khi
     nói, font đẹp, ko to quá che khuất."*

     Ba thay đổi, mỗi cái chữa một điều anh nêu:

     1. **Bỏ HẲN dải tối ở đáy.** Nó từng cao 34% khung, hạ xuống 20% vẫn là một mảng tối nằm
        chình ình. Tương phản nay do quầng bám sát chữ gánh trọn — thứ đã đo là đủ ở `SoLieu`.
        Không còn milimét ảnh nào bị che.

     2. **Chữ nhỏ lại 0,044 → 0,036** (−18%). Phụ đề là thứ đọc lướt, không phải tiêu đề; to quá
        thì nó chiếm chỗ của hình, đúng chỗ anh nói "che khuất nhiều".

     3. **Từ đang nói tô VÀNG.** Trước tô bằng màu kênh — mà kênh tối (`howloud` đỏ #C2352E) phải
        làm sáng lên mới đọc được, và mỗi kênh ra một sắc khác nhau. Vàng #FFD400 đọc tốt trên
        MỌI nền và là quy ước karaoke ai cũng nhận ra ngay. Một quy ước sẵn có luôn thắng một
        sắc thương hiệu mà người xem phải học.

     Quầng chữ: bốn lớp bóng KHÔNG LỆCH bám sát nét, bán kính nhỏ. Không dùng viền
     `paintOrder="stroke"` — §12.12: *không hãng phim nào viền chữ.* */
  const fs = H * 0.036;
  return (
    <>
      <div style={{
        position: "absolute", left: W * 0.08, right: W * 0.08, bottom: H * 0.075,
        display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 0.30em",
        fontFamily: F, fontWeight: 700, fontSize: fs, lineHeight: 1.25,
        textAlign: "center", letterSpacing: "-0.01em",
        /* 3/9 — SIẾT QUẦNG SAU KHI ĐO. Bỏ dải đen xong, cổng `kiem_hinh` báo tương phản phụ đề
             **4,2:1 < 4,5:1** — sát chuẩn nhưng dưới chuẩn. Đây đúng cái đã xảy ra hồi 1/9 khi bỏ
             hộp đen: hình đẹp hơn thật, nhưng đổi lấy chữ khó đọc mà KHÔNG ĐO.
             Lần này có cổng nên biết ngay. Bù bằng quầng dày hơn — vẫn bám sát nét nên không tạo
             mảng tối, chỉ tăng tương phản đúng chỗ chữ đứng. */
          textShadow: `0 0 ${H * 0.006}px #000000ff, 0 0 ${H * 0.013}px #000000ff, 0 0 ${H * 0.024}px #000000ee, 0 0 ${H * 0.038}px #000000aa, 0 ${H * 0.003}px ${H * 0.009}px #000000ee`,
        pointerEvents: "none",
      }}>
        {cua.map((w, k) => (
          <span key={k} style={{ color: a + k === i ? "#FFD400" : "#FFFFFF" }}>{w.w}</span>
        ))}
      </div>
    </>
  );
};

/* Làm sẫm một mã màu #RRGGBB theo tỉ lệ. Dùng cho sàn của nền vẽ bằng code — xem chú thích
   tại chỗ gọi. Giữ ở đây (ngoài component) để không tính lại mỗi khung. */
/* MÀU TỪ ĐANG ĐỌC TRONG PHỤ ĐỀ.
   Bản trước dùng thẳng màu kênh. Nhưng dải phụ đề gần như đen, và với kênh màu tối — `howloud`
   đỏ #C2352E đo 3,2:1, `whatweighs` ô-liu #4A5C2B đo 2,4:1 — chính từ QUAN TRỌNG NHẤT của câu
   lại là từ khó đọc nhất. Đổi sang trắng thì mất luôn tín hiệu thương hiệu.
   Nên LÀM SÁNG chính màu ấy tới khi đủ 4,5:1: vẫn nhận ra là màu kênh, mà đọc được. Kênh nào
   vốn đã đạt (howlong 4,8:1) thì giữ nguyên — sửa đúng chỗ sai, không sửa tất cả. */
const _sangMau = (h: string, t: number): string => {
  const m = /^#([0-9a-f]{6})$/i.exec((h || "").trim());
  if (!m) return h;
  return "#" + [0, 2, 4].map((i) => {
    const v = parseInt(m[1].slice(i, i + 2), 16);
    return Math.min(255, Math.round(v + (255 - v) * t)).toString(16).padStart(2, "0");
  }).join("");
};
const _lumGT = (h: string): number => {
  const m = /^#([0-9a-f]{6})$/i.exec((h || "").trim());
  if (!m) return 0;
  const v = [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16) / 255)
    .map((u) => (u <= 0.03928 ? u / 12.92 : Math.pow((u + 0.055) / 1.055, 2.4)));
  return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
};
/** Màu nhấn đủ đọc trên dải phụ đề (xấp xỉ #1A1A1A sau lớp phủ). */
const nhanDocDuoc = (mau: string): string => {
  const nen = _lumGT("#1A1A1A");
  let c = mau;
  for (let t = 0; t <= 0.75; t += 0.15) {
    c = _sangMau(mau, t);
    if ((_lumGT(c) + 0.05) / (nen + 0.05) >= 4.5) return c;
  }
  return c;
};

const _samMau = (h: string, t: number): string => {
  const m = /^#([0-9a-f]{6})$/i.exec(h.trim());
  if (!m) return h;
  return "#" + [0, 2, 4].map((i) =>
    Math.max(0, Math.round(parseInt(m[1].slice(i, i + 2), 16) * (1 - t)))
      .toString(16).padStart(2, "0")).join("");
};

export const KichGiaiThich: React.FC<PropsGT> = ({
  nhip = [], tu = [], voMp3 = "", nhac = "", nhacVol = 0.13,
  tieuDe = "", handle = "", mau = "#E0533D", mauPhu = "#2F7D6B", doc = false, hat = 0,
  nenTrang = "#EFE7D6", chuTrang = "#2C2722",
}) => {
  const frame = useCurrentFrame();
  const { fps, width: W, height: H } = useVideoConfig();
  const t = frame / fps;

  const N = nhip.find((x) => t >= x.s && t < x.e) || nhip[nhip.length - 1];
  if (!N) return <AbsoluteFill style={{ background: nenTrang }} />;
  const p = kep((t - N.s) / Math.max(0.4, N.e - N.s));      // 0..1 trong nhịp
  const vao = kep((t - N.s) / 0.22);                        // 0..1 lúc vừa cắt vào

  const SAN = 0.66, sanY = H * SAN, NGUOI = H * (doc ? 0.38 : 0.46);

  /* Nền: ưu tiên ảnh AI vẽ ĐÚNG THEO LỜI của nhịp này (anh dặn), không có thì `NenQue` vẽ
     bằng code. Hai tầng, tầng dưới không bao giờ hỏng vì không gọi mạng. */
  /* TRÔI MÁY — BIÊN ĐỘ LẤY TỪ SỐ ĐO, KHÔNG TỪ CẢM GIÁC.
     Đo trên video tham chiếu bằng `mpdecimate` ở ba ngưỡng:
       ngưỡng thô  -> 0,4 khung khác nhau/giây, đúng bằng nhịp cắt (22 cắt/60s)
       ngưỡng vừa  -> 5,2/giây
       ngưỡng mịn  -> 22,2/giây, tức GẦN NHƯ MỌI KHUNG đều khác nhau một chút
     Đọc ra: trong cảnh CÓ trôi máy liên tục, nhưng biên độ nhỏ tới mức ngưỡng thô coi là ảnh
     tĩnh. Bản đầu em phóng 3,5% và đẩy ngang 1% — quá tay, thành ra thấy rõ là đang zoom.
     Nay 1,6% và bỏ hẳn đẩy ngang: đẩy ngang là thứ ăn mất mép ảnh, mà mép ảnh chính là chỗ
     luật bố cục vừa dặn đặt đồ đạc vào.
     Và: cắt CỨNG, không dissolve — đo được 0 cặp điểm cắt cách nhau dưới 0,09 giây trên cả
     244 nhát cắt. Nên không thêm mờ chồng; cái làm nó mượt là NHỊP đều, không phải hiệu ứng. */
  const kb = 1.0 + p * 0.016;

  const Nen = (
    <>
      {N.nenAnh ? (
        <Img src={staticFile(N.nenAnh)}
             style={{ position: "absolute", inset: 0, width: W, height: H, objectFit: "cover",
                      transform: `scale(${kb})` }} />
      ) : N.noi ? (
        <NenQue noi={N.noi} W={W} H={H} san={sanY} nguoi={NGUOI} t={t} />
      ) : (
        /* NƠI CHỐN RỖNG = câu này TRỪU TƯỢNG (nói về con số, về vũ trụ, về ý niệm).
           Dựng nền trơn có đường chân trời, không dựng phòng ốc. Bản đầu mặc định về
           "phong_khach", nên một câu về tốc độ ánh sáng lại diễn trong phòng khách có sofa —
           nền ấy nói một điều SAI về nội dung câu, tệ hơn hẳn nền trống. */
        <AbsoluteFill>
          <div style={{ position: "absolute", inset: 0,
                        /* Đáy pha màu CHỮ (nâu ấm) nên khi dải phụ đề đen phủ lên, hai lớp cộng lại
                           ra một vệt NÂU BÙN — thấy rõ ở khung đầu `howmuch`. Nền không-ảnh phải
                           trung tính lạnh, để dải phụ đề đọc ra là bóng chứ không ra mảng màu lạ. */
                        background: `linear-gradient(180deg,${nenTrang},#C9C6C0)` }} />
                        /* MÀU SÀN TỪ BẢNG MÀU KÊNH, không phải hằng nâu dùng chung: `#CDBE9F`
                           đúng với một kênh, sai với mười bảy kênh kia, và dưới dải phụ đề
                           đen nó cộng thành vệt BÙN (soi khung đầu `howmuch`). Sàn chỉ cần
                           SẪM HƠN tường để mắt đọc ra mặt phẳng. */
          <div style={{ position: "absolute", left: 0, right: 0, top: sanY,
                        height: H - sanY, background: _samMau(nenTrang, 0.22) }} />
          <div style={{ position: "absolute", left: 0, right: 0, top: sanY,
                        height: Math.max(3, H * 0.004), background: "#00000022" }} />

          {/* ── VẬT ĐANG NÓI TỚI, VẼ BẰNG CODE  (2/9/2026) ────────────────────────────────
              Anh gửi khung toàn nền trơn: *"hình ảnh còn xấu kém"*. Đo được `canh` có **30
              nhịp, 0 nhịp có biểu tượng** — thiết kế giả định luôn có ảnh AI. Hôm CF còn
              neuron thì 29/30 có ảnh nên không ai thấy; hôm cạn thì cả 30 rơi xuống gradient.

              Đúng luật §7 (bốn tầng nền): *tầng cuối không gọi mạng nên không bao giờ hỏng* —
              mà `canh` thiếu đúng tầng ấy. Nay dây chuyền cấp `bt` từ chính lời của nhịp
              (`giai_thich._bt_canh`), và ở đây vẽ vật ấy TO, mờ, đứng trên đường chân trời.

              Ba lựa chọn có chủ đích:
                · **mờ 0.16** — nó là NỀN, không được tranh chỗ với số liệu và phụ đề đè lên.
                · **đặt trên sàn**, không lơ lửng giữa khung: có đường chân trời rồi thì vật
                  phải đứng trên nó, nếu không mắt đọc ra hai lớp rời nhau.
                · **không có `bt` thì không vẽ gì** — câu trừu tượng ("Nothing happens.") mà
                  gắn một cái ô tô là nói một điều SAI, tệ hơn nền trống (§12.5). */}
          {N.bt ? (
            <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: H,
                          display: "flex", alignItems: "flex-end", justifyContent: "center",
                          /* 3/9 — 0.16 -> 0.34. Anh soi khung HOW BIG: nhịp không có ảnh AI
                             hiện ra gần như TRỐNG TRƠN — người que xám nhạt trên nền xám, nhìn
                             ra như hỏng chứ không như một lựa chọn.
                             0.16 chọn để "không tranh chỗ với số liệu đè lên". Nhưng ở nhịp
                             `canh` thì KHÔNG có số liệu đè lên — chỉ có phụ đề ở đáy khung.
                             Một con số chọn cho tình huống A đem dùng cho tình huống B: mờ tới
                             mức ấy chỉ đúng khi có lớp khác phủ lên, còn ở đây nó là lớp DUY
                             NHẤT, và một lớp duy nhất thì phải nhìn thấy được. */
                          paddingBottom: H - sanY, opacity: 0.34 }}>
              <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
                   style={{ position: "absolute", left: 0, top: 0 }}>
                <g transform={`translate(${W / 2} ${sanY - Math.min(H * 0.17, W * 0.19)})`}>
                  <BieuTuong ten={N.bt} s={Math.min(H * 0.42, W * 0.48)} />
                </g>
              </svg>
            </div>
          ) : null}
        </AbsoluteFill>
      )}
    </>
  );

  const than = () => {
    switch (N.khuon) {
      case "chia_doi":
        return { nen: <AbsoluteFill style={{ background: nenTrang }} />,
                 lop: <ChiaDoi W={W} H={H * 0.80} trai={N.trai || {}} phai={N.phai || {}} mau={mau} p={p} /> };
      case "so_lieu":
        return { nen: Nen,
                 lop: <g>
                   {/* 1/9 — KHÔNG VẼ BIỂU TƯỢNG KHI ĐÃ CÓ ẢNH.
                       Soi khung kênh HOW BIG: ảnh AI đã vẽ đúng xe buýt và máy bay, mà lớp code
                       vẫn vẽ thêm một chiếc ô tô nhỏ đè lên trước. Hai lớp cùng nói một điều,
                       và nói khác nhau. Biểu tượng sinh ra để THAY ảnh khi không có ảnh, không
                       phải để đứng cạnh ảnh. */}
                   <SoLieu W={W} H={H * 0.80} so={N.so || ""} don={N.don || ""} chu={N.chu || ""}
                           bt={N.nenAnh ? "" : (N.bt || "")} mau={mau} p={p}
                           tren_anh={!!N.nenAnh} nen={nenTrang} bo={hat % 3} />
                   {N.dai_chu ? <DaiChu W={W} H={H * 0.80} chu={N.dai_chu} p={p} /> : null}
                 </g> };
      case "truc":
        return { nen: <AbsoluteFill style={{ background: nenTrang }} />,
                 lop: <Truc W={W} H={H * 0.80} moc={N.moc || []} vt={N.vt ?? -1} mau={mau} p={p} /> };
      case "kinh_lup":
        return { nen: Nen,
                 lop: <KinhLup W={W} H={H * 0.80} x={W * (N.x ?? 0.34)} y={H * 0.80 * (N.y ?? 0.5)}
                               nhan={N.nhan || ""} mau={mau} p={p}
                               con={N.nenAnh ? (
                                 <image href={staticFile(N.nenAnh)} x={0} y={0}
                                        width={W} height={H * 0.80}
                                        preserveAspectRatio="xMidYMid slice" />
                               ) : null} /> };
      /* `nhom` không còn là một khuôn riêng: một nhóm người là việc của ẢNH, không phải của
         code. Bản trước nhân bản một tạo hình năm lần — soi khung ra năm người giống hệt nhau,
         tay chồng lên nhau. Nay ảnh vẽ nhóm, code chỉ đặt dải chữ lên. */
      case "nhom":
        return { nen: Nen,
                 lop: N.dai_chu ? <DaiChu W={W} H={H * 0.80} chu={N.dai_chu} p={p} /> : null };
      case "dem":
        return { nen: Nen,
                 lop: <Dem W={W} H={H * 0.80} n={N.n || 4} ngay={N.ngay !== false}
                           chu={N.chu || ""} p={p} mau={mau} /> };
      case "chart":
        return { nen: <AbsoluteFill style={{ background: nenTrang }} />,
                 lop: <Chart W={W} H={H * 0.80} cot={N.cot || []} don={N.don || ""}
                             mau={mau} mauPhu={mauPhu} p={p} /> };
      case "the_chu":
        return { nen: <AbsoluteFill style={{ background: nenTrang }} />,
                 lop: <TheChu W={W} H={H * 0.80} chu={N.the || N.loi} p={p} mau={mau} /> };
      case "anh":
        return { nen: N.tep ? (
          <Img src={staticFile(N.tep)} style={{ position: "absolute", inset: 0, width: W, height: H,
                objectFit: "cover", transform: `scale(${1.04 + p * 0.05})` }} />
        ) : Nen, lop: null };
      default: {
        /* QUY TẮC D — CẢNH SAU KẾ THỪA CẢNH TRƯỚC.
           Bằng chứng: vệt dấu chân của nhân vật DÀI THÊM RA qua từng cảnh trong cùng một mạch.
           Không phải trang trí — nó là thứ nói "vẫn là chuyến đi ấy, chỉ muộn hơn". Cắt rời
           từng cảnh thì mỗi cảnh là một lần bắt đầu lại, và cả đoạn mất mạch.
           `ke_thua` = cảnh thứ mấy trong mạch; vệt dài theo đúng con số ấy. */
        /* Anh: *"khi viết kịch bản thì sẽ viết cả prompt tạo ảnh bối cảnh, nhân vật tĩnh mô
           phỏng kèm luôn sao cho khớp đúng là được, ko cần vector chuyển động."*
           Nên `canh` giờ chỉ còn: ảnh + dải chữ. Người vector bỏ hẳn — nó là chỗ xấu nhất của
           bản trước, và là thứ duy nhất em vẽ tay trong khi máy vẽ đẹp hơn hẳn.
           Khi CHƯA có ảnh (API hỏng) thì `Nen` tự rơi về `NenQue` vẽ bằng code — tầng đỡ ấy
           không gọi mạng nên không bao giờ hỏng theo. */
        return { nen: Nen,
                 lop: N.dai_chu ? <DaiChu W={W} H={H * 0.80} chu={N.dai_chu} p={p} /> : null };
      }
    }
  };
  const { nen, lop } = than();

  return (
    <AbsoluteFill style={{ background: nenTrang, overflow: "hidden" }}>
      {/* Vào cảnh: đẩy nhẹ + hiện dần trong 0,22 giây. Ở nhịp 2,1 giây thì chuyển cảnh dài hơn
          thế là ăn mất một phần tư thời lượng của chính cảnh ấy. */}
      {/* THẺ HOOK VÀ NỘI DUNG KHUÔN KHÔNG ĐƯỢC TRANH CHỖ.
          Anh khoanh đúng: badge "8.8 YEARS" đè lên đầu nhân vật. Cả hai lớp đều tự đặt mình ở
          nửa trên khung mà không lớp nào biết lớp nào — cùng họ lỗi với vụ biểu tượng đè con số.
          Trong 3 giây có hook, đẩy nội dung khuôn xuống đúng bằng chiều cao thẻ. */}
      <AbsoluteFill style={{
        opacity: 0.35 + 0.65 * vao,
        transform: `scale(${1.02 - vao * 0.02})`,
      }}>
        {nen}
        {lop ? (
          <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
            {lop}
          </svg>
        ) : null}
      </AbsoluteFill>

      {/* ══ ĐÃ BỎ THẺ HOOK ĐẦU VIDEO (1/9/2026) ═══════════════════════════════════════
          Anh: *"đầu videos thì bị che khuất quá nhiều, bỏ cái bảng text chà bá đầu videos."*

          Anh đúng, và cái sai nằm ở chỗ tôi hiểu sai chữ "hook". Video tham chiếu KHÔNG có
          tấm thẻ tiêu đề nào cả — hook của họ là NỘI DUNG của cảnh đầu tiên (khung chia đôi
          `YOU | HIM`), không phải một tấm biển dán đè lên cảnh.
          Dán thẻ lên là làm hai việc cùng lúc trên một chỗ: cảnh đang kể một điều, tấm thẻ
          che mất nó để nói lại điều ấy bằng chữ. Người xem mất ba giây đầu — đúng ba giây
          quyết định họ ở hay lướt.
          Nay hook phải nằm trong nhịp đầu tiên: một hình mạnh + một câu ngắn. */}
      {/* ── LỚP HOÀN THIỆN CHUNG ────────────────────────────────────────────────────────
          Đây mới là thứ làm mười lăm ảnh rời rạc "dính" vào nhau thành một bộ phim — hơn hẳn
          việc chỉnh màu từng ảnh (đã thử: tách tông ở cường độ 0,32 vẫn gần như không thấy).
          Lý do: lớp này phủ lên CẢ ẢNH LẪN ĐỒ HOẠ VẼ BẰNG CODE, nên hai thứ vốn khác hẳn nhau
          về bản chất lại chung một bề mặt.
            · vignette: tối nhẹ bốn góc, dẫn mắt vào giữa — mọi ống kính thật đều có
            · grain: hạt mịn, phá cái "sạch bong" của ảnh máy sinh ra
          Cả hai phải RẤT NHẸ. Thấy được là hỏng; nhiệm vụ của chúng là không ai nhận ra. */}
      {/* ── LỚP CHỈNH MÀU PHỦ TOÀN KHUNG  (3/9/2026) ──────────────────────────────────────
          Anh: *"tông màu ảnh vẫn hơi xấu và chưa điện ảnh bắt mắt."*

          Bộ `to_mau` hiện có chỉnh TỪNG ẢNH AI — nên nó không chạm được vào đồ hoạ vẽ bằng code
          (biểu đồ, thẻ số, chia đôi). Đó chính là lý do hai loại vẫn đọc ra hai thế giới: chúng
          chưa bao giờ đi qua cùng một bề mặt.

          §12.12 đã chỉ đúng cách: *vignette + grain rất nhẹ phủ TOÀN khung, vì nó phủ lên cả ảnh
          lẫn đồ hoạ code nên hai thứ khác bản chất mới chung một bề mặt.* Lớp này làm nốt phần
          MÀU của ý ấy — grain và vignette đã có, còn thiếu tông màu.

          Hai lớp, cố ý rất nhẹ:
            · `overlay` ấm ở 6% — kéo vùng sáng ngả vàng nhẹ, cho cảm giác nắng thay vì đèn huỳnh
              quang. Đây là thứ mắt đọc ra là "điện ảnh".
            · `soft-light` lạnh ở 5% — hạ vùng tối về phía xanh lam. Sáng ấm / tối lạnh là công
              thức phân tách tông cơ bản nhất, và nó rẻ vì chỉ là hai lớp phủ.

          Không dùng số lớn hơn: đây là bộ giải thích, không phải phim hành động. §13.4 ghi lại
          một lần tôi tưởng chỉnh màu là đòn bẩy lớn rồi ghép trước/sau thấy gần như không khác —
          nên lần này đặt nhẹ và để nó cộng dồn với grain + vignette, không kỳ vọng nó tự gánh. */}
      {/* ── ĐO RỒI BỎ LỚP LẠNH  (3/9/2026) ────────────────────────────────────────────────
          Bản đầu có HAI lớp: ấm `overlay` 6% + lạnh `soft-light` 5%, theo công thức "sáng ấm /
          tối lạnh". Đo trên khung thật sau khi dựng:

              R = 130 · G = 130 · B = 129      → **không ấm lên một chút nào**

          Hai lớp **triệt tiêu nhau**: cái này kéo vàng, cái kia kéo lam, kết quả là trung tính —
          nhưng vẫn hạ độ sáng và độ trong. Tức nó chỉ để lại phần THIỆT của cả hai.

          §13.4 đã ghi đúng bẫy này một lần: *"tuyên bố chỉnh màu là đòn bẩy lớn nhất; làm xong,
          ghép trước/sau thì gần như không thấy khác biệt"*. Lần ấy là vô hại, lần này là có hại.

          Bỏ lớp lạnh, giữ một lớp ấm đủ để ĐO ĐƯỢC. Một lớp làm được việc hơn hai lớp cãi nhau. */}
      <AbsoluteFill style={{
        pointerEvents: "none", opacity: 0.10, mixBlendMode: "soft-light",
        background: "linear-gradient(180deg,#FFE0B2 0%,#FFCB8F 60%,#FFBE7A 100%)",
      }} />
      <AbsoluteFill style={{
        pointerEvents: "none",
        background: `radial-gradient(120% 78% at 50% 46%, #00000000 52%, #00000048 100%)`,
      }} />
      <AbsoluteFill style={{
        pointerEvents: "none", opacity: 0.05, mixBlendMode: "overlay",
        backgroundImage:
          "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'>"
          + "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/></filter>"
          + "<rect width='140' height='140' filter='url(%23n)'/></svg>\")",
        backgroundSize: `${Math.round(W * 0.13)}px ${Math.round(W * 0.13)}px`,
      }} />

      {/* ── THẺ CHỮ THÌ TẮT PHỤ ĐỀ — MỘT CÂU, KHÔNG PHẢI HAI  (2/9/2026) ─────────────────
          Anh: *"sao nhàm chán chất lượng kém thế, hơi rối."* Trích khung ra nhìn thì thấy ngay:
          khuôn `the_chu` vẽ nguyên câu lời kể thành thẻ chữ GIỮA khung, rồi phụ đề vẽ **đúng
          câu ấy** lần nữa ở dưới. Cùng một câu, hai chỗ, hai cỡ chữ — đó là cái "rối".

          Không phải lỗi ngẫu nhiên mà là hệ quả của thiết kế: `_n("the_chu", "<lời>", the="<lời>")`
          — chữ trên thẻ CHÍNH LÀ câu lời kể, chỉ thêm dấu ngắt dòng.

          CLAUDE.md §12.12 đã liệt kê đúng điều này trong danh sách "dấu hiệu nghiệp dư": *"thẻ
          chữ giữ 3 giây ở cú chốt → đóng bằng cảnh, câu chốt để phụ đề nói"*. Tôi viết ra luật
          ấy rồi để engine vi phạm nó ở mọi tập.

          Tắt PHỤ ĐỀ chứ không bỏ thẻ chữ: thẻ chữ là khuôn hình có chủ đích (chữ lớn, ngắt dòng
          theo nhịp), phụ đề chỉ là bản chép lại. Giữ cái được thiết kế, bỏ cái lặp. */}
      {String((N as any)?.khuon || "") === "the_chu"
        ? null
        : <PhuDe tu={tu} t={t} W={W} H={H} mau={mau} />}

      {/* ══ ĐÃ BỎ DẢI TÊN KÊNH (1/9/2026) ══════════════════════════════════════════════
          Đóng dấu tên kênh lên MỌI khung là thói quen của kênh nhỏ — nó lấy mất 5% chiều cao
          của mọi cảnh để nói một điều mà người xem đã biết (họ đang ở trên trang kênh, hoặc
          vừa bấm vào từ đó). Hai video tham chiếu chỉ có một watermark nhỏ ở góc.
          Nay: một watermark rất nhạt ở góc dưới phải, không chiếm dòng nào. */}
      <div style={{
        position: "absolute", right: W * 0.035, bottom: H * 0.022,
        fontFamily: "Poppins, Arial, sans-serif", fontWeight: 700,
        fontSize: H * 0.016, color: "#FFFFFF", opacity: 0.42, letterSpacing: 2,
        textShadow: `0 ${H * 0.002}px ${H * 0.006}px #00000099`, pointerEvents: "none",
      }}>{handle}</div>

      {voMp3 ? <Audio src={staticFile(voMp3)} /> : null}
      {nhac ? <Audio src={staticFile(nhac)} loop volume={nhacVol} /> : null}
    </AbsoluteFill>
  );
};
