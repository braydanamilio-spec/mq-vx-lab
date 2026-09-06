import React from "react";
import { interpolate, spring, useVideoConfig } from "remotion";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   LỚP DỮ LIỆU — THỨ DUY NHẤT CÒN VẼ BẰNG CODE  (6/9/2026)

   Anh: *"ko dùng generate code tạo ảnh xấu, chỉ dùng cho phần chart và số liệu động."*

   Ranh giới ấy được cưỡng chế ở đây bằng cách đơn giản nhất: tệp này KHÔNG có một hàm nào vẽ
   người, phòng, cây, đồ vật hay nơi chốn. Nó chỉ biết bốn thứ — con số, cột, thanh, nhãn — và
   cả bốn đều là thứ mô hình sinh ảnh làm SAI (chữ trong ảnh là chỗ nó hỏng nặng nhất, §12.7)
   trong khi code làm đúng tuyệt đối và còn CHUYỂN ĐỘNG được theo thời gian.

   Đây cũng là lý do phân công này không phải một sự thoả hiệp: hai bên làm đúng hai việc mà
   bên kia không làm được, chứ không phải một bên gánh phần thừa của bên kia.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

export type Lop =
  | { k: "so"; so: string; don?: string; nhan?: string }
  | { k: "chart"; cot: { nhan: string; v: number }[]; don?: string; nhan?: string }
  | { k: "ss"; trai: { nhan: string; v: number }; phai: { nhan: string; v: number }; don?: string }
  | { k: "doi"; trai: { nhan: string; so: string }; phai: { nhan: string; so: string } }
  | { k: "nhan"; chu: string };

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));

/* ── ĐƠN VỊ CỠ CHỮ NEO THEO CHIỀU CAO KHUNG  (6/9/2026) ──────────────────────────────────
   Ba lượt mới ra đúng đơn vị, và ba lượt ấy đáng ghi vì mỗi lượt sai một kiểu khác nhau:

     u = W            9:16 đúng · 16:9 chữ to gấp 1,78 lần (nhãn cột cao 58px)
     u = min(W,H)     hai khung CÙNG cỡ chữ tuyệt đối — nhưng ở 16:9 khung chỉ cao 1080 nên
                      con số 216px chiếm 20% chiều cao, gấp đôi mức ở 9:16
     u = H * 0.5625   ✓

   Cỡ chữ trên màn hình đọc theo TỈ LỆ VỚI CHIỀU CAO KHUNG, không theo bề ngang và cũng không
   theo cạnh ngắn — đó là cách mọi bảng chuẩn phụ đề phát sóng quy định. `H * 0.5625` cho ra
   đúng 1080 ở khung dọc (nên mọi hằng số đã căn ở đó giữ nguyên) và 607 ở khung ngang.

   §17.2 lần thứ hai trong cùng một buổi: *một kích thước chịu hai ràng buộc mà công thức chỉ
   mã hoá một*. Lần đầu tôi mã hoá bề ngang, lần sau mã hoá cạnh ngắn; cả hai đều bỏ sót rằng
   thứ mắt so sánh là CHIỀU CAO KHUNG.

   Hệ số 0,70 cho khung NGANG (thay vì 0,5625) không phải để cho khác nhau: khung ngang chỉ
   cao 1080 và người ta xem nó ở xa hơn khung dọc trên điện thoại, nên cùng một TỈ LỆ với
   chiều cao lại đọc ra nhỏ hơn. 0,5625 cho phụ đề 38px trên bản 1080p — dưới mức đọc được. */
const U = (W: number, H: number) => H * (H >= W ? 0.5625 : 0.70);


/** Tách "24,901 miles" -> { n: 24901, duoi: " miles", dinh: 0 }. Giữ nguyên dấu phẩy khi vẽ
 *  lại, vì người Mỹ đọc `24,901` nhanh hơn `24901` — và đó là lý do duy nhất con số ở đây tồn
 *  tại. Không tách được (chuỗi không có số) thì trả null và chữ hiện nguyên, không đếm. */
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

/** Số đếm lên. `p` = 0..1 trong nhịp.
 *  Đếm xong ở 55% nhịp chứ không ở 100%: nhịp chỉ dài 1,5–2,5 giây, và một con số vẫn đang
 *  nhảy lúc cảnh cắt đi thì người xem KHÔNG BAO GIỜ đọc được giá trị cuối — tức mất trắng
 *  đúng thứ nhịp ấy sinh ra để nói. */
