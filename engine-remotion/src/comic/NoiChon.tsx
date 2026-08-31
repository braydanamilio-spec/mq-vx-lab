import React from "react";
import { MO_DUN, MO_MY, MO_TREO, TEN_MO_TREO, nhat, ThamSo } from "./MoDun";

// ══════════════════════════════════════════════════════════════════════════════════════════
// NƠI CHỐN — mười nơi cho mỗi kênh, mỗi nơi là MỘT DÒNG dữ liệu
// ------------------------------------------------------------------------------------------
// Nhân với ba góc nhìn (máy dịch trái / giữa / phải, xem `NenComic`) là ba mươi khung khác nhau
// cho mỗi kênh — đủ để chạy hàng trăm tập mà không tập nào đứng ở đúng chỗ tập trước.
//
// Vị trí `x` tính theo tỉ lệ bề ngang. Hai nhân vật đứng ở 28% và 72%, nên đồ đạc phải nằm
// ngoài hai vùng ấy: mép trái (0.04–0.20), mép phải (0.80–0.96), hoặc chính giữa (0.46–0.54)
// nếu là vật thấp. Đây là ràng buộc DUY NHẤT khi thêm nơi mới — mọi thứ còn lại đã do mô-đun
// tự lo (chạm sàn, co theo khung, nét mực đúng độ dày).
// ══════════════════════════════════════════════════════════════════════════════════════════

// ══ MỘT MẶT SÀN DUY NHẤT CHO CẢ KHUNG ═══════════════════════════════════════════════════
// 31/8 — Anh: *"bối cảnh nhảy, nhiều khi ghép vào nhân vật thấy nó lơ lửng giữa, cần có rule
// gì đó để ko cảnh nào lỗi"*. Đo ra ngay: ba nơi đặt "mặt sàn" bằng ba con số khác nhau —
// nhân vật đứng ở 0,95·h, sàn của nền ở 0,93·h, đạo cụ cũng 0,93·h. Lệch 36 pixel, và 36 pixel
// là đủ để mắt đọc ra "cái điện thoại đang bay".
//
// Rule không phải là "nhớ chỉnh cho khớp" — nhớ thì sẽ quên, và đã quên ba lần rồi. Rule là
// KHÔNG CÒN CHỖ NÀO ĐƯỢC TỰ ĐẶT SỐ: chỉ có một hằng ở đây, mọi thứ đứng trên mặt đất đều
// import nó về. Muốn đổi mức sàn thì đổi một chỗ, và không thể đổi lệch nhau nữa.
export const SAN = 0.95;

// Vật CAO (chiếm hơn 40% chiều cao sân khấu) thì phần trên của nó nằm trên đầu nhân vật, nên
// đặt GIỮA khung vẫn đọc ra được — và giữa là chỗ duy nhất đủ rộng cho một vật lớn. Vật THẤP
// thì ngược lại: đặt giữa là bị che sạch, phải ra mép mới thấy trọn.
// Phép đo dẫn tới quy tắc này: khung dọc 992px, hai nhân vật chiếm 153–403 và 589–839, nên
// khoảng trống lớn nhất chỉ 186px — không chỗ nào chứa nổi một vật rộng 758px.
const VAT_CAO = new Set([
  "tu_lanh", "ke_sach", "tu_ho_so", "cua_ra_vao", "guong", "gia_treo", "cua_so",
  "cua_luoi", "cua_cuon", "gia_ta", "may_nuoc",
]);

export type Manh = {
  m: string; x: number; co?: number; treo?: boolean;
  // ── BA LỚP CHIỀU SÂU (2,5D) ──────────────────────────────────────────────────────────
  // 31/8 — Anh hỏi có nên chuyển 3D. Không: GitHub Actions không có GPU, nên render 3D bằng
  // CPU chậm gấp hàng chục lần, và chuyển 3D là vứt cả hệ mô-đun vẽ-bằng-code này. Nhưng cái
  // anh thấy thiếu — chiều sâu — thì có cách rẻ hơn nhiều: chia nền làm BA LỚP.
  //   xa   — nhỏ hơn, nhạt hơn, đứng cao hơn trên khung (phối cảnh: xa thì lên cao)
  //   giữa — mặc định, cùng mặt sàn với nhân vật
  //   gần  — to hơn, đậm hơn, vẽ SAU nhân vật nên che một phần và bị mép khung cắt
  // Ba lớp cộng bóng đổ cùng một hướng cho ra phần lớn cảm giác chiều sâu của 3D, mà vẫn là
  // hình vẽ phẳng — không model, không ánh sáng, không có gì để hỏng.
  lop?: "xa" | "gan";
  // Vật CHỦ ĐẠO: anh nói *"nhiều bối cảnh nhìn còn lộn xộn, chưa nhận ra được bối cảnh gì"*.
  // Nguyên nhân là mỗi nơi chỉ có ba bốn vật cỡ ngang nhau — không vật nào đủ lớn để tuyên bố
  // đây là chỗ nào. Mỗi nơi từ nay có ĐÚNG MỘT vật chủ đạo, to gấp rưỡi, đặt sát mép.
  chu?: boolean;
};
export type Noi = {
  ten: string;              // nhãn tiếng Anh — bộ sinh kịch bản chọn theo nhãn này
  mo: Manh[];
  san?: string;             // màu sàn riêng (mặc định: pha từ màu kênh)
  yS?: number;              // mức sàn theo tỉ lệ chiều cao sân khấu
  ngoai?: boolean;          // ngoài trời -> phần trên là trời, không phải trần
};

