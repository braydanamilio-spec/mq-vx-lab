import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

/**
 * SỐ BIẾT CHẠY + CHỮ SỐ ĐỀU + DÒNG NGUỒN — bộ dùng chung cho mọi dạng thế hệ 2 (27/8/2026).
 *
 * VÌ SAO CÓ TỆP NÀY
 * -----------------
 * Soi cả 6 dạng thì ra ba lỗ hổng giống nhau, và đều là thứ tách một video dữ liệu hạng nhất
 * khỏi một video dữ liệu hạng thường:
 *
 *   1. SỐ KHÔNG CHẠY — 4/6 dạng không có một phép nội suy nào cho con số. Số hiện "bụp" một cái
 *      rồi đứng im. Đây là chỗ phí phạm lớn nhất: trong video dữ liệu, con số ĐANG CHẠY là công
 *      cụ giữ mắt mạnh nhất — người xem không rời mắt khi thấy một con số còn đang lớn dần, vì
 *      não muốn biết nó dừng ở đâu. Hiện sẵn giá trị cuối là vứt bỏ đúng thứ đó.
 *
 *   2. KHÔNG GHI NGUỒN — 4/6 dạng không in một chữ nào về nguồn dữ liệu. Mất hai thứ cùng lúc:
 *      lòng tin của người xem (số ở đâu ra?), và bằng chứng trước chính sách "nội dung lặp lại,
 *      sản xuất hàng loạt" của YouTube — trong khi dữ liệu của mình VỐN là dữ liệu công khai
 *      tra được, tức là một lợi thế đang bị bỏ không.
 *
 *   3. CHỮ SỐ KHÔNG ĐỀU — 5/6 dạng không đặt `tabular-nums`. Phông chữ mặc định cho chữ số bề
 *      ngang KHÁC NHAU (số 1 hẹp hơn số 8), nên số đang chạy thì cả khối chữ giật trái phải theo
 *      từng khung hình, và các cột số xếp cạnh nhau thì không thẳng hàng. Đây là dấu hiệu
 *      nghiệp dư dễ thấy nhất mà lại rẻ nhất để sửa: đúng một dòng CSS.
 */

/** Chữ số đều bề ngang — đặt vào MỌI chỗ hiển thị số. */
export const SO_DEU: React.CSSProperties = { fontVariantNumeric: "tabular-nums" };

/** Tách "1,234.5K" / "$833,877" / "8x" / "1 in 27" thành (đầu, số, đuôi) để chạy đúng phần số. */
const _boc = (s: string): [string, number, string] => {
  const m = String(s ?? "").match(/^(\D*?)([\d][\d,.]*)(.*)$/s);
  if (!m) return [String(s ?? ""), NaN, ""];
  const so = parseFloat(m[2].replace(/,/g, ""));
  return [m[1], so, m[3]];
};

/** Có bao nhiêu chữ số sau dấu chấm trong chuỗi gốc — để lúc chạy không đổi độ chính xác. */
const _le = (s: string): number => {
  const m = String(s ?? "").match(/\.(\d+)/);
  return m ? m[1].length : 0;
};

/**
 * Con số CHẠY TỪ 0 LÊN giá trị thật rồi dừng.
 *
 * `s` là chuỗi đã định dạng sẵn ("269.7K", "$833,877", "1 in 27") — component tự tách phần số,
 * chạy đúng phần đó, và giữ nguyên tiền tố/hậu tố. Nhờ vậy mọi dạng dùng chung được mà không
 * phải đổi cấu trúc dữ liệu.
 *
 * `tuFrame` = khung hình bắt đầu chạy; `giay` = chạy trong bao lâu.
 * Đường cong dồn nhanh lúc đầu rồi chậm dần về đích (ease-out mạnh): mắt bắt được ĐỘ LỚN gần
 * như ngay lập tức, còn hai chữ số cuối thì thong thả — vừa nhanh vừa vẫn có cảm giác "đang đếm".
 */
export const SoChay: React.FC<{
  s?: string; tuFrame?: number; giay?: number; style?: React.CSSProperties;
}> = ({ s = "", tuFrame = 0, giay = 1.15, style }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [dau, so, duoi] = _boc(s);
  if (!isFinite(so)) return <span style={{ ...SO_DEU, ...style }}>{s}</span>;
  const n = Math.max(1, Math.round(giay * fps));
  const t = interpolate(f - tuFrame, [0, n], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const e = 1 - Math.pow(1 - t, 3);                 // ease-out bậc ba
  const v = so * e;
  const le = _le(s);
  const hien = t >= 1
    ? s.slice(dau.length, s.length - duoi.length)   // về đích thì trả lại ĐÚNG chuỗi gốc
    : v.toLocaleString("en-US", { minimumFractionDigits: le, maximumFractionDigits: le });
  return <span style={{ ...SO_DEU, ...style }}>{dau}{hien}{duoi}</span>;
};

/**
 * Dòng nguồn — nhỏ, kín đáo, luôn ở cùng một chỗ trên mọi dạng.
 *
 * Cố ý KHÔNG làm nổi: nó không phải thứ để khoe, nó là thứ để người hoài nghi tìm thấy khi họ
 * đi tìm. Đặt sát đáy, mờ, chữ nhỏ — có mặt suốt video mà không tranh chỗ với dữ liệu.
 */
export const DongNguon: React.FC<{ nguon?: string; day?: number }> = ({ nguon, day = 96 }) => {
  if (!nguon) return null;
  return (
    <div style={{
      position: "absolute", bottom: day, left: 0, right: 0, textAlign: "center",
      color: "#ffffff4d", fontWeight: 600, fontSize: 21, letterSpacing: 0.3,
      padding: "0 60px", textShadow: "0 1px 6px #0009",
      whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
    }}>
      Source: {nguon}
    </div>
  );
};
