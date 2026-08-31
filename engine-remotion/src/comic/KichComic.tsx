import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { DienVienHai } from "../v4/DienVienHai";
import { KIEU_MAU, visemeTai, Kieu, TenCamXuc, TenCuChi, Tu } from "../v2/DienVien";
import type { Luot } from "../v4/KichHai";
import { NenPanel, NenGan, DaoCu, doDaoCu } from "./NenComic";
import { noiCuaTap, Noi, SAN } from "./NoiChon";

// ══════════════════════════════════════════════════════════════════════════════════════════
// KỊCH COMIC — 31/8/2026
// ------------------------------------------------------------------------------------------
// Anh xem ba khung của bản hài cũ rồi bảo xoá đi làm lại. Ba khung ấy hỏng vì MỘT nguyên nhân
// kiến trúc, không phải vì thiếu tinh chỉnh:
//
//   bản cũ DÁN NGƯỜI VECTOR LÊN ẢNH AI.
//
// Từ đó chảy ra cả bốn lỗi anh nhìn thấy. Nền photoreal không hoà được với người vẽ phẳng. Ảnh
// sinh bằng prompt rời nên không đọc nội dung thoại — thoại nói về đường dốc mà nền là phòng
// khách với cái giỏ giặt chắn ngang bụng. Khung ảnh không phải khung hình, nên 60% diện tích là
// tường trống. Và một khung chỉ đủ chỗ cho một người ở cỡ cận, nên người thứ hai biến mất —
// hài đối đáp mất nửa còn lại của trò đùa.
//
// Nền vẽ bằng CODE chữa cả bốn cùng lúc, vì nó cùng cây bút với nhân vật và vì tôi biết sàn
// nằm ở đâu. Xem `NenComic.tsx`.
//
// ── MỘT LƯỢT = MỘT CẢNH = MỘT KHUNG (đổi lần hai, cùng ngày) ────────────────────────────
// Bản comic đầu xếp ba bốn ô lên một trang rồi điền dần. Anh xem xong: *"hơi giống truyện quá,
// a muốn nó hiện ra từ từ chỉ 1 cảnh 1 xong chuyển cảnh để giống videos hơn"*.
//
// Đúng — và đúng theo cách đo được: ba ô cùng hiện nghĩa là ở mọi thời điểm có hai ô không nói
// gì mà vẫn chiếm hai phần ba màn hình, nên khuôn mặt đang thoại chỉ còn một phần ba khung để
// diễn. Với hài thì đó là chỗ đắt nhất bị chia ba. Nay mỗi lượt chiếm trọn khung.
//
// Chất truyện tranh không mất theo: nó nằm ở viền mực, bong bóng có đuôi, halftone, chữ nổ —
// chỉ bỏ đúng cái xếp-nhiều-ô-một-trang.
// ══════════════════════════════════════════════════════════════════════════════════════════

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const trn = (a: number, b: number, t: number) => a + (b - a) * kep(t);
const muot = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const bat = (t: number) => 1 - Math.pow(1 - kep(t), 3);

/** Băm ổn định — cùng tên kênh thì cùng nhịp dựng, khác kênh thì khác. */
const bam = (s: string) => {
  let a = 7;
  for (let i = 0; i < s.length; i++) a = (a * 31 + s.charCodeAt(i)) % 100003;
  return a;
};

// ── HÌNH HỌC NHÂN VẬT ─────────────────────────────────────────────────────────────────────
// Lấy từ CHÍNH `DienVienHai.tsx` (`Y_HONG` = −168, `Y_VAI` = −262, `R_DAU_GOC` = 58) và đo lại
// trên khung đã render. Bản đầu tôi chép 545 / −437 / 119 từ `KichHai.tsx` — ở đó chúng nằm
// trong hệ đã nhân zoom, nên mang sang đây thì mọi phép tính vị trí lệch mà không lệch đều: có
// khung thừa chỗ, có khung mất đầu. Bảy vòng sửa bố cục không vòng nào tới gốc, vì gốc là đây.
const CAO_NGUOI = 460;        // đỉnh tóc -> gót
const Y_HONG = 168;           // hông cách gót (số dương)
const Y_NGUC = 230;           // ngực dưới cách gót
const NUA_RONG = 100;         // nửa bề ngang khi tay ghim ngực

const LE = 44;                // lề mực quanh khung
const NET = 7;                // độ dày viền mực MẶC ĐỊNH (mỗi kênh ghi đè, xem `netMuc`)
const CAO_TEN = 62;           // dải tên kênh dưới đáy

type ONhoPanel = { i: number; x: number; y: number; w: number; h: number };

// ── BONG BÓNG THOẠI ───────────────────────────────────────────────────────────────────────
/**
 * Cỡ chữ lấy giá trị NHỎ HƠN giữa hai ràng buộc: vừa hộp, và vừa số chữ phải chứa.
 * Một tuần trước tôi viết `fontSize = cạnh × 0.19` cho ô vuông trong biểu đồ — công thức chỉ
 * hỏi ô to bao nhiêu, không hỏi phải chứa bao nhiêu chữ — và chuỗi `365.1K km` tràn ra ngoài ô.
 * Ở đây chữ dài gấp mười lần (PIPELINE_RULES mục 8.1).
 */
const coChu = (chu: string, W: number, H: number, toiDa: number) => {
  const n = Math.max(8, chu.length);
  const theoDienTich = Math.sqrt((W * H) / 0.682 / n);
  return Math.max(17, Math.min(toiDa, theoDienTich));
};

