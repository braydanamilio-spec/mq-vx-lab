import React from "react";
import { AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { PHONG } from "../Phong";
import { Lop, SoDong, ChartDong, SoKe, DoiChieu, NhanTren } from "./LopSo";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   PHIM GIẢI THÍCH v10 — MỘT NHỊP = MỘT KHUNG PHIM  (6/9/2026)

   Anh: *"đổi hoàn toàn lại template và nền videos"*, *"mỗi chuyển cảnh hook 1.5 tới 2.5s,
   ko kéo dài quá lâu 1 footage gây nhàm chán"*, *"100% các cảnh đều generate từ gemini +
   cloudflare"*.

   ── BỘ CŨ SAI Ở CẤU TRÚC, KHÔNG SAI Ở THẨM MỸ ────────────────────────────────────────────
   `KichGiaiThich.tsx` có TÁM khuôn hình và bảy trong tám khuôn ấy TỰ VẼ LẤY nội dung khung —
   `ChiaDoi`, `Truc`, `KinhLup`, `Dem`, `TheChu`, `SoLieu`, `Chart` đều vẽ nền của chính chúng
   bằng SVG. Nên trên một tập thật, đo được: 6/16 nhịp có ảnh AI, 10 nhịp là đồ hoạ code. Đó
   là gốc của cả hai lời chê — "xấu" (đồ hoạ code không bao giờ bằng một khung phim) và "lặp
   đi lặp lại cùng 1 motip" (mười nhịp ấy rút từ đúng tám khuôn).

   Bộ này chỉ có MỘT khuôn hình: **một tấm ảnh AI tràn khung**. Số liệu, biểu đồ và nhãn trở
   thành LỚP PHỦ trên tấm ảnh ấy, không còn là khung hình thay thế nó. Hệ quả trực tiếp:
     · 100% nhịp có ảnh AI — không còn nhánh nào vẽ cảnh bằng code
     · không còn "motip" để mà lặp: mỗi nhịp là một cảnh phim khác nhau
     · lớp dữ liệu vẫn giữ nguyên sức mạnh của nó (đếm lên, mọc cột) mà không chiếm cả khung

   ── NHỊP 1,5–2,5 GIÂY LÀ VIỆC CỦA KHÂU VIẾT, KHÔNG PHẢI KHÂU DỰNG ────────────────────────
   Engine không cắt được cái mà kịch bản không chia. `phim.py` chia nhịp theo mốc TỪ của giọng
   đọc và ép trần 2,6 giây; cổng `kiem_phim` đo lại trên danh sách nhịp TRƯỚC khi render.

   ── VÌ SAO CÓ KEN BURNS, VÀ VÌ SAO NÓ RẤT NHẸ ────────────────────────────────────────────
   Ảnh tĩnh đứng yên 2 giây đọc ra là một slideshow, kể cả khi tấm ảnh đẹp. 4–6% dịch chuyển
   trong 2 giây là đủ để mắt đọc ra "máy quay", và ít tới mức không ai nhận ra có hiệu ứng —
   đúng tiêu chí của một lớp hoàn thiện (§12.12). Hướng dịch lấy từ hạt của nhịp nên hai nhịp
   liền nhau không bao giờ cùng hướng.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));

export type NhipPhim = {
  s: number;
  e: number;
  anh?: string;
  lop?: Lop;
  dinh?: boolean;
  moi?: boolean;
};

export type PropsPhim = {
  ma?: string;
  tieuDe?: string;
  handle?: string;
  chinh?: string;
  phu?: string;
  nen?: string;
  phong?: string;
  doc?: boolean;
  dai?: number;
  hat?: number;
  voMp3?: string;
  nhac?: string;
  nhacVol?: number;
  tu?: { t: number; d: number; w: string }[];
  nhip?: NhipPhim[];
};

export const calcPhim = async ({ props }: { props: PropsPhim }) => ({
  durationInFrames: Math.max(60, Math.round((props.dai || 30) * 30)),
  fps: 30,
});

