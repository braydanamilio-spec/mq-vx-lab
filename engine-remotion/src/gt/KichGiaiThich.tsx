import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, Img } from "remotion";
import { NenQue } from "../que/NenQue";
import { TuVe } from "./TuVe";
import { IconVe, co_icon } from "./IconVe";
import { HinhNhap, co_hinh_nhap } from "./HinhNhap";
import { chanTroi, DAY_HINH, coHinh, ChiaDoi, SoLieu, Truc, KinhLup, DaiChu, Dem, TheChu, Chart, BieuTuong, NenPhong, tiLe, nguonSang} from "./Khuon";
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
import { chu, datChu } from "./Chu";
const F = () => chu();

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
  ma?: string;                     // mã kênh — chọn PHÔNG CHỮ, xem `Chu.tsx`
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
        fontFamily: F(), fontWeight: 700, fontSize: fs, lineHeight: 1.25,
        textAlign: "center", letterSpacing: "-0.01em",
        /* 3/9 — SIẾT QUẦNG SAU KHI ĐO. Bỏ dải đen xong, cổng `kiem_hinh` báo tương phản phụ đề
             **4,2:1 < 4,5:1** — sát chuẩn nhưng dưới chuẩn. Đây đúng cái đã xảy ra hồi 1/9 khi bỏ
             hộp đen: hình đẹp hơn thật, nhưng đổi lấy chữ khó đọc mà KHÔNG ĐO.
             Lần này có cổng nên biết ngay. Bù bằng quầng dày hơn — vẫn bám sát nét nên không tạo
             mảng tối, chỉ tăng tương phản đúng chỗ chữ đứng. */
        /* Quầng phải NGƯỢC sắc với mực: chữ đậm trên nền sáng cần quầng SÁNG để tách, quầng
           đen quanh chữ đen thì không tách được gì. */
        textShadow: (Number(sangNen ?? -1) >= 117)
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

            ── NGƯỠNG 170 SAI THEO CHÍNH CÔNG THỨC CỦA CỔNG  (4/9/2026) ──────────────────
            Cổng đo tương phản bằng `(sáng+5)/(tối+5)` trên thang xám. Giải ngược ra ngưỡng:

                chữ TRẮNG (243) đạt 4,5:1 khi nền  <=  50
                chữ TỐI  (#14161C ≈ 22) đạt 4,5:1 khi nền >= 117

            Tức 170 quá cao: mọi nền trong khoảng **117–170** đáng lẽ dùng mực TỐI thì lại
            nhận mực trắng. Đo trên bản dài `howlong`: nền dưới chữ 140 · 142 · 156 · 158 —
            nằm trọn trong khoảng ấy, và cho ra **1,4–1,7:1** thay vì 5,4–6,0:1.

            Con số 170 chưa bao giờ được tính, nó được đặt. Nay lấy từ công thức: 117.
            (Khoảng 50–117 thì KHÔNG mực nào đạt 4,5:1 — ở đó chọn mực trắng vì nó khá hơn,
            và ghi ra đây rằng vùng ấy chưa giải được thay vì giả vờ là đã.)
            Từ đang đọc giữ màu vàng khi nền tối, và chuyển sang cam đậm khi nền sáng — vẫn là
            tín hiệu "từ này đang được đọc", chỉ đổi sắc để còn đọc được. */}
        {(() => {
          const sd = Number(sangNen ?? -1);
          const sang = sd >= 117;   // >= 117 thì mực TỐI đạt 4,5:1 — xem dẫn giải ở trên
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

/* Khuôn nào là một CẢNH (cần một chủ thể đứng trong bối cảnh) và khuôn nào là một SƠ ĐỒ (tự
   vẽ kín khung). Liệt kê phía CẢNH chứ không phía sơ đồ: khuôn thêm sau mặc định là sơ đồ,
   tức mặc định KHÔNG chồng thêm lớp — hướng an toàn. */
const KHUON_CANH = new Set(["canh", "nhom"]);

export const KichGiaiThich: React.FC<PropsGT> = ({
  nhip = [], tu = [], voMp3 = "", nhac = "", nhacVol = 0.13,
  tieuDe = "", handle = "", mau = "#E0533D", mauPhu = "#2F7D6B", doc = false, hat = 0,
  nenTrang = "#EFE7D6", chuTrang = "#2C2722", ma = "",
}) => {
  const frame = useCurrentFrame();
  const { fps, width: W, height: H } = useVideoConfig();
  const t = frame / fps;

  const N = nhip.find((x) => t >= x.s && t < x.e) || nhip[nhip.length - 1];
  /* PHÔNG CỦA KÊNH — đặt MỘT LẦN, trước khi dựng bất cứ con nào. React dựng cây từ trên
     xuống trong cùng một lượt đồng bộ nên mọi `F()` bên dưới đọc đúng phông này. Đặt sau
     `if (!N)` thì khung rỗng sẽ giữ phông của kênh dựng TRƯỚC — hiếm, nhưng là đúng loại lỗi
     không ai tìm ra. Xem `Chu.tsx`. */
  datChu(ma);
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
      {/* ── TRANH NHẬP LÀ CẢ KHUNG  (5/9/2026) ─────────────────────────────────────────
          Anh: *"vẫn xấu lơ lửng và lặp đi lặp lại quá nhiều, đổi cách làm mới"*. Ba vòng
          trước em co bức tranh về một hộp rồi neo đáy vào SÀN CỦA MÌNH — nhưng mỗi bức
          unDraw mang theo mặt đất của chính nó ở một độ cao khác nhau, nên nhân vật đứng
          trên đất của bức tranh còn bóng của mình nằm tách phía dưới. Không hằng số nào
          chữa được vì con số ấy khác ở từng bức.
          Nay bức tranh chiếm TRỌN khung: một mặt đất duy nhất, của chính nó. Không sàn thứ
          hai, không bóng thứ hai, không cảnh thứ hai — nên không còn gì để lệch.
          Chọn hình do Python quyết theo NGHĨA của câu (`_rai_hinh_nhap`, 300 hình chứ không
          phải 2), engine chỉ đọc — §15.3: nơi CHỌN và nơi biết bản sắc phải là một. */}
      {(N as any)?.hinh_nhap ? (
        <AbsoluteFill>
          <div style={{ position: "absolute", inset: 0, background: nenTrang }} />
          <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
               style={{ position: "absolute", left: 0, top: 0 }}>
            {/* Canh giữa vùng NỘI DUNG (trên dải phụ đề), không giữa khung: nửa dưới khung
                dành cho chữ, và một bức tranh canh giữa khung thì chân nó chui vào chữ. */}
            <g transform={`translate(${W / 2} ${sanY * 0.52})`}>
              <HinhNhap bt={String((N as any).hinh_nhap)} s={W * 0.94} p={p / 0.26}
                        mau={mau} mauPhu={mauPhu} nen={nenTrang} />
            </g>
          </svg>
        </AbsoluteFill>
      ) : N.nenAnh ? (
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
          {/* ── HÌNH NHẬP LÀ CẢ MỘT CẢNH, KHÔNG PHẢI MỘT VẬT  (5/9/2026) ────────────
              Soi lưới: khung có hình unDraw hiện HAI bộ cây — một bộ của `CanhVe` mình vẽ,
              một bộ nằm sẵn trong chính bức unDraw. Hình của kho ấy được vẽ như một bức
              tranh hoàn chỉnh (người + cây + mặt trời + mặt đất), không như một hình cắt
              rời để dán lên nền khác.
              Đây đúng luật đã rút sáng nay và lần này áp cho một lớp mới: MỘT KHUNG MỘT BỨC
              TRANH. Có hình nhập thì nó LÀ cảnh — nền chỉ còn tường và sàn. */}
          {N.canh_ve && !(N as any)?.hinh_nhap ? (
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
            <NenPhong W={W} H={H} nen={nenTrang} mau={mau} hat={hat}
                  /* Tắt cửa sổ khi khung đã có chủ thể toàn khung. Anh: *"bối cảnh sau không
                      liên quan và làm chồng chéo"*. Đúng: `NenPhong` vẽ một CĂN PHÒNG CHUNG
                      sau 222/264 nhịp `canh` — những nhịp không có nơi chốn nào cả — nên cái
                      cửa sổ ấy không nói gì về câu đang kể, mà lại đứng đúng chỗ chủ thể
                      đứng. Một bối cảnh không liên quan thì không phải bối cảnh, nó là nhiễu:
                      bỏ đi vừa hết chồng chéo vừa hết vô can, một nhát hai lỗi. */
                  anCua={!!btVe}
                dauAn={(N as any)?.dau_an ?? 0} />
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
            {/* ── CHỦ THỂ CHỈ VẼ CHO KHUÔN *CẢNH*, KHÔNG VẼ CHO KHUÔN *SƠ ĐỒ*  (4/9) ─────
                Điều kiện cũ loại đúng `so_lieu`. Nhưng `so_lieu` không phải khuôn sơ đồ duy
                nhất — `dem`, `truc`, `chart`, `chia_doi`, `the_chu`, `kinh_lup` đều tự vẽ kín
                khung bằng đồ hoạ của chúng. Vẽ thêm một chủ thể phía sau là hai sơ đồ trong
                một khung.
                Anh gửi khung DAY IN LIFE: tám mặt trời xếp lưới VÀ một người đứng giữa, chữ
                "19 miles" chạy xuyên qua chân người. Ba lớp, không lớp nào biết lớp nào.
                Chú thích ngay dưới đã ghi đúng họ lỗi này (*"cổng chỉ chặn ảnh + biểu tượng,
                không chặn biểu tượng + biểu tượng"*) và bản vá ấy chỉ liệt kê MỘT khuôn —
                đúng §13.9: danh sách ngoại lệ là danh sách vô hạn. Nay hỏi ngược lại, và hỏi
                theo VAI: khuôn này là một CẢNH hay một SƠ ĐỒ? Cảnh thì cần chủ thể; sơ đồ
                thì chủ thể của nó chính là đồ hoạ nó vẽ. */}
            {btVe && KHUON_CANH.has(String((N as any)?.khuon || "canh")) ? (
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
                  /* ── HỘP CHỦ THỂ ĐANG BỊ BỀ NGANG GHÌM  (4/9/2026) ────────────────
                     Anh: *"vẫn còn xấu và chồng chéo, chưa thể hiện được cái nói"* — sau
                     ba vòng em vá chồng chéo bằng ba cách khác nhau. §2: sửa vòng thứ ba
                     mà vẫn cùng họ lỗi thì thứ sai là cách tiếp cận.
                     Đo thay vì đoán. Hình người vẽ ra cao 0,867·s và rộng 0,30·s — cao gấp
                     ba lần rộng. Hộp `s` lấy `min(H*0,54, W*0,62)`; ở khung dọc 1080×1920
                     thì `W*0,62 = 670` chặn trước `H*0,54 = 1037`. Kết quả: nhân vật cao
                     **581px = 30% khung** trong khi chỉ rộng 19% khung.
                     Tức cái chặn bề ngang đang ghìm chiều cao để giữ một bề ngang còn thừa
                     hơn tám mươi phần trăm. Bốn ảnh tham khảo anh gửi đều để nhân vật
                     chiếm 55–65% chiều cao — đó là thứ tách "một cảnh có nhân vật" khỏi
                     "một phông nền có dán hình nhỏ", và nó cũng là lý do khung mình đọc ra
                     CHỒNG CHÉO: một chủ thể nhỏ đứng giữa những món đồ cùng cỡ thì mắt đọc
                     ra va chạm, không đọc ra chiều sâu.
                     Trần mới: không hình nào vẽ rộng quá hộp của nó, nên `W*0,90` đủ bảo
                     đảm lọt khung cho cả hình bè ngang nhất (xe buýt, máy bay). Chiều cao
                     vẫn do `traTren` chặn ở dưới, nên chủ thể không bao giờ đội lên vùng
                     số hay vùng chữ. */
                  const s0 = Math.min(H * 0.68, W * 0.90);
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
                  /* Quy đổi qua TỈ LỆ THẬT của hình (xem `TI_LE`), thay vì kẹp hộp
                     vuông bằng hai trần rồi lấy min. Trần cao đo bằng khoảng trống thật
                     từ đỉnh vùng nội dung xuống mặt sàn; trần ngang vẫn giữ để hình bè
                     ngang không tràn khung. Với hình người, trần ngang thôi chặn — đúng
                     như nó phải thế, vì nhân vật là hình cao. */
                  const tl = tiLe(btVe);
                  /* 0,45 chứ không phải 0,62  (4/9, sau khi anh soi bản 60%).
                     Em đo ảnh tham khảo ra "nhân vật chiếm 55–65% khung" rồi chỉnh thẳng
                     tới đó — và anh nói *"to chà bá vô, không hợp"*. Anh đúng, và chỗ em
                     đọc sai là NGỮ CẢNH của con số ấy: trong ảnh tham khảo nhân vật to vì
                     nó ngồi trong một CĂN PHÒNG ĐẦY ĐỦ — sofa, đèn, chậu cây, sàn gỗ — nên
                     khung vẫn cân. Bản mình chỉ có tường trơn với một cửa sổ, nên cùng tỉ
                     lệ ấy đọc ra một hình dán khổng lồ giữa nền trống.
                     Đúng §12.5 lần nữa: một con số đúng ở ngữ cảnh nó được đo, sai ở ngữ
                     cảnh mới. Chép tỉ lệ mà không chép mật độ bối cảnh là chép nửa vời.
                     0,45 là mức nhân vật vẫn đọc ra nhân vật mà khung còn thở. */
                  const caoDuoc = Math.min(traTren - H * 0.04, H * 0.45);
                  const sz = Math.min(caoDuoc / tl.cao, (W * 0.90) / tl.rong, s0 * cz * 2)
                             * coHinh(btVe);
                  /* Đĩa tách lớp — xem chú thích tại chỗ vẽ. Khai ở đây, TRƯỚC mọi chỗ
                     dùng: `const` đọc trước dòng khai là `ReferenceError` lúc chạy mà
                     `esbuild` vẫn xanh (§15.18, đã trả giá một lần ở `Chart`). */
                  const _canhVe = !!(N as any)?.canh_ve;
                  /* 0,90 / 1,02 là bản đầu và nó ĐI QUÁ: soi clip demo thì cái đĩa
                     xoá luôn cả căn cảnh nó sinh ra để tách khỏi — khung còn lại một
                     bức tường trơn với một cái bóng. Chữa gốc đã nằm ở phía Python
                     (khuôn sơ đồ không nhận cảnh vẽ nữa), nên ở đây chỉ cần đủ để tách
                     chiều sâu, không cần xoá.
                     0,74 / 0,90: đồ đạc sau lưng chủ thể lùi hẳn một bậc mà vẫn ĐỌC ĐƯỢC
                     là đồ đạc — đúng như ảnh tham chiếu, nơi cái tủ vẫn rõ nét ở mép trái. */
                  const _dam = _canhVe ? 0.74 : 0.58;
                  const _ban = _canhVe ? 0.90 : 0.78;
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
                      {/* ── ĐĨA TÁCH LỚP SAU CHỦ THỂ  (4/9/2026) ────────────────────────
                          Anh gửi bốn khung: đồng hồ đè lên dãy tủ · cốc cà phê đè lên hạt và
                          hai cột · mặt trời đè vai người · số "560" đè quả cầu. Cùng một gốc:
                          `CanhVe` đặt đồ đạc bằng toạ độ ghi cứng, phần lớn quanh giữa khung
                          (`W*0.415–0.585`, `W*0.46–0.71`), còn chủ thể cũng vẽ ở giữa. Hai lớp
                          chọn chỗ độc lập và không lớp nào biết lớp kia.
                          Sửa toạ độ của từng cảnh trong `CanhVe` là sửa vài chục hàm và vẫn
                          hở ở cảnh thêm sau. Cách nhà đã dùng cho đúng bài này ở ảnh bìa
                          (§13.27): **một đĩa mờ đặt SAU biểu tượng** — cách mọi hãng đặt logo
                          lên một khung hình bất kỳ. Nó không xoá đồ đạc, nó tách CHIỀU SÂU,
                          nên chủ thể đọc ra ngay cả khi có vật phía sau.
                          Màu lấy từ chính nền (`nenTrang`) chứ không phải trắng/đen: đĩa trắng
                          trên nền ấm đọc ra một vệt bẩn, còn đĩa cùng tông thì đọc ra khoảng
                          lùi. Bo theo cỡ hình, mờ dần ra mép để không thành một cái huy hiệu
                          tròn — đúng thứ §TRAN_KHUNG vừa phải đi cấm ở phía prompt. */}
                      {/* Cảnh vẽ code phía sau thì cần dìm mạnh và rộng hơn hẳn; tường
                          trơn thì giữ nguyên mức đã đo. */}
                      <defs>
                        <radialGradient id={`dia${Math.round(cx)}`}>
                          {/* Ba nấc, và cả ba đo bằng MẮT ở cỡ thật, không chọn cho đẹp
                              số: bản đầu 0,92/0,82/0 đọc ra một QUẦNG SÁNG rõ rệt — nó tách
                              được chủ thể nhưng lại thành một vật thứ ba trong khung, đúng
                              cái nó sinh ra để tránh. Đĩa tách lớp làm đúng việc khi người
                              xem KHÔNG nhận ra là có nó: chỉ vừa đủ dìm đồ đạc phía sau. */}
                          {/* ── ĐỘ MẠNH THEO CÁI NẰM SAU NÓ  (5/9/2026) ──────────────
                              Ba nấc dưới đây được đo trên nền TƯỜNG TRƠN, và ở đó chúng
                              đúng: 0,58 vừa đủ tách chiều sâu mà người xem không nhận ra
                              có một cái đĩa. Nhưng nhịp `canh_ve` đặt sau chủ thể cả một
                              CẢNH VẼ — tủ, đồng hồ, núi, bia mộ — và cùng con số ấy chỉ
                              dìm được 42%: anh gửi bốn khung, khung nào đồ đạc cũng xuyên
                              qua chủ thể.
                              Đúng §12.5: một con số đúng ở ngữ cảnh nó được đo, sai ở ngữ
                              cảnh mới. Đĩa tách lớp không có MỘT độ mạnh đúng — nó có một
                              CÔNG VIỆC (tách chủ thể khỏi thứ phía sau), và công sức cần
                              bỏ ra phụ thuộc thứ phía sau bận đến đâu.
                              Ảnh tham chiếu anh gửi (cậu bé + chồng báo) làm đúng việc này
                              bằng bố cục: tủ dạt hẳn mép trái, tường sau lưng để TRỐNG.
                              Mình không di được đồ đạc của mười nơi chốn, nhưng dìm chúng
                              sau lưng chủ thể cho cùng một kết quả — và dìm bằng chính màu
                              tường nên nó đọc ra khoảng lùi, không đọc ra tấm dán. */}
                          <stop offset="0%" stopColor={nenTrang} stopOpacity={_dam} />
                          <stop offset="45%" stopColor={nenTrang} stopOpacity={_dam * 0.79} />
                          <stop offset="100%" stopColor={nenTrang} stopOpacity={0} />
                        </radialGradient>
                      </defs>
                      <ellipse cx={cx} cy={sanY - sz * DAY_HINH}
                               rx={sz * _ban} ry={sz * (_ban + 0.02)}
                               fill={`url(#dia${Math.round(cx)})`} />
                      {/* Đáy hình chạm sàn: xem `DAY_HINH`. `0,5` giả định hình chạm hết hộp
                          của nó, mà không hình nào chạm — nên vật treo 6,8% cỡ của nó. */}
                      <g transform={`translate(${cx} ${sanY - sz * DAY_HINH})`}>
                        {/* `tu` do Python quyết theo chính lời của nhịp — xem `_rai_tu_the`.
                            Engine chỉ đọc, đúng nguyên tắc §15.3. */}
                        {/* Chủ thể tự vẽ ra như cảnh — xem `TuVe.tsx`. Chậm hơn nền một
                            nhịp (0,26 thay vì 0,20) để mắt đọc được thứ tự: cảnh dựng lên
                            trước, rồi nhân vật bước vào. Vẽ cùng lúc thì hai thứ tranh sự
                            chú ý và không thứ nào được nhìn. */}
                        {/* ── HÌNH NHẬP THẮNG HÌNH TỰ VẼ  (5/9/2026) ─────────────────
                            Xem `HinhNhap.tsx`. Điều kiện là `co_hinh_nhap(btVe)`, không
                            phải một danh sách tên chép tay: kho hình do `tai_svg.py` sinh
                            ra và sẽ nở thêm, nên engine phải HỎI kho chứ đừng giữ một bản
                            sao của nó (§13.2 — cổng cầm danh sách chép tay là cổng che lỗi).
                            `bien` lấy TƯ THẾ đã rải sẵn: `_rai_tu_the` phát năm tư thế cho
                            54% số nhịp, và nếu ở đây lấy một hình cố định thì cả trục đa
                            dạng ấy bị vứt đi ngay chỗ nó đáng lẽ hiện ra. */}
                        {/* ── `bien` PHẢI ĐỔI THEO NHỊP  (5/9/2026, sau khi soi lưới) ────
                            Bản đầu lấy `tu + nv`. Soi bốn khung thì BA khung liền nhau ra
                            đúng một hình — vì `tu` và `nv` là hằng trên cả một mạch cảnh
                            (chúng rải theo thứ tự NGƯỜI xuất hiện, không theo nhịp). Đúng
                            §14.9: chọn sai đại lượng thì số đo đẹp mà sản phẩm vẫn lặp —
                            thứ người xem cảm được là "hai nhịp liền nhau có khác nhau
                            không", không phải "cả kho có được dùng đều không". */}
                        {/* ── ICON THẮNG BIỂU TƯỢNG TỰ VẼ  (5/9/2026) ────────────────
                            Xem `IconVe.tsx` và `tai_icon.py`. Icon do hoạ sĩ vẽ, chọn theo
                            đúng chữ trong câu, ~400 từ thay vì 23 biểu tượng.
                            Đáy icon neo vào MẶT SÀN (`IconVe` dịch `-vh*k`, tức gốc toạ độ
                            nằm ở đáy hình), nên nó đứng trên sàn ở mọi icon — khác hẳn
                            tranh unDraw vốn mang mặt đất riêng và lơ lửng một lượng khác
                            nhau ở từng bức. */}
                        {co_icon(String((N as any)?.icon || "")) ? (
                          /* ── BÙ LẠI PHÉP NÂNG CỦA LỚP CHA  (5/9/2026) ──────────────────
                             Thẻ cha đã dịch lên `sz * DAY_HINH` để ĐÁY của `BieuTuong` chạm
                             sàn — `DAY_HINH` là phần hình người không chạm hết hộp của nó.
                             `IconVe` thì tự neo đáy (nó dịch `-vh*k`), nên đi qua thẻ cha là
                             bị nâng LẦN HAI: soi khung thấy icon tràn hẳn khỏi mép trên và
                             mặt sàn thì trống với một cái bóng không chủ.
                             Đúng họ lỗi §6 *chép hằng số sang hệ quy chiếu khác* — không báo
                             lỗi, chỉ làm hình sai. Cộng lại đúng lượng đã trừ. */
                          <g transform={`translate(0 ${sz * DAY_HINH})`}>
                            {/* ── ICON LÀ ĐẠO CỤ, KHÔNG PHẢI CHỦ THỂ  (5/9/2026) ─────────────────
                              `sz` là cỡ của CHỦ THỂ (nhân vật cao 45% khung). Cho icon mượn
                              nguyên cỡ ấy thì cái cây, cái phong bì choán nửa khung và đọc
                              ra một biểu tượng ứng dụng phóng to, không đọc ra một cảnh.
                              Ảnh mẫu: đạo cụ cao bằng khoảng nửa nhân vật và ĐỨNG CẠNH, vì
                              nó là thứ nhân vật nói tới chứ không phải nhân vật.
                              Đúng §6 — mượn một giá trị cho việc nó không sinh ra để làm. */}
                          <IconVe tu={String((N as any).icon)} s={sz * 0.50} p={p / 0.26}
                                    mau={mau} mauPhu={mauPhu} />
                          </g>
                        ) : (
                          <TuVe p={p / 0.26}>
                            <BieuTuong ten={btVe} s={sz} tu={(N as any)?.tu ?? 0}
                                       nv={(N as any)?.nv ?? 0} />
                          </TuVe>
                        )}
                      {/* ── ÁNH SÁNG PHỦ LÊN CHỦ THỂ  (4/9/2026) ─────────────────────────
                          Bốn ảnh anh gửi: ba người ngồi quanh lửa đều có **viền cam trên
                          nửa mặt phía lửa**. Đó là thứ tách "nhân vật đứng trong một cảnh
                          có ánh sáng" khỏi "hình dán đặt trên một nền sáng" — và nó là
                          khoảng cách rõ nhất còn lại giữa bản mình với ảnh tham khảo.
                          Không cắt hình theo đường bao nhân vật (SVG không làm rẻ được):
                          phủ một lớp ấm TOÀN KHUNG có tâm ở đúng nguồn sáng, vẽ SAU nhân
                          vật. Phần nhân vật gần nguồn ăn nhiều ánh sáng hơn phần xa — đúng
                          cách tranh phẳng giả lập ánh sáng, và nó cũng nối nhân vật vào
                          cùng một hệ sáng với nền thay vì để hai lớp sáng độc lập.
                          Độ đục thấp: đây là lớp NỐI, không phải lớp tô màu. */}
                      <defs>
                        <radialGradient id={`ls${Math.round(cx)}`}>
                          <stop offset="0%" stopColor="#FFD9A0" stopOpacity={0.30} />
                          <stop offset="60%" stopColor="#FFD9A0" stopOpacity={0.10} />
                          <stop offset="100%" stopColor="#FFD9A0" stopOpacity={0} />
                        </radialGradient>
                      </defs>
                      <ellipse cx={nguonSang(W, hat)} cy={sanY - sz * 0.42}
                               rx={W * 0.72} ry={H * 0.42}
                               fill={`url(#ls${Math.round(cx)})`} />
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
        return { nen: <NenPhong W={W} H={H} nen={nenTrang} mau={mau} hat={hat} anTroi dauAn={(N as any)?.dau_an ?? 0} />,
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
                           dauAnSo={(N as any)?.dau_an_so ?? 0}
                           bo={N.bo_so ?? (hat % 3)}
                           /* `kieu_so` do Python quyết — xem `GU_SO`. Engine chỉ đọc. */
                           kieu={N.kieu_so ?? 0} />
                   {N.dai_chu ? <DaiChu W={W} H={H * 0.80} chu={N.dai_chu} p={p} /> : null}
                 </g> };
      case "truc":
        return { nen: <NenPhong W={W} H={H} nen={nenTrang} mau={mau} hat={hat} dauAn={(N as any)?.dau_an ?? 0} />,
                 lop: <Truc W={W} H={H * 0.80} moc={N.moc || []} vt={N.vt ?? -1} mau={mau} p={p} /> };
      case "kinh_lup":
        return { nen: Nen,
                 /* Điểm soi mặc định 0,34/0,50 là một chỗ TUỲ TIỆN — soi khung THE RULES
                    thấy ống kính phóng to đúng một mảng giấy trắng, đọc ra cái đĩa rỗng. Ảnh
                    của bộ này luôn đặt chủ thể ở giữa khung (luật `SAN_NEN`: *open space in
                    the centre*), nên giữa khung là chỗ đúng để soi. */
                 lop: <KinhLup W={W} H={H * 0.80} x={W * (N.x ?? 0.50)} y={H * 0.80 * (N.y ?? 0.44)}
                               nhan={N.nhan || ""} mau={mau} p={p}
                               /* 4/9 — `N.bt`, KHÔNG PHẢI `btVe`. `btVe` xoá biểu tượng khi có
                                  ảnh, và đúng ở lớp CẢNH: ở đó biểu tượng là lớp ĐÈ lên ảnh,
                                  hai lớp cùng nói một điều. Trong ống kính thì ngược hẳn —
                                  biểu tượng LÀ nội dung được soi. Truyền `btVe` vào đây tức là
                                  bảo `KinhLup` rơi xuống nhánh phóng-lát-ảnh đúng lúc nó CÓ
                                  ảnh, mà chú thích của chính hàm ấy đã đo ba lần là ra đĩa
                                  trắng. Một câu luật đúng ở ngữ cảnh sinh ra nó, sai ở đây. */
                               bt={N.bt || ""}
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
        return { nen: <NenPhong W={W} H={H} nen={nenTrang} mau={mau} hat={hat} anTroi dauAn={(N as any)?.dau_an ?? 0} />,
                 lop: <Chart W={W} H={H * 0.80} cot={N.cot || []} don={N.don || ""}
                             mau={mau} mauPhu={mauPhu} p={p} nen={nenTrang} hat={hat}
                             /* `kieu_chart` do Python quyết — xem `GU_CHART`. */
                             kieu={N.kieu_chart ?? 0} /> };
      case "the_chu":
        return { nen: <NenPhong W={W} H={H} nen={nenTrang} mau={mau} hat={hat} dauAn={(N as any)?.dau_an ?? 0} />,
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
        {/* ══ VÂN GIẤY — LỚP TRÊN CÙNG CỦA NỀN  (5/9/2026) ═════════════════════════════
            Bản đầu em đặt vân giấy BÊN TRONG `NenPhong`. Sai: `NenPhong` chỉ chạy cho một
            phần nhịp — nhịp có `canh_ve` đi qua `CanhVe`, nhịp có ảnh đi qua `Img`. Soi lưới
            thì 3/4 khung không có vân giấy nào, và em suýt kết luận "feTurbulence không
            chạy" trong khi nó chạy đúng ở đúng một nhánh.
            Đây là họ lỗi §6 quen thuộc: đặt một thứ DÙNG CHUNG vào trong một nhánh.
            Nay nó phủ MỌI nhánh nền, và nằm dưới chủ thể + chữ nên không làm mờ chúng. */
        }
        <AbsoluteFill style={{ mixBlendMode: "multiply", opacity: 0.22 }}>
          <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
            <defs>
              <filter id="giay0" x="0" y="0" width="100%" height="100%">
                {/* 0,85 cho hạt mịn như sợi giấy. Dưới 0,3 ra vệt loang như mây — thử rồi. */}
                <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4"
                              seed={Math.abs(hat) % 100} result="n" />
                <feColorMatrix in="n" type="saturate" values="0" />
              </filter>
            </defs>
            <rect x={0} y={0} width={W} height={H} filter="url(#giay0)" />
          </svg>
        </AbsoluteFill>
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
                  /* ── NHỊP KHÔNG CÓ ẢNH CŨNG PHẢI KHAI ĐỘ SÁNG  (4/9/2026) ──────────
                     Nhánh cũ chỉ biết hai loại nền: ảnh CF (`sangDay` đo lúc sinh) và cảnh
                     vẽ code (`sangDayCanh`). Nhịp `dem` · `nhom` · `chart` dùng `NenPhong`
                     thì rơi vào `-1` = "không biết", và `PhuDe` mặc định mực TRẮNG.
                     Đo trên bản dài: đúng hai nhịp `dem` ấy có nền 140 và 142 — mực trắng
                     cho 1,4:1 trong khi mực tối cho 5,4:1. Không biết thì đoán, và đoán sai.
                     `NenPhong` pha sàn từ cùng `nen`+`mau`, nên `sangDayCanh` với nơi chốn
                     rỗng trả đúng độ sáng đáy của nó. */
                  sangNen={N.canh_ve
                    ? sangDayCanh(N.canh_ve, nenTrang, mau, mauPhu)
                    : N.nenAnh
                      ? Number((N as any)?.sangDay ?? -1)
                      : sangDayCanh("", nenTrang, mau, mauPhu)} />}

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
