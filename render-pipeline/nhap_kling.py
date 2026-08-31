#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RÚT KỊCH BẢN TỪ GÓI PROMPT KLING -> `kho_kling.json`  (1/9/2026)

Anh gửi `Kling_1500_Funny_USA_Hook_6s_100100.txt`: 1.500 prompt viết cho Kling (sinh video
bằng AI). Đọc kỹ thì **1.500 ấy là 149 tình huống × 10 biến thể**, và mười biến thể chỉ đổi
NHỊP CUỐI (FAST REVEAL / DEADPAN / PUSH-IN…) — thoại y hệt nhau. Nên nội dung thật là 149 tập.

Ta KHÔNG dựng bằng Kling: hệ trên GitHub chạy bằng khoá sẵn có (Gemini/Cloudflare) và Kling
không nằm trong đường chạy tự động (kênh Kling cũ đã phải tạm dừng vì lý do này). Nhưng phần
giá trị nhất của gói prompt không phải là chỗ nó gọi Kling — mà là **kịch bản**: dàn nhân vật
khoá cứng, nhịp 6 giây đã tính sẵn, và một cú lật ở mỗi tập. Engine truyện tranh của mình vẽ
đúng thứ prompt mô tả: 2D, viền mực đậm, màu tươi, 9:16, thoại có khẩu hình.

Ra hai tầng:
    `tinh_huong` — 143 tình huống: hook · 2 lượt thoại · cú lật
    `tap`        — 1.430 TẬP = tình huống × biến thể, mỗi tập một nhịp chốt và một LỐI DỰNG

Mười lối dựng không phải nhãn trang trí: engine dựng chúng thành mười cách chốt khác nhau
(đẩy máy, cắt sang mặt người nghe, đóng băng, giữ mặt tỉnh bơ…). Nếu không làm thế thì mười
biến thể ra mười video giống hệt, và đó là cách nhanh nhất để một kênh bị coi là rác.

