#!/usr/bin/env python3
"""Tải kho hình SVG ngoài về, chuẩn hoá, và xuất thành một mô-đun TS cho engine.

Anh: *"lên các kho ảnh tải file Vector (.SVG) về rồi import vào template của e chỉnh sửa
lại cho chuẩn đẹp"*. Đúng hướng, và nó vá đúng khoảng cách còn lại: nét vector mình tự vẽ
là HÌNH QUE, còn hình nhập về là người được vẽ thật.

── VÌ SAO KHÔNG DÙNG FREEPIK / VECTEEZY ────────────────────────────────────────────────
Cả hai kho ấy ở gói miễn phí đều **bắt ghi nguồn** và hạn chế phân phối lại. Một kênh
YouTube bật kiếm tiền, chạy tự động hàng trăm tập, không gắn được dòng ghi nguồn vào mỗi
video — nên tài sản của hai kho ấy là rủi ro pháp lý thật, không phải rủi ro lý thuyết.

Kho dùng ở đây là **unDraw** (qua bản gương MIT `balazser/undraw-svg-collection`):
cho dùng thương mại, **không bắt ghi nguồn**, không giới hạn số lượng. Đây là lý do chọn
nó thay vì Humaaans (CC-BY-4.0 — vẫn phải ghi nguồn) hay Open Doodles (kho gốc đã rời đi).

── VÌ SAO XUẤT RA .TS CHỨ KHÔNG ĐỌC TỆP LÚC DỰNG ───────────────────────────────────────
Remotion dựng khung trong trình duyệt; đọc tệp lúc ấy là một lượt mạng bất đồng bộ cho MỖI
khung — chậm, và hỏng khác nhau giữa máy anh với Actions (§8). Xuất sẵn thành mô-đun TS thì
engine `import` đồng bộ, tất định, và không gọi mạng lúc dựng.

── HAI PHÉP CHUẨN HOÁ, CẢ HAI BẮT BUỘC ─────────────────────────────────────────────────
1. Chèn `pathLength="1"` vào mọi thẻ hình. Không có nó thì hiệu ứng nét tự vẽ (`TuVe.tsx`)
   không chạy trên hình nhập về — mà đó chính là thứ làm hình nhập hoà vào cảnh mình vẽ
   thay vì trông như một tấm dán.
2. Đổi 4 mã màu của unDraw thành BIẾN, để engine thay bằng màu kênh. Giữ nguyên mã gốc thì
   mười tám kênh dùng chung một bảng tím-xanh của unDraw, tức đánh mất đúng trục bản sắc
   vừa dựng xong (§14.5).
"""
import json, os, re, sys, urllib.request
from typing import Optional, Tuple, Dict, List

GOC = "https://raw.githubusercontent.com/balazser/undraw-svg-collection/main/svgs/"
RA = os.path.join(os.path.dirname(__file__), "..", "engine-remotion", "src", "gt", "KhoSVG.ts")

