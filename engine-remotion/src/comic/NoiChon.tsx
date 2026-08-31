import React from "react";
import { MO_DUN, MO_TREO, TEN_MO_TREO, nhat, ThamSo } from "./MoDun";

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

export type Manh = { m: string; x: number; co?: number; treo?: boolean };
export type Noi = {
  ten: string;              // nhãn tiếng Anh — bộ sinh kịch bản chọn theo nhãn này
  mo: Manh[];
  san?: string;             // màu sàn riêng (mặc định: pha từ màu kênh)
  yS?: number;              // mức sàn theo tỉ lệ chiều cao sân khấu
  ngoai?: boolean;          // ngoài trời -> phần trên là trời, không phải trần
};

export const NOI: Record<string, Noi[]> = {
  tech: [
    { ten: "the IT help desk", mo: [{ m: "ban", x: 0.14 }, { m: "may_tinh", x: 0.14, co: 0.9 }, { m: "tu_ho_so", x: 0.88 }] },
    { ten: "a server room", mo: [{ m: "tu_ho_so", x: 0.1 }, { m: "tu_ho_so", x: 0.9, co: 1.1 }, { m: "bang_hieu", x: 0.5, co: 0.7 }] },
    { ten: "the customer's living room", mo: [{ m: "sofa", x: 0.86 }, { m: "tv", x: 0.12 }, { m: "cay", x: 0.5, co: 0.7 }] },
    { ten: "the office reception", mo: [{ m: "quay", x: 0.12 }, { m: "ghe", x: 0.88 }, { m: "cay", x: 0.5, co: 0.8 }] },
    { ten: "a cramped supply closet", mo: [{ m: "ke_sach", x: 0.1 }, { m: "thung", x: 0.88 }, { m: "thung", x: 0.5, co: 0.7 }] },
    { ten: "the break room", mo: [{ m: "may_ca_phe", x: 0.14 }, { m: "ban", x: 0.86, co: 0.9 }, { m: "bang_ghim", x: 0.5, co: 0.7 }] },
    { ten: "a meeting room", mo: [{ m: "ban_dai", x: 0.5, co: 0.8 }, { m: "cua_so", x: 0.88 }, { m: "bang_ghim", x: 0.1 }] },
    { ten: "the home office", mo: [{ m: "ban", x: 0.86 }, { m: "may_tinh", x: 0.86, co: 0.85 }, { m: "ke_sach", x: 0.1 }] },
    { ten: "the office hallway", mo: [{ m: "cua_ra_vao", x: 0.1 }, { m: "bang_ghim", x: 0.88 }, { m: "cay", x: 0.5, co: 0.7 }] },
    { ten: "a phone repair counter", mo: [{ m: "quay", x: 0.5, co: 0.8 }, { m: "gia_treo", x: 0.12 }, { m: "bang_hieu", x: 0.86, co: 0.8 }] },
  ],
  rent: [
    { ten: "the apartment hallway", mo: [{ m: "cua_ra_vao", x: 0.1 }, { m: "cua_ra_vao", x: 0.9, co: 0.9 }, { m: "cay", x: 0.5, co: 0.6 }] },
    { ten: "the mailbox lobby", mo: [{ m: "ke_sach", x: 0.12, co: 0.8 }, { m: "bang_ghim", x: 0.88 }, { m: "thung", x: 0.5, co: 0.6 }] },
    { ten: "an empty apartment", mo: [{ m: "cua_so", x: 0.12 }, { m: "thung", x: 0.86 }, { m: "thung", x: 0.5, co: 0.7 }] },
    { ten: "the building manager's office", mo: [{ m: "ban", x: 0.14 }, { m: "tu_ho_so", x: 0.88 }, { m: "bang_ghim", x: 0.5, co: 0.7 }] },
    { ten: "the shared laundry room", mo: [{ m: "tu_lanh", x: 0.1, co: 0.9 }, { m: "ban", x: 0.88, co: 0.8 }, { m: "thung", x: 0.5, co: 0.7 }] },
    { ten: "the stairwell", mo: [{ m: "cua_ra_vao", x: 0.88 }, { m: "bang_hieu", x: 0.12, co: 0.7 }] },
    { ten: "the back courtyard", mo: [{ m: "hang_rao", x: 0.5, co: 0.9 }, { m: "cay", x: 0.1 }, { m: "thung", x: 0.9, co: 0.7 }], ngoai: true, san: "#8FBF6A" },
    { ten: "the parking lot", mo: [{ m: "xe", x: 0.12, co: 0.8 }, { m: "bang_hieu", x: 0.88, co: 0.8 }], ngoai: true, san: "#8C8C94" },
    { ten: "a small living room", mo: [{ m: "sofa", x: 0.86 }, { m: "cua_so", x: 0.12 }, { m: "tv", x: 0.5, co: 0.6 }] },
    { ten: "the front door of the unit", mo: [{ m: "cua_ra_vao", x: 0.5, co: 0.9 }, { m: "cay", x: 0.1, co: 0.8 }, { m: "thung", x: 0.9, co: 0.6 }] },
  ],
  gym: [
    { ten: "the weight floor", mo: [{ m: "gia_ta", x: 0.12 }, { m: "guong", x: 0.88 }], san: "#8A8A93" },
    { ten: "the cardio row", mo: [{ m: "ban_dai", x: 0.5, co: 0.7 }, { m: "guong", x: 0.1 }, { m: "cay", x: 0.9, co: 0.7 }], san: "#8A8A93" },
    { ten: "the locker room", mo: [{ m: "tu_ho_so", x: 0.1 }, { m: "tu_ho_so", x: 0.9 }, { m: "ghe", x: 0.5, co: 0.8 }] },
    { ten: "the gym front desk", mo: [{ m: "quay", x: 0.14 }, { m: "bang_hieu", x: 0.86 }, { m: "cay", x: 0.5, co: 0.7 }] },
    { ten: "the stretching corner", mo: [{ m: "guong", x: 0.12 }, { m: "gia_ta", x: 0.88, co: 0.8 }], san: "#8A8A93" },
    { ten: "the smoothie bar", mo: [{ m: "quay", x: 0.5, co: 0.8 }, { m: "may_ca_phe", x: 0.12 }, { m: "ghe", x: 0.88, co: 0.8 }] },
    { ten: "the equipment storage", mo: [{ m: "ke_sach", x: 0.1 }, { m: "thung", x: 0.9 }, { m: "gia_ta", x: 0.5, co: 0.7 }] },
    { ten: "the yoga studio", mo: [{ m: "guong", x: 0.88 }, { m: "cua_so", x: 0.12 }] },
    { ten: "the gym parking lot", mo: [{ m: "xe", x: 0.14, co: 0.8 }, { m: "bang_hieu", x: 0.86, co: 0.8 }], ngoai: true, san: "#8C8C94" },
    { ten: "a personal training room", mo: [{ m: "gia_ta", x: 0.1, co: 0.9 }, { m: "ban", x: 0.9, co: 0.8 }, { m: "guong", x: 0.5, co: 0.7 }] },
  ],
  airport: [
    { ten: "the check-in counter", mo: [{ m: "quay", x: 0.5, co: 0.9 }, { m: "bang_hieu", x: 0.12 }, { m: "gia_treo", x: 0.9, co: 0.8 }] },
    { ten: "the departure gate", mo: [{ m: "ghe", x: 0.1 }, { m: "ghe", x: 0.9 }, { m: "bang_hieu", x: 0.5, co: 0.9 }] },
    { ten: "baggage claim", mo: [{ m: "ban_dai", x: 0.5, co: 0.9 }, { m: "thung", x: 0.12 }, { m: "thung", x: 0.88, co: 0.8 }] },
    { ten: "the security line", mo: [{ m: "ban", x: 0.14 }, { m: "hang_rao", x: 0.86, co: 0.7 }, { m: "bang_hieu", x: 0.5, co: 0.7 }] },
    { ten: "an airport coffee stand", mo: [{ m: "may_ca_phe", x: 0.12 }, { m: "quay", x: 0.86, co: 0.8 }, { m: "ghe", x: 0.5, co: 0.7 }] },
    { ten: "the moving walkway", mo: [{ m: "ban_dai", x: 0.5, co: 0.8 }, { m: "cua_so", x: 0.1 }, { m: "cua_so", x: 0.9 }] },
    { ten: "the rebooking desk", mo: [{ m: "quay", x: 0.14 }, { m: "may_tinh", x: 0.14, co: 0.8 }, { m: "bang_hieu", x: 0.86 }] },
    { ten: "the airline lounge", mo: [{ m: "sofa", x: 0.86 }, { m: "cay", x: 0.12 }, { m: "ban", x: 0.5, co: 0.6 }] },
    { ten: "the jet bridge door", mo: [{ m: "cua_ra_vao", x: 0.5 }, { m: "bang_hieu", x: 0.12, co: 0.8 }, { m: "ghe", x: 0.9, co: 0.7 }] },
    { ten: "the information desk", mo: [{ m: "quay", x: 0.5, co: 0.8 }, { m: "bang_ghim", x: 0.1 }, { m: "cay", x: 0.9, co: 0.8 }] },
  ],
  car: [
    { ten: "the repair bay", mo: [{ m: "xe", x: 0.12 }, { m: "gia_treo", x: 0.9 }], san: "#7C7C84" },
    { ten: "the service counter", mo: [{ m: "quay", x: 0.14 }, { m: "may_tinh", x: 0.14, co: 0.8 }, { m: "bang_hieu", x: 0.86 }] },
    { ten: "the parts room", mo: [{ m: "ke_sach", x: 0.1 }, { m: "ke_sach", x: 0.9 }, { m: "thung", x: 0.5, co: 0.7 }] },
    { ten: "the waiting area", mo: [{ m: "ghe", x: 0.1 }, { m: "may_ca_phe", x: 0.9, co: 0.8 }, { m: "ban", x: 0.5, co: 0.6 }] },
    { ten: "the car lift", mo: [{ m: "xe", x: 0.5, co: 0.9 }, { m: "gia_treo", x: 0.1 }, { m: "thung", x: 0.9, co: 0.7 }], san: "#7C7C84" },
    { ten: "the front lot", mo: [{ m: "xe", x: 0.86, co: 0.8 }, { m: "bang_hieu", x: 0.12 }], ngoai: true, san: "#8C8C94" },
    { ten: "the tire wall", mo: [{ m: "ke_sach", x: 0.88 }, { m: "gia_treo", x: 0.12 }], san: "#7C7C84" },
    { ten: "the garage office", mo: [{ m: "ban", x: 0.14 }, { m: "tu_ho_so", x: 0.88 }, { m: "bang_ghim", x: 0.5, co: 0.7 }] },
    { ten: "the wash bay", mo: [{ m: "xe", x: 0.5, co: 0.85 }, { m: "gia_treo", x: 0.9, co: 0.8 }], san: "#7C7C84" },
    { ten: "the customer driveway", mo: [{ m: "xe", x: 0.14, co: 0.8 }, { m: "hang_rao", x: 0.86, co: 0.7 }], ngoai: true, san: "#8FBF6A" },
  ],
  office: [
    { ten: "the cubicle row", mo: [{ m: "ban", x: 0.12 }, { m: "may_tinh", x: 0.12, co: 0.8 }, { m: "bang_ghim", x: 0.88 }] },
    { ten: "the coffee machine", mo: [{ m: "may_ca_phe", x: 0.14 }, { m: "tu_bep", x: 0.86, co: 0.8 }] },
    { ten: "the meeting room", mo: [{ m: "ban_dai", x: 0.5, co: 0.8 }, { m: "cua_so", x: 0.9 }, { m: "bang_ghim", x: 0.1 }] },
    { ten: "the elevator lobby", mo: [{ m: "cua_ra_vao", x: 0.1 }, { m: "cua_ra_vao", x: 0.9 }, { m: "cay", x: 0.5, co: 0.7 }] },
    { ten: "the copy room", mo: [{ m: "ban", x: 0.86, co: 0.9 }, { m: "thung", x: 0.12 }, { m: "ke_sach", x: 0.5, co: 0.6 }] },
    { ten: "the reception desk", mo: [{ m: "quay", x: 0.5, co: 0.85 }, { m: "cay", x: 0.1 }, { m: "ghe", x: 0.9, co: 0.8 }] },
    { ten: "the break room", mo: [{ m: "tu_lanh", x: 0.9, co: 0.9 }, { m: "ban", x: 0.12, co: 0.9 }, { m: "may_ca_phe", x: 0.5, co: 0.7 }] },
    { ten: "the boss's office", mo: [{ m: "ban", x: 0.5, co: 0.9 }, { m: "ke_sach", x: 0.1 }, { m: "cua_so", x: 0.9 }] },
    { ten: "the open floor", mo: [{ m: "ban_dai", x: 0.5, co: 0.9 }, { m: "cay", x: 0.1 }, { m: "cay", x: 0.9, co: 0.8 }] },
    { ten: "the office kitchen", mo: [{ m: "tu_bep", x: 0.5, co: 0.9 }, { m: "tu_lanh", x: 0.1, co: 0.9 }, { m: "may_ca_phe", x: 0.9, co: 0.8 }] },
  ],
  diet: [
    { ten: "the kitchen", mo: [{ m: "tu_lanh", x: 0.88 }, { m: "tu_bep", x: 0.14, co: 0.9 }] },
    { ten: "in front of the open fridge", mo: [{ m: "tu_lanh", x: 0.5, co: 1.05 }, { m: "tu_bep", x: 0.1, co: 0.8 }] },
    { ten: "the dinner table", mo: [{ m: "ban", x: 0.5, co: 0.9 }, { m: "ghe", x: 0.12 }, { m: "ghe", x: 0.88 }] },
    { ten: "a grocery aisle", mo: [{ m: "ke_sach", x: 0.1, co: 1.1 }, { m: "ke_sach", x: 0.9, co: 1.1 }] },
    { ten: "the kitchen island", mo: [{ m: "tu_bep", x: 0.5 }, { m: "tu_lanh", x: 0.9, co: 0.9 }, { m: "may_ca_phe", x: 0.1, co: 0.8 }] },
    { ten: "the living room couch", mo: [{ m: "sofa", x: 0.86 }, { m: "tv", x: 0.12 }] },
    { ten: "the backyard grill", mo: [{ m: "ban", x: 0.12, co: 0.9 }, { m: "hang_rao", x: 0.86, co: 0.8 }, { m: "cay", x: 0.5, co: 0.7 }], ngoai: true, san: "#8FBF6A" },
    { ten: "a coffee shop table", mo: [{ m: "ban", x: 0.5, co: 0.75 }, { m: "quay", x: 0.1, co: 0.8 }, { m: "cay", x: 0.9, co: 0.8 }] },
    { ten: "the snack cupboard", mo: [{ m: "tu_bep", x: 0.5, co: 1.0 }, { m: "ke_sach", x: 0.1, co: 0.9 }] },
    { ten: "the bathroom scale", mo: [{ m: "guong", x: 0.88 }, { m: "tu_bep", x: 0.12, co: 0.7 }] },
  ],
  parent: [
    { ten: "the living room", mo: [{ m: "sofa", x: 0.86 }, { m: "tv", x: 0.12 }, { m: "thung", x: 0.5, co: 0.55 }] },
    { ten: "the kid's bedroom", mo: [{ m: "giuong", x: 0.86 }, { m: "ke_sach", x: 0.1 }, { m: "thung", x: 0.5, co: 0.6 }] },
    { ten: "the kitchen table", mo: [{ m: "ban", x: 0.5, co: 0.9 }, { m: "tu_lanh", x: 0.9, co: 0.9 }, { m: "ghe", x: 0.1, co: 0.9 }] },
    { ten: "the homework desk", mo: [{ m: "ban", x: 0.14 }, { m: "ke_sach", x: 0.88 }, { m: "ghe", x: 0.5, co: 0.7 }] },
    { ten: "the backyard", mo: [{ m: "hang_rao", x: 0.5, co: 0.9 }, { m: "cay", x: 0.1 }, { m: "thung", x: 0.9, co: 0.6 }], ngoai: true, san: "#8FBF6A" },
    { ten: "the car back seat", mo: [{ m: "ghe", x: 0.14, co: 1.1 }, { m: "ghe", x: 0.86, co: 1.1 }] },
    { ten: "a toy store aisle", mo: [{ m: "ke_sach", x: 0.1, co: 1.1 }, { m: "ke_sach", x: 0.9, co: 1.1 }, { m: "thung", x: 0.5, co: 0.6 }] },
    { ten: "the laundry room", mo: [{ m: "tu_lanh", x: 0.12, co: 0.9 }, { m: "thung", x: 0.88 }, { m: "gia_treo", x: 0.5, co: 0.7 }] },
    { ten: "the front hallway", mo: [{ m: "cua_ra_vao", x: 0.5 }, { m: "gia_treo", x: 0.1 }, { m: "thung", x: 0.9, co: 0.6 }] },
    { ten: "the playroom floor", mo: [{ m: "thung", x: 0.12 }, { m: "thung", x: 0.88, co: 0.8 }, { m: "tv", x: 0.5, co: 0.6 }] },
  ],
  neighbor: [
    { ten: "over the front fence", mo: [{ m: "hang_rao", x: 0.5 }, { m: "cay", x: 0.1 }, { m: "cay", x: 0.9, co: 0.8 }], ngoai: true, san: "#8FBF6A" },
    { ten: "by the mailboxes", mo: [{ m: "gia_treo", x: 0.12, co: 0.8 }, { m: "hang_rao", x: 0.86, co: 0.8 }], ngoai: true, san: "#8FBF6A" },
    { ten: "the front porch", mo: [{ m: "cua_ra_vao", x: 0.12 }, { m: "ghe", x: 0.88 }, { m: "cay", x: 0.5, co: 0.7 }], ngoai: true },
    { ten: "the shared driveway", mo: [{ m: "xe", x: 0.86, co: 0.8 }, { m: "hang_rao", x: 0.12, co: 0.7 }], ngoai: true, san: "#8C8C94" },
    { ten: "the open garage", mo: [{ m: "gia_treo", x: 0.1 }, { m: "thung", x: 0.9 }, { m: "xe", x: 0.5, co: 0.7 }], san: "#7C7C84" },
    { ten: "the sidewalk", mo: [{ m: "cay", x: 0.12 }, { m: "hang_rao", x: 0.86, co: 0.8 }], ngoai: true, san: "#9A9A9E" },
    { ten: "the back garden", mo: [{ m: "cay", x: 0.1 }, { m: "cay", x: 0.9 }, { m: "thung", x: 0.5, co: 0.6 }], ngoai: true, san: "#8FBF6A" },
    { ten: "the trash bins", mo: [{ m: "thung", x: 0.14, co: 1.2 }, { m: "thung", x: 0.86, co: 1.1 }], ngoai: true, san: "#9A9A9E" },
    { ten: "the front door", mo: [{ m: "cua_ra_vao", x: 0.5 }, { m: "cay", x: 0.1, co: 0.8 }, { m: "thung", x: 0.9, co: 0.6 }] },
    { ten: "the neighborhood watch table", mo: [{ m: "ban", x: 0.5, co: 0.85 }, { m: "bang_hieu", x: 0.12 }, { m: "ghe", x: 0.88, co: 0.8 }], ngoai: true, san: "#8FBF6A" },
  ],
  dating: [
    { ten: "a coffee shop", mo: [{ m: "ban", x: 0.5, co: 0.75 }, { m: "quay", x: 0.1, co: 0.85 }, { m: "cay", x: 0.9, co: 0.8 }] },
    { ten: "a restaurant table", mo: [{ m: "ban", x: 0.5, co: 0.85 }, { m: "ghe", x: 0.1 }, { m: "ghe", x: 0.9 }] },
    { ten: "a park bench", mo: [{ m: "ghe", x: 0.5, co: 1.1 }, { m: "cay", x: 0.1 }, { m: "cay", x: 0.9, co: 0.8 }], ngoai: true, san: "#8FBF6A" },
    { ten: "the bar counter", mo: [{ m: "quay", x: 0.5, co: 0.9 }, { m: "gia_treo", x: 0.1, co: 0.8 }, { m: "may_ca_phe", x: 0.9, co: 0.8 }] },
    { ten: "her living room", mo: [{ m: "sofa", x: 0.86 }, { m: "tv", x: 0.12 }, { m: "cay", x: 0.5, co: 0.6 }] },
    { ten: "the car front seats", mo: [{ m: "ghe", x: 0.14, co: 1.1 }, { m: "ghe", x: 0.86, co: 1.1 }] },
    { ten: "a movie theater lobby", mo: [{ m: "quay", x: 0.12 }, { m: "bang_hieu", x: 0.88 }, { m: "thung", x: 0.5, co: 0.6 }] },
    { ten: "a grocery checkout", mo: [{ m: "quay", x: 0.5, co: 0.85 }, { m: "ke_sach", x: 0.1, co: 1.0 }, { m: "thung", x: 0.9, co: 0.7 }] },
    { ten: "the apartment doorway", mo: [{ m: "cua_ra_vao", x: 0.5 }, { m: "cay", x: 0.1, co: 0.8 }, { m: "gia_treo", x: 0.9, co: 0.8 }] },
    { ten: "a rooftop terrace", mo: [{ m: "ban", x: 0.5, co: 0.7 }, { m: "cay", x: 0.12 }, { m: "hang_rao", x: 0.88, co: 0.7 }], ngoai: true },
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
const MANH_HOP: Record<string, string[]> = {
  tech:     ["ban", "may_tinh", "tu_ho_so", "ke_sach", "ghe", "quay", "cua_so", "bang_ghim",
             "thung", "may_ca_phe", "cay", "sofa", "tv", "cua_ra_vao", "bang_hieu"],
  rent:     ["cua_ra_vao", "cua_so", "ke_sach", "thung", "ban", "ghe", "sofa", "cay", "tv",
             "bang_ghim", "tu_ho_so", "gia_treo", "hang_rao", "guong", "tu_lanh"],
  gym:      ["gia_ta", "guong", "ghe", "quay", "tu_ho_so", "ke_sach", "thung", "cay", "ban",
             "may_ca_phe", "cua_so", "bang_hieu", "gia_treo", "ban_dai", "bang_ghim"],
  airport:  ["ghe", "quay", "ban_dai", "bang_hieu", "thung", "cua_so", "cay", "may_ca_phe",
             "gia_treo", "hang_rao", "cua_ra_vao", "ban", "may_tinh", "sofa", "ke_sach"],
  car:      ["xe", "gia_treo", "ke_sach", "thung", "quay", "ghe", "ban", "may_tinh", "bang_hieu",
             "may_ca_phe", "tu_ho_so", "hang_rao", "cay", "bang_ghim", "guong"],
  office:   ["ban", "may_tinh", "bang_ghim", "may_ca_phe", "ban_dai", "cua_so", "cay", "ke_sach",
             "quay", "ghe", "tu_lanh", "tu_bep", "cua_ra_vao", "thung", "tu_ho_so"],
  diet:     ["tu_lanh", "tu_bep", "ban", "ghe", "ke_sach", "sofa", "tv", "may_ca_phe", "quay",
             "cay", "guong", "hang_rao", "thung", "cua_so", "giuong"],
  parent:   ["sofa", "tv", "giuong", "ke_sach", "ban", "ghe", "thung", "tu_lanh", "cay",
             "gia_treo", "cua_ra_vao", "hang_rao", "tu_bep", "cua_so", "guong"],
  neighbor: ["hang_rao", "cay", "thung", "xe", "cua_ra_vao", "ghe", "ban", "gia_treo",
             "bang_hieu", "ke_sach", "guong", "quay", "tv", "sofa", "cua_so"],
  dating:   ["ban", "ghe", "quay", "cay", "sofa", "tv", "may_ca_phe", "ke_sach", "thung",
             "bang_hieu", "cua_ra_vao", "gia_treo", "hang_rao", "cua_so", "guong"],
};

// Ba khuôn đặt chỗ. Cả ba đều chừa vùng 0.24–0.76 cho hai nhân vật — ràng buộc bất biến của hệ.
const KHUON: { x: number; co: number }[][] = [
  [{ x: 0.12, co: 1 }, { x: 0.88, co: 0.9 }, { x: 0.5, co: 0.62 }],
  [{ x: 0.1, co: 1.05 }, { x: 0.5, co: 0.8 }, { x: 0.9, co: 0.85 }],
  [{ x: 0.14, co: 0.9 }, { x: 0.86, co: 1.05 }],
];

const bam2 = (a: number, b: number) => ((a * 73856093) ^ (b * 19349663)) >>> 0;

/** Nơi chốn của một tập. Dưới 10 thì lấy nơi viết tay (có tên); từ 10 trở lên thì sinh tổ hợp. */
export const noiCuaTap = (kenh: string, tap: number): Noi => {
  const ds = NOI[kenh] || [];
  if (tap < ds.length) return ds[tap];
  const manh = MANH_HOP[kenh] || MANH_HOP.office;
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
  const yS = h * (noi.yS ?? 0.93);
  const ts = (m: Manh): ThamSo => ({ x: m.x, co: m.co, yS, w, h, mau, mauPhu });
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
      {[...noi.mo, ...treo].map((m, i) => {
        const Ve = m.treo ? MO_TREO[m.m] : MO_DUN[m.m];
        if (!Ve) return null;                       // mảnh lạ thì bỏ qua, không làm hỏng cả cảnh
        // Mảnh treo đặt ở tầm mắt trở lên — chỗ nhân vật không che; mảnh đứng thì chân chạm sàn.
        const y = m.treo ? h * 0.26 : yS;
        return <g key={i} transform={`translate(${w * m.x} ${y})`}>{Ve(ts(m))}</g>;
      })}
    </>
  );
};

/** Danh sách nhãn nơi chốn của một kênh — bộ sinh kịch bản chọn trong đây. */
export const nhanNoi = (kenh: string): string[] => (NOI[kenh] || []).map((n) => n.ten);