const BongThoai: React.FC<{
  chu: string; tu: Tu[]; giay: number; W: number; H: number;
  ben: "trai" | "phai"; duoi?: "trai" | "phai"; hep?: boolean;
  p: number; mau: string; la: boolean; s0?: number; e0?: number;
  net?: number; boGoc?: number; hook?: number; duoiKhung?: boolean;
}> = ({ chu, tu, giay, W, H, ben, duoi, hep, p, mau, la, s0 = 0, e0 = 0,
        net = NET, boGoc = 26, hook = 0, duoiKhung = false }) => {
  // 31/8 — CHỮ SÁNG PHẢI ĐI THEO MỐC TIẾNG THẬT, KHÔNG THEO VỊ TRÍ TRONG CÂU.
  // Anh: *"voice nhớ khớp với sub 100%"*. Bản trước lấy từ thứ i của câu rồi tra vào `tu` theo
  // tỉ lệ `i / số_từ` — mà `tu` là mốc từ của CẢ VIDEO, nên từ thứ hai của lượt bốn tra ra mốc
  // của một từ nào đó ở lượt một, và chữ sáng chạy loạn so với tiếng. Nay lọc đúng những từ nằm
  // trong khoảng [s, e] của lượt này rồi khớp theo thứ tự: mỗi từ một mốc đo từ WAV.
  const tuLuot = React.useMemo(
    () => (tu || []).filter((x) => x.t >= s0 - 0.06 && x.t < e0 + 0.06),
    [tu, s0, e0],
  );
  const _duoi = duoi || ben;
  const rong = hep ? Math.min(W * 0.46, W - 40) : Math.min(W * 0.86, W - 56);
  const caoToiDa = hep ? H * 0.62 : H * 0.3;
  // HOOK: bong bóng của lượt MỞ MÀN bắt đầu to gấp rưỡi rồi co về cỡ thật trong một giây.
  // Anh chấm hạng mục hook 55/100 và đúng: giây 0 của bản trước là một câu setup cỡ thường,
  // không có lý do gì để người lướt dừng lại. Phóng to chính câu đầu là cách hook KHÔNG phải
  // bịa thêm chữ — chữ vẫn là lời thoại thật, vẫn khớp tiếng, chỉ chiếm chỗ như một tấm bìa.
  const phongHook = hook > 0 ? trn(1.5, 1, muot(kep(hook))) : 1;
  const fs = coChu(chu, rong - 36, caoToiDa - 30, la ? 62 : 52) * phongHook;
  const sc = p < 0.55 ? trn(0.72, 1.06, muot(p / 0.55)) : trn(1.06, 1, muot((p - 0.55) / 0.45));
  const nghieng = ben === "trai" ? -1.2 : 1.2;

  return (
    <div style={{
      position: "absolute", [duoiKhung ? "bottom" : "top"]: 18,
      [ben === "trai" ? "left" : "right"]: 24,
      maxWidth: rong, transform: `scale(${sc}) rotate(${nghieng}deg)`,
      transformOrigin: `${ben === "trai" ? "left" : "right"} ${duoiKhung ? "bottom" : "top"}`,
      zIndex: 6,
    } as React.CSSProperties}>
      <div style={{
        background: "#FFFFFF", border: `${Math.max(4, NET - 2)}px solid #14110F`,
        borderRadius: la ? 14 : 26, padding: la ? "12px 18px" : "14px 20px",
        boxShadow: "6px 7px 0 #14110F",
        fontFamily: "Poppins, Arial Black, sans-serif", fontWeight: 800,
        fontSize: fs, lineHeight: 1.18, color: "#14110F",
        letterSpacing: la ? 0.6 : 0, textTransform: la ? "uppercase" : "none",
      }}>
        {chu.split(" ").map((w, i, arr) => {
          const t0 = tuLuot[i] || null;
          const dang = t0 ? giay >= t0.t && giay < t0.t + t0.d : false;
          return <span key={i} style={{ color: dang ? mau : "#14110F" }}>{w}{i < arr.length - 1 ? " " : ""}</span>;
        })}
      </div>
      {/* Đuôi bong bóng chỉ về người nói — thứ thay cho nhãn tên. `duoi` tách khỏi `ben` để bong
          bóng nằm nửa này mà đuôi chỉ sang nửa kia (bố cục cận cảnh lệch bên). */}
      <svg width="50" height="42" viewBox="0 0 46 40" style={{
        position: "absolute", bottom: -34, [_duoi === "trai" ? "left" : "right"]: 28,
        transform: _duoi === "trai" ? "none" : "scaleX(-1)",
      } as React.CSSProperties}>
        <path d="M4 2 L44 2 L14 36 Z" fill="#FFFFFF" stroke="#14110F" strokeWidth={5}
              strokeLinejoin="round" />
        <rect x="2" y="0" width="44" height="5" fill="#FFFFFF" />
      </svg>
    </div>
  );
};

// ── HIỆU ỨNG TRUYỆN TRANH ─────────────────────────────────────────────────────────────────
const VachToc: React.FC<{ w: number; h: number; p: number; mau: string }> = ({ w, h, p, mau }) => {
  const n = 26, cx = w / 2, cy = h / 2, R = Math.hypot(w, h);
  return (
    <svg width={w} height={h} style={{ position: "absolute", inset: 0, zIndex: 2, opacity: 0.42 * (1 - p) }}>
      {Array.from({ length: n }, (_, i) => {
        const g = (i / n) * Math.PI * 2 + p * 0.4;
        const r0 = R * (0.30 + 0.10 * ((i * 7) % 5) / 5);
        return <line key={i} x1={cx + Math.cos(g) * r0} y1={cy + Math.sin(g) * r0}
                     x2={cx + Math.cos(g) * R} y2={cy + Math.sin(g) * R}
                     stroke={mau} strokeWidth={2 + ((i * 3) % 4)} strokeLinecap="round" />;
      })}
    </svg>
  );
};

