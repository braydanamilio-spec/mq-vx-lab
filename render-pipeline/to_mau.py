#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHỈNH MÀU ẢNH VỀ BẢNG MÀU CỦA KÊNH.  (1/9/2026)

Anh: *"tìm cách nâng cấp sao cho chuyên nghiệp chất lượng top 1, không rẻ tiền, nghiệp dư xấu."*

── VÌ SAO ĐÂY LÀ ĐÒN BẨY LỚN NHẤT ──────────────────────────────────────────────────────────
Soi lại chính bản của mình: mười lăm ảnh trong một tập, mỗi ảnh một bảng màu do FLUX tự chọn —
cảnh sa mạc vàng cam, cảnh bếp xanh lạnh, cảnh xưởng xám thép. Từng ảnh không xấu. Ghép lại thì
đọc ra ngay là *một thư mục ảnh*, không phải *một bộ phim*.

Đây chính là ranh giới giữa nghiệp dư và chuyên nghiệp trong loại video này, và nó không nằm ở
chỗ vẽ đẹp hơn. Mọi hãng phim đều **chỉnh màu toàn bộ cảnh quay về một bảng màu** sau khi quay
xong; không ai phát hành bản chưa chỉnh màu. Ảnh AI cũng vậy: chưa chỉnh màu thì còn là nguyên
liệu, chưa phải phim.

── LÀM GÌ, VÀ VÌ SAO ĐÚNG BA BƯỚC ẤY ───────────────────────────────────────────────────────
1. HẠ BÃO HOÀ ~14%. Ảnh AI luôn rực hơn phim thật. Rực là dấu hiệu "chưa qua tay ai".
2. TÁCH TÔNG (split-tone): đẩy vùng TỐI về màu chữ của kênh, vùng SÁNG về màu nền của kênh.
   Đây là bước gánh gần hết hiệu quả — nó làm mọi ảnh có chung một "chất khí". Cường độ phải
   NHẸ (0,10–0,18): mạnh tay thì thành ảnh nhuộm, và nhuộm còn rẻ tiền hơn không chỉnh.
3. ĐƯỜNG CONG CHỮ S NHẸ. Nâng tương phản ở vùng giữa, giữ nguyên hai đầu — chống bệt mà không
   cháy sáng, không tắc bóng.

KHÔNG dùng numpy: máy này không có, và cả ba bước đều là phép ánh xạ từng kênh màu nên bảng tra
256 phần tử của PIL chạy đủ nhanh (một ảnh 1024² mất ~40 ms).
"""
import os


def _lut_s(manh: float = 0.16):
    """Đường cong chữ S quanh điểm giữa. `manh` là độ nâng tương phản."""
    ra = []
    for i in range(256):
        x = i / 255.0
        # smoothstep pha với đường thẳng: giữ được hai đầu, chỉ dốc thêm ở giữa
        s = x * x * (3 - 2 * x)
        ra.append(max(0, min(255, int(round(255 * (x * (1 - manh) + s * manh))))))
    return ra


def _lut_tone(toi: int, sang: int, manh: float):
    """Ánh xạ MỘT kênh màu: vùng tối kéo về `toi`, vùng sáng kéo về `sang`.

    Trọng số theo chính độ sáng của điểm ảnh, nên vùng giữa gần như không đổi — đó là chỗ da
    người và chi tiết nằm, đụng vào là ảnh trông giả ngay."""
    ra = []
    for i in range(256):
        x = i / 255.0
        w_toi = (1 - x) ** 2          # chỉ ăn mạnh ở vùng thật tối
        w_sang = x ** 2               # và vùng thật sáng
        v = i + manh * (w_toi * (toi - i) + w_sang * (sang - i))
        ra.append(max(0, min(255, int(round(v)))))
    return ra


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[k:k + 2], 16) for k in (0, 2, 4))


def to_mau(tep: str, mau_chu: str, mau_nen: str, manh: float = 0.14,
           bao_hoa: float = 0.86, tuong_phan: float = 0.16) -> bool:
    """Chỉnh một ảnh tại chỗ. Trả True nếu đã ghi đè.

    Hỏng thì trả False và GIỮ NGUYÊN ảnh gốc — chỉnh màu là bước làm đẹp, không được phép làm
    mất ảnh. Cùng nguyên tắc với `chuan_am.py`: giải mã kiểm tra trước khi thay bản gốc."""
    try:
        from PIL import Image, ImageEnhance
    except Exception:
        return False
    try:
        im = Image.open(tep).convert("RGB")
        im = ImageEnhance.Color(im).enhance(bao_hoa)

        t, s = _rgb(mau_chu), _rgb(mau_nen)
        sc = _lut_s(tuong_phan)
        lut = []
        for k in range(3):
            tone = _lut_tone(t[k], s[k], manh)
            lut += [tone[sc[i]] for i in range(256)]     # tương phản trước, tách tông sau
        im = im.point(lut)

        tam = tep + ".tmp.jpg"
        im.save(tam, "JPEG", quality=92, optimize=True)
        if os.path.getsize(tam) < 20000:
            os.remove(tam)
            return False
        os.replace(tam, tep)
        return True
    except Exception:
        try:
            if os.path.exists(tep + ".tmp.jpg"):
                os.remove(tep + ".tmp.jpg")
        except Exception:
            pass
        return False
