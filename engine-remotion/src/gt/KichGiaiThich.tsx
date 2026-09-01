import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, Img } from "remotion";
import { POSES, live } from "../StickAnim";
import { NguoiQue, QUE_CAO, QUE_GOT, Vai } from "../que/NguoiQue";
import { NenQue } from "../que/NenQue";
import { ChiaDoi, SoLieu, Truc, KinhLup, BieuTuong, DaiChu, Dem, TheChu } from "./Khuon";

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
const F = "Poppins, Arial Black, sans-serif";

export type NhipGT = {
  s: number; e: number;
  khuon: string;               // canh | chia_doi | so_lieu | truc | kinh_lup | nhom | anh
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
  tep?: string;
};

export type PropsGT = {
  nhip?: NhipGT[]; vai?: (Vai & { ten: string; cao: number })[];
  tu?: { t: number; d: number; w: string }[];
  voMp3?: string; nhac?: string; nhacVol?: number;
  tieuDe?: string; handle?: string; mau?: string; mauPhu?: string;
  hook?: string; hookPhu?: string; dai?: number; doc?: boolean;
};

export const calcGT = async ({ props }: { props: PropsGT }) => ({
  durationInFrames: Math.max(90, Math.round((props.dai || 60) * 30)), fps: 30,
});

/* ── PHỤ ĐỀ KARAOKE ───────────────────────────────────────────────────────────────────────
   Từ đang đọc đổi màu. Không phải trang trí: mắt bám được dòng chữ khi tiếng tắt, và đây đúng
   là thứ video tham chiếu thiếu.
   Chỉ hiện CỬA SỔ 7 từ quanh từ đang đọc — hiện cả câu dài thì chữ phải nhỏ lại và mất tác dụng. */
const PhuDe: React.FC<{ tu: any[]; t: number; W: number; H: number; mau: string }> =
({ tu, t, W, H, mau }) => {
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
  const fs = H * 0.042;
  return (
    <div style={{
      position: "absolute", left: 0, right: 0, bottom: H * 0.085,
      display: "flex", justifyContent: "center", pointerEvents: "none",
    }}>
      <div style={{
        display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 0.34em",
        maxWidth: W * 0.86, background: "#12151Ce6", borderRadius: H * 0.018,
        padding: `${H * 0.016}px ${H * 0.028}px`,
        fontFamily: F, fontWeight: 800, fontSize: fs, lineHeight: 1.22,
        textAlign: "center",
      }}>
        {cua.map((w, k) => (
          <span key={k} style={{ color: a + k === i ? mau : "#FFFFFF" }}>{w.w}</span>
        ))}
      </div>
    </div>
  );
};

