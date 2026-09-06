import React from "react";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   LỚP SỐ LIỆU CHO PANEL COMIC  (6/9/2026)

   Vì sao tệp này phải tồn tại: dựng thử nội dung GIẢI THÍCH bằng engine comic thì đường ống
   chạy thông ngay lượt đầu — nhưng **con số biến mất**. Bản pilot nói *"That's a single day's
   work, huh?"* mà `19 MILES` không xuất hiện ở đâu cả, vì engine comic chỉ có bong bóng thoại
   và không có chỗ nào đặt số.

   Với kênh hài thì không sao. Với kênh giải thích thì đó là mất đúng thứ kênh ấy bán: người
   xem tới vì CON SỐ, không tới vì hai người nói chuyện.

   Và cổng của em lúc ấy **báo ĐỦ** — vì nó so lời thoại với lời DẪN, trong khi con số nằm ở
   trường `so`/`don` của nhịp, không nằm trong lời dẫn. Cổng đúng cú pháp, đo nhầm nguồn, xanh
   một cách rỗng. Đúng §12.8, lần này do chính em dựng lại.

   ── VÌ SAO KHÔNG BÊ NGUYÊN `LopSo.tsx` CỦA v10 SANG ─────────────────────────────────────
   `LopSo` vẽ cho khung ĐẦY 1080×1920. Panel comic chỉ là một ô trong lưới, có ô rộng nửa
   khung, có ô cao một phần ba — nên mọi cỡ phải tính theo KÍCH THƯỚC PANEL, không theo khung.
   Bê nguyên sang là đúng cái lỗi "chép hằng sang hệ quy chiếu khác" (§6 CLAUDE.md).

   Lớp này nằm TRÊN nền, DƯỚI bong bóng thoại: bong bóng là thứ dẫn nhịp, số là thứ chứng minh.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

export type LopComic =
  | { k: "so"; so: string; don?: string }
  | { k: "chart"; cot: { nhan: string; v: number }[]; don?: string }
  | { k: "doi"; trai: { nhan: string; so: string }; phai: { nhan: string; so: string } };

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));

/** "24,901 miles" -> đếm lên và giữ nguyên dấu phẩy. Không đọc được số thì hiện nguyên chữ. */
const tach = (s: string) => {
  const m = String(s || "").match(/^([^\d\-]*)(-?[\d.,]+)(.*)$/);
  if (!m) return null;
  const tho = m[2].replace(/,/g, "");
  const n = parseFloat(tho);
  if (!isFinite(n)) return null;
  const dot = tho.indexOf(".");
  return { truoc: m[1], n, duoi: m[3], le: dot < 0 ? 0 : tho.length - dot - 1,
           phay: m[2].includes(",") };
};

const soChu = (n: number, le: number, phay: boolean) => {
  const s = n.toFixed(le);
  if (!phay) return s;
  const [a, b] = s.split(".");
  return a.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (b ? "." + b : "");
};

/* Đế mờ sau con số. Panel comic có nền là một căn phòng sáng, chữ trắng đặt thẳng lên đó sẽ
   chìm ở nửa số phòng. Đế tối là cách mọi bản tin làm, và nó đúng ở MỌI tấm nền — khác hẳn
   việc trông chờ nền tự đủ tối (§13.27: biểu tượng tàng hình khi khung trùng tông). */
const De: React.FC<{ children: React.ReactNode; u: number; nhe?: boolean }> =
  ({ children, u, nhe }) => (
  <div style={{
    background: nhe ? "rgba(12,10,9,0.46)" : "rgba(12,10,9,0.62)",
    borderRadius: u * 0.10, padding: `${u * 0.075}px ${u * 0.11}px`,
    display: "inline-block", backdropFilter: "blur(3px)",
  }}>{children}</div>
);