export const NOI: Record<string, Noi[]> = {
  tech: [
    { ten: "the IT help desk", mo: [{ m: "ban", x: 0.1, chu: true }, { m: "may_tinh", x: 0.14, co: 0.9 }, { m: "tu_ho_so", x: 0.88, lop: "xa" }] },
    { ten: "a server room", mo: [{ m: "tu_ho_so", x: 0.5, chu: true }, { m: "tu_ho_so", x: 0.9, co: 1.1 }, { m: "bang_hieu", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the customer's living room", mo: [{ m: "sofa", x: 0.9, chu: true }, { m: "tv", x: 0.12 }, { m: "cay", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the office reception", mo: [{ m: "quay", x: 0.1, chu: true }, { m: "ghe", x: 0.88 }, { m: "cay", x: 0.5, co: 0.8, lop: "xa" }] },
    { ten: "a cramped supply closet", mo: [{ m: "ke_sach", x: 0.5, chu: true }, { m: "thung", x: 0.88 }, { m: "thung", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the break room", mo: [{ m: "may_ca_phe", x: 0.1, chu: true }, { m: "ban", x: 0.86, co: 0.9 }, { m: "bang_ghim", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "a meeting room", mo: [{ m: "ban_dai", x: 0.9, co: 0.8, chu: true }, { m: "cua_so", x: 0.88 }, { m: "bang_ghim", x: 0.1, lop: "xa" }] },
    { ten: "the home office", mo: [{ m: "ban", x: 0.9, chu: true }, { m: "may_tinh", x: 0.86, co: 0.85 }, { m: "ke_sach", x: 0.1, lop: "xa" }] },
    { ten: "the office hallway", mo: [{ m: "cua_ra_vao", x: 0.5, chu: true }, { m: "bang_ghim", x: 0.88 }, { m: "cay", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "a phone repair counter", mo: [{ m: "quay", x: 0.9, co: 0.8, chu: true }, { m: "gia_treo", x: 0.12 }, { m: "bang_hieu", x: 0.86, co: 0.8, lop: "xa" }] },
  ],
  rent: [
    { ten: "the apartment hallway", mo: [{ m: "cua_ra_vao", x: 0.5, chu: true }, { m: "cua_ra_vao", x: 0.9, co: 0.9 }, { m: "cay", x: 0.5, co: 0.6, lop: "xa" }] },
    { ten: "the mailbox lobby", mo: [{ m: "ke_sach", x: 0.5, co: 0.8, chu: true }, { m: "bang_ghim", x: 0.88 }, { m: "thung", x: 0.5, co: 0.6, lop: "xa" }] },
    { ten: "an empty apartment", mo: [{ m: "cua_so", x: 0.5, chu: true }, { m: "thung", x: 0.86 }, { m: "thung", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the building manager's office", mo: [{ m: "ban", x: 0.1, chu: true }, { m: "tu_ho_so", x: 0.88 }, { m: "bang_ghim", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the shared laundry room", mo: [{ m: "tu_lanh", x: 0.5, co: 0.9, chu: true }, { m: "ban", x: 0.88, co: 0.8 }, { m: "thung", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the stairwell", mo: [{ m: "cua_ra_vao", x: 0.5, chu: true }, { m: "bang_hieu", x: 0.12, co: 0.7 }] },
    { ten: "the back courtyard", mo: [{ m: "hang_rao", x: 0.9, co: 0.9, chu: true }, { m: "cay", x: 0.1 }, { m: "thung", x: 0.9, co: 0.7, lop: "xa" }], ngoai: true, san: "#8FBF6A" },
    { ten: "the parking lot", mo: [{ m: "xe", x: 0.1, co: 0.8, chu: true }, { m: "bang_hieu", x: 0.88, co: 0.8 }], ngoai: true, san: "#8C8C94" },
    { ten: "a small living room", mo: [{ m: "sofa", x: 0.9, chu: true }, { m: "cua_so", x: 0.12 }, { m: "tv", x: 0.5, co: 0.6, lop: "xa" }] },
    { ten: "the front door of the unit", mo: [{ m: "cua_ra_vao", x: 0.5, co: 0.9, chu: true }, { m: "cay", x: 0.1, co: 0.8 }, { m: "thung", x: 0.9, co: 0.6, lop: "xa" }] },
  ],
  gym: [
    { ten: "the weight floor", mo: [{ m: "gia_ta", x: 0.5, chu: true }, { m: "guong", x: 0.88 }], san: "#8A8A93" },
    { ten: "the cardio row", mo: [{ m: "ban_dai", x: 0.9, co: 0.7, chu: true }, { m: "guong", x: 0.1 }, { m: "cay", x: 0.9, co: 0.7, lop: "xa" }], san: "#8A8A93" },
    { ten: "the locker room", mo: [{ m: "tu_ho_so", x: 0.5, chu: true }, { m: "tu_ho_so", x: 0.9 }, { m: "ghe", x: 0.5, co: 0.8, lop: "xa" }] },
    { ten: "the gym front desk", mo: [{ m: "quay", x: 0.1, chu: true }, { m: "bang_hieu", x: 0.86 }, { m: "cay", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the stretching corner", mo: [{ m: "guong", x: 0.5, chu: true }, { m: "gia_ta", x: 0.88, co: 0.8 }], san: "#8A8A93" },
    { ten: "the smoothie bar", mo: [{ m: "quay", x: 0.9, co: 0.8, chu: true }, { m: "may_ca_phe", x: 0.12 }, { m: "ghe", x: 0.88, co: 0.8, lop: "xa" }] },
    { ten: "the equipment storage", mo: [{ m: "ke_sach", x: 0.5, chu: true }, { m: "thung", x: 0.9 }, { m: "gia_ta", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the yoga studio", mo: [{ m: "guong", x: 0.5, chu: true }, { m: "cua_so", x: 0.12 }] },
    { ten: "the gym parking lot", mo: [{ m: "xe", x: 0.1, co: 0.8, chu: true }, { m: "bang_hieu", x: 0.86, co: 0.8 }], ngoai: true, san: "#8C8C94" },
    { ten: "a personal training room", mo: [{ m: "gia_ta", x: 0.5, co: 0.9, chu: true }, { m: "ban", x: 0.9, co: 0.8 }, { m: "guong", x: 0.5, co: 0.7, lop: "xa" }] },
  ],
  airport: [
    { ten: "the check-in counter", mo: [{ m: "quay", x: 0.9, co: 0.9, chu: true }, { m: "bang_hieu", x: 0.12 }, { m: "gia_treo", x: 0.9, co: 0.8, lop: "xa" }] },
    { ten: "the departure gate", mo: [{ m: "ghe", x: 0.1, chu: true }, { m: "ghe", x: 0.9 }, { m: "bang_hieu", x: 0.5, co: 0.9, lop: "xa" }] },
    { ten: "baggage claim", mo: [{ m: "ban_dai", x: 0.9, co: 0.9, chu: true }, { m: "thung", x: 0.12 }, { m: "thung", x: 0.88, co: 0.8, lop: "xa" }] },
    { ten: "the security line", mo: [{ m: "ban", x: 0.1, chu: true }, { m: "hang_rao", x: 0.86, co: 0.7 }, { m: "bang_hieu", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "an airport coffee stand", mo: [{ m: "may_ca_phe", x: 0.1, chu: true }, { m: "quay", x: 0.86, co: 0.8 }, { m: "ghe", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the moving walkway", mo: [{ m: "ban_dai", x: 0.9, co: 0.8, chu: true }, { m: "cua_so", x: 0.1 }, { m: "cua_so", x: 0.9, lop: "xa" }] },
    { ten: "the rebooking desk", mo: [{ m: "quay", x: 0.1, chu: true }, { m: "may_tinh", x: 0.14, co: 0.8 }, { m: "bang_hieu", x: 0.86, lop: "xa" }] },
    { ten: "the airline lounge", mo: [{ m: "sofa", x: 0.9, chu: true }, { m: "cay", x: 0.12 }, { m: "ban", x: 0.5, co: 0.6, lop: "xa" }] },
    { ten: "the jet bridge door", mo: [{ m: "cua_ra_vao", x: 0.5, chu: true }, { m: "bang_hieu", x: 0.12, co: 0.8 }, { m: "ghe", x: 0.9, co: 0.7, lop: "xa" }] },
    { ten: "the information desk", mo: [{ m: "quay", x: 0.9, co: 0.8, chu: true }, { m: "bang_ghim", x: 0.1 }, { m: "cay", x: 0.9, co: 0.8, lop: "xa" }] },
  ],
  car: [
    { ten: "the repair bay", mo: [{ m: "xe", x: 0.1, chu: true }, { m: "gia_treo", x: 0.9 }], san: "#7C7C84" },
    { ten: "the service counter", mo: [{ m: "quay", x: 0.1, chu: true }, { m: "may_tinh", x: 0.14, co: 0.8 }, { m: "bang_hieu", x: 0.86, lop: "xa" }] },
    { ten: "the parts room", mo: [{ m: "ke_sach", x: 0.5, chu: true }, { m: "ke_sach", x: 0.9 }, { m: "thung", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the waiting area", mo: [{ m: "ghe", x: 0.1, chu: true }, { m: "may_ca_phe", x: 0.9, co: 0.8 }, { m: "ban", x: 0.5, co: 0.6, lop: "xa" }] },
    { ten: "the car lift", mo: [{ m: "xe", x: 0.9, co: 0.9, chu: true }, { m: "gia_treo", x: 0.1 }, { m: "thung", x: 0.9, co: 0.7, lop: "xa" }], san: "#7C7C84" },
    { ten: "the front lot", mo: [{ m: "xe", x: 0.9, co: 0.8, chu: true }, { m: "bang_hieu", x: 0.12 }], ngoai: true, san: "#8C8C94" },
    { ten: "the tire wall", mo: [{ m: "ke_sach", x: 0.5, chu: true }, { m: "gia_treo", x: 0.12 }], san: "#7C7C84" },
    { ten: "the garage office", mo: [{ m: "ban", x: 0.1, chu: true }, { m: "tu_ho_so", x: 0.88 }, { m: "bang_ghim", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the wash bay", mo: [{ m: "xe", x: 0.9, co: 0.85, chu: true }, { m: "gia_treo", x: 0.9, co: 0.8 }], san: "#7C7C84" },
    { ten: "the customer driveway", mo: [{ m: "xe", x: 0.1, co: 0.8, chu: true }, { m: "hang_rao", x: 0.86, co: 0.7 }], ngoai: true, san: "#8FBF6A" },
  ],
  office: [
    { ten: "the cubicle row", mo: [{ m: "ban", x: 0.1, chu: true }, { m: "may_tinh", x: 0.12, co: 0.8 }, { m: "bang_ghim", x: 0.88, lop: "xa" }] },
    { ten: "the coffee machine", mo: [{ m: "may_ca_phe", x: 0.1, chu: true }, { m: "tu_bep", x: 0.86, co: 0.8 }] },
    { ten: "the meeting room", mo: [{ m: "ban_dai", x: 0.9, co: 0.8, chu: true }, { m: "cua_so", x: 0.9 }, { m: "bang_ghim", x: 0.1, lop: "xa" }] },
    { ten: "the elevator lobby", mo: [{ m: "cua_ra_vao", x: 0.5, chu: true }, { m: "cua_ra_vao", x: 0.9 }, { m: "cay", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the copy room", mo: [{ m: "ban", x: 0.9, co: 0.9, chu: true }, { m: "thung", x: 0.12 }, { m: "ke_sach", x: 0.5, co: 0.6, lop: "xa" }] },
    { ten: "the reception desk", mo: [{ m: "quay", x: 0.9, co: 0.85, chu: true }, { m: "cay", x: 0.1 }, { m: "ghe", x: 0.9, co: 0.8, lop: "xa" }] },
    { ten: "the break room", mo: [{ m: "tu_lanh", x: 0.5, co: 0.9, chu: true }, { m: "ban", x: 0.12, co: 0.9 }, { m: "may_ca_phe", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the boss's office", mo: [{ m: "ban", x: 0.9, co: 0.9, chu: true }, { m: "ke_sach", x: 0.1 }, { m: "cua_so", x: 0.9, lop: "xa" }] },
    { ten: "the open floor", mo: [{ m: "ban_dai", x: 0.9, co: 0.9, chu: true }, { m: "cay", x: 0.1 }, { m: "cay", x: 0.9, co: 0.8, lop: "xa" }] },
    { ten: "the office kitchen", mo: [{ m: "tu_bep", x: 0.9, co: 0.9, chu: true }, { m: "tu_lanh", x: 0.1, co: 0.9 }, { m: "may_ca_phe", x: 0.9, co: 0.8, lop: "xa" }] },
  ],
  diet: [
    { ten: "the kitchen", mo: [{ m: "tu_lanh", x: 0.5, chu: true }, { m: "tu_bep", x: 0.14, co: 0.9 }] },
    { ten: "in front of the open fridge", mo: [{ m: "tu_lanh", x: 0.5, co: 1.05, chu: true }, { m: "tu_bep", x: 0.1, co: 0.8 }] },
    { ten: "the dinner table", mo: [{ m: "ban", x: 0.9, co: 0.9, chu: true }, { m: "ghe", x: 0.12 }, { m: "ghe", x: 0.88, lop: "xa" }] },
    { ten: "a grocery aisle", mo: [{ m: "ke_sach", x: 0.5, co: 1.1, chu: true }, { m: "ke_sach", x: 0.9, co: 1.1 }] },
    { ten: "the kitchen island", mo: [{ m: "tu_bep", x: 0.9, chu: true }, { m: "tu_lanh", x: 0.9, co: 0.9 }, { m: "may_ca_phe", x: 0.1, co: 0.8, lop: "xa" }] },
    { ten: "the living room couch", mo: [{ m: "sofa", x: 0.9, chu: true }, { m: "tv", x: 0.12 }] },
    { ten: "the backyard grill", mo: [{ m: "ban", x: 0.1, co: 0.9, chu: true }, { m: "hang_rao", x: 0.86, co: 0.8 }, { m: "cay", x: 0.5, co: 0.7, lop: "xa" }], ngoai: true, san: "#8FBF6A" },
    { ten: "a coffee shop table", mo: [{ m: "ban", x: 0.9, co: 0.75, chu: true }, { m: "quay", x: 0.1, co: 0.8 }, { m: "cay", x: 0.9, co: 0.8, lop: "xa" }] },
    { ten: "the snack cupboard", mo: [{ m: "tu_bep", x: 0.9, co: 1.0, chu: true }, { m: "ke_sach", x: 0.1, co: 0.9 }] },
    { ten: "the bathroom scale", mo: [{ m: "guong", x: 0.5, chu: true }, { m: "tu_bep", x: 0.12, co: 0.7 }] },
  ],
  parent: [
    { ten: "the living room", mo: [{ m: "sofa", x: 0.9, chu: true }, { m: "tv", x: 0.12 }, { m: "thung", x: 0.5, co: 0.55, lop: "xa" }] },
    { ten: "the kid's bedroom", mo: [{ m: "giuong", x: 0.9, chu: true }, { m: "ke_sach", x: 0.1 }, { m: "thung", x: 0.5, co: 0.6, lop: "xa" }] },
    { ten: "the kitchen table", mo: [{ m: "ban", x: 0.9, co: 0.9, chu: true }, { m: "tu_lanh", x: 0.9, co: 0.9 }, { m: "ghe", x: 0.1, co: 0.9, lop: "xa" }] },
    { ten: "the homework desk", mo: [{ m: "ban", x: 0.1, chu: true }, { m: "ke_sach", x: 0.88 }, { m: "ghe", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the backyard", mo: [{ m: "hang_rao", x: 0.9, co: 0.9, chu: true }, { m: "cay", x: 0.1 }, { m: "thung", x: 0.9, co: 0.6, lop: "xa" }], ngoai: true, san: "#8FBF6A" },
    { ten: "the car back seat", mo: [{ m: "ghe", x: 0.1, co: 1.1, chu: true }, { m: "ghe", x: 0.86, co: 1.1 }] },
    { ten: "a toy store aisle", mo: [{ m: "ke_sach", x: 0.5, co: 1.1, chu: true }, { m: "ke_sach", x: 0.9, co: 1.1 }, { m: "thung", x: 0.5, co: 0.6, lop: "xa" }] },
    { ten: "the laundry room", mo: [{ m: "tu_lanh", x: 0.5, co: 0.9, chu: true }, { m: "thung", x: 0.88 }, { m: "gia_treo", x: 0.5, co: 0.7, lop: "xa" }] },
    { ten: "the front hallway", mo: [{ m: "cua_ra_vao", x: 0.5, chu: true }, { m: "gia_treo", x: 0.1 }, { m: "thung", x: 0.9, co: 0.6, lop: "xa" }] },
    { ten: "the playroom floor", mo: [{ m: "thung", x: 0.1, chu: true }, { m: "thung", x: 0.88, co: 0.8 }, { m: "tv", x: 0.5, co: 0.6, lop: "xa" }] },
  ],
  neighbor: [
    { ten: "over the front fence", mo: [{ m: "hang_rao", x: 0.9, chu: true }, { m: "cay", x: 0.1 }, { m: "cay", x: 0.9, co: 0.8, lop: "xa" }], ngoai: true, san: "#8FBF6A" },
    { ten: "by the mailboxes", mo: [{ m: "gia_treo", x: 0.5, co: 0.8, chu: true }, { m: "hang_rao", x: 0.86, co: 0.8 }], ngoai: true, san: "#8FBF6A" },
    { ten: "the front porch", mo: [{ m: "cua_ra_vao", x: 0.5, chu: true }, { m: "ghe", x: 0.88 }, { m: "cay", x: 0.5, co: 0.7, lop: "xa" }], ngoai: true },
    { ten: "the shared driveway", mo: [{ m: "xe", x: 0.9, co: 0.8, chu: true }, { m: "hang_rao", x: 0.12, co: 0.7 }], ngoai: true, san: "#8C8C94" },
    { ten: "the open garage", mo: [{ m: "gia_treo", x: 0.5, chu: true }, { m: "thung", x: 0.9 }, { m: "xe", x: 0.5, co: 0.7, lop: "xa" }], san: "#7C7C84" },
    { ten: "the sidewalk", mo: [{ m: "cay", x: 0.1, chu: true }, { m: "hang_rao", x: 0.86, co: 0.8 }], ngoai: true, san: "#9A9A9E" },
    { ten: "the back garden", mo: [{ m: "cay", x: 0.1, chu: true }, { m: "cay", x: 0.9 }, { m: "thung", x: 0.5, co: 0.6, lop: "xa" }], ngoai: true, san: "#8FBF6A" },
    { ten: "the trash bins", mo: [{ m: "thung", x: 0.1, co: 1.2, chu: true }, { m: "thung", x: 0.86, co: 1.1 }], ngoai: true, san: "#9A9A9E" },
    { ten: "the front door", mo: [{ m: "cua_ra_vao", x: 0.5, chu: true }, { m: "cay", x: 0.1, co: 0.8 }, { m: "thung", x: 0.9, co: 0.6, lop: "xa" }] },
    { ten: "the neighborhood watch table", mo: [{ m: "ban", x: 0.9, co: 0.85, chu: true }, { m: "bang_hieu", x: 0.12 }, { m: "ghe", x: 0.88, co: 0.8, lop: "xa" }], ngoai: true, san: "#8FBF6A" },
  ],
  dating: [
    { ten: "a coffee shop", mo: [{ m: "ban", x: 0.9, co: 0.75, chu: true }, { m: "quay", x: 0.1, co: 0.85 }, { m: "cay", x: 0.9, co: 0.8, lop: "xa" }] },
    { ten: "a restaurant table", mo: [{ m: "ban", x: 0.9, co: 0.85, chu: true }, { m: "ghe", x: 0.1 }, { m: "ghe", x: 0.9, lop: "xa" }] },
    { ten: "a park bench", mo: [{ m: "ghe", x: 0.9, co: 1.1, chu: true }, { m: "cay", x: 0.1 }, { m: "cay", x: 0.9, co: 0.8, lop: "xa" }], ngoai: true, san: "#8FBF6A" },
    { ten: "the bar counter", mo: [{ m: "quay", x: 0.9, co: 0.9, chu: true }, { m: "gia_treo", x: 0.1, co: 0.8 }, { m: "may_ca_phe", x: 0.9, co: 0.8, lop: "xa" }] },
    { ten: "her living room", mo: [{ m: "sofa", x: 0.9, chu: true }, { m: "tv", x: 0.12 }, { m: "cay", x: 0.5, co: 0.6, lop: "xa" }] },
    { ten: "the car front seats", mo: [{ m: "ghe", x: 0.1, co: 1.1, chu: true }, { m: "ghe", x: 0.86, co: 1.1 }] },
    { ten: "a movie theater lobby", mo: [{ m: "quay", x: 0.1, chu: true }, { m: "bang_hieu", x: 0.88 }, { m: "thung", x: 0.5, co: 0.6, lop: "xa" }] },
    { ten: "a grocery checkout", mo: [{ m: "quay", x: 0.9, co: 0.85, chu: true }, { m: "ke_sach", x: 0.1, co: 1.0 }, { m: "thung", x: 0.9, co: 0.7, lop: "xa" }] },
    { ten: "the apartment doorway", mo: [{ m: "cua_ra_vao", x: 0.5, chu: true }, { m: "cay", x: 0.1, co: 0.8 }, { m: "gia_treo", x: 0.9, co: 0.8, lop: "xa" }] },
    { ten: "a rooftop terrace", mo: [{ m: "ban", x: 0.9, co: 0.7, chu: true }, { m: "cay", x: 0.12 }, { m: "hang_rao", x: 0.88, co: 0.7, lop: "xa" }], ngoai: true },
  ],
};

// ══ SINH NƠI CHỐN KHÔNG GIỚI HẠN ═══════════════════════════════════════════════════════
// Anh: *"nếu vẽ bằng mô-đun thì có thể mở rộng lên 50 mỗi channel được ko"* và *"nó có chiếm ổ
// nhiều ko khi có hàng chục channel"* — rồi *"tối ưu a nha"*.
//
// Viết tay 50 nơi cho mỗi kênh là 500 dòng, và mỗi lần thêm kênh lại thêm 50 dòng nữa. Cách
// tối ưu hơn: nơi chốn KHÔNG phải một bảng, mà là một HÀM của (kênh, số tập). Mỗi kênh chỉ khai
// báo bộ mảnh hợp cảnh của mình; tổ hợp ba mảnh trong mười lăm đã cho 455 nơi, nhân ba vị trí
// và ba góc nhìn là con số không bao giờ dùng hết. Tốn 0 byte dữ liệu và không giới hạn 50.
//
// Mười nơi viết tay ở trên vẫn giữ, và vẫn đứng trước: chúng có TÊN đẹp để bộ sinh kịch bản
// chọn ("the server room", "over the front fence"), còn nơi sinh tổ hợp chỉ có tên ghép máy
// móc. Mười tập đầu của mỗi kênh dùng nơi có tên; từ tập mười một trở đi dùng nơi sinh.
// 31/8 — Anh: *"bối cảnh phải vẽ logic đúng, ko vẽ bừa lộn xộn"*. Đây là chỗ dễ vẽ bừa nhất:
// nơi chốn SINH TỔ HỢP (từ tập thứ mười một) bốc mảnh từ danh sách của kênh, và nếu danh sách
// ấy trộn lẫn mọi loại phòng thì sẽ có lúc ra "giường + tủ lạnh + hàng rào" trong một phòng
// server. Ngẫu nhiên trong một túi lẫn lộn thì sớm muộn cũng ra thứ vô lý.
//
// Nên mảnh chia theo NHÓM KHÔNG GIAN, và một nơi chốn chỉ lấy mảnh trong CÙNG nhóm, cộng thêm
// nhóm "trung tính" (ghế, cây, thùng, bảng ghim — thứ có mặt ở đâu cũng hợp lý).
const NHOM: Record<string, string[]> = {
  vanphong: ["ban", "ban_dai", "may_tinh", "tu_ho_so", "bang_ghim", "may_ca_phe", "quay", "tv", "may_nuoc"],
  bep:      ["tu_lanh", "tu_bep", "ban", "ghe", "may_ca_phe", "ke_sach", "lo_vi_song"],
  phongkhach: ["sofa", "tv", "giuong", "ke_sach", "ban", "gia_treo", "cua_so"],
  gara:     ["xe", "gia_treo", "thung", "ke_sach", "quay", "cua_cuon"],
  ngoaitroi: ["hang_rao", "cay", "thung", "xe", "cua_ra_vao", "ghe", "bang_hieu", "hop_thu_tru", "cua_luoi"],
  phongtap: ["gia_ta", "guong", "ghe", "tu_ho_so", "quay", "ban_dai", "may_ca_phe"],
  // Sân bay và quán ăn có bộ đồ đạc riêng, không nhét vừa "văn phòng" hay "phòng khách":
  // sân bay thì hàng ghế nối + biển chỉ dẫn treo; quán thì quầy bar + booth + máy pha.
  sanbay:   ["ghe", "quay", "ban_dai", "bang_hieu", "cua_so", "gia_treo", "thung", "may_ca_phe"],
  quan:     ["ban", "ghe", "quay", "may_ca_phe", "gia_treo", "cay", "ke_sach", "bang_hieu", "booth"],
  trungtinh: ["ghe", "cay", "thung", "bang_ghim", "cua_so", "cua_ra_vao"],
};

/** Nhóm không gian chính của mỗi kênh — nơi sinh tổ hợp chỉ được lấy trong nhóm này. */
const NHOM_KENH: Record<string, string> = {
  tech: "vanphong", office: "vanphong", rent: "phongkhach", gym: "phongtap",
  airport: "sanbay", car: "gara", diet: "bep", parent: "phongkhach",
  neighbor: "ngoaitroi", dating: "quan",
};

const MANH_HOP: Record<string, string[]> = {
  tech:     ["may_nuoc", "ban", "may_tinh", "tu_ho_so", "ke_sach", "ghe", "quay", "cua_so", "bang_ghim",
             "thung", "may_ca_phe", "cay", "sofa", "tv", "cua_ra_vao", "bang_hieu"],
  rent:     ["cua_ra_vao", "cua_so", "ke_sach", "thung", "ban", "ghe", "sofa", "cay", "tv",
             "bang_ghim", "tu_ho_so", "gia_treo", "hang_rao", "guong", "tu_lanh"],
  gym:      ["gia_ta", "guong", "ghe", "quay", "tu_ho_so", "ke_sach", "thung", "cay", "ban",
             "may_ca_phe", "cua_so", "bang_hieu", "gia_treo", "ban_dai", "bang_ghim"],
  airport:  ["ghe", "quay", "ban_dai", "bang_hieu", "thung", "cua_so", "cay", "may_ca_phe",
             "gia_treo", "hang_rao", "cua_ra_vao", "ban", "may_tinh", "sofa", "ke_sach"],
  car:      ["cua_cuon", "xe", "gia_treo", "ke_sach", "thung", "quay", "ghe", "ban", "may_tinh", "bang_hieu",
             "may_ca_phe", "tu_ho_so", "hang_rao", "cay", "bang_ghim", "guong"],
  office:   ["may_nuoc", "ban", "may_tinh", "bang_ghim", "may_ca_phe", "ban_dai", "cua_so", "cay", "ke_sach",
             "quay", "ghe", "tu_lanh", "tu_bep", "cua_ra_vao", "thung", "tu_ho_so"],
  diet:     ["lo_vi_song", "tu_lanh", "tu_bep", "ban", "ghe", "ke_sach", "sofa", "tv", "may_ca_phe", "quay",
             "cay", "guong", "hang_rao", "thung", "cua_so", "giuong"],
  parent:   ["cua_luoi", "sofa", "tv", "giuong", "ke_sach", "ban", "ghe", "thung", "tu_lanh", "cay",
             "gia_treo", "cua_ra_vao", "hang_rao", "tu_bep", "cua_so", "guong"],
  neighbor: ["hop_thu_tru", "cua_luoi", "hang_rao", "cay", "thung", "xe", "cua_ra_vao", "ghe", "ban", "gia_treo",
             "bang_hieu", "ke_sach", "guong", "quay", "tv", "sofa", "cua_so"],
  dating:   ["booth", "ban", "ghe", "quay", "cay", "sofa", "tv", "may_ca_phe", "ke_sach", "thung",
             "bang_hieu", "cua_ra_vao", "gia_treo", "hang_rao", "cua_so", "guong"],
};

// Ba khuôn đặt chỗ. Cả ba đều chừa vùng 0.24–0.76 cho hai nhân vật — ràng buộc bất biến của hệ.
const KHUON: { x: number; co: number }[][] = [
  // Bốn chỗ, không phải hai-ba: nơi sinh tổ hợp trước đây chỉ có hai mảnh ở hai mép, và ở
  // khung dọc thì hai mép là chỗ nhân vật che nhiều nhất — nên nền ra trống dù danh sách mảnh
  // rất dài. Chỗ thứ tư nằm sát mép ngoài, chỗ giữa để vật thấp.
  [{ x: 0.08, co: 1 }, { x: 0.92, co: 0.9 }, { x: 0.5, co: 0.6 }, { x: 0.2, co: 0.75 }],
  [{ x: 0.06, co: 1.05 }, { x: 0.5, co: 0.75 }, { x: 0.94, co: 0.85 }, { x: 0.82, co: 0.7 }],
  [{ x: 0.1, co: 0.95 }, { x: 0.9, co: 1.05 }, { x: 0.26, co: 0.7 }, { x: 0.74, co: 0.68 }],
];

const bam2 = (a: number, b: number) => ((a * 73856093) ^ (b * 19349663)) >>> 0;

/** Nơi chốn của một tập. Dưới 10 thì lấy nơi viết tay (có tên); từ 10 trở lên thì sinh tổ hợp. */
export const noiCuaTap = (kenh: string, tap: number): Noi => {
  const ds = NOI[kenh] || [];
  if (tap < ds.length) return ds[tap];
  // Lấy mảnh trong ĐÚNG nhóm không gian của kênh, cộng nhóm trung tính. Danh sách `MANH_HOP`
  // vẫn dùng làm thứ tự ưu tiên, nhưng bị lọc qua nhóm — nên không tổ hợp nào ra một căn phòng
  // chứa những thứ không bao giờ ở cùng nhau.
  const nhom = NHOM_KENH[kenh] || "vanphong";
  const chophep = new Set([...(NHOM[nhom] || []), ...NHOM.trungtinh]);
  const manh = (MANH_HOP[kenh] || MANH_HOP.office).filter((x) => chophep.has(x));
  const hs = bam2(kenh.length * 31 + tap, tap + 7);
  const kh = KHUON[hs % KHUON.length];
  // chọn các mảnh cách đều nhau trong danh sách bằng một bước nguyên tố — cùng một tập luôn ra
  // cùng một nơi (dựng lại được), mà hai tập liền nhau thì không dùng chung mảnh nào.
  const buoc = 7;
  const dau = hs % manh.length;
  const mo: Manh[] = kh.map((v, i) => ({ m: manh[(dau + i * buoc) % manh.length], x: v.x, co: v.co }));
  const goc = ds[hs % Math.max(1, ds.length)];
  return { ten: `${kenh} scene ${tap}`, mo, san: goc?.san, ngoai: goc?.ngoai, yS: goc?.yS };
};

/** Lắp một nơi chốn: vẽ tường, sàn, rồi từng mảnh đứng đúng chỗ trên đường sàn. */
export const LapNoi: React.FC<{
  noi: Noi; w: number; h: number; mau: string; mauPhu: string; net: number;
}> = ({ noi, w, h, mau, mauPhu, net }) => {
  // Đường sàn đặt ngay dưới chân nhân vật (chân ở 0.95·h khi vẽ cả người), không phải ở 0.76
  // như bản trước — nếu không, người và đồ đạc đứng trên hai mặt đất khác nhau.
  const yS = h * (noi.yS ?? SAN);
  // 31/8 — ĐỒ ĐẠC PHẢI TÍNH THEO CHIỀU NGANG KHUNG, KHÔNG THEO CHIỀU CAO.
  // Đây là gốc của chuyện "bối cảnh lộn xộn, không nhận ra là gì" mà anh chỉ ra ba lần. Mọi
  // mô-đun tính kích thước theo `p.h`. Ở khung ngang thì không sao — h và w gần nhau. Nhưng
  // khung dọc 992×1786 thì h gấp 1,8 lần w, nên mỗi vật to lên 1,8 lần: cái tủ bếp rộng
  // 1124px trong một khung rộng 992px, tràn ra ngoài và chỉ còn thấy MỘT MẢNG MÀU.
  //
  // Không phải mô-đun vẽ xấu — chúng vẽ đúng, chỉ là bị phóng quá cỡ nên người xem chỉ nhìn
  // thấy một góc của chúng. Chốt thước đo theo bề ngang thì mọi vật về đúng cỡ một món đồ đạc.
  const hDo = Math.min(h, w * 1.05);
  const ts = (m: Manh): ThamSo => ({ x: m.x, co: m.co, yS, w, h: hDo, mau, mauPhu });
  // Vật treo thêm vào TỰ ĐỘNG, không phải khai trong từng dòng dữ liệu: mọi nơi trong nhà đều
  // có tường, và tường trống là thứ duy nhất khung dọc không tha thứ. Chọn theo tên nơi nên
  // cùng một nơi luôn ra cùng bộ tranh — dựng lại được.
  const hs = noi.ten.split("").reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 99991, 7);
  const treo: Manh[] = noi.ngoai ? [] : [
    { m: TEN_MO_TREO[hs % TEN_MO_TREO.length], x: 0.13, treo: true },
    { m: TEN_MO_TREO[(hs + 3) % TEN_MO_TREO.length], x: 0.87, treo: true, co: 0.85 },
  ];
  return (
    <>
      <rect x={0} y={0} width={w} height={yS} fill={nhat(mau, 0.85)} />
      <rect x={0} y={yS} width={w} height={h - yS} fill={noi.san || nhat(mau, 0.62)} />
      <line x1={0} y1={yS} x2={w} y2={yS} stroke="#14110F" strokeWidth={4} opacity={0.5} />
      {/* chân tường và vệt sáng chéo — hai thứ rẻ nhất để mảng tường phẳng có chiều sâu */}
      <rect x={0} y={yS - h * 0.04} width={w} height={h * 0.04} fill="#00000010" />
      <path d={`M${w * 0.62} 0 L${w * 0.86} 0 L${w * 0.5} ${yS} L${w * 0.3} ${yS} Z`}
            fill="#FFFFFF" opacity={0.13} />
      {[...noi.mo, ...treo].filter((m) => m.lop !== "gan").map((m, i) => {
        const Ve = m.treo ? MO_TREO[m.m] : (MO_DUN[m.m] || MO_MY[m.m]);
        if (!Ve) return null;                       // mảnh lạ thì bỏ qua, không làm hỏng cả cảnh
        const xa = m.lop === "xa";
        // Mảnh treo ở tầm mắt trở lên; mảnh xa lùi lên cao và co nhỏ; còn lại chân chạm sàn.
        const y = m.treo ? h * 0.26 : xa ? yS - h * 0.1 : yS;
        const m2 = { ...m, co: (m.co ?? 1) * (xa ? 0.66 : m.chu ? (VAT_CAO.has(m.m) ? 1.12 : 1.3) : 1) };
        return (
          <g key={i} transform={`translate(${w * m.x} ${y})`}
             opacity={xa ? 0.5 : 1}>
            {/* bóng đổ cùng một hướng cho MỌI vật đứng sàn — thứ rẻ nhất tạo cảm giác cùng
                một nguồn sáng, và thiếu nó thì vật nào cũng như dán lên */}
            {!m.treo && !xa ? (
              <ellipse cx={h * 0.012} cy={2} rx={h * (m.chu ? 0.085 : 0.05)} ry={h * 0.012}
                       fill="#14110F" opacity={0.13} />
            ) : null}
            {Ve(ts(m2))}
          </g>
        );
      })}
    </>
  );
};

/**
 * LỚP GẦN — vẽ SAU nhân vật, nên nó che một phần người và bị mép khung cắt.
 * Đây là mảnh làm nên chiều sâu rõ nhất: mắt đọc "có thứ gì đó ở trước mặt nhân vật" và tự suy
 * ra khoảng cách. Luôn đặt ở mép (x ≤ 0,12 hoặc ≥ 0,88) và chỉ MỘT mảnh — hai mảnh gần thì
 * khung thành ra chật.
 */
export const LopGan: React.FC<{
  noi: Noi; w: number; h: number; mau: string; mauPhu: string;
}> = ({ noi, w, h, mau, mauPhu }) => {
  const gan = noi.mo.filter((m) => m.lop === "gan");
  if (!gan.length) return null;
  const yS = h * (noi.yS ?? SAN);
  return (
    <>
      {gan.slice(0, 1).map((m, i) => {
        const Ve = MO_DUN[m.m] || MO_MY[m.m];
        if (!Ve) return null;
        return (
          <g key={i} transform={`translate(${w * m.x} ${yS + h * 0.06})`} opacity={0.97}>
            {Ve({ x: m.x, co: (m.co ?? 1) * 1.7, yS, w, h: Math.min(h, w * 1.05), mau, mauPhu })}
          </g>
        );
      })}
    </>
  );
};

/** Danh sách nhãn nơi chốn của một kênh — bộ sinh kịch bản chọn trong đây. */
export const nhanNoi = (kenh: string): string[] => (NOI[kenh] || []).map((n) => n.ten);
