import { loadFont as fKanit } from "@remotion/google-fonts/Kanit";
import { loadFont as fSora } from "@remotion/google-fonts/Sora";
import { loadFont as fOutfit } from "@remotion/google-fonts/Outfit";
import { loadFont as fLexend } from "@remotion/google-fonts/Lexend";
import { loadFont as fManrope } from "@remotion/google-fonts/Manrope";
import { loadFont as fSaira } from "@remotion/google-fonts/Saira";
import { loadFont as fKhand } from "@remotion/google-fonts/Khand";
import { loadFont as fAlfa } from "@remotion/google-fonts/AlfaSlabOne";
import { loadFont as fArvo } from "@remotion/google-fonts/Arvo";
import { loadFont as fBitter } from "@remotion/google-fonts/Bitter";
import { loadFont as fAnton } from "@remotion/google-fonts/Anton";
import { loadFont as fBebas } from "@remotion/google-fonts/BebasNeue";
import { loadFont as fOswald } from "@remotion/google-fonts/Oswald";
import { loadFont as fArchivo } from "@remotion/google-fonts/ArchivoBlack";
import { loadFont as fTeko } from "@remotion/google-fonts/Teko";
import { loadFont as fBarlow } from "@remotion/google-fonts/BarlowCondensed";
import { loadFont as fPlayfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as fRubik } from "@remotion/google-fonts/Rubik";
import { loadFont as fMontserrat } from "@remotion/google-fonts/Montserrat";
import { loadFont as fStaatliches } from "@remotion/google-fonts/Staatliches";
import { loadFont as fFjalla } from "@remotion/google-fonts/FjallaOne";
import { loadFont as fChivo } from "@remotion/google-fonts/Chivo";
import { loadFont as fSpace } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as fPoppins } from "@remotion/google-fonts/Poppins";

// ─────────────────────────────────────────────────────────────────────────────
// SỔ PHÔNG CHỮ DÙNG CHUNG (26/8/2026)
//
// Đếm trước khi làm: `brandkit_the_he_2.py` ghi `"font": "Poppins"` cho **cả 50 kênh**, và trong
// mã engine có 83 chỗ viết cứng `fontFamily: "'Poppins',Arial"`. Nghĩa là 50 kênh "khác nhau" thực
// ra dùng chung một khuôn chữ — mà chữ là thứ chiếm nửa khung hình ở dạng dọc 1080×1920.
//
// Phông tải LÚC BUILD qua @remotion/google-fonts (nhúng vào bundle), nên chạy được trong CI không
// mạng — khác hẳn cách nhúng bằng link CDN, thứ sẽ âm thầm rơi về Arial khi bị chặn.
//
// Chọn 13 phông theo TÍNH CÁCH, không theo "cho nhiều": mỗi nhóm hợp một loại kênh khác nhau.
// ─────────────────────────────────────────────────────────────────────────────

type Nap = () => { fontFamily: string };

// Nạp ngay khi mô-đun được import: Remotion cần phông sẵn sàng TRƯỚC khung đầu tiên, nạp trễ
// trong lúc render là ra một vài khung chữ Arial rồi mới đổi — lỗi nhấp nháy rất khó truy.
const _n = (f: Nap, w: string[]): string => {
  try {
    return f().fontFamily;
  } catch {
    return "Poppins";
  }
};

export const PHONG: Record<string, string> = {
  // Khối đặc, hét lên — hợp kênh số liệu gây sốc, xếp hạng, tiền bạc
  anton: _n(fAnton as any, []),
  archivo: _n(fArchivo as any, []),
  staatliches: _n(fStaatliches as any, []),
  // Hẹp cao, kiểu bảng hiệu/thể thao — hợp kênh đua, so kè, thi đấu
  bebas: _n(fBebas as any, []),
  oswald: _n(fOswald as any, []),
  teko: _n(fTeko as any, []),
  fjalla: _n(fFjalla as any, []),
  barlow: _n(fBarlow as any, []),
  // Có chân, trang trọng — hợp hồ sơ toà án, lưu trữ, lịch sử
  playfair: _n(fPlayfair as any, []),
  // Hình học hiện đại — hợp khoa học, không gian, công nghệ
  space: _n(fSpace as any, []),
  chivo: _n(fChivo as any, []),
  // Trung tính, dễ đọc — hợp kênh giải thích dài dòng
  rubik: _n(fRubik as any, []),
  montserrat: _n(fMontserrat as any, []),
  poppins: _n(fPoppins as any, []),
  // Bổ sung 26/8: nhóm `ranked` có 18 kênh, mà 13 phông thì 5 cặp buộc phải trùng. Thêm 10 phông
  // nữa để MỌI kênh trong cùng một định dạng đều khác chữ — chữ là thứ chiếm nửa khung hình dọc.
  kanit: _n(fKanit as any, []),
  sora: _n(fSora as any, []),
  outfit: _n(fOutfit as any, []),
  lexend: _n(fLexend as any, []),
  manrope: _n(fManrope as any, []),
  saira: _n(fSaira as any, []),
  khand: _n(fKhand as any, []),
  alfa: _n(fAlfa as any, []),
  arvo: _n(fArvo as any, []),
  bitter: _n(fBitter as any, []),
};

/** Trả về chuỗi `fontFamily` đầy đủ, luôn có phông lùi để không bao giờ ra khung trắng chữ.
 *  Tên lạ (gõ sai, kênh cũ chưa gán) -> Poppins, đúng hành vi trước đây. */
export const phong = (ten?: string): string => {
  const k = String(ten || "").toLowerCase().trim();
  const f = PHONG[k] || PHONG.poppins;
  return `'${f}','Poppins',Arial,sans-serif`;
};

export const TEN_PHONG = Object.keys(PHONG);