/* Sáu kiểu máy. Biên độ giữ ở 5% — xem chú thích đầu tệp. Kiểu chọn theo hạt nhịp, và hàm
   `_kieu` cộng thêm chỉ số nhịp để hai nhịp liền nhau lệch pha, chứ không băm lại từ đầu:
   băm lại có thể ra cùng số hai lần liên tiếp và mắt đọc ra ngay là "không đổi". */
const KIEU = 6;
const _kieu = (hat: number, i: number) => (Math.abs(hat) + i * 5) % KIEU;

/* ── PHÓNG TỪ MÉP TRÊN, KHÔNG PHÓNG TỪ TÂM  (6/9/2026) ─────────────────────────────────────
   Anh gửi ba khung, cả ba cùng một lỗi: nhân vật BỊ CẮT MẤT ĐẦU.
   Đo cơ chế: ảnh 768×1344 (tỉ lệ 0,5714) vào khung 1080×1920 (0,5625) — `cover` khớp chiều
   cao và chỉ cắt 1,6% hai MÉP, không cắt trên dưới. Thủ phạm là Ken Burns: `scale 1.05` phóng
   TỪ TÂM nên ăn 2,8% mỗi cạnh, cộng kiểu trôi DỌC ±2,75% nữa là **đỉnh khung mất tới 5,5%**.
   Trên khung 1920 đó là 106 pixel — vừa đúng phần đầu của một nhân vật đứng cao trong khung.

   Chữa bằng GỐC PHÓNG, không bằng cách bỏ hiệu ứng: đặt `transformOrigin` ở 8% từ trên xuống
   thì phần bị cắt dồn hết xuống ĐÁY — nơi đã có dải tối phủ phụ đề, tức chỗ mất đi không ai
   thấy. Và biên độ hạ 0,055 -> 0,038: vẫn đủ để mắt đọc ra "máy quay", vì ngưỡng nhận ra
   chuyển động thấp hơn nhiều so với ngưỡng nhận ra méo bố cục.
   Trôi dọc cũng chỉ còn đi XUỐNG (lộ thêm phần sàn), không bao giờ đi lên. */
const GOC_PHONG = "50% 8%";

const may = (k: number, q: number) => {
  const e = q;
  const B = 0.038;
  switch (k) {
    case 0: return { s: 1.0 + B * e, x: 0, y: 0 };
    case 1: return { s: 1.0 + B * (1 - e), x: 0, y: 0 };
    case 2: return { s: 1.0 + B, x: (-B / 2 + B * e) * 100, y: 0 };
    case 3: return { s: 1.0 + B, x: (B / 2 - B * e) * 100, y: 0 };
    case 4: return { s: 1.0 + B, x: 0, y: -B * e * 100 };
    default: return { s: 1.0 + B, x: 0, y: -B * (1 - e) * 100 };
  }
};

/* ── PHỤ ĐỀ KARAOKE ────────────────────────────────────────────────────────────────────────
   Chữ trắng, bóng mềm rộng, KHÔNG hộp đen bo góc — hộp đen là mặc định của trình tạo phụ đề
   điện thoại và người xem đọc ra "nghiệp dư" trong nửa giây (§12.12). Chỗ dựa để chữ đọc được
   là dải tối chuyển dần ở chân khung, phủ sẵn dưới lớp này.
   Từ đang đọc tô VÀNG — quy ước karaoke ai cũng nhận ra, và nó là thứ giữ mắt ở lại dòng chữ
   thay vì lướt xuống. */
