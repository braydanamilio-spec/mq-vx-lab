import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, Img } from "remotion";
import { NenQue } from "../que/NenQue";
import { chanTroi, DAY_HINH, coHinh, ChiaDoi, SoLieu, Truc, KinhLup, DaiChu, Dem, TheChu, Chart, BieuTuong, NenPhong } from "./Khuon";
import { CanhVe, sangDayCanh } from "./CanhVe";

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
  canh_ve?: string;          // nơi chốn vẽ bằng code — thay cho ảnh CF ở nhịp này
  canh_hat?: number;         // hạt riêng của nhịp — hai cảnh cùng nơi phải khác nhau
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
const PhuDe: React.FC<{ tu: any[]; t: number; W: number; H: number; mau: string;
                        sangNen?: number }> =
({ tu, t, W, H, mau, sangNen = -1 }) => {
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
  /* ── CỠ CHỮ THEO CẠNH NGẮN, KHÔNG THEO CHIỀU CAO  (3/9/2026) ────────────────────────────
     Anh: *"long cũng chuẩn ko lỗi nha."* Dựng bản dài 16:9 rồi soi: phụ đề **nhỏ li ti**.

     Đo bằng chính công thức. `fs = H · 0,036`:
         dọc  9:16  → H=1920 ⇒ 69px trên khung rộng 1080  = 6,4% bề ngang
         ngang 16:9 → H=1080 ⇒ 39px trên khung rộng 1920  = **2,0% bề ngang**
     Cùng một hằng số, hai kết quả lệch nhau **hơn ba lần** về mặt thị giác.

     Vì chữ được đọc theo BỀ NGANG dòng, không theo chiều cao khung. Neo vào `H` chỉ đúng ở khổ
     dọc — nơi H là cạnh dài. Sang khổ ngang thì H thành cạnh NGẮN và chữ teo lại.

     Đúng họ lỗi đã trả giá nhiều lần: *chép hằng số sang hệ quy chiếu khác* (§6). Không báo lỗi,
     chỉ làm chữ bé — nên chỉ lộ khi có người ngồi xem bản dài.

     Neo vào `min(W,H)` thì một hằng số đúng cho cả hai khổ. */
  /* ── SỬA LẠI: NEO VÀO CHIỀU CAO, KHÔNG PHẢI CẠNH NGẮN  (3/9/2026, sửa trong cùng lượt) ──
     Bản vá đầu của tôi neo cỡ chữ vào `min(W,H)` vì thấy phụ đề bản dài "nhỏ li ti" trong lưới
     khung. Kiểm lại bằng con số thì tôi sai:

         fs = H · 0,036  →  dọc 3,6% chiều cao · ngang 3,6% chiều cao   ← ĐÃ bằng nhau
         fs = min(W,H) · 0,045 → dọc 2,6% chiều cao · ngang 4,5%        ← làm DỌC bé đi

     Chuẩn phụ đề đo theo **chiều cao khung** (4–5%), không theo bề ngang — vì màn hình nào cũng
     scale theo chiều cao. Cảm giác "nhỏ" của tôi đến từ chỗ khác: khi ghép lưới, khung NGANG bị
     thu nhỏ nhiều hơn khung dọc để vừa cùng một bề rộng.

     Tức tôi suýt sửa một thứ không hỏng, và bản vá ấy sẽ làm hỏng khổ dọc — nơi 90% video nằm.
     Đúng luật §13.4: *khi con số và con mắt bất đồng, đo cái đang bị chấm rồi mới quyết bên nào
     sai.* Ở đây con mắt sai vì nó nhìn qua một phép thu nhỏ không đều.

     Giữ neo `H`, chỉ nâng 0,036 → 0,042 (3,6% → 4,2% chiều cao) cho vào giữa dải chuẩn 4–5%. */
  const fs = H * 0.042;
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
        /* Quầng phải NGƯỢC sắc với mực: chữ đậm trên nền sáng cần quầng SÁNG để tách, quầng
           đen quanh chữ đen thì không tách được gì. */
        textShadow: (Number(sangNen ?? -1) >= 170)
          ? `0 0 ${H * 0.006}px #FFFFFFff, 0 0 ${H * 0.014}px #FFFFFFff, 0 0 ${H * 0.026}px #FFFFFFee, 0 0 ${H * 0.040}px #FFFFFFaa`
          : `0 0 ${H * 0.006}px #000000ff, 0 0 ${H * 0.013}px #000000ff, 0 0 ${H * 0.024}px #000000ee, 0 0 ${H * 0.038}px #000000aa, 0 ${H * 0.003}px ${H * 0.009}px #000000ee`,
        pointerEvents: "none",
      }}>
        {/* ── NỀN SÁNG THÌ ĐỔI MỰC, KHÔNG ĐẮP THÊM TẤM CHE  (3/9/2026) ─────────────────────
            Quầng đen đã siết một lần và vẫn không đủ với ảnh SÁNG: đo dải đáy của bốn ảnh
            SURVIVE ra **212–231**, tức chữ trắng chỉ đạt **1,9–2,0:1** trên chuẩn 4,5.
            Quầng không cứu được chênh lệch nền ấy — nó viền nét chứ không đổi nền.

            Anh đã bảo bỏ tấm che đen, nên cách còn lại là ĐỔI MỰC: nền sáng thì chữ đậm. Độ
            sáng dải đáy do `nen_gt.sang_day` đo ngay lúc sinh ảnh và ghi vào nhịp (`sangDay`) —
            engine chỉ đọc, không đo lại. Cùng nguyên tắc `bo_the`/`kieu_so`: nơi BIẾT thì
            quyết rồi truyền kết quả.

            Ngưỡng 170: trên mức ấy chữ trắng không thể đạt 4,5:1 dù quầng dày bao nhiêu.
            Từ đang đọc giữ màu vàng khi nền tối, và chuyển sang cam đậm khi nền sáng — vẫn là
            tín hiệu "từ này đang được đọc", chỉ đổi sắc để còn đọc được. */}
        {(() => {
          const sd = Number(sangNen ?? -1);
          const sang = sd >= 170;                       // nền dưới phụ đề quá sáng
          const mucThuong = sang ? "#14161C" : "#FFFFFF";
          const mucDoc = sang ? "#8A4B00" : "#FFD400";
          return cua.map((w, k) => (
            <span key={k} style={{ color: a + k === i ? mucDoc : mucThuong }}>{w.w}</span>
          ));
        })()}
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

  /* Mặt sàn hỏi `chanTroi` — nguồn sự thật duy nhất, xem chú thích của nó trong `Khuon.tsx`.
     Hằng `SAN = 0.66` cũ ghi cứng và KHÔNG đổi theo `hat`, trong khi chân trời của căn phòng
     thì có: 5/6 số tập chủ thể và bóng của nó lơ lửng trên sàn. */
  const sanY = chanTroi(H, hat), SAN = sanY / H, NGUOI = H * (doc ? 0.38 : 0.46);

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

  /* ── MỘT CHỖ QUYẾT ĐỊNH CÓ VẼ BIỂU TƯỢNG CHỦ THỂ HAY KHÔNG  (4/9/2026) ─────────────────
     Anh soi khung và nói *"người sao lơ lửng lỗi và xấu quá"*. Đúng, và bằng chứng ngay
     trong khung DAY IN LIFE: người que ĐỨNG TRÊN NÓC GIÁ KHO. Biểu tượng chủ thể là một
     lớp đè, đặt ở đường chân trời, và nó KHÔNG BIẾT phía sau có gì — nên hễ cảnh có vật
     cao ngang chân trời (giá kho, bàn, toà nhà) thì nhân vật đứng lên đầu vật ấy.

     Mã đã có sẵn đúng luật cho chuyện này ở dòng ngay trên: *"không vẽ biểu tượng khi đã
     có ảnh"* — vì ảnh AI đã vẽ chủ thể rồi, vẽ thêm là hai chủ thể trong một khung. Cảnh
     vẽ bằng code cũng là một nền CÓ NỘI DUNG, nên nó thuộc cùng luật ấy. Bản đầu của em
     bỏ sót vế thứ hai: đúng họ lỗi số 6 — vá một nhánh, để nguyên nhánh song song.

     Đặt ở MỘT biến thay vì ba điều kiện rời, vì ba chỗ vẽ biểu tượng (nền · `SoLieu` ·
     `KinhLup`) từng lệch nhau đúng theo kiểu ấy. */
  /* ── CẢNH VẼ CODE VẪN CẦN MỘT CHỦ THỂ  (4/9/2026) ────────────────────────────────────
     Điều kiện cũ tắt biểu tượng cho CẢ `canh_ve`, với lý do "cảnh vẽ code cũng là nền CÓ
     NỘI DUNG". Lý do ấy đúng cho `nenAnh` — ảnh CF vẽ sẵn chủ thể trong ảnh — và SAI cho
     `canh_ve`: `CanhVe` chỉ dựng BỐI CẢNH (kệ hàng, bàn ghế, mái nhà máy), không vẽ chủ thể
     của câu.
     Hậu quả soi được: kênh DAY IN LIFE có 4/8 nhịp vẽ code, và cả bốn ra một căn phòng
     trống — kể cả **nhịp mở đầu**, tức đúng ba giây quyết định người xem có lướt hay không.
     Cả 50/50 nhịp `canh` đều mang sẵn `bt`; nó chỉ bị chặn ở đây.
     Đây là chiều NGƯỢC của cùng họ lỗi §6: bản trước gộp hai nhánh vốn khác nhau. */
  const btVe = N.nenAnh ? "" : (N.bt || "");

  const Nen = (
    <>
      {N.nenAnh ? (
        <Img src={staticFile(N.nenAnh)}
             style={{ position: "absolute", inset: 0, width: W, height: H, objectFit: "cover",
                      transform: `scale(${kb})` }} />
      ) : (N.noi && !N.canh_ve) ? (
        <NenQue noi={N.noi} W={W} H={H} san={sanY} nguoi={NGUOI} t={t} />
      ) : (
        /* ── MỘT NHÁNH DUY NHẤT CHO MỌI NỀN VẼ BẰNG CODE  (4/9/2026) ────────────────────
           Trước bản này `canh_ve` là một nhánh RIÊNG, đứng trước nhánh nền phẳng — nên khối
           vẽ CHỦ THỂ (bóng đổ chân, biểu tượng, vệt chân kế thừa) chỉ tồn tại ở nhánh nền
           phẳng và không bao giờ chạy cho cảnh vẽ code. Gộp lại: cùng một nhánh, chỉ khác
           tấm nền phía sau. Thêm một loại nền mới sau này cũng không làm mất chủ thể nữa. */
        <AbsoluteFill>
          {N.canh_ve ? (
        /* ── CẢNH VẼ BẰNG CODE — lớp XEN KẼ, không phải lớp dự phòng  (4/9/2026) ──────────
           Đặt NGAY SAU `nenAnh` và TRƯỚC `noi`: `canh_ve` là một quyết định biên tập do
           Python đưa ra (xem `giai_thich.NOI_KENH` — vì sao, và tỉ lệ bao nhiêu), còn `noi`
           là lưới an toàn của bộ truyện tranh. Hai thứ khác hẳn nhau về ý định, nên thứ tự
           ở đây là một phần của chính sách chứ không phải tiện tay.

           Đo trước khi làm: 999/1.640 nhịp (60%) đặt một ảnh CF, riêng `canh` là 586/586.
           Sau khi xen kẽ: 403/1.640 = 24%. Một tập HOW LONG từ 134 ảnh còn 39.

           `CanhVe` dùng CHUNG `chanTroi(H, hat)` với `NenPhong`, nên nhịp vẽ code và nhịp
           đồ hoạ có cùng một mặt sàn — thiếu điều đó thì hai loại nhịp đọc ra hai bộ phim. */
        <CanhVe W={W} H={H} noi={N.canh_ve} nen={nenTrang} mau={mau} mauPhu={mauPhu}
                /* `canh_hat` là hạt RIÊNG của nhịp này, không phải hạt của tập: hai nhịp
                   cùng nơi chốn trong một tập phải ra hai đường bao khác nhau. Python
                   quyết và ghi vào nhịp — engine không tự suy, vì chọn ở hai nơi là hai
                   nơi để lệch nhau. */
                hat={N.canh_hat ?? hat} hatSan={hat} p={p} />
          ) : (
        /* NƠI CHỐN RỖNG = câu này TRỪU TƯỢNG (nói về con số, về vũ trụ, về ý niệm).
           Dựng nền trơn có đường chân trời, không dựng phòng ốc. Bản đầu mặc định về
           "phong_khach", nên một câu về tốc độ ánh sáng lại diễn trong phòng khách có sofa —
           nền ấy nói một điều SAI về nội dung câu, tệ hơn hẳn nền trống. */
        /* 3/9 — DÙNG CHUNG `NenPhong` VỚI MỌI KHUÔN CODE.
           Nhánh này từng tự vẽ gradient + sàn riêng, nên một video có thể có HAI kiểu nền
           khác nhau: nhịp `canh` không ảnh dùng gradient này, còn `chart`/`chia_doi` dùng
           nền phẳng. Hai nền khác nhau trong cùng một tập là chỗ mắt đọc ra "chắp vá".
           Nay cả hai đi qua cùng một bề mặt — cùng tường, cùng sàn, cùng quầng sáng, và
           cùng đổi kiểu theo `hat` nên vẫn đa dạng giữa các tập. */
            <NenPhong W={W} H={H} nen={nenTrang} mau={mau} hat={hat} />
          )}
            {/* CHỦ THỂ CỦA KHUNG — vẽ ĐẶC, không mờ.  (3/9/2026)
                Bản trước để `opacity: 0.34` với lý do "thuộc về căn phòng, không lơ lửng như
                hình dán". Lý do ấy đúng khi vật là thứ PHỤ đứng sau một ảnh hoặc một khối số.
                Ở nhánh này thì không có gì khác trong khung — phụ đề nằm hẳn dưới đáy — nên vật
                mờ 0,34 không đọc ra "thuộc về phòng", nó đọc ra "khung trống có vệt xám".
                Soi lưới bản dài SURVIVE: 3/6 khung rơi đúng vào cảnh ấy.
                Thứ làm vật thuộc về căn phòng không phải độ mờ mà là **bóng đổ chân** — nên vẽ
                bóng ellipse trên sàn, và vẽ vật đặc ở trên. */}
            {/* ── KHÔNG VẼ BIỂU TƯỢNG KHI LỚP TRÊN ĐÃ VẼ  (4/9/2026) ─────────────────────
                Nhịp `so_lieu` không có ảnh thì `SoLieu` TỰ vẽ `bt` (nó nhận
                `bt={N.nenAnh ? "" : N.bt}`), ở cỡ và chỗ riêng của bố cục ấy. Lớp nền này vẽ
                thêm một lần nữa ở mặt sàn — **hai biểu tượng giống hệt nhau trong một khung**,
                khác cỡ, khác chỗ.
                Đo: 42/245 nhịp `so_lieu` KHÔNG có prompt ảnh nào (không bao giờ có ảnh) nên
                chắc chắn dính; 203 nhịp còn lại dính mỗi khi hồ CF cạn.
                Cổng đã có ở `SoLieu` chỉ chặn *ảnh + biểu tượng*, không chặn *biểu tượng +
                biểu tượng* — đúng họ "vá một nhánh, để nguyên nhánh song song".
                Nhường cho lớp trên: nó biết bố cục nên đặt đúng chỗ hơn. */}
            {btVe && String((N as any)?.khuon || "") !== "so_lieu" ? (
              <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
                   style={{ position: "absolute", left: 0, top: 0 }}>
                {(() => {
                  /* ── CHỦ THỂ PHẢI LÀ CHỦ THỂ  (4/9/2026) ──────────────────────────────
                     Đo trên khung dựng thật: nét nhân vật cao **0,30·H**, và khoảng trống
                     phía trên chiếm gần nửa khung. Mọi ảnh anh gửi đều để chủ thể chiếm
                     quá nửa chiều cao — đó là thứ tách "một cảnh có nhân vật" khỏi "một
                     phông nền có dán hình nhỏ ở góc".
                     Chân đã neo vào mặt sàn (`DAY_HINH`) và mặt sàn đã lên trên vùng chữ,
                     nên phóng to giờ chỉ ăn vào khoảng trống — trước hai bản vá ấy thì
                     phóng to sẽ đâm thẳng vào dải chữ. Thứ tự sửa quyết định được phép
                     sửa cái gì. */
                  const s0 = Math.min(H * 0.54, W * 0.62);
                  /* Lệch trái/giữa/phải theo `hat` — chủ thể đứng chính giữa ở MỌI tập là dấu
                     hiệu khuôn mẫu rõ nhất, đúng thứ luật YouTube gọi là "bố cục giống nhau". */
                  /* Đổi theo `hat` (tập) VÀ theo mốc vào của chính nhịp (`N.s`) — chỉ theo
                     `hat` thì mọi cảnh trong CÙNG một tập đứng đúng một chỗ, và một tập tám
                     phút có mười tám cảnh chồng khít lên nhau. Đúng luật 14.9: đa dạng phải
                     nằm ở thứ người xem NHÌN THẤY, mà thứ họ thấy là hai cảnh liền nhau. */
                  const kv = Math.abs(hat + Math.round(N.s * 7)) % 6;
                  const cx = W * [0.5, 0.38, 0.62, 0.5, 0.42, 0.58][kv];
                  /* ── CỠ KHUNG: XA · VỪA · GẦN  (3/9/2026) ────────────────────────────────
                     `canh` chiếm **35% tổng số nhịp** — nhiều nhất trong bộ. Trước bản này mọi
                     cảnh vẽ chủ thể ở ĐÚNG MỘT CỠ (`s0`), chỉ đổi chỗ đứng. Xem một tập tám
                     phút thì mười tám cảnh có cùng khoảng cách máy, và mắt đọc ra "một cú máy
                     duy nhất" dù vật vẽ khác nhau.
                     Nghề dựng phim gọi đây là cỡ cảnh, và nó là thứ tách một chuỗi cảnh khỏi
                     một chuỗi hình dán. Ba cỡ, xoay cùng nhịp với vị trí:
                       xa   0,74  vật nhỏ giữa không gian — dùng cho câu nói về quy mô
                       vừa  1,00  cỡ gốc
                       gần  1,26  vật tràn khung — dùng cho câu nói về chi tiết
                     Chủ thể to hơn thì phải HẠ xuống để chân vẫn chạm sàn, nếu không nó lơ
                     lửng — đó là lý do `sanY` nhân theo cùng hệ số. */
                  const cz = [1.0, 0.74, 1.26, 0.86, 1.14, 1.0][kv];
                  /* CHỦ THỂ KHÔNG ĐƯỢC CHẠM DẢI PHỤ ĐỀ.  (3/9/2026)
                     Cỡ cảnh 1,26× làm hình tràn xuống vùng chữ — soi lưới thấy tay của hình
                     người cắt ngang câu phụ đề ở HOW MUCH, và con vi-rút của SMALLEST cũng
                     chạm mép chữ. Cỡ cảnh là thứ tốt, nhưng nó phải chịu thêm một ràng buộc mà
                     công thức chưa mã hoá: **chiều cao còn lại phía trên dải phụ đề**.
                     Đúng họ lỗi §6 — một kích thước chịu hai ràng buộc mà công thức chỉ có một. */
                  const traTren = sanY - H * 0.02;          // khoảng trống từ đỉnh khung tới sàn
                  const sz = Math.min(s0 * cz, traTren * 1.92) * coHinh(btVe);
                  /* ── QUY TẮC D: CẢNH SAU KẾ THỪA CẢNH TRƯỚC  (4/9/2026) ──────────────
                     §12.11 D: *cảnh sau mang dấu vết cảnh trước (vệt chân dài dần)* — thứ tách
                     một CHUỖI CẢNH khỏi một chuỗi hình rời rạc.
                     `ap_gu` đã ghi `ke_thua` (cảnh thứ mấy trong một mạch) cho **94/300 nhịp
                     `canh`** ở 7 kênh, engine khai kiểu cho nó, và có năm dòng chú thích mô tả
                     quy tắc này ngay trên nhánh dựng — nhưng `N.ke_thua` KHÔNG xuất hiện một
                     lần nào trong cả ba tệp TSX. Quy tắc D chưa từng được dựng, và chú thích
                     Python còn khẳng định "Engine dùng nó để…".
                     Nay vẽ đúng thứ luật mô tả: mỗi cảnh trong mạch để lại thêm một vệt chân
                     trên sàn, mờ dần về phía sau. Cảnh 1 không có vệt nào (chưa có gì trước
                     nó), cảnh 4 có ba vệt — người xem đọc ra "vẫn đang đi tiếp". */
                  const mach = Math.max(0, Math.min(6, Number(N.ke_thua ?? 0) - 1));
                  return (
                    <>
                      {Array.from({ length: mach }).map((_, m) => {
                        const lui = (m + 1) / (mach + 1);
                        return (
                          <ellipse key={`vet${m}`}
                                   cx={cx - sz * 0.30 * (m + 1)} cy={sanY + sz * 0.03}
                                   rx={sz * 0.13} ry={sz * 0.026}
                                   fill="#000000" opacity={0.10 * (1 - lui * 0.7)} />
                        );
                      })}
                      {/* BÓNG ĐỔ NẰM ĐÚNG MẶT SÀN, không nằm dưới nó. `sanY + sz*0,03` đẩy
                          bóng xuống dưới đường chân trời một khoảng đổi theo cỡ hình — nên
                          hình càng to thì bóng càng rời xa chân, và mắt đọc ra "vật lơ lửng
                          có một vệt bẩn bên dưới". Bóng là thứ NEO vật vào nền, nên nó phải ở
                          đúng chỗ vật chạm nền. */}
                      <ellipse cx={cx} cy={sanY} rx={sz * 0.34} ry={sz * 0.048}
                               fill="#000000" opacity={0.13} />
                      {/* Đáy hình chạm sàn: xem `DAY_HINH`. `0,5` giả định hình chạm hết hộp
                          của nó, mà không hình nào chạm — nên vật treo 6,8% cỡ của nó. */}
                      <g transform={`translate(${cx} ${sanY - sz * DAY_HINH})`}>
                        <BieuTuong ten={btVe} s={sz} />
                      </g>
                    </>
                  );
                })()}
              </svg>
            ) : null}
        </AbsoluteFill>
      )}
    </>
  );

  const than = () => {
    switch (N.khuon) {
      case "chia_doi":
        return { nen: <NenPhong W={W} H={H} nen={nenTrang} mau={mau} hat={hat} anTroi />,
                 lop: <ChiaDoi W={W} H={H * 0.80} trai={N.trai || {}} phai={N.phai || {}} mau={mau} p={p}
                               nen={nenTrang}
                               /* `bo_ss` do Python quyết — cùng lý do với `bo_the`.
                                  Truyền RIÊNG `hat` (hạt của tập) để bo góc và độ đậm tấm nền
                                  vẫn đổi theo TẬP. Bản cũ nhét `bo_ss` vào chỗ `hat`, nên hai
                                  thứ khác hẳn nhau dùng chung một con số: tấm nền hết đổi theo
                                  tập, và biến thể `rx` nhỏ nhất không bao giờ đạt tới. */
                               hat={N.bo_ss ?? 0} hatTap={hat} /> };
      case "so_lieu":
        return { nen: Nen,
                 lop: <g>
                   {/* 1/9 — KHÔNG VẼ BIỂU TƯỢNG KHI ĐÃ CÓ ẢNH.
                       Soi khung kênh HOW BIG: ảnh AI đã vẽ đúng xe buýt và máy bay, mà lớp code
                       vẫn vẽ thêm một chiếc ô tô nhỏ đè lên trước. Hai lớp cùng nói một điều,
                       và nói khác nhau. Biểu tượng sinh ra để THAY ảnh khi không có ảnh, không
                       phải để đứng cạnh ảnh. */}
                   <SoLieu W={W} H={H * 0.80} so={N.so || ""} don={N.don || ""} chu={N.chu || ""}
                           bt={btVe} mau={mau} p={p}
                           /* MẶT SÀN — TRUYỀN THẲNG PIXEL, KHÔNG QUY ĐỔI.
                              `SoLieu` nhận `H={H*0.80}` nên các PHÂN SỐ bên trong nó (0,64·H…)
                              là phân số của 0,8·H — nhưng hộp không bị CO, nó chỉ được khai
                              chiều cao nhỏ hơn. Toạ độ pixel vì thế ánh xạ 1:1 với khung thật.
                              Bản đầu em chia `sanY/0.80` theo phản xạ "đổi hệ quy chiếu" và
                              đẩy nhân vật xuống 25% — đo lại thấy chân ở 0,722·H trong khi sàn
                              ở 0,66·H. Cùng một họ lỗi hai lần liên tiếp, lần này là quy đổi
                              THỪA thay vì quy đổi THIẾU: phải đo, đừng suy (§13.4). */
                           san={sanY}
                           tren_anh={!!N.nenAnh} nen={nenTrang}
                           /* `bo` là trục bố cục THỨ HAI của `SoLieu` (đổi cỡ và chỗ đặt khối
                              số). Bản cũ tính ngay tại đây bằng `hat % 3` — tức engine tự
                              quyết, không có đối ứng nào ở Python, trong khi dòng ngay dưới
                              ghi "`kieu_so` do Python quyết… Engine chỉ đọc". Câu ấy đúng cho
                              `kieu`, SAI cho `bo`, nên sửa bảng `GU_SO` không chạm được nửa
                              còn lại của khuôn chiếm 29% số nhịp.
                              Nay Python ghi `bo_so` vào nhịp; đây chỉ là đường lui. */
                           bo={N.bo_so ?? (hat % 3)}
                           /* `kieu_so` do Python quyết — xem `GU_SO`. Engine chỉ đọc. */
                           kieu={N.kieu_so ?? 0} />
                   {N.dai_chu ? <DaiChu W={W} H={H * 0.80} chu={N.dai_chu} p={p} /> : null}
                 </g> };
      case "truc":
        return { nen: <NenPhong W={W} H={H} nen={nenTrang} mau={mau} hat={hat} />,
                 lop: <Truc W={W} H={H * 0.80} moc={N.moc || []} vt={N.vt ?? -1} mau={mau} p={p} /> };
      case "kinh_lup":
        return { nen: Nen,
                 /* Điểm soi mặc định 0,34/0,50 là một chỗ TUỲ TIỆN — soi khung THE RULES
                    thấy ống kính phóng to đúng một mảng giấy trắng, đọc ra cái đĩa rỗng. Ảnh
                    của bộ này luôn đặt chủ thể ở giữa khung (luật `SAN_NEN`: *open space in
                    the centre*), nên giữa khung là chỗ đúng để soi. */
                 lop: <KinhLup W={W} H={H * 0.80} x={W * (N.x ?? 0.50)} y={H * 0.80 * (N.y ?? 0.44)}
                               nhan={N.nhan || ""} mau={mau} p={p}
                               bt={btVe}
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
        /* `dai_chu` đỡ cho `chu`.  (4/9/2026)
           Mọi khuôn khác vẽ `dai_chu`, riêng nhánh này bỏ nó — nên nhịp `howlong` bản dài
           ghi `dai_chu: "CAR — 11 months"` mà KHÔNG có `chu`, và người xem nhận 11 biểu
           tượng không nhãn: mất đúng thứ quy tắc C cần (đếm được thì phải biết đếm cái gì).
           Đỡ vào chính ô nhãn của `Dem` chứ không chồng thêm một lớp `DaiChu` — ô ấy đã
           nằm đúng chỗ dưới lưới và tự co cỡ chữ theo bề ngang, còn chồng lớp thì một
           nhịp có cả hai trường sẽ hiện hai dòng đè nhau. */
        return { nen: Nen,
                 lop: <Dem W={W} H={H * 0.80} n={N.n || 4} ngay={N.ngay !== false}
                           chu={N.chu || N.dai_chu
                                || (N.so && N.don ? `${N.so} ${N.don}` : "")}
                             p={p} mau={mau} /> };
      case "chart":
        return { nen: <NenPhong W={W} H={H} nen={nenTrang} mau={mau} hat={hat} anTroi />,
                 lop: <Chart W={W} H={H * 0.80} cot={N.cot || []} don={N.don || ""}
                             mau={mau} mauPhu={mauPhu} p={p} nen={nenTrang} hat={hat}
                             /* `kieu_chart` do Python quyết — xem `GU_CHART`. */
                             kieu={N.kieu_chart ?? 0} /> };
      case "the_chu":
        return { nen: <NenPhong W={W} H={H} nen={nenTrang} mau={mau} hat={hat} />,
                 lop: <TheChu W={W} H={H * 0.80} chu={N.the || N.loi} p={p} mau={mau}
                              nen={nenTrang}
                              /* `bo_the` do Python quyết và ghi vào nhịp — xem `GU_KHUON`.
                                 Engine KHÔNG tự suy ra: chọn ở hai nơi là hai nơi để lệch nhau,
                                 và lệch kiểu ấy không báo lỗi, chỉ dựng ra bố cục khác. */
                              bo={N.bo_the ?? hat} /> };
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
        /* 4/9 — NHẸ TAY LẠI: #48 (28% đen) -> #24 (14%), và bắt đầu muộn hơn (52% -> 64%).
             Đo mép đáy ba khung: sáng 25–32%. Vignette không phải thủ phạm duy nhất, nhưng
             nó cộng vào MỌI khung kể cả khung đã sáng, nên nó là cái rẻ nhất để nới.
             Vignette tồn tại để dẫn mắt vào giữa (§12.12) — 14% vẫn làm được việc ấy; 28%
             thì nó thôi dẫn mắt và bắt đầu làm tối phim. */
        background: `radial-gradient(120% 78% at 50% 46%, #00000000 64%, #00000024 100%)`,
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
        : <PhuDe tu={tu} t={t} W={W} H={H} mau={mau}
                  /* Độ sáng dải đáy của ẢNH nhịp này — `nen_gt.sang_day` đo lúc sinh và ghi
                     vào nhịp. Nhịp không có ảnh thì -1, và `PhuDe` giữ mực trắng vì sàn phòng
                     đã được làm sẫm ở mép dưới. */
                  /* Cảnh vẽ code cũng phải khai độ sáng đáy, không chỉ ảnh CF — nếu
                     không thì nhánh "nền sáng thì đổi mực" của `PhuDe` không bao giờ
                     chạy cho chúng, và ta lại phải làm tối sàn để cứu chữ. */
                  sangNen={N.canh_ve
                    ? sangDayCanh(N.canh_ve, nenTrang, mau, mauPhu)
                    : Number((N as any)?.sangDay ?? -1)} />}

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