# Bảng màu gốc của unDraw -> vai trò trong bảng màu của mình. Bốn mã này có mặt ở gần như
# mọi tệp của kho (đo trên mẫu), nên ánh xạ một lần là đủ cho cả 1.362 hình.
# ── PHÂN LOẠI MÀU, KHÔNG LIỆT KÊ MÃ  (5/9/2026, sau khi soi lưới) ──────────────────────
# Bản đầu là một bảng chín mã chép tay. Đo kho đã tải: **165 mã màu còn sót** không có trong
# bảng — và những mã tối trong số đó ra các MẢNG ĐEN ĐẶC to bằng nửa khung (tán cây, tóc).
# Đúng §13.9: *danh sách ngoại lệ là danh sách vô hạn*, và §13.2: *cổng cầm danh sách chép
# tay là cổng che lỗi*. unDraw có 1.362 hình do nhiều người vẽ; không ai đếm hết bảng màu của
# họ, và mỗi hình thêm vào lại sinh mã mới.
#
# Nay phân loại theo TÍNH CHẤT của màu, nên mã lạ cũng vào đúng vai:
#     rất tối        -> vùng tối     (KHÔNG phải nét mực: nét do CSS đặt riêng)
#     gần trắng/xám  -> mảng nhạt
#     tông da        -> giữ nguyên vai da người
#     còn lại        -> màu kênh
def _vai(hex6):
    r, g, b = (int(hex6[i:i + 2], 16) / 255 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    sang = 0.2126 * r + 0.7152 * g + 0.0722 * b
    bao = 0 if mx == 0 else (mx - mn) / mx
    if sang < 0.20:
        return "TOI"
    if bao < 0.12:
        return "NHAT" if sang > 0.55 else "XAM"
    # Tông da: sắc đỏ-cam và sáng vừa. Ngưỡng rộng vì unDraw vẽ nhiều tông da khác nhau,
    # và nhận nhầm một mảng áo thành da chỉ làm sai một mảng, còn nhận nhầm da thành màu
    # kênh thì mặt người đổi màu — hỏng nặng hơn hẳn.
    goc = 0.0
    if mx != mn:
        if mx == r: goc = (60 * ((g - b) / (mx - mn)) + 360) % 360
        elif mx == g: goc = 60 * ((b - r) / (mx - mn)) + 120
        else: goc = 60 * ((r - g) / (mx - mn)) + 240
    if (goc <= 38 or goc >= 340) and sang > 0.42:
        return "DA"
    return "CHINH"


THE_HINH = ("path", "rect", "circle", "ellipse", "line", "polyline", "polygon")

# Ánh xạ biểu tượng của mình -> tên tệp unDraw. `nguoi` có NĂM tư thế vì `_rai_tu_the` đã
# rải năm tư thế cho 54% số nhịp — nạp một hình người duy nhất là vứt bỏ trục đa dạng ấy.
BANG = {
    # ── HÌNH NGƯỜI PHẢI TRUNG TÍNH  (5/9/2026, sau khi soi lưới) ────────────────────────
    # Bản đầu lấy cả `questions` và `decide`. Soi khung: `questions` vẽ một DẤU HỎI khổng lồ
    # chiếm nửa khung, và nó hiện trên ba câu chẳng liên quan gì tới câu hỏi
    # (*"Then the letter arrives"* · *"It decides your fence"*). `stand-out` thì có cả một
    # đám người mờ phía sau, tranh chỗ với cảnh mình đã vẽ.
    #
    # Hình unDraw MANG SẴN NGHĨA của nó. `nguoi` trong hệ mình là một vai TRUNG TÍNH — nó
    # đứng thay cho "một người" ở bất kỳ câu nào — nên chỉ được lấy những hình mà thứ duy
    # nhất trong khung là con người. Hình mang biểu tượng riêng phải được gán cho ĐÚNG khái
    # niệm ấy, không được dùng làm hình người chung.
    # `walk-dreaming` hoá ra vẽ MỘT CON GẤU, `dog-walking` có thêm con chó, `questions` có
    # một dấu hỏi khổng lồ. Ba lần liên tiếp cùng một bài học: **hình unDraw mang sẵn chủ đề
    # của nó**, nên không tên nào đoán được bằng cách đọc tên tệp — phải NHÌN.
    # `nguoi` là vai trung tính (đứng thay cho "một người" ở câu bất kỳ), nên chỉ nhận hình
    # mà thứ duy nhất trong khung là con người. Hai hình, và thà ít mà đúng còn hơn nhiều mà
    # có tập nói về lá thư lại hiện một con gấu tím.
    "nguoi":      ["walking-outside", "relaxing-walk"],
    "dong_ho":    ["time-management", "in-no-time"],
    "tien":       ["transfer-money", "savings"],
    "xe":         ["car-repair"],
    "nha":        ["buy-house", "house-searching"],
    "may_bay":    ["airport"],
    "xe_buyt":    ["bus-stop"],
    "trai_dat":   ["around-the-world"],
    "dien_thoai": ["phone-call"],
    "cay":        ["social-tree"],
    "mat_troi":   ["sunny-day"],
    "giay":       ["contract"],
    "hop":        ["delivery-truck"],
    "giuong":     ["sleep-analysis"],
    "lua":        ["fire"],
    "coc":        ["coffee-time"],
}


def _tai(ten):
    try:
        rq = urllib.request.Request(GOC + ten + ".svg", headers={"User-Agent": "mm0/1.0"})
        return urllib.request.urlopen(rq, timeout=30).read().decode("utf-8", "replace")
    except Exception as e:
        print(f"   ⚠ {ten}: {str(e)[:60]}")
        return None


def _chuan(svg):
    """Trả (viewBox, phần ruột đã chuẩn hoá). None nếu tệp không dùng được."""
    m = re.search(r'viewBox="([^"]+)"', svg)
    if not m:
        return None
    vb = m.group(1)
    # Bỏ vỏ <svg …> và mọi thứ ngoài nó. `<style>`/`<image>` thì BỎ HẲN tệp: style toàn cục
    # rò sang phần còn lại của khung, còn <image> là ảnh bitmap nhúng — cả hai phá đúng lý do
    # mình chọn SVG. Bỏ một tệp rẻ hơn nhiều so với gỡ một lỗi chỉ hiện ở vài tập.
    if "<style" in svg or "<image" in svg:
        return None
    ruot = re.sub(r"(?s)^.*?<svg[^>]*>", "", svg)
    ruot = re.sub(r"(?s)</svg>\s*$", "", ruot)
    ruot = re.sub(r"(?s)<!--.*?-->", "", ruot).strip()
    # 1. pathLength — xem docstring
    def _pl(mo):
        the = mo.group(1)
        return mo.group(0) if 'pathLength' in mo.group(0) else f"<{the} pathLength=\"1\""
    ruot = re.sub(r"<(" + "|".join(THE_HINH) + r")\b", _pl, ruot)
    # 2. màu -> biến
    def _mau(mo):
        h = mo.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return "{" + _vai(h.lower()) + "}"
    ruot = re.sub(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", _mau, ruot)
    return vb, ruot


def main() -> int:
    kho = {}
    tong = bo = 0
    for bt, ds in BANG.items():
        kho[bt] = []
        for ten in ds:
            svg = _tai(ten)
            if not svg:
                bo += 1
                continue
            c = _chuan(svg)
            if not c:
                print(f"   ⚠ {ten}: có <style>/<image> hoặc thiếu viewBox — bỏ")
                bo += 1
                continue
            kho[bt].append({"ten": ten, "vb": c[0], "ruot": c[1]})
            tong += 1
        if not kho[bt]:
            del kho[bt]
    if not kho:
        raise RuntimeError("không tải được hình nào — KHÔNG ghi đè kho cũ")

    with open(RA, "w", encoding="utf-8") as f:
        f.write("/* SINH TỰ ĐỘNG bởi `render-pipeline/tai_svg.py` — ĐỪNG SỬA TAY.\n"
                "   Nguồn: unDraw (gương MIT `balazser/undraw-svg-collection`).\n"
                "   Giấy phép unDraw: dùng thương mại tự do, KHÔNG phải ghi nguồn.\n"
                "   Bốn mã màu gốc đã đổi thành biến để engine thay bằng màu kênh. */\n")
        f.write("export type HinhSVG = { ten: string; vb: string; ruot: string };\n")
        f.write("export const KHO_SVG: Record<string, HinhSVG[]> = ")
        f.write(json.dumps(kho, ensure_ascii=False, indent=1))
        f.write(";\n")
    print(f"   ✅ {tong} hình vào kho · {bo} bỏ · {len(kho)} biểu tượng có hình")
    return 0


if __name__ == "__main__":
    sys.exit(main())
