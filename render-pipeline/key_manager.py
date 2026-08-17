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
    """Thứ tự thử key cho 1 kênh: BẮT ĐẦU từ key sticky của kênh, rồi xoay vòng (ổn định, không random).
    QUAN TRỌNG: sort key theo id TRƯỚC -> Firestore trả thứ tự nào thì sticky vẫn KHÔNG đổi."""
    ks = sorted(keys, key=lambda k: str(k.get("id") or k.get("email") or k.get("key", "")))
    n = len(ks)
    if n == 0:
        return []
    start = int(hashlib.md5(channel.encode("utf-8")).hexdigest(), 16) % n
    return [ks[(start + i) % n] for i in range(n)]


def model_for(tier: str) -> str:
    """Kênh quan trọng -> model cao hơn. (content_brain tự dò lại nếu model này 404 với key)."""
    return "gemini-3.1-pro-preview" if tier == "flagship" else "gemini-3.5-flash"


def write_story(channel: str, keys: list[dict], seed: str,
                vtype: str = "short", tier: str = "normal", on_limit=None) -> dict:
    """Viết 1 data-story cho kênh: bám key sticky, đổi key khi limit, hạ model nếu cần.
    on_limit(key_id): callback khi 1 key bị rate-limit -> tầng trên cho key NGHỈ (cool_key) chống die."""
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
            return CB.generate(seed, vtype, api_key=k["key"], model_name=model)
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
                    return CB.generate(seed, vtype, api_key=k["key"], model_name=model)
                except CB.RateLimited:
                    tried.append(tag)
                    if on_limit and k.get("id"):
                        on_limit(k["id"])
                    continue
            raise
    raise CB.RateLimited(f"Tất cả {len(keys)} key đều hết quota (đã thử: {', '.join(tried)}). "
                         f"Chờ reset (thường theo ngày) hoặc thêm key ở tab Render Studio.")
