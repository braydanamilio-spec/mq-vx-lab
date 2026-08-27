import { AbsoluteFill, useVideoConfig } from "remotion";
import React from "react";
import { Icon } from "./BrandV2";
import { phong } from "./Phong";

/**
 * NHẬN DIỆN V4 — 50 KÊNH, 50 BỘ MẶT (27/8/2026)
 *
 * VÌ SAO PHẢI VIẾT LẠI V3
 * -----------------------
 * Nhìn 25 avatar và 12 cover cạnh nhau thì thấy ngay: V3 chỉ có MỘT bố cục.
 *   • avatar: khung tối + vòng tròn màu + 2 chữ cái + nhãn nhỏ  → 50 cái giống hệt, khác mỗi sắc
 *   • cover : title/tagline/@handle xếp giữa trên nền thanh xám → 50 cái giống hệt
 *   • và nhãn nhỏ đó IN TÊN ĐỊNH DẠNG NỘI BỘ (RANKED/RACE/CINEMATIC…). Người xem không hiểu nó
 *     là gì, nhưng nó GOM 50 KÊNH THÀNH 7 CỤM NHÌN THẤY ĐƯỢC — đúng thứ dấu vân tay phải xoá.
 * V3 lại vứt hết nguyên liệu đã có sẵn: 24 phông trong `Phong.tsx`, 22 biểu tượng trong
 * `BrandV2.tsx`, bảng 50 màu cách xa nhau trong `brandkit_the_he_2.py`. Nó chỉ dùng đúng 1 màu.
 *
 * NGUYÊN TẮC V4
 * -------------
 * Đổi màu KHÔNG phải đổi nhận diện. Muốn 50 kênh không lộ ra cùng một chủ thì phải đổi thứ mắt
 * đọc trước màu: NỀN SÁNG HAY TỐI, BỐ CỤC, và DẤU HIỆU là chữ hay là hình.
 *   1. `nen`  — 3 chất nền: tối / giấy sáng / màu đặc. Đây là đòn bẩy mạnh nhất; V3 để cả 50 kênh
 *               nền tối nên tự nó đã đủ làm mọi thứ trông giống nhau.
 *   2. `bo`   — 8 nguyên mẫu avatar và 8 nguyên mẫu cover, khác nhau về CẤU TRÚC chứ không phải
 *               về trang trí.
 *   3. `dau`  — kênh thì lấy monogram làm dấu, kênh thì lấy biểu tượng niche làm dấu.
 * Ba trục này bốc từ BĂM TÊN KÊNH, **không** từ `dinh_dang` — nên không còn cụm nào trùng khớp
 * với dạng render. Băm cố định nên chạy lại luôn ra đúng bộ cũ: nhận diện không được đổi giữa
 * các lần sinh, đổi là mất người theo dõi.
 *
 * RÀNG BUỘC KHÔNG ĐƯỢC PHÁ
 * ------------------------
 *   • YouTube banner: chữ chỉ nằm trong vùng an toàn 1546×423 chính giữa (điện thoại cắt tới đó).
 *   • Avatar: YouTube cắt TRÒN và hiện ở 48px trên điện thoại → mỗi nguyên mẫu phải có ĐÚNG MỘT
 *     hình khối trội, tương phản cao. Bố cục hai dòng chữ ở 48px là một vệt xám.
 *   • Facebook cover: điện thoại cắt còn khoảng giữa → chữ giữ trong 78% bề ngang.
 *   • Chữ luôn lấy màu theo ĐỘ SÁNG của nền ngay dưới nó, không viết cứng màu trắng.
 */

export type NhanV4Props = {
  kind?: string;            // banner | avatar | watermark | fb_cover | fb_avatar | ig_avatar | ig_post | x_header
  name?: string;
  tagline?: string;
  handle?: string;
  motif?: string;           // biểu tượng theo niche (BrandV2.Icon)
  font?: string;            // khoá phông trong Phong.tsx
  palette?: { bg?: string; primary?: string; secondary?: string; accent?: string; text?: string };
  /** BỘ MẶT ĐÃ CHỐT trong `kenh_the_he_2.json > brand.hinh` (xem brandkit_the_he_2.chia_hinh).
   *  Thiếu thì mới rơi về băm tên — băm rải lệch 10/3 và tính lại mỗi lần, không dùng làm chuẩn. */
  hinh?: { nen?: number; av?: number; bang?: number };
};