export const SoDong: React.FC<{
  so: string; don?: string; nhan?: string; p: number; W: number; H: number;
  mau: string; chu: string;
}> = ({ so, don, nhan, p, W, H, mau, chu }) => {
  const u = U(W, H);
  const t = tach(so);
  const q = kep(p / 0.55);
  const e = 1 - Math.pow(1 - q, 3);
  const hien = t ? t.truoc + soChu(t.n * e, t.le, t.phay) + t.duoi : so;
  /* CÚ ĐẤM VÀO KHUNG, KHÔNG PHẢI TRƯỢT VÀO.
     Con số là LỜI HỨA của cả tập, và nó phải tới trước khi ngón tay người xem kịp quyết định
     (đo công bố: quyết định lướt ~400ms). Trượt lên 0,03·H trong 0,12·nhịp là một chuyển động
     mắt gần như không thấy; một cú nảy từ 1,22 xuống 1,00 trong ~0,25 giây thì thấy ngay và
     nó là quy ước "số liệu vừa hiện" mà mọi bản tin thể thao Mỹ đều dùng. */
  const vao = kep(p / 0.12);
  const nay = 1.22 - 0.22 * (1 - Math.pow(1 - kep(p / 0.16), 3));
  const co = W * (hien.length > 9 ? 0.135 : hien.length > 6 ? 0.165 : 0.20);
  return (
    <div style={{
      position: "absolute", left: 0, right: 0, top: H * 0.115,
      display: "flex", flexDirection: "column", alignItems: "center",
      opacity: vao, transform: `scale(${nay})`, transformOrigin: "50% 40%",
    }}>
      {nhan ? (
        <div style={{
          fontFamily: chu, fontWeight: 700, fontSize: u * 0.036, letterSpacing: u * 0.006,
          color: "#FFFFFF", opacity: 0.86, marginBottom: u * 0.012,
          textShadow: "0 2px 18px rgba(0,0,0,0.75)",
        }}>{nhan.toUpperCase()}</div>
      ) : null}
      <div style={{
        fontFamily: chu, fontWeight: 900, fontSize: co, lineHeight: 0.95, color: "#FFFFFF",
        textShadow: "0 6px 34px rgba(0,0,0,0.85), 0 2px 8px rgba(0,0,0,0.6)",
      }}>{hien}</div>
      <div style={{
        width: co * 0.55 * kep(p / 0.3), height: Math.max(3, u * 0.007),
        background: mau, borderRadius: 99, marginTop: u * 0.016,
        boxShadow: `0 0 ${u * 0.03}px ${mau}`,
      }} />
      {don ? (
        <div style={{
          fontFamily: chu, fontWeight: 800, fontSize: u * 0.048, color: "#FFFFFF",
          marginTop: u * 0.014, letterSpacing: u * 0.004,
          textShadow: "0 3px 20px rgba(0,0,0,0.8)",
        }}>{don.toUpperCase()}</div>
      ) : null}
    </div>
  );
};

/** Biểu đồ cột — mọc lên theo nhịp. Nằm ở dải giữa, TRÊN dải phụ đề.
 *  Sàn chiều cao cột đo theo BỀ NGANG CỘT chứ không theo một hằng chung: §15.20 đã trả giá —
 *  cùng con số sàn, cột đứng thì nhìn thấy, cột ngang thì biến mất. */