/* ── VÌ SAO CÓ `tran`  (6/9/2026) ────────────────────────────────────────────────────────
   Soi khung 16,0s của `pilot_realcost_0002`: nhãn **YEAR 5** của biểu đồ bị ĐỈNH ĐẦU nhân vật
   che mất, chỉ còn đọc ra "YEA". Ba lớp cùng chọn giữa khung mà không lớp nào biết lớp nào —
   đúng §17.4 CLAUDE.md, lần này giữa lớp SỐ và lớp NGƯỜI.

   Chữa ở gốc: `KichComic` ĐÃ tính đỉnh đầu (`yChan − CAO_NGUOI·cao·k`) để đặt bóng đổ, nên nó
   truyền luôn con số ấy xuống đây; khối số ước lượng chiều cao của CHÍNH NÓ rồi co cho vừa dải
   trống. Không đặt thêm một hằng số đoán (§13.7) — dải trống lấy từ hình học đang có.

   Ước lượng CAO hơn thực tế thì an toàn (khối co nhỏ hơn mức cần); ước lượng thấp thì lại che.
   Nên mọi hệ số dưới đây lấy cận TRÊN của từng dòng chữ. */
export const SoPanel: React.FC<{
  lop: LopComic; w: number; h: number; p: number; mau: string; phu: string; chu: string;
  tran?: number;
}> = ({ lop, w, h, p, mau, phu, chu, tran }) => {
  // Đơn vị theo CẠNH NGẮN của panel: panel comic có ô ngang và ô dọc, và một hằng theo bề
  // ngang sẽ cho hai cỡ chữ khác hẳn nhau ở hai loại ô.
  const u = Math.min(w, h);
  const DINH = h * 0.10;                 // mép trên của khối — phải khớp `top` ở `chung`
  const DEM = u * 0.15;                  // đệm trên + dưới của `De`
  // Dải trống thật: từ mép trên khối tới đỉnh đầu, chừa một khoảng thở 2% chiều cao.
  const cho = Math.max(h * 0.16, (tran ?? h) - DINH - h * 0.02);
  const vua = (cao: number) => Math.min(1, cho / Math.max(1, cao));
  const vao = kep(p / 0.14);
  const chung: React.CSSProperties = {
    position: "absolute", left: 0, right: 0, top: h * 0.10,
    display: "flex", flexDirection: "column", alignItems: "center",
    opacity: vao, pointerEvents: "none",
  };

  if (lop.k === "so") {
    const t = tach(lop.so);
    const q = kep(p / 0.5);
    const e = 1 - Math.pow(1 - q, 3);
    const hien = t ? t.truoc + soChu(t.n * e, t.le, t.phay) + t.duoi : lop.so;
    // Cú nảy vào khung, không trượt: con số là lời hứa của cả tập và phải tới trước khi
    // ngón tay người xem kịp quyết định.
    const nay = 1.18 - 0.18 * (1 - Math.pow(1 - kep(p / 0.18), 3));
    const co = u * (hien.length > 8 ? 0.20 : hien.length > 5 ? 0.25 : 0.31);
    const khoi = co * 0.95 + u * 0.035 + Math.max(3, u * 0.014)
               + (lop.don ? u * 0.03 + u * 0.072 * 1.2 : 0) + DEM;
    return (
      <div style={{ ...chung, transform: `scale(${nay * vua(khoi)})`,
                    transformOrigin: "50% 0%" }}>
        <De u={u}>
          <div style={{
            fontFamily: chu, fontWeight: 900, fontSize: co, lineHeight: 0.95,
            color: "#FFFFFF", textAlign: "center",
          }}>{hien}</div>
          <div style={{
            height: Math.max(3, u * 0.014), width: "62%", margin: `${u * 0.035}px auto 0`,
            background: mau, borderRadius: 99,
          }} />
          {lop.don ? (
            <div style={{
              fontFamily: chu, fontWeight: 800, fontSize: u * 0.072, color: "#FFFFFF",
              letterSpacing: u * 0.006, marginTop: u * 0.03, textAlign: "center",
            }}>{lop.don.toUpperCase()}</div>
          ) : null}
        </De>
      </div>
    );
  }

  if (lop.k === "doi") {
    const o = (c: { nhan: string; so: string }, m: string, tre: number) => {
      const q = kep((p - tre) / 0.24);
      return (
        <div style={{ opacity: q, borderLeft: `${Math.max(3, u * 0.016)}px solid ${m}`,
                      paddingLeft: u * 0.05, marginBottom: u * 0.05 }}>
          <div style={{ fontFamily: chu, fontWeight: 700, fontSize: u * 0.052,
                        color: "#FFFFFF", opacity: 0.85 }}>
            {String(c.nhan || "").toUpperCase()}</div>
          <div style={{ fontFamily: chu, fontWeight: 900, fontSize: u * 0.105,
                        color: "#FFFFFF", lineHeight: 1.05 }}>{c.so}</div>
        </div>
      );
    };
    const khoi = 2 * (u * 0.052 * 1.25 + u * 0.105 * 1.05 + u * 0.05) + DEM;
    return (
      <div style={{ ...chung, alignItems: "stretch", left: w * 0.08, right: w * 0.08,
                    transform: `scale(${vua(khoi)})`, transformOrigin: "50% 0%" }}>
        <De u={u}>{o(lop.trai, phu, 0.02)}{o(lop.phai, mau, 0.18)}</De>
      </div>
    );
  }

  const ds = (lop.cot || []).slice(0, 4);
  if (!ds.length) return null;
  const max = Math.max(...ds.map((c) => Math.abs(c.v)), 1e-9);
  // Nhãn cột được phép xuống DÒNG THỨ HAI ("year 10" ngắn, nhưng "hourly wage" thì không) —
  // nên cận trên là hai dòng, không phải một.
  const _CHU = u * 0.02 + u * 0.040 * 1.15 * 2 + DEM;   // phần KHÔNG co được: chữ + đệm
  // Thu chiều cao CỘT cho vừa dải trống, thay vì co cả khối bằng `vua`. Hai cách đều hết che
  // đầu, nhưng co cả khối thì CHỮ nhỏ theo — mà chữ nhỏ là đúng thứ §15.9/§15.11 đã trả giá.
  // Cột thấp vẫn đọc được vì nó so tương đối với nhau; nhãn nhỏ thì không đọc được gì.
  const KH = Math.max(h * 0.09, Math.min(h * 0.22, cho - _CHU));
  const khoi = KH + _CHU;
  return (
    <div style={{ ...chung, alignItems: "stretch", left: w * 0.08, right: w * 0.08,
                  transform: `scale(${vua(khoi)})`, transformOrigin: "50% 0%" }}>
      <De u={u}>
        <div style={{ display: "flex", alignItems: "flex-end", height: KH, gap: u * 0.03 }}>
          {ds.map((c, i) => {
            const q = kep((p - i * 0.06) / 0.5);
            const hh = Math.max(KH * 0.05, (Math.abs(c.v) / max) * KH * (1 - Math.pow(1 - q, 3)));
            return (
              <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column",
                                    justifyContent: "flex-end", height: "100%" }}>
                <div style={{ fontFamily: chu, fontWeight: 900, fontSize: u * 0.048,
                              color: "#FFFFFF", textAlign: "center",
                              marginBottom: u * 0.012, opacity: kep((q - 0.6) / 0.3) }}>
                  {c.v >= 1000 ? Math.round(c.v).toLocaleString("en-US") : c.v}</div>
                <div style={{ height: hh, borderRadius: u * 0.02,
                              background: i === ds.length - 1 ? mau : phu }} />
              </div>
            );
          })}
        </div>
        <div style={{ display: "flex", gap: u * 0.03, marginTop: u * 0.02 }}>
          {ds.map((c, i) => (
            <div key={i} style={{ flex: 1, fontFamily: chu, fontWeight: 700,
                                  fontSize: u * 0.040, color: "#FFFFFF", opacity: 0.9,
                                  textAlign: "center", lineHeight: 1.15 }}>
              {String(c.nhan || "").toUpperCase()}</div>
          ))}
        </div>
      </De>
    </div>
  );
};