const PhuDe: React.FC<{
  tu: { t: number; d: number; w: string }[]; t: number; W: number; H: number; chu: string;
}> = ({ tu, t, W, H, chu }) => {
  if (!tu || !tu.length) return null;
  let i = -1;
  for (let k = 0; k < tu.length; k++) if (t >= tu[k].t - 0.05) i = k;
  if (i < 0) return null;
  const het = (w: string) => /[.!?]$/.test(w);
  let a = 0;
  for (let k = i - 1; k >= 0; k--) if (het(tu[k].w)) { a = k + 1; break; }
  let b = tu.length;
  for (let k = i; k < tu.length; k++) if (het(tu[k].w)) { b = k + 1; break; }
  const cua = tu.slice(a, Math.min(b, a + 13));
  if (!cua.length) return null;
  const n = cua.reduce((s, x) => s + x.w.length + 1, 0);
  const u = H * (H >= W ? 0.5625 : 0.70);
  const co = u * (n > 46 ? 0.046 : n > 30 ? 0.054 : 0.062);
  return (
    <div style={{
      position: "absolute", left: W * 0.07, right: W * 0.07, bottom: H * 0.085,
      display: "flex", flexWrap: "wrap", justifyContent: "center",
      columnGap: co * 0.30, rowGap: co * 0.16,
    }}>
      {cua.map((x, k) => {
        const dang = t >= x.t - 0.05 && t < x.t + Math.max(x.d, 0.12) + 0.05;
        return (
          <span key={k} style={{
            fontFamily: chu, fontWeight: 800, fontSize: co, lineHeight: 1.18,
            color: dang ? "#FFD447" : "#FFFFFF",
            textShadow: "0 3px 22px rgba(0,0,0,0.92), 0 1px 4px rgba(0,0,0,0.85)",
          }}>{x.w}</span>
        );
      })}
    </div>
  );
};