export const ChartDong: React.FC<{
  cot: { nhan: string; v: number }[]; don?: string; nhan?: string;
  p: number; W: number; H: number; mau: string; phu: string; chu: string;
}> = ({ cot, don, nhan, p, W, H, mau, phu, chu }) => {
  const u = U(W, H);
  const ds = (cot || []).slice(0, 6);
  if (!ds.length) return null;
  const max = Math.max(...ds.map((c) => Math.abs(c.v)), 1e-9);
  const KH = Math.min(H * 0.30, u * 0.26);
  const bw = (u * 0.80) / ds.length;
  return (
    <div style={{
      position: "absolute", left: W * 0.10, right: W * 0.10, top: H * 0.115,
      opacity: kep(p / 0.12),
      background: "rgba(8,10,14,0.52)", borderRadius: u * 0.028,
      padding: `${u * 0.030}px ${u * 0.034}px ${u * 0.024}px`,
      backdropFilter: "blur(6px)",
    }}>
      {nhan ? (
        <div style={{
          fontFamily: chu, fontWeight: 800, fontSize: u * 0.038, color: "#FFFFFF",
          marginBottom: u * 0.02, letterSpacing: u * 0.004,
          textShadow: "0 2px 16px rgba(0,0,0,0.8)",
        }}>{nhan.toUpperCase()}</div>
      ) : null}
      <div style={{ display: "flex", alignItems: "flex-end", height: KH, gap: bw * 0.16 }}>
        {ds.map((c, i) => {
          const q = kep((p - i * 0.05) / 0.45);
          const e = 1 - Math.pow(1 - q, 3);
          const h = Math.max(KH * 0.035, (Math.abs(c.v) / max) * KH * e);
          return (
            <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column",
                                  justifyContent: "flex-end", height: "100%" }}>
              <div style={{
                fontFamily: chu, fontWeight: 900, fontSize: u * 0.030, color: "#FFFFFF",
                textAlign: "center", marginBottom: u * 0.008, opacity: kep((q - 0.6) / 0.3),
                textShadow: "0 2px 12px rgba(0,0,0,0.85)",
              }}>{c.v >= 1000 ? Math.round(c.v).toLocaleString("en-US") : c.v}</div>
              <div style={{
                height: h, borderRadius: u * 0.010,
                background: i === ds.length - 1
                  ? `linear-gradient(180deg,${mau},${mau}CC)`
                  : `linear-gradient(180deg,${phu}EE,${phu}99)`,
                boxShadow: "0 8px 26px rgba(0,0,0,0.45)",
              }} />
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", gap: bw * 0.16, marginTop: u * 0.014 }}>
        {ds.map((c, i) => (
          <div key={i} style={{
            flex: 1, fontFamily: chu, fontWeight: 700, fontSize: u * 0.024,
            color: "#FFFFFF", opacity: 0.9, textAlign: "center", lineHeight: 1.15,
            textShadow: "0 2px 12px rgba(0,0,0,0.85)",
          }}>{String(c.nhan || "").toUpperCase()}</div>
        ))}
      </div>
      {don ? (
        <div style={{
          fontFamily: chu, fontWeight: 700, fontSize: u * 0.024, color: "#FFFFFF",
          opacity: 0.62, marginTop: u * 0.012, textAlign: "right",
        }}>{don.toUpperCase()}</div>
      ) : null}
    </div>
  );
};

/** Hai thanh so kè. Dùng cho nhịp "cái này so với cái kia" — khuôn dễ đọc nhất trong 2 giây. */
export const SoKe: React.FC<{
  trai: { nhan: string; v: number }; phai: { nhan: string; v: number }; don?: string;
  p: number; W: number; H: number; mau: string; phu: string; chu: string;
}> = ({ trai, phai, don, p, W, H, mau, phu, chu }) => {
  const u = U(W, H);
  const max = Math.max(Math.abs(trai.v), Math.abs(phai.v), 1e-9);
  const e = 1 - Math.pow(1 - kep(p / 0.5), 3);
  const hang = (c: { nhan: string; v: number }, m: string, d: number) => (
    <div style={{ marginBottom: u * 0.05 }}>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "baseline",
        marginBottom: u * 0.012,
      }}>
        <span style={{
          fontFamily: chu, fontWeight: 800, fontSize: u * 0.034, color: "#FFFFFF",
          textShadow: "0 2px 14px rgba(0,0,0,0.85)",
        }}>{String(c.nhan || "").toUpperCase()}</span>
        <span style={{
          fontFamily: chu, fontWeight: 900, fontSize: u * 0.048, color: "#FFFFFF",
          textShadow: "0 2px 14px rgba(0,0,0,0.85)",
        }}>{c.v >= 1000 ? Math.round(c.v).toLocaleString("en-US") : c.v}</span>
      </div>
      <div style={{ height: u * 0.036, borderRadius: 99, background: "rgba(255,255,255,0.16)" }}>
        <div style={{
          width: `${kep((Math.abs(c.v) / max) * e) * 100}%`, height: "100%",
          borderRadius: 99, background: m,
          boxShadow: `0 0 ${u * 0.03}px ${m}88`,
          transitionProperty: "none",
        }} />
      </div>
    </div>
  );
  return (
    <div style={{
      position: "absolute", left: W * 0.10, right: W * 0.10, top: H * 0.145,
      opacity: kep(p / 0.12),
    }}>
      {hang(trai, phu, 0)}
      {hang(phai, mau, 1)}
      {don ? (
        <div style={{
          fontFamily: chu, fontWeight: 700, fontSize: u * 0.024, color: "#FFFFFF",
          opacity: 0.62, textAlign: "right",
        }}>{don.toUpperCase()}</div>
      ) : null}
    </div>
  );
};

