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


_RR = [0]   # bộ đếm round-robin trong tiến trình -> mỗi lần chọn key XOAY 1 nấc -> video kế dùng key KHÁC (không dội 1 key)
_REQ = {}   # đếm số request/key TRONG tiến trình -> flush cuối phiên vào req_today (biết còn bao nhiêu quota)


def _count(k):
    kid = k.get("id")
    if kid:
        _REQ[kid] = _REQ.get(kid, 0) + 1


def flush_requests() -> dict:
    """Lấy (và xóa) bảng đếm request/key trong tiến trình -> caller ghi vào Firestore req_today."""
    global _REQ
    out = dict(_REQ); _REQ = {}
    return out


def key_order(channel: str, keys: list[dict]) -> list[dict]:
    """Thứ tự thử key cho 1 kênh (theo yêu cầu user — CHIA ĐỀU, tránh dội 1 key bị chặn):
    1. ƯU TIÊN key ÍT REQUEST HÔM NAY NHẤT (req_today nhỏ) -> chia đều tải, còn nhiều quota free.
    2. NÉ key VỪA bỏ chặn + ưu tiên lâu chưa xài: max(last_used, cooling_until) tăng dần.
    3. XOAY theo kênh + ROUND-ROBIN mỗi lần -> 10 luồng không dồn 1 key, video kế trong 1 kênh cũng đổi key."""
    n = len(keys)
    if n == 0:
        return []
    def score(k):
        # req_today (Firestore, xuyên phiên) + _REQ (đã dùng TRONG phiên này) -> key CÒN NHIỀU QUOTA lên đầu.
        used = int(k.get("req_today") or 0) + _REQ.get(k.get("id"), 0)
        return (used,                                                           # 1. ít dùng nhất (còn quota) -> ưu tiên
                max(str(k.get("last_used") or ""), str(k.get("cooling_until") or "")),  # 2. né key vừa mở chặn + lâu chưa xài
                str(k.get("id") or ""))
    ks = sorted(keys, key=score)
    if n == 1:
        return ks
    start = (int(hashlib.md5(channel.encode("utf-8")).hexdigest(), 16) + _RR[0]) % n
    _RR[0] += 1                                                                  # xoay 1 nấc mỗi lần chọn -> spread đều trong phiên
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

    def _cool(k, exc):
        """Cho key NGHỈ — giới hạn PHÚT (per-minute/region) reset sau 60s -> nghỉ 90s (dư 30s cho chắc); quota NGÀY -> 90'."""
        if not (on_limit and k.get("id")):
            return
        low = str(exc).lower()
        mins = 1.5 if ("per minute" in low or "per-minute" in low or "requests per min" in low or "per region" in low) else 90
        try:
            on_limit(k["id"], mins)
        except TypeError:
            on_limit(k["id"])                     # callback cũ chỉ nhận 1 tham số

    tried = []
    for rnd in range(2):                          # 2 VÒNG: nếu CẢ LOẠT key dính giới hạn PHÚT -> chờ reset rồi thử lại (cứu kênh khỏi fail oan).
        tried = []
        for idx, k in enumerate(order):
            tag = k.get("email") or ("••••" + (k.get("key", "")[-4:]))
            if idx:
                time.sleep(1.5)                   # nhịp nhẹ giữa các key -> không burst -> không bị coi là spam
            try:
                print(f"   🔑 kênh {channel} dùng key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate(seed, vtype, api_key=k["key"], model_name=model))
            except CB.RateLimited as e:
                tried.append(tag); _cool(k, e)
                print(f"   ⚠️ key [{tag}] hết quota → nghỉ + đổi key kế")
                continue
            except Exception as e:
                if "404" in str(e) and model != "gemini-2.5-flash":
                    model = "gemini-2.5-flash"
                    print(f"   ↓ model cao không có cho [{tag}] → hạ {model}")
                    try:
                        _count(k)
                        return _ok(k, CB.generate(seed, vtype, api_key=k["key"], model_name=model))
                    except CB.RateLimited as e2:
                        tried.append(tag); _cool(k, e2)
                        continue
                raise
        if rnd == 0:                              # hết loạt key ở vòng 1 -> chờ 65s (>60s) cho giới hạn PHÚT reset hẳn, thử lại 1 lần
            print(f"   ⏳ Cả {len(order)} key dính giới hạn — chờ 65s cho giới hạn PHÚT reset rồi thử lại…")
            time.sleep(65)
    raise CB.RateLimited(f"Tất cả {len(keys)} key đều hết quota (đã thử 2 vòng: {', '.join(tried)}). "
                         f"Thêm key hoặc chờ reset ngày.")


def write_guess(channel: str, keys: list[dict], category: str, n_rounds: int = 3, tier: str = "normal",
                avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh bộ câu đố GUESS — bám key sticky, đổi key khi limit (cùng cơ chế write_story)."""
    def _ok(k, r):
        if on_ok and k.get("id"):
            try: on_ok(k["id"])
            except Exception: pass
        return r
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key nào — thêm ở tab 🎬 Render Studio.")
    order = key_order(channel, keys)
    model = model_for(tier)

    def _cool(k, exc):
        if not (on_limit and k.get("id")): return
        low = str(exc).lower()
        mins = 1.5 if ("per minute" in low or "per-minute" in low or "requests per min" in low or "per region" in low) else 90
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    tried = []
    for rnd in range(2):
        tried = []
        for idx, k in enumerate(order):
            tag = k.get("email") or ("••••" + (k.get("key", "")[-4:]))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 GUESS {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_guess(category, n_rounds, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                tried.append(tag); _cool(k, e); continue
            except Exception as e:
                if "404" in str(e) and model != "gemini-2.5-flash":
                    model = "gemini-2.5-flash"
                    try:
                        _count(k)
                        return _ok(k, CB.generate_guess(category, n_rounds, api_key=k["key"], model_name=model, avoid=avoid))
                    except CB.RateLimited as e2:
                        tried.append(tag); _cool(k, e2); continue
                raise
        if rnd == 0:
            time.sleep(65)
    raise CB.RateLimited(f"Tất cả {len(keys)} key hết quota (GUESS). Thêm key hoặc chờ reset.")


def write_mapped(channel: str, keys: list[dict], niche: str, tier: str = "normal",
                 avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh câu chuyện MAPPED — bám key sticky, đổi key khi limit (cùng cơ chế write_story)."""
    def _ok(k, r):
        if on_ok and k.get("id"):
            try: on_ok(k["id"])
            except Exception: pass
        return r
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key nào — thêm ở tab 🎬 Render Studio.")
    order = key_order(channel, keys); model = model_for(tier)

    def _cool(k, exc):
        if not (on_limit and k.get("id")): return
        low = str(exc).lower()
        mins = 1.5 if ("per minute" in low or "per-minute" in low or "requests per min" in low or "per region" in low) else 90
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    for rnd in range(2):
        for idx, k in enumerate(order):
            tag = k.get("email") or ("••••" + (k.get("key", "")[-4:]))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 MAPPED {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_mapped(niche, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                if "404" in str(e) and model != "gemini-2.5-flash":
                    model = "gemini-2.5-flash"
                    try:
                        _count(k); return _ok(k, CB.generate_mapped(niche, api_key=k["key"], model_name=model, avoid=avoid))
                    except CB.RateLimited as e2:
                        _cool(k, e2); continue
                raise
        if rnd == 0:
            time.sleep(65)
    raise CB.RateLimited(f"Tất cả {len(keys)} key hết quota (MAPPED). Thêm key hoặc chờ reset.")


def write_ranked(channel: str, keys: list[dict], niche: str, tier: str = "normal",
                 avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh tier list RANKED — bám key sticky, đổi key khi limit."""
    def _ok(k, r):
        if on_ok and k.get("id"):
            try: on_ok(k["id"])
            except Exception: pass
        return r
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key nào — thêm ở tab 🎬 Render Studio.")
    order = key_order(channel, keys); model = model_for(tier)

    def _cool(k, exc):
        if not (on_limit and k.get("id")): return
        low = str(exc).lower()
        mins = 1.5 if ("per minute" in low or "per-minute" in low or "requests per min" in low or "per region" in low) else 90
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    for rnd in range(2):
        for idx, k in enumerate(order):
            tag = k.get("email") or ("••••" + (k.get("key", "")[-4:]))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 RANKED {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_ranked(niche, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                if "404" in str(e) and model != "gemini-2.5-flash":
                    model = "gemini-2.5-flash"
                    try:
                        _count(k); return _ok(k, CB.generate_ranked(niche, api_key=k["key"], model_name=model, avoid=avoid))
                    except CB.RateLimited as e2:
                        _cool(k, e2); continue
                raise
        if rnd == 0:
            time.sleep(65)
    raise CB.RateLimited(f"Tất cả {len(keys)} key hết quota (RANKED). Thêm key hoặc chờ reset.")


def write_scaled(channel: str, keys: list[dict], niche: str, tier: str = "normal",
                 avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh so sánh kích thước SCALED — bám key sticky, đổi key khi limit."""
    def _ok(k, r):
        if on_ok and k.get("id"):
            try: on_ok(k["id"])
            except Exception: pass
        return r
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key nào — thêm ở tab 🎬 Render Studio.")
    order = key_order(channel, keys); model = model_for(tier)

    def _cool(k, exc):
        if not (on_limit and k.get("id")): return
        low = str(exc).lower()
        mins = 1.5 if ("per minute" in low or "per-minute" in low or "requests per min" in low or "per region" in low) else 90
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    for rnd in range(2):
        for idx, k in enumerate(order):
            tag = k.get("email") or ("••••" + (k.get("key", "")[-4:]))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 SCALED {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_scaled(niche, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                if "404" in str(e) and model != "gemini-2.5-flash":
                    model = "gemini-2.5-flash"
                    try:
                        _count(k); return _ok(k, CB.generate_scaled(niche, api_key=k["key"], model_name=model, avoid=avoid))
                    except CB.RateLimited as e2:
                        _cool(k, e2); continue
                raise
        if rnd == 0:
            time.sleep(65)
    raise CB.RateLimited(f"Tất cả {len(keys)} key hết quota (SCALED). Thêm key hoặc chờ reset.")


def write_thennow(channel: str, keys: list[dict], niche: str, tier: str = "normal",
                  avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh so sánh XƯA/NAY — bám key sticky, đổi key khi limit."""
    def _ok(k, r):
        if on_ok and k.get("id"):
            try: on_ok(k["id"])
            except Exception: pass
        return r
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key nào — thêm ở tab 🎬 Render Studio.")
    order = key_order(channel, keys); model = model_for(tier)

    def _cool(k, exc):
        if not (on_limit and k.get("id")): return
        low = str(exc).lower()
        mins = 1.5 if ("per minute" in low or "per-minute" in low or "requests per min" in low or "per region" in low) else 90
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    for rnd in range(2):
        for idx, k in enumerate(order):
            tag = k.get("email") or ("••••" + (k.get("key", "")[-4:]))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 THENNOW {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_thennow(niche, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                if "404" in str(e) and model != "gemini-2.5-flash":
                    model = "gemini-2.5-flash"
                    try:
                        _count(k); return _ok(k, CB.generate_thennow(niche, api_key=k["key"], model_name=model, avoid=avoid))
                    except CB.RateLimited as e2:
                        _cool(k, e2); continue
                raise
        if rnd == 0:
            time.sleep(65)
    raise CB.RateLimited(f"Tất cả {len(keys)} key hết quota (THENNOW). Thêm key hoặc chờ reset.")


def write_doc(channel: str, keys: list[dict], niche: str, style: str = "awe, cinematic", tier: str = "normal",
              avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh kịch bản TÀI LIỆU (Wave 2) — bám key sticky, đổi key khi limit."""
    def _ok(k, r):
        if on_ok and k.get("id"):
            try: on_ok(k["id"])
            except Exception: pass
        return r
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key nào — thêm ở tab 🎬 Render Studio.")
    order = key_order(channel, keys); model = model_for(tier)

    def _cool(k, exc):
        if not (on_limit and k.get("id")): return
        low = str(exc).lower()
        mins = 1.5 if ("per minute" in low or "per-minute" in low or "requests per min" in low or "per region" in low) else 90
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    for rnd in range(2):
        for idx, k in enumerate(order):
            tag = k.get("email") or ("••••" + (k.get("key", "")[-4:]))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 DOC {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_doc(niche, style, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                if "404" in str(e) and model != "gemini-2.5-flash":
                    model = "gemini-2.5-flash"
                    try:
                        _count(k); return _ok(k, CB.generate_doc(niche, style, api_key=k["key"], model_name=model, avoid=avoid))
                    except CB.RateLimited as e2:
                        _cool(k, e2); continue
                raise
        if rnd == 0:
            time.sleep(65)
    raise CB.RateLimited(f"Tất cả {len(keys)} key hết quota (DOC). Thêm key hoặc chờ reset.")