// ── nền tảng ────────────────────────────────────────────────────────────────────────────────
const HEX = (s: string | undefined, d: string) => (s && /^#[0-9a-fA-F]{6}$/.test(s) ? s : d);

/** Băm ổn định (FNV-1a 32-bit). Cùng tên kênh luôn ra cùng số, mọi lần chạy, mọi máy. */
const bam = (s: string): number => {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return h >>> 0;
};

const rgb = (h: string) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];

/** Độ sáng cảm nhận (WCAG relative luminance). Dùng để CHỌN màu chữ, không đoán. */
const sang = (h: string): number => {
  const f = (v: number) => { const x = v / 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); };
  const [r, g, b] = rgb(h);
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
};

/** Màu chữ tương phản đủ trên nền `n`. Ngưỡng 0.34 cho tỉ lệ tương phản ≥ ~4.5:1 hai phía. */
const chuTren = (n: string, toi = "#0B0D12", sangMau = "#FFFFFF") => (sang(n) > 0.34 ? toi : sangMau);

/** Trộn màu về phía trắng/đen theo tỉ lệ t. */
const tron = (h: string, den: string, t: number) => {
  const [a1, a2, a3] = rgb(h), [b1, b2, b3] = rgb(den);
  const k = (x: number, y: number) => Math.round(x + (y - x) * t).toString(16).padStart(2, "0");
  return `#${k(a1, b1)}${k(a2, b2)}${k(a3, b3)}`;
};

const monogram = (ten: string) => {
  const w = String(ten).trim().split(/\s+/).filter(Boolean);
  if (w.length >= 2) return (w[0][0] + w[1][0]).toUpperCase();
  return String(ten).slice(0, 2).toUpperCase();
};

// ── ba trục biến thể, bốc từ băm tên kênh ───────────────────────────────────────────────────
type Chat = { nen: string; chu: string; phu: string; nhan: string; sangNen: boolean };

/**
 * Chất nền. `k` 0..2:
 *   0 tối    — nền `bg` của kênh, chữ sáng, nhấn là accent
 *   1 giấy   — nền rất sáng pha chút accent, chữ mực đen, nhấn là primary đậm
 *   2 đặc    — nền chính là accent/primary ở cường độ đầy, chữ tự chọn theo độ sáng
 */
const chatNen = (k: number, P: Required<NonNullable<NhanV4Props["palette"]>>): Chat => {
  if (k === 1) {
    const nen = tron(P.accent, "#FFFFFF", 0.9);          // giấy nhuộm rất nhạt màu kênh
    const nhan = sang(P.primary) > 0.55 ? tron(P.primary, "#000000", 0.35) : P.primary;
    return { nen, chu: "#12151C", phu: tron("#12151C", nen, 0.42), nhan, sangNen: true };
  }
  if (k === 2) {
    const nen = sang(P.accent) > 0.62 ? tron(P.accent, "#000000", 0.18) : P.accent;
    const chu = chuTren(nen);
    return { nen, chu, phu: tron(chu, nen, 0.34), nhan: chu === "#FFFFFF" ? tron(nen, "#000000", 0.55) : "#FFFFFF", sangNen: sang(nen) > 0.34 };
  }
  const nen = P.bg;
  return { nen, chu: "#FFFFFF", phu: "#C9D3E2", nhan: P.accent, sangNen: false };
};