const ChuNo: React.FC<{ chu: string; w: number; h: number; p: number; mau: string; tren?: boolean }> =
({ chu, w, h, p, mau, tren }) => {
  const sc = p < 0.4 ? trn(0.3, 1.14, bat(p / 0.4)) : trn(1.14, 1, muot((p - 0.4) / 0.6));
  return (
    <div style={{
      // Chữ nổ phải ở phía ĐỐI DIỆN bong bóng. Kênh dùng lối bong bóng-dưới thì góc dưới-trái
      // không còn trống nữa — khung GYM LIES vừa cho ra "OOF!" đè thẳng lên câu chốt. Một chỗ
      // "chắc chắn trống" chỉ chắc chắn trong bố cục đã sinh ra nó.
      position: "absolute", left: "6%",
      [tren ? "top" : "bottom"]: h * 0.05,
      transform: `scale(${sc}) rotate(-7deg)`,
      transformOrigin: `left ${tren ? "top" : "bottom"}`,
      fontFamily: "Poppins, Arial Black, sans-serif", fontWeight: 900,
      fontSize: Math.min(w * 0.17, 96), color: mau, WebkitTextStroke: "10px #14110F",
      paintOrder: "stroke fill", letterSpacing: 1, zIndex: 7, whiteSpace: "nowrap",
    } as React.CSSProperties}>{chu}</div>
  );
};

// ── MỘT CẢNH ──────────────────────────────────────────────────────────────────────────────
/** Bóng của một người: lớp tiếp đất + lớp đổ xiên theo hướng sáng của ảnh nền. */
const BongNguoi: React.FC<{ x: number; y: number; k: number; cao: number; huong: number; manh: number }> =
({ x, y, k, cao, huong, manh }) => {
  const rx = 92 * k * cao;
  const ry = 13 * k * cao;
  // CHỖ CHẠM SÀN, đo trong ĐÚNG hệ toạ độ của `DienVienHai`: ở đó chân chạm y = 0 và người mọc
  // lên theo chiều âm, còn ĐẾ giày nằm ở y = +11 (`p[1] + 15` với `p[1] = -4`). Bóng cũ đặt ở
  // `y - 3` nên rơi ngang THÂN giày — phóng to là thấy ngay: khối bóng nổi phía sau giày thay
  // vì nằm dưới đế. Và `+11` KHÔNG nhân `cao`: toạ độ bàn chân trong hàm vẽ không nhân `cao`
  // (chỉ các đốt thân trên mới nhân), nên nhân vào đây là chép hằng sang hệ quy chiếu khác —
  // đúng họ lỗi đã trả giá ở `545 / −437 / 119`.
  const yCham = y + 11 * k;
  const dai = 1 + manh * 1.15;                                    // nắng gắt thì bóng dài
  const lech = huong === 0 ? 0 : -huong * rx * (0.28 + manh * 0.5);
  return (
    <>
      {huong !== 0 || manh > 0.1 ? (
        <ellipse cx={x + lech} cy={yCham} rx={rx * dai} ry={ry * 0.92}
                 fill="#14110F" opacity={0.10 + manh * 0.07}
                 transform={`rotate(${-huong * manh * 7} ${x} ${yCham})`} />
      ) : null}
      {/* Lớp tiếp đất: hẹp và đậm hơn hẳn bóng cũ — 0x22 (≈13%) quá nhạt để neo một hình vẽ
          phẳng xuống sàn của ảnh 3D có tương phản thật. */}
      <ellipse cx={x} cy={yCham} rx={rx * 0.62} ry={ry * 0.66} fill="#14110F" opacity={0.30} />
    </>
  );
};

