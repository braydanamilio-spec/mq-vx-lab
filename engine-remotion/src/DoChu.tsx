import { AbsoluteFill } from "remotion";
import React from "react";
import { phong } from "./Phong";

// THƯỚC ĐO BỀ RỘNG CHỮ (26/8/2026).
// `fitSize` trong DocThumb dùng hằng CHAR_W = 0.62, và chú thích của nó nói rõ con số đó đo cho
// **Poppins**. Khi hệ chuyển sang 24 phông thì hằng đó sai theo cả hai chiều: phông hẹp (Anton,
// Bebas, Teko, Khand) bị tính rộng hơn thực -> chữ thu nhỏ vô cớ, phí nửa khung hình; phông rộng
// (Playfair, Arvo, AlfaSlabOne, ArchivoBlack) bị tính hẹp hơn thực -> CHỮ TRÀN RA NGOÀI KHUNG.
// Thấy tận mắt trên thumbnail thử: template `duoi` (Playfair) và `khoi` (Oswald) đều cụt dấu "$".
//
// Composition này chỉ để ĐO: in một chuỗi biết trước, cỡ 100px, chữ trắng nền đen, KHÔNG viền
// không glow — rồi đếm bề rộng vệt mực bằng PIL. Không đoán, đúng như luật đã ghi cho CHAR_W.
export const DoChu: React.FC<{ text?: string; font?: string }> = ({
  text = "ABCDEFGHIJ", font = "poppins",
}) => (
  <AbsoluteFill style={{ background: "#000" }}>
    <div style={{
      position: "absolute", left: 0, top: 0, whiteSpace: "nowrap",
      fontFamily: phong(font), fontSize: 100, fontWeight: 900, color: "#fff", lineHeight: 1.4,
    }}>{text.toUpperCase()}</div>
  </AbsoluteFill>
);