// ═══════════════════════════════════════════════════════════════════════════════════════════
// AVATAR — 8 nguyên mẫu. Mỗi cái phải đọc được ở 48px sau khi bị cắt tròn.
// Vẽ trong khung vuông S; mọi chi tiết quan trọng nằm trong đường tròn nội tiếp.
// ═══════════════════════════════════════════════════════════════════════════════════════════
const AvatarBo: React.FC<{ bo: number; S: S; C: Chat; P: any; ten: string; motif: string; chu: string }> =
({ bo, S: s, C, P, ten, motif, chu }) => {
  const W = s.W;
  const mg = monogram(ten);
  const co = (t: number) => W * t;
  const chuChinh: React.CSSProperties = {
    fontFamily: chu, fontWeight: 900, lineHeight: 1,
    letterSpacing: -W * 0.015, position: "relative",
  };

  switch (bo % 8) {
    // 0 — CHỮ ĐỤC: nền màu đặc, monogram khoét thủng gần kín khung. To nhất, rõ nhất ở 48px.
    case 0: return (
      <AbsoluteFill style={{ background: C.nhan, alignItems: "center", justifyContent: "center" }}>
        <div style={{ ...chuChinh, color: chuTren(C.nhan), fontSize: co(mg.length > 2 ? 0.52 : 0.66) }}>{mg}</div>
      </AbsoluteFill>
    );

    // 1 — CHÉO: khung cắt đôi theo đường chéo, monogram nằm vắt qua ranh giới.
    case 1: return (
      <AbsoluteFill style={{ background: C.nen, alignItems: "center", justifyContent: "center" }}>
        <AbsoluteFill style={{ background: C.nhan, clipPath: "polygon(0 0, 100% 0, 0 100%)" }} />
        <div style={{ ...chuChinh, color: C.sangNen ? "#0B0D12" : "#FFFFFF", fontSize: co(0.48),
                      mixBlendMode: "difference" as const, filter: "invert(1)" }}>{mg}</div>
      </AbsoluteFill>
    );

    // 2 — KHUNG VUÔNG: viền dày, monogram ở giữa. Khối vuông trong vòng tròn = tương phản hình học.
    case 2: return (
      <AbsoluteFill style={{ background: C.nen, alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "absolute", inset: co(0.13), border: `${co(0.055)}px solid ${C.nhan}` }} />
        <div style={{ ...chuChinh, color: C.chu, fontSize: co(0.40) }}>{mg}</div>
      </AbsoluteFill>
    );

    // 3 — ĐĨA: đĩa màu đặc trên nền ngược, monogram khoét thủng đĩa.
    case 3: return (
      <AbsoluteFill style={{ background: C.nen, alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "absolute", width: co(0.80), height: co(0.80), borderRadius: "50%", background: C.nhan }} />
        <div style={{ ...chuChinh, color: chuTren(C.nhan), fontSize: co(0.40) }}>{mg}</div>
      </AbsoluteFill>
    );

    // 4 — BĂNG NGANG: ba dải, monogram đè lên. Dải ngang sống sót tốt khi bị thu nhỏ.
    case 4: return (
      <AbsoluteFill style={{ background: C.nen, alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "absolute", inset: 0, top: "34%", height: "32%", background: C.nhan }} />
        <div style={{ position: "absolute", inset: 0, top: "70%", height: "8%", background: P.secondary }} />
        <div style={{ ...chuChinh, color: chuTren(C.nhan), fontSize: co(0.34), marginTop: -co(0.02) }}>{mg}</div>
      </AbsoluteFill>
    );

    // 5 — DẤU HIỆU: bỏ chữ hẳn, lấy biểu tượng niche làm mặt kênh.
    case 5: return (
      <AbsoluteFill style={{ background: C.nen, alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "absolute", width: co(0.86), height: co(0.86), borderRadius: "50%",
                      background: C.sangNen ? "#FFFFFF" : tron(C.nen, "#FFFFFF", 0.08) }} />
        <div style={{ position: "relative", transform: "scale(1.05)" }}>
          <Icon m={motif} c={C.nhan} s={co(0.52)} />
        </div>
      </AbsoluteFill>
    );

    // 6 — NÉT RỖNG: monogram chỉ còn viền, nét rất dày để 48px vẫn thành hình.
    case 6: return (
      <AbsoluteFill style={{ background: C.nhan, alignItems: "center", justifyContent: "center" }}>
        <div style={{ ...chuChinh, fontSize: co(0.52), color: "transparent",
                      WebkitTextStroke: `${co(0.030)}px ${chuTren(C.nhan)}` }}>{mg}</div>
      </AbsoluteFill>
    );

    // 7 — GÓC: nêm phần tư ở góc, monogram lệch về góc đối.
    default: return (
      <AbsoluteFill style={{ background: C.nen, alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "absolute", left: 0, top: 0, width: co(0.62), height: co(0.62),
                      background: C.nhan, borderBottomRightRadius: "100%" }} />
        {/* 27/8 — chữ căn GIỮA, chỉ nêm màu lệch góc. Bản đầu đẩy cả chữ về góc đối; nhưng
            YouTube cắt TRÒN, mọi thứ ngoài đường tròn nội tiếp đều mất, chữ lệch là bị xén. */}
        <div style={{ ...chuChinh, color: C.chu, fontSize: co(0.38) }}>{mg}</div>
      </AbsoluteFill>
    );
  }
};