const Panel: React.FC<{
  L: Luot; o: ONhoPanel; A: Kieu; B: Kieu; tu: Tu[]; giay: number;
  kenh: string; mau: string; mauPhu: string; hat: number; thuTu: number;
  dangNoi: boolean; hai?: boolean; noi: Noi; anhNen?: string;
  netMuc?: number; cham?: number; boGoc?: number; tiLe?: number; hook?: number;
  bongDuoi?: boolean; boKhung?: number; chuNo?: string;
  sang?: { huong: number; manh: number };
}> = ({ L, o, A, B, tu, giay, kenh, mau, mauPhu, hat, thuTu, dangNoi, hai, noi, anhNen,
        netMuc = NET, cham = 9, boGoc = 26, tiLe = 0.60, hook = 0,
        bongDuoi = false, boKhung = 0, chuNo = "BOOM!", sang }) => {
  const { w, h } = o;
  const p = kep((giay - L.s) / 0.38);
  const trong = giay - L.s;

  // Cỡ cảnh do NGƯỜI DỰNG quyết (`hai`), không do kịch bản và cũng không còn do panel tự đo —
  // mỗi lượt chiếm trọn khung nên không có chuyện ô bé không chứa nổi hai người.
  const doiNguoi = hai !== undefined ? hai : (w >= 620 && h >= 540);
  const khungDoc = h > w * 1.1;
  const noiA = L.ai === 0;

  // 31/8, sửa lại — CHÊNH LỆCH CHIỀU CAO LÀ CHỦ Ý, PHẢI GIỮ NGUYÊN.
  // Sáng nay tôi thấy hai người chênh nhau nhiều quá nên chia tỉ lệ cho căn bậc hai của `cao`
  // để kéo họ gần bằng nhau. Sai hướng: anh nói ngay sau đó *"con đứng với mẹ thì con phải
  // thấp hơn mẹ, vợ đứng với chồng thì vợ thường thấp hơn chồng — nhớ logic nha e"*. Chênh
  // lệch chính là thông tin: nhìn một giây là ra quan hệ, trước cả câu thoại đầu tiên.
  //
  // Cái cần sửa không phải chiều cao mà là MỨC CẮT. Cả hai đứng chung một mặt đất và chung
  // một tỉ lệ; chỉ cần chọn tỉ lệ theo người CAO NHẤT (để đỉnh đầu không chui vào vùng bong
  // bóng) và chọn mức cắt theo người THẤP NHẤT (để người thấp không bị cắt mất mặt). Hai mốc
  // khác nhau cho hai mục đích khác nhau — trước đây tôi dùng chung một mốc nên phải chọn:
  // hoặc người cao mất đầu, hoặc người thấp mất mặt.
  const caoA = A.cao ?? 1, caoB = B.cao ?? 1;
  const caoMax = Math.max(caoA, caoB), caoMin = Math.min(caoA, caoB);


  // Chỗ chừa cho bong bóng theo ĐỘ DÀI CÂU. Câu chốt hai dòng cao gấp rưỡi câu một dòng, nên
  // một con số cố định vừa đủ cho câu ngắn vẫn đè đầu ở câu dài — cùng họ lỗi với cỡ chữ ở 8.1.
  const dongUoc = Math.max(1, Math.ceil(L.nar.length / 27));
  const chuaTren = Math.min(0.44, 0.20 + 0.08 * dongUoc);
  // Kênh dùng lối bong bóng-dưới thì chỗ chừa nằm ở đáy, nên nhân vật nhích lên và chỉ cần
  // chừa một dải mỏng phía trên cho thoáng.
  const chua = bongDuoi ? 0.06 : chuaTren;

  // KHUNG DỌC THÌ VẼ CẢ NGƯỜI. Cắt ngang hông là bố cục của ô NGANG — nó dồn hết chiều cao ít
  // ỏi cho phần thân trên. Trong khung dọc 1080×1786, cắt hông để lại hơn nghìn pixel trống
  // phía trên. Khung dọc có chỗ cho cả người: người đứng nửa dưới, bong bóng trên, nền lấp giữa.
  const CAO_TREN = khungDoc ? CAO_NGUOI : CAO_NGUOI - Y_HONG;
  const kRong = khungDoc
    ? Math.min((h * (bongDuoi ? tiLe * 0.82 : tiLe)) / (CAO_NGUOI * caoMax), (w / 2 - 24) / (NUA_RONG * 2.15))
    // Khung ngang: đỉnh đầu người cao ở mức chừa bong bóng, hông người thấp ở đáy khung.
    // Hai điều kiện ấy giải ra đúng một tỉ lệ.
    : Math.min((h * (1 - chuaTren)) / (CAO_NGUOI * caoMax - Y_HONG * caoMin),
               (w / 2 - 30) / (NUA_RONG * 2.15));

  const canRong = !doiNguoi && w > h * 1.15;      // ô NGANG chứa một người -> lệch hẳn một mép
  const _chuaCan = canRong ? 0.08 : chuaTren;
  const kCan = Math.min((w * (khungDoc ? 0.74 : 0.46)) / (NUA_RONG * 2.1),
                        (h * (1 - _chuaCan)) / ((CAO_NGUOI - Y_NGUC) * (noiA ? caoA : caoB)));
  const k = doiNguoi ? kRong : kCan;
  const yChan = doiNguoi
    ? (khungDoc ? h * (bongDuoi ? SAN - 0.21 : SAN) : h + Y_HONG * caoMin * k)
    : h * (khungDoc ? 0.30 : _chuaCan) + CAO_NGUOI * (noiA ? caoA : caoB) * kCan;

  // Người NGHE không được đứng yên tay buông — nửa còn lại của trò đùa nằm ở phản ứng của nó.
  const CU_CHI_NGHE: Record<string, TenCuChi> = {
    bat_ngo: "gio_len", nghi_ngo: "suy_nghi", tuc: "khoanh_tay", vui: "mo_tay",
    so: "khoanh_tay", buon: "nhun_vai", tu_tin: "khoanh_tay", trung_tinh: "nghi",
  };
  // Không có `camXucKia` thì suy ra phản ứng ĐỐI LẬP. Để cả hai "trung_tinh" là cách chắc chắn
  // nhất ra hai hình nộm đứng cạnh nhau — đúng thứ anh chê ở bản cũ.
  const DOI_LAP: Record<string, TenCamXuc> = {
    tuc: "bat_ngo", so: "trung_tinh", vui: "nghi_ngo", buon: "bat_ngo",
    bat_ngo: "tu_tin", nghi_ngo: "vui", tu_tin: "nghi_ngo", trung_tinh: "nghi_ngo",
  };
  const cxNghe = L.camXucKia || DOI_LAP[(L.camXuc || "trung_tinh") as string] || "nghi_ngo";
  const cuChiNghe = CU_CHI_NGHE[cxNghe as string] || "nghi";

  // 31/8 — Anh: *"lúc nói thì tất cả hình nhân vật đều mấp máy miệng"*. Gốc nằm ở một dòng:
  // `visemeTai(tu, giay, 0)` tra mốc từ của CẢ VIDEO tại giây hiện tại, nên cảnh nào cũng nhận
  // khẩu hình ấy — kể cả cảnh đã nói xong. Khẩu hình CHỈ thuộc về lượt đang phát.
  const imLang = { w: 12, h: 3, tron: 0 } as any;
  const viseme = dangNoi ? visemeTai(tu, giay, 0) : imLang;

  // Hướng sáng đọc từ chính ảnh nền đang dùng. Không có số đo thì đổ thẳng — mặc định an
  // toàn, và cũng đúng với 63/100 nền là phòng trong sáng đều.
  const huongSang = sang ? sang.huong : 0;
  const manhSang = sang ? sang.manh : 0;

  const cxA = doiNguoi ? w * 0.28 : canRong ? w * 0.29 : w * 0.5;
  const cxB = doiNguoi ? w * 0.72 : canRong ? w * 0.71 : w * 0.5;

  return (
    <div style={{
      position: "absolute", left: o.x, top: o.y, width: w, height: h, overflow: "hidden",
      border: `${netMuc}px solid #14110F`, borderRadius: boKhung,
      background: "#EDE7DA", boxSizing: "border-box",
      boxShadow: "6px 7px 0 #14110F22",
      // CẢNH PHẢI ĐỘNG. Anh chấm dựng phim 70/100 với lý do máy đứng yên suốt. Một cú đẩy máy
      // rất chậm (3,5% trong cả cảnh) không ai gọi tên được, nhưng nó là khác biệt giữa "một
      // đoạn phim" và "một bức tranh có tiếng". Cú chốt thì rung nhẹ — cú đấm của trò đùa.
      transform: `scale(${trn(0.985, 1, bat(p)) * (1 + kep(trong / 3.2) * 0.035)})`
                 + (L.chot && trong > 0.25 && trong < 0.75
                    ? ` translate(${Math.sin(trong * 62) * 5}px, ${Math.cos(trong * 54) * 4}px)` : ""),
    }}>
      <NenPanel kenh={kenh} noi={noi} anh={anhNen} w={w} h={h} mau={mau} mauPhu={mauPhu} hat={hat + thuTu * 13}
                bien={(hat + thuTu * 5) % 3} rong net={netMuc} cham={cham} />

      {/* Đạo cụ đọc ra từ chính câu thoại của cảnh này — thoại nói "router" thì trong khung có
          cái router. Không gọi mô hình: câu thoại là văn bản, dò từ khoá là đủ. */}
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}
           style={{ position: "absolute", inset: 0, zIndex: 2 }}>
        <DaoCu ten={doDaoCu(L.nar)} w={w} h={h} mau={mau} mauPhu={mauPhu} hai={doiNguoi} />
      </svg>

      {L.chot ? <VachToc w={w} h={h} p={kep(trong / 0.7)} mau={mauPhu} /> : null}

      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ position: "absolute", inset: 0, zIndex: 3 }}>
        {/* BÓNG — 31/8. Anh: *"người vẽ phẳng trên nền có chiều sâu vẫn hơi như dán lên"*.
            Hai lỗi ở cùng một chỗ. (1) Khối cũ nằm trong nhánh `doiNguoi`, nên CẢNH MỘT NGƯỜI
            KHÔNG CÓ BÓNG NÀO — mà cảnh một người chiếm quá nửa số khung, đúng những khung
            trông như dán. Lại là họ lỗi "vá một nhánh, để nguyên nhánh song song". (2) Bóng cũ
            đối xứng, đổ thẳng xuống: đó là bóng đèn studio, đặt lên ảnh có nắng xiên thì mắt
            bắt được ngay dù không gọi tên được.
            Nay mỗi người hai lớp, và chỗ ăn thua là lớp TIẾP ĐẤT (đậm, ôm sát chân) — nó nói
            "vật này đứng trên mặt phẳng"; còn lớp ĐỔ (nhạt, dài, xiên theo `huongSang` đo từ
            chính ảnh nền) nói "cùng một mặt trời với căn phòng". */}
        <BongNguoi x={cxA} y={yChan} k={k} cao={caoA} huong={huongSang} manh={manhSang} />
        {doiNguoi ? <BongNguoi x={cxB} y={yChan} k={k} cao={caoB} huong={huongSang} manh={manhSang} /> : null}

        {(doiNguoi || noiA) ? (
          <DienVienHai
            kieu={A}
            camXuc={(noiA ? (L.camXuc || "trung_tinh") : cxNghe) as TenCamXuc}
            cuChi={(noiA ? (L.cuChi || "mo_tay") : cuChiNghe) as TenCuChi}
            nhin={doiNguoi ? [noiA ? 0.45 : 0.5, 0] : [0, 0]}
            noi={noiA ? viseme : imLang}
            t={giay} dangNoi={noiA} kyHieu={false} ghimNguc nghieng={doiNguoi ? 0.09 : 0}
            // 31/8 — DIỄN LIÊN TỤC, KHÔNG PHẢI ĐỔI MỘT LẦN.
            // Bản trước cho `doiCuChi` chạy 0→1 trong nửa giây rồi đứng yên tới hết cảnh: nhân
            // vật đổi tư thế đúng một lần rồi bất động ba giây. Anh chấm dựng phim 84 và đây là
            // phần lớn số điểm bị trừ. Nay nó dao động liên tục theo một nhịp lệch pha với nhịp
            // thở của engine — hai chuyển động không bao giờ trùng nhau, nên không đọc ra là
            // vòng lặp. `nhan` lấy từ độ mở miệng: nói to thì cả người nhấn theo.
            cuChiTruoc={"nghi" as TenCuChi}
            doiCuChi={0.5 + 0.5 * Math.sin((giay - L.s) * 2.3 - 1.2)}
            nhan={noiA ? kep((viseme as any).h / 26) : 0}
            doVat={L.vatA || ""}
            x={cxA} y={yChan} scale={k}
          />
        ) : null}

        {(doiNguoi || !noiA) ? (
          <DienVienHai
            kieu={B}
            camXuc={(!noiA ? (L.camXuc || "trung_tinh") : cxNghe) as TenCamXuc}
            cuChi={(!noiA ? (L.cuChi || "mo_tay") : cuChiNghe) as TenCuChi}
            nhin={doiNguoi ? [!noiA ? -0.45 : -0.5, 0] : [0, 0]}
            noi={!noiA ? viseme : imLang}
            t={giay + 0.7} dangNoi={!noiA} kyHieu={false} ghimNguc nghieng={doiNguoi ? -0.09 : 0}
            cuChiTruoc={"nghi" as TenCuChi}
            doiCuChi={0.5 + 0.5 * Math.sin((giay - L.s) * 1.9 + 0.7)}
            nhan={!noiA ? kep((viseme as any).h / 26) : 0}
            doVat={L.vatB || ""}
            x={cxB} y={yChan} scale={k} lat
          />
        ) : null}
      </svg>

      {/* lớp gần vẽ SAU nhân vật -> che một phần người, cho ra chiều sâu */}
      <NenGan noi={noi} w={w} h={h} mau={mau} mauPhu={mauPhu} rong={doiNguoi} />

      <BongThoai chu={L.nar} tu={tu} giay={giay} W={w} H={h}
                 ben={canRong ? (noiA ? "phai" : "trai") : (noiA ? "trai" : "phai")}
                 duoi={canRong ? (noiA ? "trai" : "phai") : undefined}
                 hep={canRong} s0={L.s} e0={L.e} net={netMuc} boGoc={boGoc} hook={hook}
                 duoiKhung={bongDuoi}
                 p={kep(trong / 0.3)} mau={mauPhu} la={L.chot === true} />

      {L.chot && trong > 0.25 ? (
        <ChuNo chu={chuNo} w={w} h={h} p={kep((trong - 0.25) / 0.45)} mau={mau} tren={bongDuoi} />
      ) : null}
    </div>
  );
};

