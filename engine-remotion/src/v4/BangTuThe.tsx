// 30/8 — kyHieu PHẢI là true. Bảng này dựng để soi cử chỉ kênh HÀI, mà kênh hài chạy
// kyHieu=true. Đặt false thì component áp bảng _GHIM_NGUC (chế độ người-dẫn, cố ý ghim tay
// trong tầm ngực để không che thẻ số ở đỉnh khung), nên `gio_len` và `chi` bị đổi thành `dem`
// TRƯỚC khi vẽ. Tôi nhìn bảng, thấy "gio_len không giơ", và suýt đi sửa một bảng số vốn đã
// đúng. Cổng đo sai chế độ thì mọi kết luận rút từ nó đều sai — đây là lần thứ năm trong
// phiên này một cổng tôi tự viết tố oan phần code lành.
import React from "react";
import { AbsoluteFill } from "remotion";
import { DienVienHai } from "./DienVienHai";
import { KIEU_MAU, TenCuChi } from "../v2/DienVien";

/**
 * BẢNG TƯ THẾ — vẽ MỌI cử chỉ ra một tấm để soi bằng mắt. (30/8/2026)
 *
 * VÌ SAO CẦN TỆP NÀY
 * ------------------
 * Anh: *"không làm được nhân vật quay thì phải vẽ nhân vật quay trước, hay gì sẵn kho vector gì
 * đó rồi mới cho quay… chứ ép nó quay xong tay rồi người lỗi tùm lum"*.
 *
 * Anh chỉ đúng chỗ tôi sai từ đầu. Tôi định nghĩa cử chỉ bằng **góc** rồi để máy tính ra hình —
 * nên mỗi lần đổi một con số là một canh bạc: có góc ra đẹp, có góc ra tay vòng qua ngực thành
 * dải băng. Suốt phiên tôi sửa góc bốn năm lần, và mỗi lần chỉ đổi chỗ xấu.
 *
 * Hoạt hình 2D thật không làm thế. Họ vẽ **model sheet** — mỗi tư thế một bản vẽ, kiểm bằng mắt,
 * rồi mới đưa vào phim. Không ai để công thức quyết định hình dáng nhân vật.
 *
 * Tệp này là bước đầu tiên của lối làm ấy: dựng **một tấm duy nhất** chứa mọi cử chỉ, ở cả hai
 * chiều lật, để soi cùng lúc. Một tư thế xấu nhìn ra trong một giây khi nó nằm cạnh chín tư thế
 * kia — trong khi nếu chỉ gặp nó thoáng qua giữa một video mười sáu giây thì phải xem đi xem lại
 * mới bắt được.
 *
 * Cách dùng:
 *     npx remotion still src/index.ts BangTuThe out/bang_tu_the.png --props='{}'
 */

// `t` truyền vào phải đủ lớn: engine "mở" vào tư thế theo `muot(t / 0.45)`, nên ở t = 0 mọi cử
// chỉ còn nằm ở giá trị mặc định và cả bảng ra GIỐNG HỆT NHAU. Lần đầu dựng bảng tôi để t = 0,
// thấy mười ô như một, và suýt đi sửa engine vốn đúng — cây thước kêu oan lần thứ tư trong ngày.
// Kiểm thước trước khi tin thước.
const T_DU = 1.2;

const CU_CHI: TenCuChi[] = [
  "nghi", "chi", "mo_tay", "dem", "suy_nghi",
  "nhun_vai", "gio_len", "khoanh_tay", "chong_nanh", "ngan_ngam",
] as TenCuChi[];

export const BangTuThe: React.FC = () => {
  const kieu = { ...(KIEU_MAU as any).nam_dam, kieuToc: "ngan", gioi: "nam" };
  const COT = 5;
  const O = 300;                      // bề rộng mỗi ô
  const CAO = 460;
  return (
    <AbsoluteFill style={{ background: "#F3EFE6", fontFamily: "Poppins, Arial, sans-serif" }}>
      <svg viewBox={`0 0 ${COT * O} ${Math.ceil(CU_CHI.length / COT) * CAO + 60}`}
           width="100%" height="100%">
        {CU_CHI.map((cc, i) => {
          const x = (i % COT) * O + O / 2;
          const y = Math.floor(i / COT) * CAO + CAO - 60;
          return (
            <g key={cc}>
              <text x={x} y={Math.floor(i / COT) * CAO + 30} textAnchor="middle"
                    fontSize={22} fontWeight={800} fill="#2A2A33">{cc}</text>
              {/* đường sàn để thấy ngay chân có chạm đất không */}
              <line x1={x - O / 2 + 20} y1={y} x2={x + O / 2 - 20} y2={y}
                    stroke="#2A2A3322" strokeWidth={2} />
              <g transform={`translate(${x} ${y})`}>
                <DienVienHai
                  kieu={kieu as any}
                  camXuc="trung_tinh"
                  cuChi={cc}
                  nhin={[0.2, 0]}
                  noi={{ w: 0.3, h: 0.1, tron: 0.2 }}
                  t={T_DU}
                  kyHieu={true}
                  doiCuChi={1}
                  scale={0.62}
                />
              </g>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