Sáu tình huống bị bỏ (60 prompt) chỉ có MỘT lượt thoại, câu đáp là hành động câm (mèo chỉ tay,
ông xoay cả người). Bịa thêm thoại là sửa kịch bản của anh — nên để riêng, ghi rõ là thiếu.
"""
import io
import json
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
NGUON = os.path.expanduser("~/Downloads/Kling_1500_Funny_USA_Hook_6s_100100.txt")
RA = os.path.join(GOC, "kho_kling.json")

# Ai nói -> vai trong bảng của kênh. "Speaker" là lỗi đánh máy của gói gốc (10 chỗ) — quy về
# Mike để không mất tập nào.
VAI_MAP = {"Mike": "mike", "Lisa": "lisa", "Tommy": "tommy", "Grandpa": "joe", "Speaker": "mike"}

# Mười lối dựng của gói gốc, theo đúng thứ tự biến thể xuất hiện trong tệp.
LOI_DUNG = ["fast_reveal", "deadpan", "push_in", "reaction_cut", "prop_reveal",
            "micro_escalation", "freeze_button", "physical_button", "muted", "clean_timing"]


# Cảm xúc suy từ chính câu nói. Bảng chấm phạt tập nào sáu lượt cùng một cảm xúc, và quan
# trọng hơn: giọng đọc lên xuống theo cảm xúc, nên đoán sai là nghe ra ngay.
def _cam_xuc(cau: str, la_lat: bool) -> str:
    c = cau.lower()
    if "?" in cau:
        return "nghi_ngo"
    if any(w in c for w in ("!", "no way", "seriously", "again")):
        return "bat_ngo"
    if la_lat:
        return "bat_ngo"
    return "trung_tinh"


def main() -> int:
    if not os.path.exists(NGUON):
        print(f"❌ không thấy {NGUON}")
        return 1
    s = io.open(NGUON, encoding="utf-8").read()
    khoi = re.split(r"\nPROMPT (\d{4}) — ", s)[1:]
    cap = list(zip(khoi[0::2], khoi[1::2]))

    kho = {}
    for _so, than in cap:
        dau = than.split("\n")[0]
        ten, _, bien = dau.partition(" / ")
        ten, bien = ten.strip(), bien.strip()

        m_hook = re.search(r"0\.0–0\.8s: HOOK — (.+)", than)
        m_setup = re.search(r"0\.8–2\.5s: SETUP — (.+)", than)
        m_lat = re.search(r"2\.5–4\.9s: PUNCHLINE/REVEAL — (.+)", than)
        m_chot = re.search(r"4\.9–6\.0s: REACTION/BUTTON — (.+)", than)
        if not (m_setup and m_lat):
            continue

        thoai = re.findall(r'([A-Z][a-z]+)(?: Joe)?:\s*"([^"]+)"', m_setup.group(1))
        if not thoai:
            continue
        # SÁU TÌNH HUỐNG CHỈ CÓ MỘT LƯỢT THOẠI — câu đáp là hành động câm ("Lisa points to a
        # receipt", "Grandpa turns his whole body around"). Bản đầu bỏ chúng, tức mất 60 prompt.
        # Anh: *"mỗi prompt là 1 videos"*. Nên chúng vào bằng NHỊP CHỐT CÂM: panel lật giữ hình
        # cộng chữ nổ, không bịa thêm lời. Câm là ngôn ngữ có thật của truyện tranh, còn thoại
        # bịa thì sửa kịch bản của anh.
        cam = len(thoai) < 2

        # KHOÁ THEO TÊN + THOẠI, không theo tên. "Cat Breakfast" xuất hiện HAI lần với hai bộ
        # thoại khác nhau (20 prompt), nên khoá bằng tên thôi là nuốt mất một tình huống — và
        # nuốt im lặng: tổng ra 1.490 thay vì 1.500, đúng cái loại lệch mà không ai để ý nếu
        # không đếm. Họ lỗi: coi một trường là DUY NHẤT khi nó chưa bao giờ hứa như thế.
        khoa = (ten, " ".join(c for _n, c in thoai)[:60])
        if khoa not in kho:
            kho[khoa] = {
                "ten": ten,
                "hook": (m_hook.group(1).strip() if m_hook else ""),
                "lat": m_lat.group(1).strip(),
                "loi": [[c.replace("’", "'"), VAI_MAP.get(n, "mike"), _cam_xuc(c, False)]
                        for n, c in thoai],
                "cam": cam,
                "nhip": [],
            }
        if m_chot:
            nc = m_chot.group(1).strip()
            if nc not in kho[khoa]["nhip"]:
                kho[khoa]["nhip"].append(nc)

    # Trải thành TẬP: mỗi (tình huống × biến thể) là một video riêng.
    tap = []
    for v in kho.values():
        for i, nc in enumerate(v["nhip"]):
            tap.append({"ten": v["ten"], "hook": v["hook"], "loi": v["loi"], "lat": v["lat"],
                        "cam": v.get("cam", False), "chot": nc,
                        "loiDung": LOI_DUNG[i % len(LOI_DUNG)]})
    # JSON không có khoá dạng tuple -> đổi sang chuỗi khi ghi.
    kho_ghi = {f"{t}|{h}": v for (t, h), v in kho.items()}
    io.open(RA, "w", encoding="utf-8").write(
        json.dumps({"tinh_huong": kho_ghi, "tap": tap}, ensure_ascii=False, indent=1))

    vai = {}
    for v in kho.values():
        for _, ai, _c in v["loi"]:
            vai[ai] = vai.get(ai, 0) + 1
    import collections
    print(f"  ✅ {len(kho)} tình huống × biến thể = {len(tap)} TẬP -> kho_kling.json")
    print(f"     lượt thoại theo vai: {vai}")
    print(f"     lối dựng: {dict(collections.Counter(t['loiDung'] for t in tap))}")
    print(f"     trong đó chốt CÂM (một lượt thoại + hành động): "
          f"{sum(1 for t in tap if t['cam'])} tập")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