// ── THẺ HOOK ──────────────────────────────────────────────────────────────────────────────
/**
 * Hai giây đầu quyết định người xem ở lại hay lướt qua, và bản trước không có gì ở đó ngoài
 * một câu thoại cỡ thường. Anh chấm hạng mục hook 55/100 — đúng, vì giây 0 không cho ai lý do
 * nào để dừng lại.
 *
 * Thẻ này là một câu VIẾT RIÊNG, không phải lời thoại: nó nêu TÌNH HUỐNG và tạo đúng một câu
 * hỏi trong đầu người xem ("HE WAITED FORTY MINUTES. FOR THIS." — "this" là cái gì?). Bộ sinh
 * kịch bản có cổng chặn hook nào trùng câu chốt: hook lộ cú chốt là hook tự huỷ, vì biết kết
 * quả rồi thì không còn lý do xem tiếp.
 *
 * Đặt ở NỬA DƯỚI khung, không phải giữa: giữa là chỗ khuôn mặt, mà mặt đang diễn ở giây đầu
 * cũng là một phần của hook. Che mặt để nhường chỗ cho chữ là đổi chác lỗ.
 */
const TheHook: React.FC<{ chu: string; W: number; H: number; p: number; mau: string }> =
({ chu, W, H, p, mau }) => {
  if (!chu || p >= 1) return null;
  const vao = kep(p / 0.09);                    // bật lên trong 0,2 giây đầu
  const ra = kep((p - 0.86) / 0.14);            // rồi trượt lên và mờ đi
  const sc = vao < 1 ? trn(0.82, 1.04, bat(vao)) : trn(1.04, 1, muot(kep((p - 0.09) / 0.08)));
  const n = Math.max(6, chu.length);
  const fs = Math.max(34, Math.min(96, Math.sqrt((W * 0.86 * H * 0.2) / 0.62 / n)));
  return (
    <div style={{
      position: "absolute", left: 0, right: 0, top: H * 0.62,
      display: "flex", justifyContent: "center", pointerEvents: "none", zIndex: 9,
      transform: `translateY(${-ra * H * 0.14}px) scale(${sc})`, opacity: 1 - ra,
    }}>
      <div style={{
        background: mau, border: "9px solid #14110F", borderRadius: 10,
        padding: "18px 26px", maxWidth: W * 0.86, textAlign: "center",
        boxShadow: "11px 12px 0 #14110F",
        fontFamily: "Poppins, Arial Black, sans-serif", fontWeight: 900,
        fontSize: fs, lineHeight: 1.04, color: "#FFFFFF", letterSpacing: 0.4,
        WebkitTextStroke: `${Math.round(fs * 0.06)}px #14110F`, paintOrder: "stroke fill",
      }}>{chu}</div>
    </div>
  );
};

