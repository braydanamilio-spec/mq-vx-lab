// 🎨 MINDLOOP DESIGN SYSTEM — nền tảng "đẹp đỉnh" kiểu Kurzgesagt cho kênh Psychology.
// Mọi cảnh dùng palette + motion helper ở đây => nhất quán, mượt, cao cấp.
import { spring, interpolate, Easing } from "remotion";

export const MIND = {
  bg: "#141229", bg2: "#241B47", bg3: "#2C2455",
  violet: "#8B5CF6", violetLo: "#6D4FD0", violetHi: "#C4B5FD",
  amber: "#FBBF24", amberHi: "#FDE68A",
  text: "#F5F3FF", muted: "#9E93C4",
  ink: "#0C0A1A",
};
export const FONT = "'Poppins','Segoe UI',Arial,sans-serif";

// Nền chuẩn: gradient indigo sâu + lưới mờ + hạt sáng chậm (tĩnh, không rối).
export const bgGradient = `radial-gradient(120% 90% at 50% 18%, ${MIND.bg2} 0%, ${MIND.bg} 62%, ${MIND.ink} 100%)`;

// ---- MOTION helpers (mượt = spring/easing, không tuyến tính cứng) ----
export const sIn = (frame: number, fps: number, delay = 0, damping = 18) =>
  spring({ frame: frame - delay, fps, config: { damping, mass: 0.9, stiffness: 120 } });

// hiện + trượt lên (entrance chuẩn)
export const rise = (frame: number, fps: number, delay = 0, dist = 40) => {
  const p = sIn(frame, fps, delay);
  return { opacity: p, transform: `translateY(${(1 - p) * dist}px)` };
};

// đếm số mượt (ease-out) cho DATA moat
export const countTo = (frame: number, target: number, delay: number, dur: number) => {
  const t = interpolate(frame, [delay, delay + dur], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });
  return target * t;
};

// nhịp thở nhẹ (glow sống) — dùng cho quầng sáng/vòng loop
export const breathe = (frame: number, speed = 26, amp = 0.12) =>
  0.5 + 0.5 * Math.sin(frame / speed) * (amp / 0.5);