// ═══════════════════════════════════════════════════════════════════════════════════════════
// BĂNG RỘNG (YouTube banner / FB cover / X header) — 8 nguyên mẫu bố cục.
// `AN` là hộp an toàn: mọi CHỮ phải nằm trong đó, nền thì tràn viền.
// ═══════════════════════════════════════════════════════════════════════════════════════════
type S = { W: number; H: number };

/**
 * RÌA NGOÀI — lấp phần khung nằm NGOÀI hộp an toàn (27/8).
 *
 * Vùng an toàn YouTube chỉ là 1546×423 giữa khung 2560×1440: 60% bề ngang, 29% bề cao. Nghĩa là
 * ~71% chiều cao khung là rìa. V3 lấp bằng thanh xám mờ trên nền đen — thành bùn. Bỏ trống thì
 * cover nền sáng trông như chưa render xong. Cách đúng: lấp bằng khối màu ĐẶC, dứt khoát, và
 * TUYỆT ĐỐI không lấn vào hộp an toàn — chữ vẫn sạch, khung vẫn đầy.
 *
 * Bốn cách lấp, chọn theo bố cục; hai bố cục 6 và 7 đã tự phủ kín khung nên bỏ qua.
 */
const RiaNgoai: React.FC<{ bo: number; S: S; T: number; AN_H: number; C: Chat; P: any; motif: string }> =
({ bo, S: s, T, AN_H, C, P, motif }) => {
  const { W, H } = s;
  const D = T + AN_H;                                   // mép dưới hộp an toàn
  const nhat = C.sangNen ? tron(C.nhan, "#FFFFFF", 0.72) : tron(C.nhan, C.nen, 0.72);
  if (bo % 8 === 6 || bo % 8 === 7) return null;
  switch (bo % 4) {
    // dải đặc tì đáy khung + chỉ nhấn mảnh phía trên nó
    case 0: return (
      <>
        <div style={{ position: "absolute", left: 0, bottom: 0, width: W, height: (H - D) * 0.46, background: C.nhan }} />
        <div style={{ position: "absolute", left: 0, bottom: (H - D) * 0.46, width: W, height: H * 0.008, background: P.secondary }} />
      </>
    );
    // hàng biểu tượng nhắc lại ở rìa trên, rất nhạt — như hoa văn giấy tiêu đề
    case 1: return (
      <div style={{ position: "absolute", left: 0, top: T * 0.16, width: W, height: T * 0.6,
                    display: "flex", alignItems: "center", justifyContent: "space-around", opacity: 0.16 }}>
        {[0, 1, 2, 3, 4, 5, 6].map((i) => <Icon key={i} m={motif} c={C.nhan} s={T * 0.42} />)}
      </div>
    );
    // hai khối vuông lệch ở hai góc đối
    case 2: return (
      <>
        <div style={{ position: "absolute", left: -W * 0.03, top: -H * 0.05, width: W * 0.20, height: T * 0.9,
                      background: nhat, transform: "rotate(-6deg)" }} />
        <div style={{ position: "absolute", right: -W * 0.03, bottom: -H * 0.05, width: W * 0.26,
                      height: (H - D) * 0.9, background: C.nhan, transform: "rotate(-6deg)" }} />
      </>
    );
    // hai vệt ngang ôm trên và dưới
    default: return (
      <>
        <div style={{ position: "absolute", left: 0, top: T * 0.42, width: W * 0.30, height: H * 0.022, background: C.nhan }} />
        <div style={{ position: "absolute", right: 0, top: T * 0.42, width: W * 0.30, height: H * 0.022, background: nhat }} />
        <div style={{ position: "absolute", left: 0, bottom: (H - D) * 0.34, width: W, height: H * 0.055, background: nhat }} />
      </>
    );
  }
};