// ── DỰNG PHIM ─────────────────────────────────────────────────────────────────────────────
/** Cỡ cảnh của từng lượt. Đây là quyết định dựng phim, không để engine tự đo. */
const coCanh = (i: number, n: number, hat: number): boolean => {
  if (i === 0) return true;                 // mở màn: cho biết ai đang ở với ai
  if (i === n - 1) return true;             // cú chốt: phải thấy mặt người nghe sững ra
  return ((i + hat) % 2) === 0;             // giữa phim xen kẽ, lệch theo kênh
};

type KieuChuyen = "ngang" | "doc" | "quet";

/**
 * Chuyển cảnh. Ba kiểu, đổi theo lượt — một phim cắt bằng đúng một kiểu suốt hai mươi giây thì
 * nhịp nghe ra là máy dựng. KHÔNG dùng mờ-chồng: hai khung tô đầy màu chồng lên nhau đọc ra là
 * ảnh phơi hai lần, đã đo được ở bản trang-nhiều-ô.
 */
const bienCanh = (kieu: KieuChuyen, p: number, cu: boolean, W: number, H: number): React.CSSProperties => {
  const m = muot(p);
  if (kieu === "ngang") return { transform: `translateX(${cu ? -m * W * 1.04 : (1 - m) * W * 1.04}px)` };
  if (kieu === "doc") return { transform: `translateY(${cu ? -m * H * 1.04 : (1 - m) * H * 1.04}px)` };
  return cu ? {} : { clipPath: `inset(0 ${(1 - m) * 100}% 0 0)` };   // quét như nét mực kéo ngang
};