export const KichGiaiThich: React.FC<PropsGT> = ({
  nhip = [], vai = [], tu = [], voMp3 = "", nhac = "", nhacVol = 0.13,
  tieuDe = "", handle = "", mau = "#E0533D", mauPhu = "#2F7D6B",
  hook = "", hookPhu = "", doc = false,
}) => {
  const frame = useCurrentFrame();
  const { fps, width: W, height: H } = useVideoConfig();
  const t = frame / fps;

  const N = nhip.find((x) => t >= x.s && t < x.e) || nhip[nhip.length - 1];
  if (!N) return <AbsoluteFill style={{ background: "#F3EEE4" }} />;
  const p = kep((t - N.s) / Math.max(0.4, N.e - N.s));      // 0..1 trong nhịp
  const vao = kep((t - N.s) / 0.22);                        // 0..1 lúc vừa cắt vào

  const SAN = 0.66, sanY = H * SAN, NGUOI = H * (doc ? 0.38 : 0.46);
  const dangNoi = tu.some((w) => t >= w.t - 0.02 && t < w.t + w.d + 0.05);
  const mo = dangNoi ? 0.35 + 0.45 * Math.abs(Math.sin(t * 21)) : 0;
  const blink = Math.sin(t * 2.6) > 0.93 ? 0.12 : 1;
  const V = vai[0] || ({ gioi: "nam", tuoi: "trung", toc: "bu", mauToc: "#5A3E28",
    ao: "#8A6A46", quan: "#6E5A3E", pk: [], cao: 1, ten: "" } as any);

  /* Nền: ưu tiên ảnh AI vẽ ĐÚNG THEO LỜI của nhịp này (anh dặn), không có thì `NenQue` vẽ
     bằng code. Hai tầng, tầng dưới không bao giờ hỏng vì không gọi mạng. */
  const Nen = (
    <>
      {N.nenAnh ? (
        <Img src={staticFile(N.nenAnh)}
             style={{ position: "absolute", inset: 0, width: W, height: H, objectFit: "cover" }} />
      ) : N.noi ? (
        <NenQue noi={N.noi} W={W} H={H} san={sanY} nguoi={NGUOI} t={t} />
      ) : (
        /* NƠI CHỐN RỖNG = câu này TRỪU TƯỢNG (nói về con số, về vũ trụ, về ý niệm).
           Dựng nền trơn có đường chân trời, không dựng phòng ốc. Bản đầu mặc định về
           "phong_khach", nên một câu về tốc độ ánh sáng lại diễn trong phòng khách có sofa —
           nền ấy nói một điều SAI về nội dung câu, tệ hơn hẳn nền trống. */
        <AbsoluteFill>
          <div style={{ position: "absolute", inset: 0,
                        background: "linear-gradient(180deg,#EDE6D8,#DCD2BE)" }} />
          <div style={{ position: "absolute", left: 0, right: 0, top: sanY,
                        height: H - sanY, background: "#CDBE9F" }} />
          <div style={{ position: "absolute", left: 0, right: 0, top: sanY,
                        height: Math.max(3, H * 0.004), background: "#00000022" }} />
        </AbsoluteFill>
      )}
    </>
  );

  const NguoiChinh = (dx: number, sc: number, ph: number) => {
    const co = (NGUOI * V.cao * sc) / QUE_CAO;
    const tuThe = live(POSES[(N.pose as string) || "idle"] || POSES.idle, t + ph, mo);
    return (
      <g>
        <ellipse cx={W * dx} cy={sanY + 4} rx={NGUOI * 0.15 * sc} ry={NGUOI * 0.026}
                 fill="#0A0C10" opacity={0.15} />
        <NguoiQue x={W * dx} y={sanY - QUE_GOT * co} scale={co} pose={tuThe} vai={V as any}
                  mouthOpen={mo} expr={N.expr || "neutral"} blink={blink} />
      </g>
    );
  };

  const than = () => {
    switch (N.khuon) {
      case "chia_doi":
        return { nen: <AbsoluteFill style={{ background: "#F6F1E6" }} />,
                 lop: <ChiaDoi W={W} H={H * 0.80} trai={N.trai || {}} phai={N.phai || {}} mau={mau} p={p} /> };
      case "so_lieu":
        return { nen: Nen,
                 lop: <g>
                   <SoLieu W={W} H={H * 0.80} so={N.so || ""} don={N.don || ""} chu={N.chu || ""}
                           bt={N.bt || ""} mau={mau} p={p} />
                   {N.dai_chu ? <DaiChu W={W} H={H * 0.80} chu={N.dai_chu} p={p} /> : null}
                 </g> };
      case "truc":
        return { nen: <AbsoluteFill style={{ background: "#F6F1E6" }} />,
                 lop: <Truc W={W} H={H * 0.80} moc={N.moc || []} vt={N.vt ?? -1} mau={mau} p={p} /> };
      case "kinh_lup":
        return { nen: Nen,
                 lop: <KinhLup W={W} H={H * 0.80} x={W * (N.x ?? 0.34)} y={H * 0.80 * (N.y ?? 0.5)}
                               nhan={N.nhan || ""} mau={mau} p={p}
                               con={NguoiChinh(0.34, 1, 0)} /> };
      case "nhom": {
        const n = Math.max(2, Math.min(5, N.n || 4));
        const cho = Array.from({ length: n }, (_, i) => 0.5 + (i - (n - 1) / 2) * (0.92 / n));
        return { nen: Nen, lop: <g>{cho.map((c, i) => (
          <g key={i}>{NguoiChinh(c, i % 2 ? 0.94 : 1, i * 0.83)}</g>))}</g> };
      }
      case "dem":
        return { nen: Nen,
                 lop: <g>{NguoiChinh(0.5, 1, 0)}
                        <Dem W={W} H={H * 0.80} n={N.n || 4} ngay={N.ngay !== false}
                             chu={N.chu || ""} p={p} mau={mau} /></g> };
      case "the_chu":
        return { nen: <AbsoluteFill style={{ background: "#EFE7D6" }} />,
                 lop: <TheChu W={W} H={H * 0.80} chu={N.the || N.loi} p={p} mau={mau} /> };
      case "anh":
        return { nen: N.tep ? (
          <Img src={staticFile(N.tep)} style={{ position: "absolute", inset: 0, width: W, height: H,
                objectFit: "cover", transform: `scale(${1.04 + p * 0.05})` }} />
        ) : Nen, lop: null };
      default: {
        /* QUY TẮC D — CẢNH SAU KẾ THỪA CẢNH TRƯỚC.
           Bằng chứng: vệt dấu chân của nhân vật DÀI THÊM RA qua từng cảnh trong cùng một mạch.
           Không phải trang trí — nó là thứ nói "vẫn là chuyến đi ấy, chỉ muộn hơn". Cắt rời
           từng cảnh thì mỗi cảnh là một lần bắt đầu lại, và cả đoạn mất mạch.
           `ke_thua` = cảnh thứ mấy trong mạch; vệt dài theo đúng con số ấy. */
        const b = N.ke_thua || 0;
        return { nen: Nen, lop: (
          <g>
            {b > 0 ? (
              <g opacity={0.5}>
                {Array.from({ length: Math.min(14, b * 3) }).map((_, i) => {
                  const fx = 0.46 - i * 0.035;
                  return <ellipse key={i} cx={W * fx} cy={sanY + H * 0.012 + (i % 2) * H * 0.008}
                                  rx={W * 0.008} ry={H * 0.004} fill="#4A3F33"
                                  opacity={1 - i / 15} />;
                })}
              </g>
            ) : null}
            {NguoiChinh(0.5, 1, 0)}
            {N.dai_chu ? <DaiChu W={W} H={H * 0.80} chu={N.dai_chu} p={p} /> : null}
          </g>) };
      }
    }
  };
  const { nen, lop } = than();

  return (
    <AbsoluteFill style={{ background: "#F3EEE4", overflow: "hidden" }}>
      {/* Vào cảnh: đẩy nhẹ + hiện dần trong 0,22 giây. Ở nhịp 2,1 giây thì chuyển cảnh dài hơn
          thế là ăn mất một phần tư thời lượng của chính cảnh ấy. */}
      <AbsoluteFill style={{ opacity: 0.35 + 0.65 * vao, transform: `scale(${1.02 - vao * 0.02})` }}>
        {nen}
        {lop ? (
          <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
            {lop}
          </svg>
        ) : null}
      </AbsoluteFill>

      {/* HOOK — ba giây đầu. Video tham chiếu mở bằng một so sánh mà người xem đang ĐỨNG TRONG
          ĐÓ ("YOU | HIM"). Mình giữ đúng thiết bị ấy nhưng thêm con số, vì con số cho người xem
          một lý do cụ thể để ở lại chứ không chỉ một cảm giác tò mò. */}
      {hook && t < 3.0 ? (
        <div style={{
          position: "absolute", left: 0, right: 0, top: H * 0.055,
          display: "flex", flexDirection: "column", alignItems: "center", gap: H * 0.012,
          pointerEvents: "none", opacity: kep((3.0 - t) / 0.35),
        }}>
          <div style={{
            background: mau, border: `${H * 0.006}px solid #12151C`, borderRadius: H * 0.012,
            padding: `${H * 0.018}px ${H * 0.030}px`, maxWidth: W * 0.88, textAlign: "center",
            boxShadow: `${H * 0.008}px ${H * 0.009}px 0 #12151C`,
            transform: `scale(${1 + (1 - kep(t / 0.22)) * 0.10}) rotate(${-1.2 + kep(t / 0.3) * 1.2}deg)`,
            fontFamily: F, fontWeight: 900, fontSize: H * 0.062, lineHeight: 1.06, color: "#FFFFFF",
          }}>{hook}</div>
          {hookPhu ? (
            <div style={{
              background: "#12151C", borderRadius: H * 0.010, padding: `${H * 0.010}px ${H * 0.022}px`,
              fontFamily: F, fontWeight: 800, fontSize: H * 0.036, color: "#FFFFFF", letterSpacing: 1.5,
              opacity: kep((t - 0.5) / 0.3),
            }}>{hookPhu}</div>
          ) : null}
        </div>
      ) : null}

      <PhuDe tu={tu} t={t} W={W} H={H} mau={mau} />

      <div style={{
        position: "absolute", left: 0, right: 0, bottom: 0, height: H * 0.048,
        background: "#12151C", display: "flex", alignItems: "center",
        justifyContent: "space-between", padding: `0 ${W * 0.025}px`,
        fontFamily: "Poppins, Arial, sans-serif", fontWeight: 800,
        fontSize: H * 0.020, color: "#FFFFFF", letterSpacing: 1.6,
      }}>
        <span>{tieuDe}</span><span style={{ color: mau }}>{handle}</span>
      </div>

      {voMp3 ? <Audio src={staticFile(voMp3)} /> : null}
      {nhac ? <Audio src={staticFile(nhac)} loop volume={nhacVol} /> : null}
    </AbsoluteFill>
  );
};
