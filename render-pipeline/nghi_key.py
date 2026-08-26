#!/usr/bin/env python3
"""PHẠT KEY CẠN HẠN MỨC — MỘT NGUỒN DUY NHẤT (24/8/2026 tối).

Ba loại 429 chữa ngược nhau, không được gộp:
  • CHẶN THEO PHÚT/GIÂY (RPM/TPM) — key vẫn tốt, thở 1-2 phút là vào lại vòng xoay. Phạt 90' là
    ném đi 88 phút hạn mức còn dùng được của một key hoàn toàn khoẻ.
  • CẠN THEO NGÀY (RPD/TPD) — gọi lại trước lúc nhà cung cấp reset thì chắc chắn 429, mà lượt hỏng
    VẪN BỊ TRỪ. Phải nghỉ tới **mốc reset thật**.
  • KHÔNG RÕ — 20 phút: đủ để không dội liên tục, đủ ngắn để không phí key.

VÌ SAO TÁCH RA FILE RIÊNG
-------------------------
Cùng một quyết định đang có HAI bản khác nhau trong hệ, và bản kém hơn nằm ở đường quan trọng hơn:
  • đường VẼ ẢNH / VISION (`datastory_ci._muc_nghi`) tính ĐÚNG số phút còn lại tới mốc reset;
  • đường VIẾT (`key_manager`, 8 chỗ) dùng con số cứng **8 tiếng**.
8 tiếng là một con số đoán, và sai cả hai chiều: key cạn lúc 20:00 UTC (Google reset 07:00 UTC)
hết hạn phạt lúc 04:00 — dội lại 3 tiếng trước khi nó thật sự hồi, mỗi lượt hỏng vẫn bị trừ; còn key
Cloudflare cạn lúc 02:00 UTC (đã reset từ 00:00 UTC) thì bị treo oan tới 10:00.

MỐC RESET
---------
  • Cloudflare Workers AI — 00:00 **UTC** (chính thông báo lỗi ghi "daily free allocation of 10,000
    neurons").
  • Google / Groq free — 00:00 giờ **Thái Bình Dương** (UTC-7).
  • Nhà cung cấp chưa có bằng chứng: KHÔNG đoán, theo mốc Thái Bình Dương như cũ.
"""
from __future__ import annotations

import datetime as _d

MO_HO_PHUT = 20          # 429 không rõ loại

_PHUT = ("per minute", "per-minute", "per second", "requests per min", "rpm", "tpm",
         "per region", "try again in")
_NGAY = ("per day", "tokens per day", "requests per day", "tpd", "rpd", "daily",
         "quota exceeded for quota metric", "free_tier", "hết hạn mức ngày")
_CF = ("cloudflare", "neuron", "aierror")


def muc_nghi(err) -> int:
    """Số PHÚT nên cho key nghỉ, suy từ nguyên văn lỗi 429."""
    t = str(err or "").lower()
    if any(x in t for x in _PHUT):
        return 2
    if any(x in t for x in _NGAY):
        utc = _d.datetime.now(_d.timezone.utc)
        goc = utc if any(x in t for x in _CF) else utc - _d.timedelta(hours=7)
        mai = (goc + _d.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return max(10, min(int((mai - goc).total_seconds() // 60), 24 * 60))
    return MO_HO_PHUT


# ══════════════════════════════════════════════════════════════════════════════════════════
# SỔ NGHẼN THEO NHÀ CUNG CẤP (26/8/2026)
# ------------------------------------------------------------------------------------------
# Anh hỏi: "không còn cách nào fix à?" — đúng, chỉ nuốt log thì không phải sửa.
# Lỗi `HTTP 500 Internal Server Error` / `AiError` là hỏng phía NHÀ CUNG CẤP, mình không sửa
# được ở nguồn. Nhưng SỐ LẦN GẶP thì giảm được: hiện thứ tự nhà cố định (Groq → CF → Gemini),
# nên khi Groq đang trục trặc, mọi lượt vẫn đâm vào Groq, thử lại cũng Groq, và nghẽn tiếp.
#
# Sổ này ghi nhận nghẽn theo NHÀ. Nhà nào nghẽn dồn dập trong ít phút gần đây thì bị đẩy xuống
# cuối thứ tự — hệ tự né sang nhà đang khoẻ, thay vì kiên trì đâm vào cửa đang đóng.
# Tự quên sau CUA_SO_GIAY, nên nhà hồi lại là được dùng lại ngay, không phạt oan.
CUA_SO_GIAY = 300          # chỉ tính nghẽn trong 5 phút gần đây
NGUONG_NE = 3              # 3 lần trong cửa sổ -> né nhà đó

_NGHEN: dict = {}


def nha_cua(api_key: str) -> str:
    k = str(api_key or "")
    if k.startswith("gsk_"):
        return "groq"
    if k.startswith("cf:"):
        return "cf"
    return "gemini"


def ghi_nghen(api_key: str) -> None:
    """Gọi khi một lượt hỏng vì NGHẼN (không phải cạn hạn mức, không phải key hỏng)."""
    import time as _t
    nha = nha_cua(api_key)
    _NGHEN.setdefault(nha, []).append(_t.time())


def nha_dang_nghen() -> set:
    """Nhà nào nên né lúc này."""
    import time as _t
    nay = _t.time()
    ra = set()
    for nha, moc in list(_NGHEN.items()):
        con = [x for x in moc if nay - x <= CUA_SO_GIAY]
        _NGHEN[nha] = con
        if len(con) >= NGUONG_NE:
            ra.add(nha)
    return ra