export type PropsComic = {
  luot?: Luot[]; tu?: Tu[]; voMp3?: string; nhac?: string;
  nhacVol?: number;   // hệ số riêng của tệp nhạc, do `can_nhac.py` tính
  kieuA?: string; kieuB?: string; kieuTuyA?: Partial<Kieu>; kieuTuyB?: Partial<Kieu>;
  tieuDe?: string; handle?: string; mau?: string; mauPhu?: string; kenh?: string;
  // ── NÉT RIÊNG CỦA KÊNH ────────────────────────────────────────────────────────────────
  // Anh: *"sao cho 10 channel có nét riêng và phong cách riêng"*. Đổi màu là chưa đủ — mười
  // kênh cùng độ dày nét, cùng cỡ chấm halftone, cùng bo góc bong bóng thì vẫn đọc ra là một
  // xưởng vẽ tô mười bảng màu. Bốn trục dưới đây đổi CHẤT của nét vẽ, và mắt đọc chúng trước
  // khi kịp đọc màu.
  soTap?: number;     // số thứ tự tập — xem ghi chú "HÀNG NGHÌN TẬP" bên dưới
  // 31/8 — NƠI CHỐN DO KỊCH BẢN CHỌN, không do số tập.
  // Bản trước lấy nơi theo `soTap`, nên hình và lời chỉ tình cờ khớp nhau: kịch bản có thể
  // viết chuyện xảy ra ở nhà khách trong khi engine vẫn vẽ bàn hỗ trợ văn phòng. Nay bộ sinh
  // kịch bản chọn nơi TRONG danh sách engine vẽ được và trả về chỉ số ấy — khớp từ gốc.
  // Để -1 (hoặc bỏ trống) thì quay về cách cũ: chọn theo số tập.
  noiIdx?: number;
  hook?: string;      // thẻ hook 2 giây đầu — xem `TheHook`
  anhNen?: string;    // nền 3D sinh bằng Cloudflare; bỏ trống thì vẽ nền vector như cũ
  // Hướng sáng ĐO TỪ chính `anhNen` (`huong_sang.py` -> `huong_sang.json`), đưa sang bằng props
  // chứ không để engine đọc tệp: bước render trên Actions không được phép chạm đĩa ngoài
  // `staticFile`, và số đo là thứ tính một lần rồi dùng mãi.
  sang?: { huong: number; manh: number };
  netMuc?: number;    // độ dày viền mực: 5 (mảnh, sạch) .. 10 (thô, mạnh)
  cham?: number;      // cỡ ô halftone: 7 (mịn) .. 14 (thô như báo in)
  boGoc?: number;     // bo góc bong bóng: 6 (vuông, đanh) .. 34 (tròn, hiền)
  tiLe?: number;      // người cao bao nhiêu phần khung: 0.54 .. 0.68
  // 31/8 — Anh: *"kiểu videos làm cũng thế e nha"* (mỗi kênh một kiểu, đừng để nhìn ra cùng
  // một người làm). Bốn trục ở trên đổi CHẤT NÉT VẼ, nhưng bố cục khung thì mười kênh vẫn y
  // hệt: viền dày như nhau, bong bóng luôn trên, dải tên luôn đáy-trái, chữ nổ luôn "BOOM!".
  // Ba trục dưới đây đổi chính BỐ CỤC — thứ mắt đọc trước cả nét.
  bongDuoi?: boolean;  // bong bóng nằm dưới (lối manga) thay vì trên
  boKhung?: number;    // bo góc khung: 0 vuông đanh .. 28 mềm
  chuNo?: string;      // chữ nổ ở cú chốt — mỗi kênh một tiếng
};

export const calcComic = async ({ props }: { props: PropsComic }) => {
  const ls = props.luot || [];
  const het = ls.length ? Math.max(...ls.map((x) => x.e)) : 20;
  return { durationInFrames: Math.max(90, Math.round((het + 0.8) * 30)), fps: 30 };
};

