"""
key_manager.py — Quản lý Gemini key THÔNG MINH (chống chặn, chống spam, chất lượng cao).

Nguyên tắc (theo yêu cầu user):
1. MỖI KÊNH bám 1 KEY CỐ ĐỊNH (sticky) -> coherent, đúng quota/tài khoản, không loạn context.
2. CHỈ đổi key khi key đó BỊ GIỚI HẠN (429/quota) -> failover sang key kế trong thứ tự sticky.
3. Kênh QUAN TRỌNG (tier=flagship) dùng MODEL CAO HƠN (pro); còn lại Flash (free rộng, ổn định).
4. Nếu model cao không khả dụng (key mới 404 pro) -> tự hạ Flash, không gãy.

keys = [{"id":..., "key":"AIza...", "email":"a@gmail.com"}, ...]  (đọc từ Firestore gemini_keys)
"""
from __future__ import annotations
import hashlib
import time
import content_brain as CB


def key_order(channel: str, keys: list[dict]) -> list[dict]:
    """Thứ tự thử key cho 1 kênh (theo yêu cầu user):
    1. ƯU TIÊN key LÂU CHƯA XÀI NHẤT (last_used cũ / chưa xài lần nào) -> chia đều, key nghỉ đủ lâu.
    2. NÉ key VỪA bỏ chặn: cooling_until mới -> đẩy xuống CUỐI (để nghỉ thêm, tránh bị chặn lại lâu hơn).
       -> sort theo max(last_used, cooling_until) TĂNG DẦN: "" (chưa xài/chưa chặn) đứng đầu, vừa-bỏ-chặn cuối.
    3. XOAY theo kênh -> 10 luồng SONG SONG không cùng chọn 1 key đầu (không dội 1 project -> tránh bị chặn)."""
    n = len(keys)
    if n == 0:
        return []
    def idle(k):   # cũ nhất -> nhỏ nhất -> ưu tiên; id để tiebreak ổn định
        return (max(str(k.get("last_used") or ""), str(k.get("cooling_until") or "")), str(k.get("id") or ""))
    ks = sorted(keys, key=idle)
    if n == 1:
        return ks
    start = int(hashlib.md5(channel.encode("utf-8")).hexdigest(), 16) % n
    return [ks[(start + i) % n] for i in range(n)]


def model_for(tier: str) -> str:
    """Kênh quan trọng -> model cao hơn. (content_brain tự dò lại nếu model này 404 với key)."""
    return "gemini-3.1-pro-preview" if tier == "flagship" else "gemini-3.5-flash"


def write_story(channel: str, keys: list[dict], seed: str,
                vtype: str = "short", tier: str = "normal", on_limit=None, on_ok=None) -> dict:
    """Viết 1 data-story cho kênh: bám key sticky, đổi key khi limit, hạ model nếu cần.
    on_limit(key_id): key bị rate-limit -> cho NGHỈ. on_ok(key_id): key viết OK -> đánh dấu SỐNG (khỏi health-check riêng)."""
    def _ok(k, r):
        if on_ok and k.get("id"):
            try: on_ok(k["id"])
            except Exception: pass
        return r
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key nào — thêm ở tab 🎬 Render Studio.")
    order = key_order(channel, keys)
    model = model_for(tier)
    tried = []
    for idx, k in enumerate(order):
        tag = k.get("email") or ("••••" + (k.get("key", "")[-4:]))
        if idx:
            time.sleep(1.5)                       # nhịp nhẹ giữa các key -> không burst -> không bị coi là spam
        try:
            print(f"   🔑 kênh {channel} dùng key [{tag}] · model {model}")
            return _ok(k, CB.generate(seed, vtype, api_key=k["key"], model_name=model))
        except CB.RateLimited:
            tried.append(tag)
            if on_limit and k.get("id"):
                on_limit(k["id"])                 # cho key này NGHỈ (cooldown) -> vòng sau bỏ qua, không hammer
            print(f"   ⚠️ key [{tag}] hết quota → nghỉ + đổi key kế")
            continue
        except Exception as e:
            if "404" in str(e) and model != "gemini-2.5-flash":
                model = "gemini-2.5-flash"
                print(f"   ↓ model cao không có cho [{tag}] → hạ {model}")
                try:
                    return _ok(k, CB.generate(seed, vtype, api_key=k["key"], model_name=model))
                except CB.RateLimited:
                    tried.append(tag)
                    if on_limit and k.get("id"):
                        on_limit(k["id"])
                    continue
            raise
    raise CB.RateLimited(f"Tất cả {len(keys)} key đều hết quota (đã thử: {', '.join(tried)}). "
                         f"Chờ reset (thường theo ngày) hoặc thêm key ở tab Render Studio.")