const BangBo: React.FC<{
  bo: number; S: S; AN: { w: number; h: number }; C: Chat; P: any;
  ten: string; tagline: string; handle: string; motif: string; chu: string; nho: boolean;
}> = ({ bo, S: s, AN, C, P, ten, tagline, handle, motif, chu, nho }) => {
  const { W, H } = s;
  const k = AN.w / 1546;                                   // hệ số co theo bề ngang hộp an toàn
  const dai = String(ten).length;
  const cTen = (dai > 18 ? 96 : dai > 13 ? 122 : dai > 9 ? 150 : 176) * k;
  const cTag = 40 * k, cHan = 32 * k;
  const L = (W - AN.w) / 2, T = (H - AN.h) / 2;

  const Ten = ({ mau }: { mau?: string }) => (
    <div style={{ fontFamily: chu, fontWeight: 900, fontSize: cTen, lineHeight: 0.94,
                  letterSpacing: -1.5 * k, color: mau || C.chu }}>{ten}</div>
  );
  const Phu = ({ mau, canh }: { mau?: string; canh?: any }) => (
    <>
      {tagline ? <div style={{ fontFamily: chu, fontWeight: 700, fontSize: cTag, marginTop: 14 * k,
                               color: mau || C.phu, textAlign: canh }}>{tagline}</div> : null}
      {handle && !nho ? <div style={{ fontFamily: chu, fontWeight: 800, fontSize: cHan, marginTop: 8 * k,
                                      color: C.nhan, textAlign: canh, opacity: 0.95 }}>{handle}</div> : null}
    </>
  );
  const hop = (extra: React.CSSProperties): React.CSSProperties =>
    ({ position: "absolute", left: L, top: T, width: AN.w, height: AN.h, display: "flex", ...extra });

  switch (bo % 8) {
    // 0 — VẠCH TRÁI: chữ căn trái sau một vạch dọc dày; biểu tượng mờ chiếm nửa phải.
    case 0: return (
      <>
        {/* 27/8 — biểu tượng neo theo HỘP AN TOÀN, không theo mép khung. Bản đầu đặt
            `right: W*0.07` với cỡ `H*0.78`: ở khổ 2560×1440 nó trải từ x≈1258, mà mép trái hộp
            an toàn là x≈507 — tức là đè thẳng lên chữ. Nay chữ giữ 58% trái của hộp, hình nằm
            trọn trong 42% phải, hai bên không bao giờ chạm nhau ở bất kỳ khổ nào. */}
        <div style={{ position: "absolute", left: L + AN.w * 0.80, top: "50%",
                      transform: "translate(-50%,-50%)", opacity: 0.18 }}>
          <Icon m={motif} c={C.nhan} s={Math.min(AN.h * 1.05, AN.w * 0.30)} />
        </div>
        <div style={hop({ width: AN.w * 0.58, flexDirection: "column", justifyContent: "center",
                          paddingLeft: 46 * k, borderLeft: `${14 * k}px solid ${C.nhan}` })}>
          <Ten /><Phu />
        </div>
      </>
    );

    // 1 — KẺ TRÊN DƯỚI: căn giữa, hai đường mảnh ôm lấy tên.
    case 1: return (
      <div style={hop({ flexDirection: "column", alignItems: "center", justifyContent: "center" })}>
        <div style={{ width: "62%", height: 3 * k, background: C.nhan, marginBottom: 22 * k }} />
        <Ten />
        <div style={{ width: "62%", height: 3 * k, background: C.nhan, marginTop: 20 * k }} />
        <Phu canh="center" />
      </div>
    );

    // 2 — CHIA Ô: dấu hiệu trong ô màu bên trái, chữ bên phải.
    case 2: return (
      <div style={hop({ alignItems: "center", gap: 52 * k })}>
        <div style={{ width: AN.h * 0.84, height: AN.h * 0.84, background: C.nhan, flex: "0 0 auto",
                      display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Icon m={motif} c={chuTren(C.nhan)} s={AN.h * 0.52} />
        </div>
        <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}><Ten /><Phu /></div>
      </div>
    );

    // 3 — ĐÁY: chữ tì xuống đáy hộp an toàn, biểu tượng lớn phía trên.
    case 3: return (
      <>
        <div style={{ position: "absolute", left: "50%", top: T - H * 0.02,
                      transform: "translate(-50%,-100%)", opacity: 0.9 }}>
          <Icon m={motif} c={C.nhan} s={H * 0.30} />
        </div>
        <div style={hop({ flexDirection: "column", alignItems: "center", justifyContent: "flex-end" })}>
          <Ten /><Phu canh="center" />
        </div>
      </>
    );

    // 4 — BIỂN: chữ nằm trong một tấm biển đặc, nổi hẳn khỏi nền.
    case 4: return (
      <div style={hop({ alignItems: "center", justifyContent: "center" })}>
        <div style={{ background: C.sangNen ? "#12151C" : "#FFFFFF", padding: `${30 * k}px ${58 * k}px`,
                      display: "flex", flexDirection: "column", alignItems: "center",
                      borderBottom: `${12 * k}px solid ${C.nhan}` }}>
          <Ten mau={C.sangNen ? "#FFFFFF" : "#12151C"} />
          <Phu mau={C.sangNen ? "#B9C4D4" : "#4A5364"} canh="center" />
        </div>
      </div>
    );

    // 5 — GẠCH ĐẬM: tên đứng trên một thanh màu dày chạy hết bề ngang chữ.
    case 5: return (
      <div style={hop({ flexDirection: "column", alignItems: "flex-start", justifyContent: "center",
                        paddingLeft: 10 * k })}>
        <Ten />
        <div style={{ width: Math.min(AN.w, dai * cTen * 0.52), height: 18 * k, background: C.nhan,
                      marginTop: 10 * k }} />
        <Phu />
      </div>
    );

    // 6 — BĂNG CHÉO: dải màu nghiêng chạy sau tên, chữ đè lên.
    case 6: return (
      <>
        <div style={{ position: "absolute", left: -W * 0.05, top: H * 0.40, width: W * 1.1, height: H * 0.26,
                      background: C.nhan, transform: "rotate(-4deg)" }} />
        <div style={hop({ flexDirection: "column", alignItems: "center", justifyContent: "center" })}>
          <Ten mau={chuTren(C.nhan)} />
          <Phu mau={tron(chuTren(C.nhan), C.nhan, 0.25)} canh="center" />
        </div>
      </>
    );

    // 7 — HAI NỬA: khung cắt dọc, chữ đặt trên nửa đậm.
    default: {
      // 27/8 — mảng màu phải BẮT ĐẦU SAU mép phải hộp an toàn. Bản đầu để `width: W*0.42`, tức
      // mảng bắt đầu ở x = 0.58W ≈ 1485, còn hộp an toàn kéo tới x ≈ 2053 → chữ đâm vào mảng.
      // Nay lấy mốc từ chính hộp an toàn, và cột chữ dừng trước mảng một khoảng đệm.
      const X = Math.max(L + AN.w * 0.60, W * 0.66);      // mép trái mảng màu
      return (
        <>
          <div style={{ position: "absolute", left: X, top: 0, width: W - X, height: H, background: C.nhan }} />
          <div style={{ position: "absolute", left: X + (W - X) / 2, top: "50%",
                        transform: "translate(-50%,-50%)", opacity: 0.5 }}>
            <Icon m={motif} c={chuTren(C.nhan)} s={Math.min(H * 0.46, (W - X) * 0.55)} />
          </div>
          <div style={hop({ width: X - L - 40 * k, flexDirection: "column",
                            justifyContent: "center", alignItems: "flex-start" })}>
            <Ten /><Phu />
          </div>
        </>
      );
    }
  }
};

// ═══════════════════════════════════════════════════════════════════════════════════════════
export const NhanV4: React.FC<NhanV4Props> = (props) => {
  const { kind = "banner", name = "MM0", tagline = "", handle = "", motif = "bars", font = "" } = props;
  const { width: W, height: H } = useVideoConfig();
  const pl = props.palette || {};
  const P = {
    bg: HEX(pl.bg, "#0A0C16"), primary: HEX(pl.primary, "#2F6BFF"),
    secondary: HEX(pl.secondary, "#7A8AA5"), accent: HEX(pl.accent, "#22D3EE"),
    text: HEX(pl.text, "#F2F6FF"),
  };
  const h = bam(String(name));
  // Bộ mặt lấy từ JSON nếu đã chốt (50 kênh = 50 bộ ba khác nhau, chia đều). Băm chỉ là đường lui
  // cho kênh chưa được cấp — và không lát băm nào dính tới `dinh_dang`, nên không còn cụm nào
  // trùng khớp với dạng render.
  const G = props.hinh || {};
  const iNen = G.nen ?? h % 3;
  const iAv = G.av ?? (h >> 3) % 8;
  const iBang = G.bang ?? (h >> 7) % 8;
  const C = chatNen(iNen, P);
  const chu = phong(font);

  // ── watermark: chỉ dấu hiệu, nền trong suốt ──────────────────────────────────────────────
  if (kind === "watermark") {
    return (
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: W * 0.86, height: W * 0.86, borderRadius: iAv % 2 ? "18%" : "50%",
                      background: C.nhan, display: "flex", alignItems: "center", justifyContent: "center",
                      fontFamily: chu, fontWeight: 900, fontSize: W * 0.42,
                      color: chuTren(C.nhan), letterSpacing: -W * 0.02 }}>
          {monogram(name)}
        </div>
      </AbsoluteFill>
    );
  }

  // ── ảnh đại diện (YouTube / Facebook / Instagram) ────────────────────────────────────────
  if (kind === "avatar" || kind === "fb_avatar" || kind === "ig_avatar") {
    return (
      <AbsoluteFill style={{ background: C.nen, overflow: "hidden" }}>
        <AvatarBo bo={iAv} S={{ W, H }} C={C} P={P} ten={name} motif={motif} chu={chu} />
      </AbsoluteFill>
    );
  }

  // ── ảnh vuông Instagram: dấu hiệu trên, tên dưới ─────────────────────────────────────────
  if (kind === "ig_post") {
    return (
      <AbsoluteFill style={{ background: C.nen, alignItems: "center", justifyContent: "center",
                             flexDirection: "column", gap: W * 0.05, padding: W * 0.09 }}>
        <div style={{ width: W * 0.42, height: W * 0.42, position: "relative" }}>
          <AvatarBo bo={iAv} S={{ W: W * 0.42, H: W * 0.42 }} C={C} P={P} ten={name} motif={motif} chu={chu} />
        </div>
        <div style={{ fontFamily: chu, fontWeight: 900, color: C.chu, textAlign: "center",
                      fontSize: W * (String(name).length > 14 ? 0.075 : 0.098), lineHeight: 0.98 }}>{name}</div>
        {tagline ? <div style={{ fontFamily: chu, fontWeight: 700, color: C.phu, textAlign: "center",
                                 fontSize: W * 0.032 }}>{tagline}</div> : null}
      </AbsoluteFill>
    );
  }

  // ── băng rộng ────────────────────────────────────────────────────────────────────────────
  // Hộp an toàn theo từng nền tảng — đây là phần V3 làm đúng và phải giữ:
  //   YouTube 2560×1440 → 1546×423 chính giữa (điện thoại cắt tới đó)
  //   Facebook cover    → điện thoại cắt hai mép, giữ chữ trong 78% ngang / 86% dọc
  //   X header 1500×500 → ảnh đại diện đè lên góc trái dưới, nên chừa mép trái
  const an =
    kind === "banner"   ? { w: Math.min(W * 0.604, 1546 * (W / 2560)), h: 423 * (W / 2560) } :
    kind === "fb_cover" ? { w: W * 0.78, h: H * 0.86 } :
                          { w: W * 0.80, h: H * 0.72 };

  return (
    <AbsoluteFill style={{ background: C.nen, overflow: "hidden" }}>
      <RiaNgoai bo={iBang} S={{ W, H }} T={(H - an.h) / 2} AN_H={an.h} C={C} P={P} motif={motif} />
      <BangBo bo={iBang} S={{ W, H }} AN={an} C={C} P={P} ten={name} tagline={tagline}
              handle={handle} motif={motif} chu={chu} nho={H < 360} />
    </AbsoluteFill>
  );
};