export const KichComic: React.FC<PropsComic> = ({
  luot = [], tu = [], voMp3 = "", nhac = "", kieuA = "hang_xom", kieuB = "bank",
  nhacVol = 0.16,
  kieuTuyA = {}, kieuTuyB = {}, tieuDe = "", handle = "", mau = "#F0483C",
  mauPhu = "#1F7AE0", kenh = "", soTap = 0, noiIdx = -1, hook = "", anhNen = "",
  sang,
  netMuc = NET, cham = 9, boGoc = 26, tiLe = 0.60,
  bongDuoi = false, boKhung = 0, chuNo = "BOOM!",
}) => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const giay = f / fps;

  const A: Kieu = { ...(KIEU_MAU[kieuA] || KIEU_MAU.hang_xom), ...kieuTuyA };
  const B: Kieu = { ...(KIEU_MAU[kieuB] || KIEU_MAU.bank), ...kieuTuyB };
  // ── HÀNG NGHÌN TẬP MÀ KHÔNG TẬP NÀO GIỐNG TẬP NÀO ────────────────────────────────────
  // Anh: *"sau mỗi channel có làm hàng nghìn videos đảm bảo được tính đa dạng sáng tạo, ko
  // nhàm chán, lặp lại hay cùng 1 motip"*.
  //
  // Hạt băm cũ chỉ lấy TÊN KÊNH, nên mười kênh khác nhau nhưng một kênh thì tập nào cũng dựng
  // y hệt tập nào: cùng thứ tự cỡ cảnh, cùng chuỗi kiểu chuyển, cùng biến thể nền. Một nghìn
  // tập như thế là một nghìn lần lặp lại một bản dựng — đúng thứ YouTube gọi tên là "minimal
  // variation".
  //
  // Cộng số tập vào hạt (nhân một số nguyên tố để hai tập liền nhau không ra hạt gần nhau) thì
  // mọi thứ đọc hạt đều đổi theo tập: thứ tự rộng/cận, chuỗi chuyển cảnh, góc nhìn của nền.
  // Sáng tạo trong khuôn khổ — khuôn vẫn là khuôn comic, nhưng không tập nào trùng bản dựng.
  const hat = bam(kenh || tieuDe || "comic") + soTap * 7919;
  // MỘT TẬP = MỘT NƠI CHỐN. Các cảnh trong tập khác nhau bằng GÓC NHÌN (máy dịch trái/giữa/
  // phải), không bằng đổi địa điểm — hai người đang nói với nhau thì không dịch chuyển tức thời
  // sang chỗ khác giữa câu. Luật này đã trả giá một lần ở bản cũ.
  const noi = React.useMemo(
    () => noiCuaTap(kenh, noiIdx >= 0 ? noiIdx : soTap),
    [kenh, noiIdx, soTap],
  );
  const o: ONhoPanel = { i: 0, x: LE, y: LE, w: width - LE * 2, h: height - LE * 2 - CAO_TEN };

  // Lượt đang phát. Sau lượt cuối thì GIỮ NGUYÊN lượt cuối — không trả -1 rồi rơi vào nhánh dự
  // phòng, đúng cái bẫy khe-lặng đã trả giá ở bản cũ (luật 7af).
  let iL = 0;
  for (let i = 0; i < luot.length; i++) if (giay >= luot[i].s - 0.16) iL = i;
  const L = luot[iL];
  const Lcu = iL > 0 ? luot[iL - 1] : null;
  const pChuyen = L ? kep((giay - (L.s - 0.16)) / 0.34) : 1;
  const kieu: KieuChuyen = (["ngang", "quet", "doc"] as KieuChuyen[])[(iL + hat) % 3];

  const veCanh = (Lx: Luot, ix: number, dangNoi: boolean) => (
    <Panel L={Lx} o={o} A={A} B={B} tu={tu} giay={dangNoi ? giay : Lx.e} kenh={kenh}
           mau={mau} mauPhu={mauPhu} hat={hat} thuTu={ix}
           hai={coCanh(ix, luot.length, hat)} dangNoi={dangNoi} noi={noi} anhNen={anhNen}
           sang={sang}
           netMuc={netMuc} cham={cham} boGoc={boGoc} tiLe={tiLe}
           bongDuoi={bongDuoi} boKhung={boKhung} chuNo={chuNo}
           hook={ix === 0 ? kep((giay - Lx.s) / 1.15) : 0} />
  );

  return (
    <AbsoluteFill style={{ background: "#F6F1E6", fontFamily: "Poppins, Arial, sans-serif" }}>
      <AbsoluteFill>
        <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
          <defs>
            <pattern id="ht" width={cham + 2} height={cham + 2} patternUnits="userSpaceOnUse">
              <circle cx="3" cy="3" r={cham * 0.19} fill={`${mau}22`} />
            </pattern>
            <linearGradient id="giay" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FBF7EE" />
              <stop offset="100%" stopColor="#EFE7D6" />
            </linearGradient>
          </defs>
          <rect width={width} height={height} fill="url(#giay)" />
          <rect width={width} height={height} fill="url(#ht)" />
        </svg>
      </AbsoluteFill>

      {/* khung CŨ đi ra — vẽ trước, để khung mới nằm đè lên khi dùng kiểu "quét" */}
      {Lcu && pChuyen < 1 ? (
        <AbsoluteFill style={bienCanh(kieu, pChuyen, true, width, height)}>
          {veCanh(Lcu, iL - 1, false)}
        </AbsoluteFill>
      ) : null}

      {L ? (
        <AbsoluteFill style={bienCanh(kieu, pChuyen, false, width, height)}>
          {veCanh(L, iL, true)}
        </AbsoluteFill>
      ) : null}

      <div style={{
        position: "absolute", left: LE, right: LE, bottom: 14, height: CAO_TEN - 20,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        color: "#14110F", opacity: 0.82,
      }}>
        <div style={{ fontWeight: 900, fontSize: 27, letterSpacing: 1.4 }}>{tieuDe}</div>
        <div style={{ fontWeight: 700, fontSize: 21, color: mau }}>{handle}</div>
      </div>

      <TheHook chu={hook} W={width} H={height} p={kep(giay / 2.2)} mau={mau} />

      {voMp3 ? <Audio src={staticFile(voMp3)} /> : null}
      {/* ÂM LƯỢNG NHẠC — 31/8. Hằng cũ `0.16` dùng chung cho 10 tệp có độ to gốc trải 26 dB
          (−12,1 .. −38,3 LUFS): OFFICE nhạc gần bằng giọng, DATING coi như câm. Nay mỗi tệp
          một hệ số riêng, tính sẵn bởi `can_nhac.py` về cùng mốc −37 LUFS (dưới giọng 17 dB).
          Thêm NÉ GIỌNG: đang có người nói thì nhạc lùi còn 55%, hết thoại thì trả lại — đây là
          thứ khiến câu chốt nghe rõ mà đoạn lặng vẫn có không khí. */}
      {nhac ? (
        <Audio src={staticFile(nhac)} loop
               volume={(f: number) => {
                 const gy = f / fps;
                 const dangThoai = luot.some(x => gy >= x.s - 0.15 && gy <= x.e + 0.25);
                 return nhacVol * (dangThoai ? 0.55 : 1);
               }} />
      ) : null}
    </AbsoluteFill>
  );
};