export const Phim: React.FC<PropsPhim> = ({
  ma = "", tieuDe = "", handle = "", chinh = "#E0642B", phu = "#4FB3C7", nen = "#121820",
  phong = "poppins", doc = true, dai = 30, hat = 7, voMp3 = "", nhac = "", nhacVol = 0.15,
  tu = [], nhip = [],
}) => {
  const frame = useCurrentFrame();
  const { width: W, height: H, fps } = useVideoConfig();
  const t = frame / fps;
  const chu = `${PHONG[phong] || PHONG.poppins}, Arial Black, sans-serif`;

  let j = 0;
  for (let k = 0; k < nhip.length; k++) if (t >= nhip[k].s) j = k;
  const N = nhip[j] || ({ s: 0, e: dai } as NhipPhim);
  const dn = Math.max(0.2, N.e - N.s);
  const p = kep((t - N.s) / dn);

  /* CHUYỂN CẢNH: 5 khung hoà tan giữa hai nhịp. Ngắn hơn 5 thì đọc ra là lỗi nháy; dài hơn 10
     thì ở nhịp 1,8 giây nó ăn mất một phần chín thời lượng của chính cảnh mới. Nhịp `moi` (mở
     một chương) hoà 12 khung để tai và mắt cùng biết là sang phần khác. */
  const hoa = (N.moi ? 12 : 5) / fps;
  const vao = kep((t - N.s) / hoa);
  const truoc = j > 0 ? nhip[j - 1] : null;

  const lopAnh = (x: NhipPhim, i: number, mo: number) => {
    if (!x.anh) return null;
    const q = kep((t - x.s) / Math.max(0.2, x.e - x.s));
    const m = may(_kieu(hat, i), q);
    return (
      <AbsoluteFill key={i} style={{ opacity: mo }}>
        <Img src={staticFile(x.anh)} style={{
          width: "100%", height: "100%", objectFit: "cover",
          transformOrigin: GOC_PHONG,
          transform: `scale(${m.s}) translate(${m.x * 0.01}%, ${m.y * 0.01}%)`,
        }} />
      </AbsoluteFill>
    );
  };

  const lop = N.lop;
  return (
    <AbsoluteFill style={{ background: nen, overflow: "hidden" }}>
      {truoc && vao < 1 ? lopAnh(truoc, j - 1, 1) : null}
      {lopAnh(N, j, vao)}

      {/* Dải tối chân khung — chỗ dựa của phụ đề. Đây là thứ THAY THẾ luật "chừa chỗ trống"
          của bộ cũ: chừa chỗ ở lớp phủ thì ảnh được vẽ đầy đủ, chừa chỗ ở prompt thì ảnh
          bị rút ruột. Cùng một mục tiêu, hai cái giá khác hẳn nhau. */}
      <AbsoluteFill style={{
        pointerEvents: "none",
        background: `linear-gradient(180deg, rgba(0,0,0,0) 62%, ${nen}B0 84%, ${nen}E8 100%)`,
      }} />
      {/* DẢI TỐI ĐỈNH KHUNG. Nhịp có lớp dữ liệu thì dải này dài và đậm hơn — con số của bộ
          này cao bằng 20% bề ngang khung, và trên một cảnh phim sáng thì nó không thể đọc
          được nếu chỉ dựa vào bóng chữ.
          Vì sao KHÔNG bảo mô hình chừa chỗ trống ở đỉnh: đó đúng là câu đã rút ruột mọi khung
          của bộ cũ (§ đầu `phim_gu.py`). Chừa chỗ ở lớp phủ thì ảnh vẫn được vẽ đầy đủ; chừa
          chỗ ở prompt thì mất luôn phần ảnh ấy. */}
      <AbsoluteFill style={{
        pointerEvents: "none",
        background: N.lop && N.lop.k !== "nhan"
          ? `linear-gradient(180deg, ${nen}D8 0%, ${nen}A8 26%, rgba(0,0,0,0) 52%)`
          : "linear-gradient(180deg, rgba(0,0,0,0.42) 0%, rgba(0,0,0,0) 18%)",
      }} />

      {lop && lop.k === "so" ? (
        <SoDong so={lop.so} don={lop.don} nhan={lop.nhan} p={p} W={W} H={H}
                mau={chinh} chu={chu} />
      ) : null}
      {lop && lop.k === "chart" ? (
        <ChartDong cot={lop.cot} don={lop.don} nhan={lop.nhan} p={p} W={W} H={H}
                   mau={chinh} phu={phu} chu={chu} />
      ) : null}
      {lop && lop.k === "ss" ? (
        <SoKe trai={lop.trai} phai={lop.phai} don={lop.don} p={p} W={W} H={H}
              mau={chinh} phu={phu} chu={chu} />
      ) : null}
      {lop && lop.k === "doi" ? (
        <DoiChieu trai={lop.trai} phai={lop.phai} p={p} W={W} H={H}
                  mau={chinh} phu={phu} chu={chu} />
      ) : null}
      {lop && lop.k === "nhan" ? (
        <NhanTren chu_={lop.chu} p={p} W={W} H={H} mau={chinh} chu={chu} />
      ) : null}

      <PhuDe tu={tu} t={t} W={W} H={H} chu={chu} />

      {/* Watermark mờ ở góc, không phải dải tên kênh dưới mọi khung (§12.12). */}
      {handle ? (
        <div style={{
          position: "absolute", right: W * 0.030, bottom: H * 0.028,
          fontFamily: chu, fontWeight: 700, fontSize: H * (H >= W ? 0.5625 : 0.70) * 0.021,
          color: "#FFFFFF", opacity: 0.34, letterSpacing: W * 0.002,
        }}>{handle}</div>
      ) : null}

      {/* LỚP HOÀN THIỆN — phủ lên CẢ ảnh AI lẫn đồ hoạ code, nên hai thứ khác bản chất mới
          chung một bề mặt. Cả ba đều rất nhẹ: thấy được là hỏng. */}
      <AbsoluteFill style={{
        pointerEvents: "none", opacity: 0.09, mixBlendMode: "soft-light",
        background: "linear-gradient(180deg,#FFE0B2 0%,#FFC98C 60%,#FFBE7A 100%)",
      }} />
      <AbsoluteFill style={{
        pointerEvents: "none",
        background: "radial-gradient(120% 80% at 50% 46%, #00000000 62%, #00000026 100%)",
      }} />
      <AbsoluteFill style={{
        pointerEvents: "none", opacity: 0.045, mixBlendMode: "overlay",
        backgroundImage:
          "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'>"
          + "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/></filter>"
          + "<rect width='140' height='140' filter='url(%23n)'/></svg>\")",
        backgroundSize: `${Math.round(W * 0.13)}px ${Math.round(W * 0.13)}px`,
      }} />

      {voMp3 ? <Audio src={staticFile(voMp3)} /> : null}
      {nhac ? <Audio src={staticFile(nhac)} volume={nhacVol} loop /> : null}
    </AbsoluteFill>
  );
};
