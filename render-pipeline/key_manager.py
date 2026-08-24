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


# Nghỉ bao lâu khi dính 429 KHÔNG rõ loại. Thông báo của Gemini free thường chỉ là
# "429 You exceeded your current quota" — không nói RPM hay RPD, nên trước đây mặc định cho nghỉ 90'.
# Đo thật 21/8: mỗi 429 cắt 1 key khỏi vòng xoay 90 phút -> pool 56 key TEO XUỐNG 5 ngay trong một
# phiên, rồi hệ in "quota cạn thật" và bỏ cuộc, trong khi 51 key kia chỉ đang nghỉ.
# 20' là mức cân: pool hồi lại NGAY TRONG phiên (phiên dài 40-60'), còn nếu key cạn hạn mức NGÀY
# thật thì nó 429 lại và nghỉ tiếp — chỉ tốn 1 lệnh gọi phí mỗi 20', rẻ hơn nhiều so với đứng hình.
AMBIG_COOL_MIN = 20
import nghi_key as _NGHI          # bảng phạt key dùng chung với đường vẽ ảnh (xem nghi_key.py)


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
    # SỔ NGHỈ CỤC BỘ: cool_key ghi Firestore qua _soft — quota ghi chết là lệnh nghỉ RƠI, và
    # read_keys (đọc từ doc) vẫn trả key đó -> bị chọn lại -> nện tiếp 429. Sổ _COOLED trong RAM
    # của firestore_bridge luôn đúng bất kể Firestore sống chết -> lọc tại đây là cooldown hoạt
    # động 100% offline. Hết giờ nghỉ thì key tự quay lại (so mốc thời gian).
    try:
        import time as _t
        import firestore_bridge as _FB
        _now = _t.time()
        _cooled = {k for k, v in getattr(_FB, "_COOLED", {}).items() if v > _now}
        if _cooled:
            ks = [k for k in ks if k.get("id") not in _cooled] or ks[-1:]   # tất cả nghỉ -> giữ 1 key đỡ crash
    except Exception:
        pass
    # 23/8 — LỌC KEY KHÔNG PHẢI AI TRƯỚC MỌI VIỆC KHÁC. `gem` bên dưới được định nghĩa là "mọi key
    # không phải groq/cf", nên key ẢNH (px:/pb:) và key BẾN R2 (r2:) rơi thẳng vào danh sách Gemini
    # và bị đem đi gọi API viết chữ: mỗi lượt là 1 lần lỗi 400/401, tốn thời gian, còn bị đánh dấu
    # nghỉ oan. User sắp thêm 10 key R2 -> nếu không lọc, hồ key viết bị pha loãng nặng.
    ks = [k for k in ks if not str(k.get("key", "")).startswith(("px:", "pb:", "r2:"))]
    n = len(ks)
    if n == 0:
        return []
    if n == 1:
        return ks
    # ƯU TIÊN GROQ CHO KHÂU VIẾT (key_order chỉ phục vụ text — pool Vision/vẽ đã lọc gsk_ riêng):
    # đạn Gemini free chỉ 20 viên/key/ngày và là thứ DUY NHẤT dùng được cho Vision; Groq ~1K/key
    # chỉ viết được chữ. Không tách thì viết đốt sạch đạn Gemini trước, đến lượt Vision thì đói.
    # Groq cạn/nghỉ hết -> tự rơi về phần Gemini như cũ, không kẹt.
    # THỨ TỰ VIẾT: Groq -> CF -> Gemini (đổi 22/8 theo user). Lý do CF đứng TRƯỚC Gemini ở khâu
    # viết: đạn Gemini là thứ DUY NHẤT không thay được (Vision kiểm ảnh); Groq trục trặc thì để CF
    # gánh chữ (ảnh thật vẫn còn Openverse/Pexels, vẽ AI còn Gemini dự phòng) — Vision được bảo toàn.
    # Groq và CF cùng chạy gpt-oss-120b nên chất lượng chữ Y HỆT, chỉ khác tốc độ/hạn mức.
    groq = [k for k in ks if str(k.get("key", "")).startswith("gsk_")]
    cf = [k for k in ks if str(k.get("key", "")).startswith("cf:")]
    gem = [k for k in ks if k not in groq and k not in cf]
    if groq:
        r = (int(hashlib.md5(channel.encode("utf-8")).hexdigest(), 16) + _RR[0]) % len(groq)
        _RR[0] += 1
        return groq[r:] + groq[:r] + cf + gem
    if cf:
        r = (int(hashlib.md5(channel.encode("utf-8")).hexdigest(), 16) + _RR[0]) % len(cf)
        _RR[0] += 1
        return cf[r:] + cf[:r] + gem
    n = len(gem)
    start = (int(hashlib.md5(channel.encode("utf-8")).hexdigest(), 16) + _RR[0]) % max(1, n)
    _RR[0] += 1                                                                  # xoay 1 nấc mỗi lần chọn -> spread đều trong phiên
    return [gem[(start + i) % n] for i in range(n)]


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
        """Key CHẾT vĩnh viễn (denied/suspended) -> đánh dấu chết (loại khỏi vòng). Giới hạn PHÚT -> nghỉ 90s; quota NGÀY -> 90'."""
        if not k.get("id"):
            return
        low = str(exc).lower()
        if any(s in low for s in ("denied", "suspended", "contact support", "has not been used", "not been used", "not enabled", "disabled", "forbidden", "permission_denied", "consumer")):
            try:
                import firestore_bridge as _FB; _FB.mark_key_alive(k["id"], False, "403 project bị khoá/denied — cần THAY key", kind="permanent")
            except Exception:
                pass
            return
        if not (on_limit and k.get("id")):
            return
        # 24/8 — PHÂN LOẠI 3 MỨC (trước chỉ 2): cạn HẠN MỨC NGÀY thì nghỉ tới hết ngày, đừng gọi lại.
        # Đêm nay 16 key Groq cạn TPD mà chỉ bị phạt 20' -> cứ 20' cả 18 luồng lại dội vào đúng những
        # key đã chết, mỗi lượt tốn 1 vòng HTTP + 1.5s chờ. Đó là lý do "xoay vòng mà vẫn dồn 1 chỗ".
        # 24/8 tối — dùng CHUNG bảng phạt với đường vẽ ảnh (nghi_key.muc_nghi): tính tới MỐC RESET
        # THẬT của đúng nhà cung cấp, thay cho con số cứng 8 tiếng. 8 tiếng sai cả hai chiều: key cạn
        # lúc 20:00 UTC (Google reset 07:00 UTC) hết phạt lúc 04:00 -> dội lại 3 tiếng trước khi nó
        # hồi, mỗi lượt hỏng vẫn bị trừ; key Cloudflare cạn 02:00 UTC (đã reset từ 00:00) bị treo
        # oan tới 10:00.
        mins = _NGHI.muc_nghi(low)
        try:
            on_limit(k["id"], mins)
        except TypeError:
            on_limit(k["id"])                     # callback cũ chỉ nhận 1 tham số

    tried = []
    for rnd in range(2):                          # 2 VÒNG: nếu CẢ LOẠT key dính giới hạn PHÚT -> chờ reset rồi thử lại (cứu kênh khỏi fail oan).
        tried = []
        for idx, k in enumerate(order):
            tag = ("⚡" if str(k.get("key", "")).startswith("gsk_") else "⛅" if str(k.get("key", "")).startswith("cf:") else "") + (k.get("email") or ("••••" + (k.get("key", "")[-4:])))
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
                # 24/8 — LƯỚI AN TOÀN: bất kỳ lỗi nào MANG DẤU HIỆU quota/nghẽn đều phải cho key nghỉ
                # rồi ĐỔI KEY, không được ném lên giết cả luồng. Đêm nay 16 key Groq cạn hạn mức ngày,
                # shim ném RuntimeError -> nhánh này `raise` -> POWERPLAY ra 0 video dù còn CF + Gemini.
                _s = str(e).lower()
                if any(t in _s for t in ("429", "rate limit", "quota", "resource_exhausted", "too many requests")):
                    _cool(k, e); continue
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
        if not k.get("id"): return
        low = str(exc).lower()
        if any(s in low for s in ("denied", "suspended", "contact support", "has not been used", "not been used", "not enabled", "disabled", "forbidden", "permission_denied", "consumer")):
            try:
                import firestore_bridge as _FB; _FB.mark_key_alive(k["id"], False, "403 project bị khoá/denied — cần THAY key", kind="permanent")   # CHẾT VĨNH VIỄN -> loại khỏi vòng xoay
            except Exception: pass
            return
        if not on_limit: return
        # 24/8 — PHÂN LOẠI 3 MỨC (trước chỉ 2): cạn HẠN MỨC NGÀY thì nghỉ tới hết ngày, đừng gọi lại.
        # Đêm nay 16 key Groq cạn TPD mà chỉ bị phạt 20' -> cứ 20' cả 18 luồng lại dội vào đúng những
        # key đã chết, mỗi lượt tốn 1 vòng HTTP + 1.5s chờ. Đó là lý do "xoay vòng mà vẫn dồn 1 chỗ".
        # 24/8 tối — dùng CHUNG bảng phạt với đường vẽ ảnh (nghi_key.muc_nghi): tính tới MỐC RESET
        # THẬT của đúng nhà cung cấp, thay cho con số cứng 8 tiếng. 8 tiếng sai cả hai chiều: key cạn
        # lúc 20:00 UTC (Google reset 07:00 UTC) hết phạt lúc 04:00 -> dội lại 3 tiếng trước khi nó
        # hồi, mỗi lượt hỏng vẫn bị trừ; key Cloudflare cạn 02:00 UTC (đã reset từ 00:00) bị treo
        # oan tới 10:00.
        mins = _NGHI.muc_nghi(low)
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    tried = []
    for rnd in range(2):
        tried = []
        for idx, k in enumerate(order):
            tag = ("⚡" if str(k.get("key", "")).startswith("gsk_") else "⛅" if str(k.get("key", "")).startswith("cf:") else "") + (k.get("email") or ("••••" + (k.get("key", "")[-4:])))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 GUESS {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_guess(category, n_rounds, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                tried.append(tag); _cool(k, e); continue
            except Exception as e:
                # 24/8 — LƯỚI AN TOÀN (áp cho MỌI hàm viết): lỗi mang dấu hiệu quota/nghẽn thì cho key
                # nghỉ rồi ĐỔI KEY. Đêm nay 16 key Groq cạn hạn mức ngày, shim ném RuntimeError nên
                # nhánh này `raise` -> POWERPLAY ra 0 video dù còn 40 key + CF + Gemini chưa đụng tới.
                _s = str(e).lower()
                if any(t in _s for t in ("429", "rate limit", "quota", "resource_exhausted", "too many requests")):
                    _cool(k, e); continue
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
        if not k.get("id"): return
        low = str(exc).lower()
        if any(s in low for s in ("denied", "suspended", "contact support", "has not been used", "not been used", "not enabled", "disabled", "forbidden", "permission_denied", "consumer")):
            try:
                import firestore_bridge as _FB; _FB.mark_key_alive(k["id"], False, "403 project bị khoá/denied — cần THAY key", kind="permanent")   # CHẾT VĨNH VIỄN -> loại khỏi vòng xoay
            except Exception: pass
            return
        if not on_limit: return
        # 24/8 — PHÂN LOẠI 3 MỨC (trước chỉ 2): cạn HẠN MỨC NGÀY thì nghỉ tới hết ngày, đừng gọi lại.
        # Đêm nay 16 key Groq cạn TPD mà chỉ bị phạt 20' -> cứ 20' cả 18 luồng lại dội vào đúng những
        # key đã chết, mỗi lượt tốn 1 vòng HTTP + 1.5s chờ. Đó là lý do "xoay vòng mà vẫn dồn 1 chỗ".
        # 24/8 tối — dùng CHUNG bảng phạt với đường vẽ ảnh (nghi_key.muc_nghi): tính tới MỐC RESET
        # THẬT của đúng nhà cung cấp, thay cho con số cứng 8 tiếng. 8 tiếng sai cả hai chiều: key cạn
        # lúc 20:00 UTC (Google reset 07:00 UTC) hết phạt lúc 04:00 -> dội lại 3 tiếng trước khi nó
        # hồi, mỗi lượt hỏng vẫn bị trừ; key Cloudflare cạn 02:00 UTC (đã reset từ 00:00) bị treo
        # oan tới 10:00.
        mins = _NGHI.muc_nghi(low)
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    for rnd in range(2):
        for idx, k in enumerate(order):
            tag = ("⚡" if str(k.get("key", "")).startswith("gsk_") else "⛅" if str(k.get("key", "")).startswith("cf:") else "") + (k.get("email") or ("••••" + (k.get("key", "")[-4:])))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 MAPPED {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_mapped(niche, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                # 24/8 — LƯỚI AN TOÀN (áp cho MỌI hàm viết): lỗi mang dấu hiệu quota/nghẽn thì cho key
                # nghỉ rồi ĐỔI KEY. Đêm nay 16 key Groq cạn hạn mức ngày, shim ném RuntimeError nên
                # nhánh này `raise` -> POWERPLAY ra 0 video dù còn 40 key + CF + Gemini chưa đụng tới.
                _s = str(e).lower()
                if any(t in _s for t in ("429", "rate limit", "quota", "resource_exhausted", "too many requests")):
                    _cool(k, e); continue
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
        if not k.get("id"): return
        low = str(exc).lower()
        if any(s in low for s in ("denied", "suspended", "contact support", "has not been used", "not been used", "not enabled", "disabled", "forbidden", "permission_denied", "consumer")):
            try:
                import firestore_bridge as _FB; _FB.mark_key_alive(k["id"], False, "403 project bị khoá/denied — cần THAY key", kind="permanent")   # CHẾT VĨNH VIỄN -> loại khỏi vòng xoay
            except Exception: pass
            return
        if not on_limit: return
        # 24/8 — PHÂN LOẠI 3 MỨC (trước chỉ 2): cạn HẠN MỨC NGÀY thì nghỉ tới hết ngày, đừng gọi lại.
        # Đêm nay 16 key Groq cạn TPD mà chỉ bị phạt 20' -> cứ 20' cả 18 luồng lại dội vào đúng những
        # key đã chết, mỗi lượt tốn 1 vòng HTTP + 1.5s chờ. Đó là lý do "xoay vòng mà vẫn dồn 1 chỗ".
        # 24/8 tối — dùng CHUNG bảng phạt với đường vẽ ảnh (nghi_key.muc_nghi): tính tới MỐC RESET
        # THẬT của đúng nhà cung cấp, thay cho con số cứng 8 tiếng. 8 tiếng sai cả hai chiều: key cạn
        # lúc 20:00 UTC (Google reset 07:00 UTC) hết phạt lúc 04:00 -> dội lại 3 tiếng trước khi nó
        # hồi, mỗi lượt hỏng vẫn bị trừ; key Cloudflare cạn 02:00 UTC (đã reset từ 00:00) bị treo
        # oan tới 10:00.
        mins = _NGHI.muc_nghi(low)
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    for rnd in range(2):
        for idx, k in enumerate(order):
            tag = ("⚡" if str(k.get("key", "")).startswith("gsk_") else "⛅" if str(k.get("key", "")).startswith("cf:") else "") + (k.get("email") or ("••••" + (k.get("key", "")[-4:])))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 RANKED {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_ranked(niche, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                # 24/8 — LƯỚI AN TOÀN (áp cho MỌI hàm viết): lỗi mang dấu hiệu quota/nghẽn thì cho key
                # nghỉ rồi ĐỔI KEY. Đêm nay 16 key Groq cạn hạn mức ngày, shim ném RuntimeError nên
                # nhánh này `raise` -> POWERPLAY ra 0 video dù còn 40 key + CF + Gemini chưa đụng tới.
                _s = str(e).lower()
                if any(t in _s for t in ("429", "rate limit", "quota", "resource_exhausted", "too many requests")):
                    _cool(k, e); continue
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
        if not k.get("id"): return
        low = str(exc).lower()
        if any(s in low for s in ("denied", "suspended", "contact support", "has not been used", "not been used", "not enabled", "disabled", "forbidden", "permission_denied", "consumer")):
            try:
                import firestore_bridge as _FB; _FB.mark_key_alive(k["id"], False, "403 project bị khoá/denied — cần THAY key", kind="permanent")   # CHẾT VĨNH VIỄN -> loại khỏi vòng xoay
            except Exception: pass
            return
        if not on_limit: return
        # 24/8 — PHÂN LOẠI 3 MỨC (trước chỉ 2): cạn HẠN MỨC NGÀY thì nghỉ tới hết ngày, đừng gọi lại.
        # Đêm nay 16 key Groq cạn TPD mà chỉ bị phạt 20' -> cứ 20' cả 18 luồng lại dội vào đúng những
        # key đã chết, mỗi lượt tốn 1 vòng HTTP + 1.5s chờ. Đó là lý do "xoay vòng mà vẫn dồn 1 chỗ".
        # 24/8 tối — dùng CHUNG bảng phạt với đường vẽ ảnh (nghi_key.muc_nghi): tính tới MỐC RESET
        # THẬT của đúng nhà cung cấp, thay cho con số cứng 8 tiếng. 8 tiếng sai cả hai chiều: key cạn
        # lúc 20:00 UTC (Google reset 07:00 UTC) hết phạt lúc 04:00 -> dội lại 3 tiếng trước khi nó
        # hồi, mỗi lượt hỏng vẫn bị trừ; key Cloudflare cạn 02:00 UTC (đã reset từ 00:00) bị treo
        # oan tới 10:00.
        mins = _NGHI.muc_nghi(low)
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    for rnd in range(2):
        for idx, k in enumerate(order):
            tag = ("⚡" if str(k.get("key", "")).startswith("gsk_") else "⛅" if str(k.get("key", "")).startswith("cf:") else "") + (k.get("email") or ("••••" + (k.get("key", "")[-4:])))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 SCALED {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_scaled(niche, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                # 24/8 — LƯỚI AN TOÀN (áp cho MỌI hàm viết): lỗi mang dấu hiệu quota/nghẽn thì cho key
                # nghỉ rồi ĐỔI KEY. Đêm nay 16 key Groq cạn hạn mức ngày, shim ném RuntimeError nên
                # nhánh này `raise` -> POWERPLAY ra 0 video dù còn 40 key + CF + Gemini chưa đụng tới.
                _s = str(e).lower()
                if any(t in _s for t in ("429", "rate limit", "quota", "resource_exhausted", "too many requests")):
                    _cool(k, e); continue
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
        if not k.get("id"): return
        low = str(exc).lower()
        if any(s in low for s in ("denied", "suspended", "contact support", "has not been used", "not been used", "not enabled", "disabled", "forbidden", "permission_denied", "consumer")):
            try:
                import firestore_bridge as _FB; _FB.mark_key_alive(k["id"], False, "403 project bị khoá/denied — cần THAY key", kind="permanent")   # CHẾT VĨNH VIỄN -> loại khỏi vòng xoay
            except Exception: pass
            return
        if not on_limit: return
        # 24/8 — PHÂN LOẠI 3 MỨC (trước chỉ 2): cạn HẠN MỨC NGÀY thì nghỉ tới hết ngày, đừng gọi lại.
        # Đêm nay 16 key Groq cạn TPD mà chỉ bị phạt 20' -> cứ 20' cả 18 luồng lại dội vào đúng những
        # key đã chết, mỗi lượt tốn 1 vòng HTTP + 1.5s chờ. Đó là lý do "xoay vòng mà vẫn dồn 1 chỗ".
        # 24/8 tối — dùng CHUNG bảng phạt với đường vẽ ảnh (nghi_key.muc_nghi): tính tới MỐC RESET
        # THẬT của đúng nhà cung cấp, thay cho con số cứng 8 tiếng. 8 tiếng sai cả hai chiều: key cạn
        # lúc 20:00 UTC (Google reset 07:00 UTC) hết phạt lúc 04:00 -> dội lại 3 tiếng trước khi nó
        # hồi, mỗi lượt hỏng vẫn bị trừ; key Cloudflare cạn 02:00 UTC (đã reset từ 00:00) bị treo
        # oan tới 10:00.
        mins = _NGHI.muc_nghi(low)
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    for rnd in range(2):
        for idx, k in enumerate(order):
            tag = ("⚡" if str(k.get("key", "")).startswith("gsk_") else "⛅" if str(k.get("key", "")).startswith("cf:") else "") + (k.get("email") or ("••••" + (k.get("key", "")[-4:])))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 THENNOW {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_thennow(niche, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                # 24/8 — LƯỚI AN TOÀN (áp cho MỌI hàm viết): lỗi mang dấu hiệu quota/nghẽn thì cho key
                # nghỉ rồi ĐỔI KEY. Đêm nay 16 key Groq cạn hạn mức ngày, shim ném RuntimeError nên
                # nhánh này `raise` -> POWERPLAY ra 0 video dù còn 40 key + CF + Gemini chưa đụng tới.
                _s = str(e).lower()
                if any(t in _s for t in ("429", "rate limit", "quota", "resource_exhausted", "too many requests")):
                    _cool(k, e); continue
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
              avoid: list = None, on_limit=None, on_ok=None, speculative: bool = False,
              audit: bool = True) -> dict:
    """Sinh kịch bản TÀI LIỆU (Wave 2) — bám key sticky, đổi key khi limit.
    speculative=True (Wave 5): dùng DOC_SYS_SPECULATIVE (img_query không bó buộc phải tìm ảnh CC0 thật)."""
    def _ok(k, r):
        if on_ok and k.get("id"):
            try: on_ok(k["id"])
            except Exception: pass
        return r
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key nào — thêm ở tab 🎬 Render Studio.")
    order = key_order(channel, keys); model = model_for(tier)

    def _cool(k, exc):
        if not k.get("id"): return
        low = str(exc).lower()
        if any(s in low for s in ("denied", "suspended", "contact support", "has not been used", "not been used", "not enabled", "disabled", "forbidden", "permission_denied", "consumer")):
            try:
                import firestore_bridge as _FB; _FB.mark_key_alive(k["id"], False, "403 project bị khoá/denied — cần THAY key", kind="permanent")   # CHẾT VĨNH VIỄN -> loại khỏi vòng xoay
            except Exception: pass
            return
        if not on_limit: return
        # 24/8 — PHÂN LOẠI 3 MỨC (trước chỉ 2): cạn HẠN MỨC NGÀY thì nghỉ tới hết ngày, đừng gọi lại.
        # Đêm nay 16 key Groq cạn TPD mà chỉ bị phạt 20' -> cứ 20' cả 18 luồng lại dội vào đúng những
        # key đã chết, mỗi lượt tốn 1 vòng HTTP + 1.5s chờ. Đó là lý do "xoay vòng mà vẫn dồn 1 chỗ".
        # 24/8 tối — dùng CHUNG bảng phạt với đường vẽ ảnh (nghi_key.muc_nghi): tính tới MỐC RESET
        # THẬT của đúng nhà cung cấp, thay cho con số cứng 8 tiếng. 8 tiếng sai cả hai chiều: key cạn
        # lúc 20:00 UTC (Google reset 07:00 UTC) hết phạt lúc 04:00 -> dội lại 3 tiếng trước khi nó
        # hồi, mỗi lượt hỏng vẫn bị trừ; key Cloudflare cạn 02:00 UTC (đã reset từ 00:00) bị treo
        # oan tới 10:00.
        mins = _NGHI.muc_nghi(low)
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    skip = set()   # nhà cung cấp bị BỎ trong lượt gọi này (413: prompt quá cỡ — key nào cùng nhà cũng dính y hệt)
    for rnd in range(2):
        for idx, k in enumerate(order):
            if any(str(k.get("key", "")).startswith(p) for p in skip):
                continue
            tag = ("⚡" if str(k.get("key", "")).startswith("gsk_") else "⛅" if str(k.get("key", "")).startswith("cf:") else "") + (k.get("email") or ("••••" + (k.get("key", "")[-4:])))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 DOC {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, CB.generate_doc(niche, style, api_key=k["key"], model_name=model, avoid=avoid, speculative=speculative, audit=audit))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                if "413" in str(e):
                    # Groq free giới hạn ~8K token/request — prompt DOC (niche+avoid+ngữ cảnh phần) vượt cỡ
                    # thì MỌI key cùng nhà đều dính y hệt (22/8: VAULTUSA thử 2 lần/key toàn 413, 0 video).
                    # -> bỏ cả nhóm nhà đó, đi thẳng tới Gemini (nuốt prompt lớn thoải mái).
                    pfx = "gsk_" if str(k.get("key", "")).startswith("gsk_") else ("cf:" if str(k.get("key", "")).startswith("cf:") else "")
                    if pfx:
                        skip.add(pfx)
                        print(f"   ↪️ 413 prompt quá cỡ với nhà [{pfx}] — bỏ nhóm này, chuyển key nhà khác.")
                        continue
                if "404" in str(e) and model != "gemini-2.5-flash":
                    model = "gemini-2.5-flash"
                    try:
                        _count(k); return _ok(k, CB.generate_doc(niche, style, api_key=k["key"], model_name=model, avoid=avoid, speculative=speculative, audit=audit))
                    except CB.RateLimited as e2:
                        _cool(k, e2); continue
                raise
        if rnd == 0:
            time.sleep(65)
    raise CB.RateLimited(f"Tất cả {len(keys)} key hết quota (DOC). Thêm key hoặc chờ reset.")


def _write_wave4(fn_name, label, channel, keys, niche, tier, avoid, on_limit, on_ok):
    """Dùng CHUNG cho SWARM/PULSE/CLOCKWORK/LONGSHOT (Wave 4) — cùng khuôn write_scaled, chỉ khác hàm sinh."""
    def _ok(k, r):
        if on_ok and k.get("id"):
            try: on_ok(k["id"])
            except Exception: pass
        return r
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key nào — thêm ở tab 🎬 Render Studio.")
    order = key_order(channel, keys); model = model_for(tier)
    gen = getattr(CB, fn_name)

    def _cool(k, exc):
        if not k.get("id"): return
        low = str(exc).lower()
        if any(s in low for s in ("denied", "suspended", "contact support", "has not been used", "not been used", "not enabled", "disabled", "forbidden", "permission_denied", "consumer")):
            try:
                import firestore_bridge as _FB; _FB.mark_key_alive(k["id"], False, "403 project bị khoá/denied — cần THAY key", kind="permanent")
            except Exception: pass
            return
        if not on_limit: return
        # 24/8 — PHÂN LOẠI 3 MỨC (trước chỉ 2): cạn HẠN MỨC NGÀY thì nghỉ tới hết ngày, đừng gọi lại.
        # Đêm nay 16 key Groq cạn TPD mà chỉ bị phạt 20' -> cứ 20' cả 18 luồng lại dội vào đúng những
        # key đã chết, mỗi lượt tốn 1 vòng HTTP + 1.5s chờ. Đó là lý do "xoay vòng mà vẫn dồn 1 chỗ".
        # 24/8 tối — dùng CHUNG bảng phạt với đường vẽ ảnh (nghi_key.muc_nghi): tính tới MỐC RESET
        # THẬT của đúng nhà cung cấp, thay cho con số cứng 8 tiếng. 8 tiếng sai cả hai chiều: key cạn
        # lúc 20:00 UTC (Google reset 07:00 UTC) hết phạt lúc 04:00 -> dội lại 3 tiếng trước khi nó
        # hồi, mỗi lượt hỏng vẫn bị trừ; key Cloudflare cạn 02:00 UTC (đã reset từ 00:00) bị treo
        # oan tới 10:00.
        mins = _NGHI.muc_nghi(low)
        try: on_limit(k["id"], mins)
        except TypeError: on_limit(k["id"])

    for rnd in range(2):
        for idx, k in enumerate(order):
            tag = ("⚡" if str(k.get("key", "")).startswith("gsk_") else "⛅" if str(k.get("key", "")).startswith("cf:") else "") + (k.get("email") or ("••••" + (k.get("key", "")[-4:])))
            if idx: time.sleep(1.5)
            try:
                print(f"   🔑 {label} {channel} key [{tag}] · model {model}")
                _count(k)
                return _ok(k, gen(niche, api_key=k["key"], model_name=model, avoid=avoid))
            except CB.RateLimited as e:
                _cool(k, e); continue
            except Exception as e:
                # 24/8 — LƯỚI AN TOÀN (áp cho MỌI hàm viết): lỗi mang dấu hiệu quota/nghẽn thì cho key
                # nghỉ rồi ĐỔI KEY. Đêm nay 16 key Groq cạn hạn mức ngày, shim ném RuntimeError nên
                # nhánh này `raise` -> POWERPLAY ra 0 video dù còn 40 key + CF + Gemini chưa đụng tới.
                _s = str(e).lower()
                if any(t in _s for t in ("429", "rate limit", "quota", "resource_exhausted", "too many requests")):
                    _cool(k, e); continue
                if "404" in str(e) and model != "gemini-2.5-flash":
                    model = "gemini-2.5-flash"
                    try:
                        _count(k); return _ok(k, gen(niche, api_key=k["key"], model_name=model, avoid=avoid))
                    except CB.RateLimited as e2:
                        _cool(k, e2); continue
                raise
        if rnd == 0:
            time.sleep(65)
    raise CB.RateLimited(f"Tất cả {len(keys)} key hết quota ({label}). Thêm key hoặc chờ reset.")


def write_swarm(channel: str, keys: list[dict], niche: str, tier: str = "normal", avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh kịch bản SWARM — bám key sticky, đổi key khi limit."""
    return _write_wave4("generate_swarm", "SWARM", channel, keys, niche, tier, avoid, on_limit, on_ok)


def write_pulse(channel: str, keys: list[dict], niche: str, tier: str = "normal", avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh kịch bản PULSE — bám key sticky, đổi key khi limit."""
    return _write_wave4("generate_pulse", "PULSE", channel, keys, niche, tier, avoid, on_limit, on_ok)


def write_clockwork(channel: str, keys: list[dict], niche: str, tier: str = "normal", avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh kịch bản CLOCKWORK — bám key sticky, đổi key khi limit."""
    return _write_wave4("generate_clockwork", "CLOCKWORK", channel, keys, niche, tier, avoid, on_limit, on_ok)


def write_longshot(channel: str, keys: list[dict], niche: str, tier: str = "normal", avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh kịch bản LONGSHOT — bám key sticky, đổi key khi limit."""
    return _write_wave4("generate_longshot", "LONGSHOT", channel, keys, niche, tier, avoid, on_limit, on_ok)


def write_toon(channel: str, keys: list[dict], niche: str, tier: str = "normal", avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh skit TOON (22/8) — cùng khuôn Wave 4: bám key, xoay khi limit."""
    return _write_wave4("generate_toon", "TOON", channel, keys, niche, tier, avoid, on_limit, on_ok)


def write_tale(channel: str, keys: list[dict], niche: str, tier: str = "normal", avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh chuyện narrator (toon mode story) — cùng khuôn Wave 4."""
    return _write_wave4("generate_tale", "TALE", channel, keys, niche, tier, avoid, on_limit, on_ok)

def review_script(channel: str, keys: list[dict], story: dict, niche: str = "", tier: str = "normal",
                  avoid: list = None) -> dict:
    """SOI LẠI kịch bản 1 lượt trước khi render (23/8). Không có key/lỗi -> trả nguyên bản, KHÔNG chặn."""
    if not keys or not isinstance(story, dict):
        return story
    model = model_for(tier)
    for k in key_order(channel, keys)[:2]:          # thử tối đa 2 key rồi thôi — đây là bước phụ
        try:
            return CB.review_script(story, niche, api_key=k.get("key"), model_name=model, avoid=avoid)
        except Exception:
            continue
    return story


def write_essay(channel: str, keys: list[dict], niche: str, tier: str = "normal", avoid: list = None, on_limit=None, on_ok=None) -> dict:
    """Sinh BÀI PHÂN TÍCH lật-ngược-niềm-tin (toon mode essay, 23/8) — cùng khuôn Wave 4."""
    return _write_wave4("generate_essay", "ESSAY", channel, keys, niche, tier, avoid, on_limit, on_ok)


# ── CỔNG CHẤT LƯỢNG BỌC NGOÀI MỌI HÀM VIẾT (23/8) ───────────────────────────────────────────
# Bọc ở đây thay vì sửa 12 hàm sinh: mọi format đều đi qua write_* nên chỉ cần một lớp áo.
# Làm 3 việc, đúng thứ tự rẻ-trước-đắt:
#   1) TRƯỚC KHI VIẾT: chèn gợi ý TRỤ NỘI DUNG đang ít tập nhất vào niche -> kênh có mạch.
#   2) SAU KHI VIẾT: so dấu vân từ khoá với tối đa 4000 bài cũ -> trùng ý thì viết lại 1 lần.
#   3) Kiểm chuẩn kiếm tiền (nguồn, số liệu, câu chữ rủi ro) -> cảnh báo sớm, khỏi tốn công render.
# Mọi lỗi của cổng đều nuốt: cổng chất lượng KHÔNG được phép làm chết luồng sản xuất.
import inspect as _inspect

_GATE_NAMES = ("write_story", "write_guess", "write_mapped", "write_ranked", "write_scaled",
               "write_thennow", "write_doc", "write_swarm", "write_pulse", "write_clockwork",
               "write_longshot", "write_toon", "write_tale", "write_essay")


def _gate_title(d):
    return str((d or {}).get("title_yt") or (d or {}).get("title") or (d or {}).get("topic") or "")


def _gate_text(d):
    """Ngữ cảnh để so trùng: tiêu đề + hook + 2 câu đầu. Chỉ mỗi tiêu đề thì quá ít từ, so không nổi."""
    d = d or {}
    parts = [_gate_title(d), str(d.get("hook") or "")]
    for key, sub in (("scenes", "nar"), ("dialog", "line"), ("waypoints", "vo"), ("pairs", "vo")):
        for x in (d.get(key) or [])[:2]:
            if isinstance(x, dict):
                parts.append(str(x.get(sub) or ""))
    return " ".join(p for p in parts if p)[:400]


def _wrap_gate(fn):
    sig_has_avoid = "avoid" in _inspect.signature(fn).parameters

    def inner(channel, keys, *a, **kw):
        import quality_gate as QG
        try:
            import firestore_bridge as _FB
            import os as _os
            owner = _os.environ.get("OWNER_UID", "")
            mem = _FB.read_channel_memory(owner, channel) if owner else {"fps": [], "pillars": {}}
        except Exception:
            owner, mem, _FB = "", {"fps": [], "pillars": {}}, None

        # (1) gợi ý trụ nội dung — chỉ chèn khi tham số thứ 3 là 'niche' dạng chuỗi
        hint = ""
        try:
            hint = QG.pillar_hint(mem.get("pillars") or {})
            if hint and a and isinstance(a[0], str) and len(a[0]) > 12:
                a = (a[0] + hint,) + a[1:]
        except Exception:
            pass

        d = fn(channel, keys, *a, **kw)

        # (2) trùng ý với bài cũ -> viết lại đúng 1 lần (không lặp vô hạn, không đốt key)
        try:
            title = _gate_title(d)
            dup, muc, _ = QG.too_similar(_gate_text(d), mem.get("fps") or [])
            if dup and sig_has_avoid:
                print(f"   ♻️ trùng ý {int(muc * 100)}% với bài cũ: '{title[:48]}' -> viết lại 1 lần")
                kw2 = dict(kw)
                kw2["avoid"] = list(kw.get("avoid") or []) + [title]
                d2 = fn(channel, keys, *a, **kw2)
                if _gate_title(d2):
                    d = d2
        except Exception:
            pass

        # (3) chuẩn kiếm tiền + ghi mạch kênh
        try:
            errs = QG.money_safe(d)
            if errs:
                print("   ⚠️ chuẩn kiếm tiền: " + " · ".join(errs[:3]))
            if owner and _FB:
                _FB.append_channel_memory(owner, channel, QG.fingerprint(_gate_text(d)),
                                          str((d or {}).get("pillar") or "")[:40])
        except Exception:
            pass
        return d

    inner.__name__ = fn.__name__
    inner.__doc__ = (fn.__doc__ or "") + "\n\n(bọc thêm cổng chất lượng: mạch kênh · chống trùng ý · chuẩn kiếm tiền)"
    return inner


for _n in _GATE_NAMES:
    _f = globals().get(_n)
    if callable(_f) and not getattr(_f, "_gated", False):
        _g = _wrap_gate(_f)
        _g._gated = True
        globals()[_n] = _g