/** Hai giá trị đặt cạnh nhau, KHÔNG có thanh tỉ lệ.
 *
 *  Vì sao tồn tại bên cạnh `SoKe`: rất nhiều cặp so sánh của bộ này khác ĐƠN VỊ ("3 mph" so
 *  với "670 million mph"). Vẽ thanh cho hai đơn vị khác nhau là vẽ một tỉ lệ không có thật —
 *  và ở cỡ 670 triệu so với 3 thì thanh ngắn hơn biến mất hẳn, tức người xem đọc ra "không có
 *  giá trị" thay vì "giá trị này bé đến thế" (§15.20). Hai con số đặt cạnh nhau nói đúng điều
 *  cần nói mà không hứa một tỉ lệ nào. */
export const DoiChieu: React.FC<{
  trai: { nhan: string; so: string }; phai: { nhan: string; so: string };
  p: number; W: number; H: number; mau: string; phu: string; chu: string;
}> = ({ trai, phai, p, W, H, mau, phu, chu }) => {
  const u = U(W, H);
  const o = (c: { nhan: string; so: string }, m: string, tre: number) => {
    const q = kep((p - tre) / 0.22);
    return (
      <div style={{
        flex: 1, opacity: q, transform: `translateY(${(1 - q) * H * 0.02}px)`,
        borderLeft: `${Math.max(3, u * 0.008)}px solid ${m}`, paddingLeft: u * 0.028,
      }}>
        <div style={{
          fontFamily: chu, fontWeight: 700, fontSize: u * 0.030, color: "#FFFFFF",
          opacity: 0.82, letterSpacing: u * 0.003,
          textShadow: "0 2px 14px rgba(0,0,0,0.85)",
        }}>{String(c.nhan || "").toUpperCase()}</div>
        <div style={{
          fontFamily: chu, fontWeight: 900, fontSize: u * 0.072, color: "#FFFFFF",
          lineHeight: 1.05, textShadow: "0 4px 24px rgba(0,0,0,0.9)",
        }}>{c.so}</div>
      </div>
    );
  };
  return (
    <div style={{
      position: "absolute", left: W * 0.09, right: W * 0.09, top: H * 0.145,
      display: "flex", gap: u * 0.06,
    }}>
      {o(trai, phu, 0.02)}
      {o(phai, mau, 0.16)}
    </div>
  );
};

/** Nhãn nhỏ góc trên — nói CHƯƠNG hoặc CHỦ ĐỀ, không nói lại lời đọc.
 *  Nằm ở đỉnh khung nên nó là thứ duy nhất được phép ở đó; mọi lớp khác đứng dưới 26%. */
export const NhanTren: React.FC<{
  chu_: string; p: number; W: number; H: number; mau: string; chu: string;
}> = ({ chu_, p, W, H, mau, chu }) => {
  const u = U(W, H);
  return (
  <div style={{
    position: "absolute", left: W * 0.06, top: H * 0.052,
    display: "flex", alignItems: "center", gap: u * 0.018,
    opacity: kep(p / 0.1),
  }}>
    <div style={{ width: u * 0.010, height: u * 0.058, background: mau, borderRadius: 99 }} />
    <div style={{
      fontFamily: chu, fontWeight: 800, fontSize: u * 0.032, color: "#FFFFFF",
      letterSpacing: u * 0.005, textShadow: "0 2px 16px rgba(0,0,0,0.8)",
    }}>{String(chu_ || "").toUpperCase()}</div>
  </div>
);
};
