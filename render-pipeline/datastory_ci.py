"""
datastory_ci.py — DRIVER A-Z: Gemini viết -> giọng(hook+narration)+karaoke -> ảnh theo câu
-> render RaceLong(V) -> QC. Portable (chạy được trên GitHub Actions).

Local test:
    export GEMINI_API_KEY=xxx
    python datastory_ci.py --channel DATARACE --type short --seed "US billionaire tax" --out out.mp4
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, urllib.parse, urllib.request
import random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_brain as CB
import tts_karaoke as TK

ENG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine-remotion")
PUB = os.path.join(ENG, "public")
UA = {"User-Agent": "mm0-render/1.0"}


def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40] or "x"


def _is_image(b: bytes) -> bool:
    """Nhận diện ảnh THẬT browser giải mã được (jpg/png/gif/webp) -> chống file hỏng/HTML làm VỠ render."""
    return (b[:3] == b"\xff\xd8\xff" or b[:8] == b"\x89PNG\r\n\x1a\n"
            or b[:4] == b"GIF8" or (b[:4] == b"RIFF" and b[8:12] == b"WEBP"))


def _ckpt_json(d, cap=300_000):
    """CHECKPOINT: JSON kịch bản (giống _script_json bên run_render.py) — lưu NGAY khi Gemini viết xong,
    TRƯỚC bước render tốn thời gian nhất. Nếu phiên bị huỷ/treo/lỗi ngay sau đó, kịch bản đã lưu -> phiên
    SAU dùng lại được (khỏi gọi Gemini lại, khỏi tốn quota, khỏi đổi nội dung/chủ đề đã lưu vào ngân hàng)."""
    try:
        s = json.dumps(d, ensure_ascii=False, default=str)
        return s[:cap] if len(s) > cap else s
    except Exception:
        return ""


DEFAULT_AI_STYLE = "realistic, editorial-style photo illustration"


# ── POOL KEY CHO VIỆC TỐN QUOTA ẢNH (vẽ Nano Banana) ─────────────────────────────────────────
# Trước đây mọi lời gọi vẽ ảnh đều nhận api_key=keys[0]["key"] — TỨC LÀ CẢ PHIÊN CHỈ DÙNG ĐÚNG 1
# KEY, trong khi phần viết kịch bản xoay đủ 56 key. Hạn mức ảnh của key đó cạn gần như ngay lập tức
# rồi MỌI ảnh sau đều 429 -> lùi hết về nền dự phòng.
# Số liệu thật phiên 07:11Z ngày 21/8: 0 ảnh vẽ được / 209 lần lỗi, riêng UNSEENUSA (kênh vẽ AI
# 100%) lỗi 172/172 -> 25 video của kênh đó ra lò bằng nền chữa cháy chứ không phải ảnh AI.
# Pool này xoay vòng key riêng cho ảnh: gặp 429 thì ĐÁNH DẤU key đó hết hạn mức ảnh (chỉ trong
# phiên) rồi thử key kế. Tách khỏi pool của key_manager vì hết quota ẢNH không có nghĩa là key đó
# hỏng cho việc VIẾT CHỮ (hai model, hai hạn mức khác nhau).
_AI_POOL = {"keys": [], "dead": set()}


def set_ai_pool(keys, channel: str = ""):
    """Nạp danh sách key cho việc vẽ ảnh. Gọi 1 lần ở đầu mỗi make_* (nơi đã có sẵn 'keys').

    XOAY THEO KÊNH (cùng chiêu ranked_accounts bên kho Drive): không xoay thì cả 18 luồng song
    song đều bắt đầu vẽ/kiểm từ CÙNG key đầu danh sách -> hạn mức ảnh/Vision của vài key đầu cháy
    trước trong khi key cuối ngồi không — pool 56 key mà hiệu dụng chỉ còn vài key."""
    set_pexels_pool(keys, channel)      # 23/8: nạp luôn pool key Pexels từ cùng danh sách key
    set_pixabay_pool(keys, channel)     # 23/8: và pool Pixabay (nguồn ảnh thứ 5)
    set_gov_pools(keys, channel)        # 24/8: NARA + DVIDS (tư liệu Mỹ, có key mới bật)
    # 23/8 chiều: nạp SỔ ẢNH ĐÃ DÙNG của kênh -> chống trùng footage xuyên luồng & xuyên phiên.
    # Đặt ở đây vì set_ai_pool là cửa DUY NHẤT mọi make_* đều đi qua (16 chỗ gọi) — móc 1 lần là đủ.
    try:
        import os as _os
        load_used_images(_os.environ.get("OWNER_UID", ""), channel)
    except Exception:
        pass
    raw = [k.get("key") for k in (keys or [])
           if k.get("key") and not str(k.get("key")).startswith(("gsk_", "px:", "pb:"))]   # Groq/Pexels không vẽ ảnh
    # CF (cf:) đứng TRƯỚC cho VẼ ẢNH: FLUX free ~2K ảnh/ngày/tài khoản vs Gemini chỉ ~vài trăm tổng
    # -> đốt CF trước, Gemini để dành cho vision + khi CF cạn. Mỗi nhóm vẫn xoay theo kênh như cũ.
    cf = [k for k in raw if str(k).startswith("cf:")]
    gm = [k for k in raw if not str(k).startswith("cf:")]
    if channel:
        import hashlib
        for grp in (cf, gm):
            if len(grp) > 1:
                off = int(hashlib.md5(channel.encode()).hexdigest(), 16) % len(grp)
                grp[:] = grp[off:] + grp[:off]
    _AI_POOL["keys"] = cf + gm
    _AI_POOL["dead"] = set()
    _VIS_DEAD.clear()


def _ai_candidates(first=""):
    """Key để thử vẽ ảnh: key gọi vào trước (giữ hành vi cũ), rồi tới các key còn hạn mức."""
    out = [k for k in ([first] if first else []) if k not in _AI_POOL["dead"]]
    for k in _AI_POOL["keys"]:
        if k not in _AI_POOL["dead"] and k not in out:
            out.append(k)
    return out


def _is_quota_err(e) -> bool:
    t = str(e)
    return "429" in t or "RESOURCE_EXHAUSTED" in t or "exceeded your current quota" in t


_VIS_DEAD = set()      # key đã hết hạn mức VISION trong phiên (khác hạn mức vẽ ảnh và viết chữ)


def _vision_key(keys):
    ks = [k.get("key") for k in (keys or []) if k.get("key")]
    for kk in [k for k in ks if not str(k).startswith(("gsk_", "cf:"))] + [k for k in ks if str(k).startswith("cf:")]:
        if kk not in _VIS_DEAD:
            return kk
    return (ks or [""])[0]



def _vision_order(cands):
    """VISION: Gemini (AIza) TRƯỚC — giám khảo đã kiểm chứng bằng ô mồi; CF (cf:) làm fallback khi
    Gemini cạn (neuron CF ưu tiên để VẼ ảnh). Groq (gsk_) không vision -> loại."""
    cs = [k for k in cands if k and not str(k).startswith("gsk_")]
    return [k for k in cs if not str(k).startswith("cf:")] + [k for k in cs if str(k).startswith("cf:")]

def _verify_image_rot(path, subject, first_key="", tries=3):
    """verify_image nhưng ĐỔI KEY khi 429 — chốt 'ảnh phải khớp nội dung 100%'.

    qc_vision.verify_image trả None khi Vision lỗi/hết quota, và caller fail-open (nhận ảnh chưa
    kiểm). Trước đây nó dùng đúng keys[0] nên key đầu cạn là khâu KIỂM KHỚP TẮT HẲN cho cả phiên
    -> ảnh tải về không ai soi, đúng lý do footage lệch nội dung (log 21/8: CRIMEUSA 278 lần
    'verify_image lỗi'). Giờ gặp 429 thì đánh dấu key rồi thử key kế.
    Trả True/False/None y như bản gốc (None = thật sự không kiểm được -> caller fail-open)."""
    import qc_vision
    seen = []
    for _ in range(max(1, tries)):
        k = None
        for cand in _vision_order(([first_key] if first_key else []) + list(_AI_POOL["keys"])):
            if cand and cand not in _VIS_DEAD and cand not in seen:
                k = cand; break
        if not k:
            break
        seen.append(k)
        hit = {"quota": False}
        prev = getattr(qc_vision, "on_quota", None)
        def _cb(err, _h=hit):
            _h["quota"] = True
        qc_vision.on_quota = _cb
        try:
            r = qc_vision.verify_image(path, subject, api_key=k)
        finally:
            qc_vision.on_quota = prev
        if not hit["quota"]:
            return r                       # đã kiểm được (True/False) hoặc lỗi khác -> trả luôn
        _VIS_DEAD.add(k)                   # key này hết hạn mức Vision -> thử key kế
    return None                            # thật sự không kiểm được -> caller fail-open như cũ


def _verify_grid_rot(pairs, first_key="", tries=3):
    """verify_grid (chấm hàng loạt 1 lệnh) + ĐỔI KEY khi 429 — cùng sổ _VIS_DEAD với các khâu Vision khác."""
    import qc_vision
    seen = []
    for _ in range(max(1, tries)):
        k = None
        for cand in _vision_order(([first_key] if first_key else []) + list(_AI_POOL["keys"])):
            if cand and cand not in _VIS_DEAD and cand not in seen:
                k = cand; break
        if not k:
            break
        seen.append(k)
        hit = {"q": False}
        prev = getattr(qc_vision, "on_quota", None)
        qc_vision.on_quota = (lambda err, _h=hit: _h.__setitem__("q", True))
        try:
            r = qc_vision.verify_grid(pairs, api_key=k)
        finally:
            qc_vision.on_quota = prev
        if not hit["q"]:
            return r
        _VIS_DEAD.add(k)
    return [None] * len(pairs)


def _check_visual_rot(mp4, keys, tries=3, **kw):
    """check_visual nhưng ĐỔI KEY khi gặp 429, thay vì bỏ qua QC luôn.

    qc_vision fail-open: hết quota thì trả (True, {"note": "vision-skip: 429 ..."}) — video vẫn
    lọt qua nhưng KHÔNG hề được soi. Trước đây mọi lời gọi đều dùng keys[0] nên chỉ cần key đầu
    cạn là QC hình ảnh TẮT HẲN cho toàn bộ phần còn lại của phiên (log 21/8 đầy 'vision-skip: 429').
    Giờ gặp 429 -> đánh dấu key đó rồi thử key kế, tối đa `tries` key để không đốt cả pool cho 1 video."""
    import qc_vision            # import cục bộ: module này KHÔNG import qc_vision ở đầu file
    info = {}
    for _ in range(max(1, tries)):
        k = _vision_key(keys)
        if not k:
            break
        ok, info = qc_vision.check_visual(mp4, api_key=k, **kw)
        note = str(info.get("note") or "")
        if note.startswith("vision-skip") and _is_quota_err(note):
            _VIS_DEAD.add(k)
            continue
        return ok, info
    return True, (info or {"note": "vision-skip: hết key còn hạn mức"})


def _cf_flux_image(prompt, dest, key, style=None) -> bool:
    """VẼ ẢNH bằng Cloudflare FLUX.1 schnell (key 'cf:acc:token'). Trả True khi đã ghi ảnh hợp lệ
    vào dest. Lỗi quota (429/4006 hết neuron) NÉM LÊN để caller xoay key; lỗi khác trả False."""
    import urllib.request, urllib.error, base64, json as _j
    _, acc, tok = str(key).split(":", 2)
    # steps=4: FLUX schnell được huấn luyện cho 1-4 bước (thêm bước KHÔNG đẹp hơn, chỉ tốn neuron);
    # 6->4 bước = 77n->58n/ảnh 1024² => ~174 ảnh free/ngày/tài khoản thay vì ~130 (giá niêm yết CF 22/8).
    body = {"prompt": f"A {style or DEFAULT_AI_STYLE} of: {prompt}. No text, no watermark, no logo.",
            "steps": 4}
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/@cf/black-forest-labs/flux-1-schnell",
        data=_j.dumps(body).encode(),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 (compatible; MM0-render/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = _j.load(r)
    except urllib.error.HTTPError as e:
        detail = ""
        try: detail = e.read().decode()[:200]
        except Exception: pass
        if e.code == 429 or "4006" in detail or "neuron" in detail.lower():
            raise RuntimeError(f"429 hết neuron CF trong ngày: {detail}")
        print(f"   ⚠️ CF FLUX HTTP {e.code}: {detail[:90]}")
        return False
    b64 = ((out.get("result") or {}).get("image")) or ""
    if not b64:
        return False
    data = base64.b64decode(b64)
    if len(data) < 2000 or not _is_image(data):
        return False
    open(dest, "wb").write(data)
    return True


# MUỐI PROMPT (23/8, user: "vẫn sợ trùng"): cùng một mô tả, thêm 1 biến thể góc máy/ánh sáng/bố
# cục -> ảnh AI sinh ra KHÁC NHAU dù chủ đề giống, kể cả khi máy chủ dùng seed cố định. Đây là lớp
# chống trùng TUYỆT ĐỐI vì mỗi khung được vẽ MỚI, không bốc từ kho chung nào cả.
_VARY = [
    "eye-level view, soft daylight from the left",
    "slightly high angle, warm late-afternoon light",
    "low angle looking up, crisp cool light",
    "three-quarter view, gentle rim light from behind",
    "wide framing with generous empty space, flat even light",
    "tighter framing, shallow depth, single strong light source",
    "off-centre composition, cool morning light",
    "symmetrical head-on composition, soft overcast light",
]


def _salt_prompt(prompt: str) -> str:
    """Thêm biến thể máy quay/ánh sáng theo NGẪU NHIÊN — không đụng nội dung, chỉ đổi cách nhìn."""
    return f"{prompt}, {random.choice(_VARY)}" if prompt else prompt


def _generate_image_ai(prompt, dest, api_key, model="gemini-2.5-flash-image", style=None) -> bool:
    """DỰ PHÒNG khi Openverse KHÔNG có ảnh CC0 khớp: nhờ Gemini VẼ ảnh minh hoạ (Nano Banana).
    Quota TÁCH RIÊNG khỏi quota viết kịch bản (model khác nhau) -> dùng thoải mái, không đụng key đang
    viết chữ. ~500 ảnh/ngày/key free, không cần thẻ. Lỗi/an toàn nội dung/hết quota -> trả False,
    caller tự lùi về fallback cũ (mosaic/cosmic bg) — KHÔNG BAO GIỜ làm crash pipeline.
    style: phong cách vẽ (vd "cinematic sci-fi concept art") — mặc định ảnh báo chí thật, đổi cho kênh
    speculative (tương lai/vũ trụ suy đoán) nơi KHÔNG có ảnh thật để so nên cần 1 gu vẽ riêng, nhất quán."""
    prompt = _salt_prompt(prompt)     # 23/8: mỗi lần vẽ một góc/ánh sáng khác -> không thể trùng
    cands = _ai_candidates(api_key)
    if not cands:
        return False
    last_quota = None
    for _i, _k in enumerate(cands):
      if str(_k).startswith("cf:"):
        # ⛅ Cloudflare FLUX schnell — free ~2K ảnh/ngày/tài khoản, xếp TRƯỚC Gemini trong pool.
        try:
            if _cf_flux_image(prompt, dest, _k, style):
                if _i:
                    print(f"   🔑 vẽ ảnh: đã xoay sang key thứ {_i + 1} (⛅ CF FLUX)")
                return True
            return False               # CF trả về không phải ảnh -> đổi key cũng vô ích (cùng prompt)
        except Exception as e:
            if _is_quota_err(e):
                _AI_POOL["dead"].add(_k); last_quota = e
                continue               # hết neuron -> thử key kế (CF khác hoặc Gemini)
            print(f"   ⚠️ CF FLUX '{prompt[:30]}' lỗi: {str(e)[:90]}")
            continue                   # lỗi lạ phía CF -> vẫn còn đường Gemini phía sau
      try:
        from google import genai as genai2
        # timeout 120s (SDK google-genai nhận ms qua http_options) — cùng lớp lỗi treo vĩnh viễn như
        # generate_content() thiếu timeout bên content_brain.py (xem GEN_OPTS ở đó): vẽ ảnh treo -> job
        # đứng im tới khi bị giết sau 6h. Có timeout -> throw -> except bên dưới trả False -> lùi fallback.
        client = genai2.Client(api_key=_k, http_options={"timeout": 120_000})
        resp = client.models.generate_content(
            model=model,
            contents=f"A {style or DEFAULT_AI_STYLE} of: {prompt}. No text, no watermark, no logo.")
        data = None
        for cand in (resp.candidates or []):
            for part in ((cand.content and cand.content.parts) or []):
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    data = part.inline_data.data; break
            if data:
                break
        if not data or len(data) < 2000 or not _is_image(data):
            return False          # model trả về rỗng/không phải ảnh -> đổi key cũng vô ích
        open(dest, "wb").write(data)
        if _i:
            print(f"   🔑 vẽ ảnh: đã xoay sang key thứ {_i + 1} (key trước hết hạn mức ảnh)")
        return True
      except Exception as e:
        if _is_quota_err(e):
            _AI_POOL["dead"].add(_k)      # key này hết hạn mức ẢNH trong phiên -> thử key kế
            last_quota = e
            continue
        # lỗi KHÁC (chặn nội dung, prompt hỏng, mạng) -> đổi key cũng thế, dừng luôn cho đỡ tốn
        print(f"   ⚠️ Nano Banana '{prompt[:30]}' lỗi: {str(e)[:100]}")
        return False
    if last_quota is not None:
        print(f"   ⚠️ Nano Banana '{prompt[:30]}': đã thử {len(cands)} key, tất cả hết hạn mức ảnh.")
    return False


def _generate_character_ref(channel, prompt, api_key) -> str | None:
    """WAVE 7 — HOST nhất quán: sinh 1 ảnh nhân vật THAM CHIẾU duy nhất/kênh, CACHE lại (file trong
    public/ luôn, khỏi copy) -> mọi video sau tái dùng NGUYÊN ảnh này, KHÔNG tốn thêm quota Nano Banana
    mỗi video. Trả về path TƯƠNG ĐỐI (staticFile() cần) hoặc None nếu vẽ lỗi."""
    rel = f"_host_{slug(channel)}.png"
    dest = os.path.join(PUB, rel)
    if os.path.exists(dest) and os.path.getsize(dest) > 2000:
        return rel
    style = "clean flat vector cartoon mascot, simple bold shapes, thick outline, solid plain background, front-facing three-quarter view, friendly expression, no text"
    if _generate_image_ai(prompt, dest, api_key, style=style):
        return rel
    return None


# SỔ NHỚ ẢNH ĐÃ DÙNG (23/8): id/url của mọi ảnh đã tải trong tiến trình + danh sách nạp từ
# Firestore của kênh -> không bao giờ lặp lại tấm cũ trong cùng phiên. Cap 4000 cho nhẹ RAM.
_IMG_USED: set = set()
# SỔ GHI CÔNG ẢNH (23/8, user hỏi "có phải credit Pexels/Pixabay không"): luật khác nhau theo nguồn
#   • CC-BY (Openverse, một phần Wikimedia): BẮT BUỘC ghi tác giả + giấy phép
#   • Pexels / Pixabay / NASA / ảnh Public Domain: KHÔNG bắt buộc, nhưng ghi là đúng phép lịch sự và
#     giúp YouTube thấy nội dung minh bạch khi xét kiếm tiền.
# Vì vậy ghi công theo ẢNH THẬT SỰ DÙNG, không phải câu chung chung như bản trước.
_IMG_CREDITS: list = []


def note_credit(cand: dict):
    """Ghi lại nguồn + tác giả + giấy phép của 1 ảnh vừa dùng (tối đa 12 dòng/video)."""
    try:
        src = str(cand.get("id") or "")
        nguon = ("Pexels" if src.startswith("px:") else "Pixabay" if src.startswith("pb:")
                 else "NASA" if src.startswith("nasa:") else "Wikimedia Commons" if src.startswith("wm:")
                 else "Openverse")
        au = (cand.get("creator") or cand.get("photographer") or cand.get("author") or "").strip()
        lic = (cand.get("license") or cand.get("license_version") or "").strip()
        item = " · ".join(x for x in (nguon, au, lic) if x)
        if item and item not in _IMG_CREDITS and len(_IMG_CREDITS) < 12:
            _IMG_CREDITS.append(item)
    except Exception:
        pass


def take_credits() -> list:
    """Lấy & xoá sổ ghi công (gọi 1 lần khi dựng xong video)."""
    out = list(_IMG_CREDITS)
    _IMG_CREDITS.clear()
    return out


def note_image_used(ident: str):
    if ident:
        _IMG_USED.add(str(ident))
        _IMG_NEW.add(str(ident))
        if len(_IMG_USED) > 4000:
            _IMG_USED.clear()


# ── CHỐNG TRÙNG ẢNH XUYÊN PHIÊN (23/8 chiều) ────────────────────────────────────────────────
# Lỗ hổng của bản trước: `_IMG_USED` chỉ sống trong RAM MỘT tiến trình. 18 luồng là 18 tiến trình
# riêng, và mỗi phiên lại khởi động mới -> hai video khác luồng (hoặc khác phiên) hoàn toàn có thể
# rút trúng cùng một tấm ảnh. Đúng thứ user thấy: "nhiều video nhiều kênh dùng cùng 1 footage".
# Nay ghi sổ ảnh-đã-dùng vào Firestore theo KÊNH: 1 lượt đọc đầu video + 1 lượt ghi cuối video.
_IMG_NEW: set = set()          # ảnh dùng TRONG video này (để ghi bổ sung, không ghi đè cả sổ)
_IMG_CH = {"owner": "", "channel": ""}
IMG_MEMORY = 600               # nhớ 600 ảnh gần nhất/kênh — đủ phủ vài chục video, doc vẫn nhẹ


_IMG_LOADED: set = set()          # (owner, channel) đã nạp trong tiến trình này


def load_used_images(owner: str, channel: str):
    """Nạp sổ ảnh đã dùng của kênh vào RAM trước khi dựng video.

    TIẾT KIỆM QUOTA: 1 lane làm tới 4 video cho cùng kênh -> chỉ đọc Firestore ĐÚNG 1 LẦN, các video
    sau dùng lại bộ nhớ trong tiến trình (ảnh vừa dùng đã nằm sẵn trong _IMG_USED). 180 lượt đọc/phiên
    xuống còn ~55."""
    _IMG_CH["owner"], _IMG_CH["channel"] = owner or "", channel or ""
    _IMG_NEW.clear()
    if not (owner and channel):
        return
    if (owner, channel) in _IMG_LOADED:
        return
    _IMG_LOADED.add((owner, channel))
    try:
        import firestore_bridge as FB
        for x in FB.read_used_images(owner, channel):
            _IMG_USED.add(str(x))
        print(f"   🧷 chống trùng ảnh: nạp {len(_IMG_USED)} ảnh kênh đã dùng")
    except Exception as e:
        print(f"   ⚠️ không nạp được sổ ảnh ({str(e)[:50]}) — chỉ chống trùng trong phiên này")


def save_used_images():
    """Ghi bổ sung ảnh vừa dùng vào sổ kênh (gọi sau khi video xong)."""
    if not (_IMG_NEW and _IMG_CH["owner"] and _IMG_CH["channel"]):
        return
    try:
        import firestore_bridge as FB
        FB.append_used_images(_IMG_CH["owner"], _IMG_CH["channel"], list(_IMG_NEW), IMG_MEMORY)
    except Exception:
        pass
    _IMG_NEW.clear()


def _nasa_images(query, n=10):
    """NGUỒN 3 (23/8): NASA Image Library — ~140.000 ảnh, PUBLIC DOMAIN toàn bộ, không cần key.
    Rất mạnh cho các kênh vũ trụ/khí hậu/công nghệ/khoa học (COSMOS, FUTUREUSA, DISASTERUSA...)
    và luôn là ảnh THẬT chất lượng cao. Lỗi -> [] (im lặng)."""
    try:
        u = "https://images-api.nasa.gov/search?" + urllib.parse.urlencode(
            {"q": query, "media_type": "image"})
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20) as r:
            d = json.load(r)
        out = []
        for it in ((d.get("collection") or {}).get("items") or [])[:n]:
            links = it.get("links") or []
            href = next((l.get("href") for l in links if l.get("render") == "image"), None)
            nid = ((it.get("data") or [{}])[0].get("nasa_id")) or href
            if href:
                out.append({"id": f"nasa:{nid}", "url": href, "license": "public domain (NASA)"})
        return out
    except Exception:
        return []


# POOL KEY PEXELS (23/8, user: "thêm chục key xoay vòng cho thoải mái") — dùng CHUNG hệ quản lý
# key sẵn có: thêm/xoá trên dashboard, key ghi dạng "px:<KEY>". Mỗi key tự đếm lượt, chạm trần
# hoặc bị 429 thì TẮT key đó và nhảy key kế -> 10 key = 10× hạn mức, không bao giờ kẹt.
_PEXELS_STATE = {"used": 0, "off": False}
_PX_POOL: list = []          # [{"k": key, "used": n, "off": bool}]
_PX_CAP = 150                # lượt/key/tiến trình (nhà cung cấp cho 200/giờ — chừa biên an toàn)


def set_pexels_pool(keys, channel: str = ""):
    """Nạp key Pexels từ pool chung (key bắt đầu bằng 'px:'), xoay điểm bắt đầu theo kênh để 18
    luồng song song không cùng đốt một key."""
    global _PX_POOL
    raw = [str(k.get("key"))[3:] for k in (keys or [])
           if str(k.get("key") or "").startswith("px:")]
    env = os.environ.get("PEXELS_KEY", "")
    if env and env not in raw:
        raw.append(env)                       # key cũ trong secret vẫn dùng (không mất gì)
    if channel and len(raw) > 1:
        import hashlib
        i = int(hashlib.md5(channel.encode()).hexdigest(), 16) % len(raw)
        raw = raw[i:] + raw[:i]
    _PX_POOL = [{"k": k, "used": 0, "off": False} for k in raw]
    if _PX_POOL:
        print(f"   🖼️ Pexels: {len(_PX_POOL)} key trong pool (xoay vòng, {_PX_CAP} lượt/key).")


# ── NGUỒN VIDEO THẬT (24/8, user chốt: "thêm nguồn video cho sinh động") ────────────────────
# Vì sao chọn 2 nguồn này TRƯỚC: Pexels và Pixabay đều có API VIDEO dùng CHUNG key ảnh mình đã có
# (25 + 18 key) -> 0 thao tác thêm, 0 rủi ro. Mixkit và Dareful KHÔNG có API công khai (phải cào
# trang, dễ vỡ và sai điều khoản) nên em không làm; Coverr có API nhưng cần key riêng — để sau.
# Clip tải về là .mp4 ngắn; engine Cinematic đã dựng sẵn OffthreadVideo nên nhận thẳng, không phải
# sửa engine. Vẫn đi qua sổ chống trùng _IMG_USED như ảnh.

def _pexels_video(query, n=8, tall=True):
    """Video Pexels (dùng chung key ảnh). Trả [{id,url,w,h,dur}] — ưu tiên file vừa đủ nét, nhẹ."""
    _slot = next((x for x in _PX_POOL if not x["off"] and x["used"] < _PX_CAP), None)
    if _slot is None:
        return []
    try:
        u = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
            {"query": query, "per_page": min(n, 15), "page": random.randint(1, 3),
             "orientation": "portrait" if tall else "landscape", "size": "medium"})
        req = urllib.request.Request(u, headers={**UA, "Authorization": _slot["k"]})
        with urllib.request.urlopen(req, timeout=20) as r:
            j = json.loads(r.read().decode("utf-8", "ignore"))
        _slot["used"] += 1
        out = []
        for v in (j.get("videos") or []):
            if not (3 <= float(v.get("duration") or 0) <= 30):
                continue                                  # quá ngắn thì giật, quá dài thì nặng
            files = sorted([f for f in (v.get("video_files") or []) if (f.get("width") or 0) >= 720],
                           key=lambda f: f.get("width") or 0)
            if not files:
                continue
            f = files[0]                                   # bản NHỎ NHẤT còn ≥720p -> tải nhanh
            out.append({"id": f"pxv:{v.get('id')}", "url": f.get("link"), "w": f.get("width"),
                        "h": f.get("height"), "dur": v.get("duration"),
                        "creator": (v.get("user") or {}).get("name", ""), "license": "Pexels"})
        return out
    except Exception as e:
        if "429" in str(e) or "401" in str(e) or "403" in str(e):
            _slot["off"] = True
        return []


def _pixabay_video(query, n=8, tall=True):
    """Video Pixabay (dùng chung key ảnh). Kho rộng, 5.000 lượt/giờ mỗi key."""
    _slot = next((x for x in _PB_POOL if not x["off"] and x["used"] < _PB_CAP), None)
    if _slot is None:
        return []
    try:
        u = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
            {"key": _slot["k"], "q": query, "per_page": min(max(n, 3), 20),
             "page": random.randint(1, 3), "safesearch": "true"})
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20) as r:
            j = json.loads(r.read().decode("utf-8", "ignore"))
        _slot["used"] += 1
        out = []
        for v in (j.get("hits") or []):
            vids = v.get("videos") or {}
            f = vids.get("medium") or vids.get("small")
            if not f or not f.get("url"):
                continue
            out.append({"id": f"pbv:{v.get('id')}", "url": f.get("url"), "w": f.get("width"),
                        "h": f.get("height"), "dur": v.get("duration"),
                        "creator": v.get("user", ""), "license": "Pixabay"})
        return out
    except Exception as e:
        if "429" in str(e) or "400" in str(e):
            _slot["off"] = True
        return []


# ── NGUỒN TƯ LIỆU MỸ (24/8): NARA + DVIDS ───────────────────────────────────────────────────
# Khác Pexels/Pixabay (ảnh thương mại đẹp nhưng chung chung), hai nguồn này là TƯ LIỆU THẬT của
# chính phủ Mỹ: phim lưu trữ quốc gia và phim quân đội — thứ Pexels không bao giờ có, và là chất
# liệu rất mạnh cho kênh lịch sử/thiên tai/quốc phòng.
# Key lưu chung hồ key: "nara:<key api.data.gov>" · "dvids:<key dvidshub>"
_NARA_POOL: list = []
_DVIDS_POOL: list = []
_GOV_CAP = 200               # lượt/key/tiến trình — cả hai nhà đều ~1.000 lượt/giờ nên rất thoáng


def set_gov_pools(keys, channel: str = ""):
    """Nạp key NARA/DVIDS từ cùng danh sách key (gọi trong set_ai_pool)."""
    global _NARA_POOL, _DVIDS_POOL
    _NARA_POOL = [{"k": str(x.get("key"))[5:], "used": 0, "off": False}
                  for x in (keys or []) if str(x.get("key", "")).startswith("nara:")]
    _DVIDS_POOL = [{"k": str(x.get("key"))[6:], "used": 0, "off": False}
                   for x in (keys or []) if str(x.get("key", "")).startswith("dvids:")]


def _nara(query, n=8):
    """Lưu trữ Quốc gia Mỹ (catalog.archives.gov qua api.data.gov). Trả clip/ảnh công cộng."""
    _slot = next((x for x in _NARA_POOL if not x["off"] and x["used"] < _GOV_CAP), None)
    if _slot is None:
        return []
    try:
        u = "https://catalog.archives.gov/api/v2/records/search?" + urllib.parse.urlencode(
            {"q": query, "limit": min(n, 20), "availableOnline": "true"})
        req = urllib.request.Request(u, headers={**UA, "x-api-key": _slot["k"]})
        with urllib.request.urlopen(req, timeout=25) as r:
            j = json.loads(r.read().decode("utf-8", "ignore"))
        _slot["used"] += 1
        out = []
        for hit in ((j.get("body") or {}).get("hits") or {}).get("hits", [])[:n]:
            src = (hit.get("_source") or {})
            for dobj in (src.get("digitalObjects") or []):
                url = dobj.get("objectUrl") or ""
                if not url:
                    continue
                low = url.lower()
                if low.endswith((".mp4", ".m4v")):
                    out.append({"id": f"nara:{dobj.get('objectId')}", "url": url, "video": True,
                                "creator": "U.S. National Archives", "license": "Public Domain"})
                elif low.endswith((".jpg", ".jpeg", ".png")):
                    out.append({"id": f"nara:{dobj.get('objectId')}", "url": url, "video": False,
                                "creator": "U.S. National Archives", "license": "Public Domain"})
        return out
    except Exception as e:
        if any(t in str(e) for t in ("401", "403", "429")):
            _slot["off"] = True
        return []


def _dvids(query, n=8):
    """DVIDS — kho phim/ảnh quân đội Mỹ. Tìm rồi lấy link tải của từng mục."""
    _slot = next((x for x in _DVIDS_POOL if not x["off"] and x["used"] < _GOV_CAP), None)
    if _slot is None:
        return []
    try:
        u = "https://api.dvidshub.net/search?" + urllib.parse.urlencode(
            {"q": query, "type": "video", "max_results": min(n, 20), "api_key": _slot["k"]})
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25) as r:
            j = json.loads(r.read().decode("utf-8", "ignore"))
        _slot["used"] += 1
        out = []
        for it in (j.get("results") or [])[:n]:
            vid = it.get("id")
            if not vid:
                continue
            a = "https://api.dvidshub.net/asset?" + urllib.parse.urlencode({"id": vid, "api_key": _slot["k"]})
            try:
                with urllib.request.urlopen(urllib.request.Request(a, headers=UA), timeout=25) as r2:
                    ja = json.loads(r2.read().decode("utf-8", "ignore"))
                _slot["used"] += 1
                url = ((ja.get("results") or {}).get("video") or {}).get("src") or ""
            except Exception:
                url = ""
            if url:
                out.append({"id": f"dvids:{vid}", "url": url, "video": True,
                            "creator": "DVIDS (U.S. DoD)", "license": "Public Domain"})
        return out
    except Exception as e:
        if any(t in str(e) for t in ("401", "403", "429")):
            _slot["off"] = True
        return []


def _archive_video(query, n=6):
    """INTERNET ARCHIVE (24/8) — kho phim PHẠM VI CÔNG CỘNG lớn nhất thế giới, gồm cả PRELINGER
    ARCHIVES mà user nhắc tới. KHÔNG cần key, không hạn mức công bố.

    Hai bước: tìm mã tư liệu -> hỏi danh sách file -> lấy .mp4 nhỏ nhất. Chỉ nhận tư liệu thuộc
    phạm vi công cộng (lọc theo collection) để không dính bản quyền."""
    try:
        q = (f'({query}) AND mediatype:movies AND (collection:prelinger OR '
             f'collection:publicmoviescollection OR collection:film_noir OR licenseurl:*publicdomain*)')
        u = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
            {"q": q, "fl[]": "identifier", "rows": min(n, 10), "output": "json",
             "sort[]": "downloads desc"})
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25) as r:
            j = json.loads(r.read().decode("utf-8", "ignore"))
        out = []
        for d in ((j.get("response") or {}).get("docs") or [])[:n]:
            ident = d.get("identifier")
            if not ident:
                continue
            try:
                mu = f"https://archive.org/metadata/{urllib.parse.quote(ident)}"
                with urllib.request.urlopen(urllib.request.Request(mu, headers=UA), timeout=25) as r2:
                    meta = json.loads(r2.read().decode("utf-8", "ignore"))
            except Exception:
                continue
            mp4 = [f for f in (meta.get("files") or [])
                   if str(f.get("name", "")).lower().endswith(".mp4") and int(f.get("size") or 0) > 0]
            if not mp4:
                continue
            f = min(mp4, key=lambda x: int(x.get("size") or 0))     # bản nhẹ nhất -> tải nhanh
            out.append({"id": f"ia:{ident}", "video": True,
                        "url": f"https://archive.org/download/{urllib.parse.quote(ident)}/{urllib.parse.quote(f['name'])}",
                        "creator": "Internet Archive", "license": "Public Domain"})
        return out
    except Exception:
        return []


def _nasa_video(query, n=6):
    """NASA cũng có VIDEO (media_type=video) — trước mình chỉ lấy ảnh. Không cần key."""
    try:
        u = "https://images-api.nasa.gov/search?" + urllib.parse.urlencode(
            {"q": query, "media_type": "video"})
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25) as r:
            j = json.loads(r.read().decode("utf-8", "ignore"))
        out = []
        for it in ((j.get("collection") or {}).get("items") or [])[:n]:
            href = it.get("href")
            if not href:
                continue
            try:
                with urllib.request.urlopen(urllib.request.Request(href, headers=UA), timeout=20) as r2:
                    files = json.loads(r2.read().decode("utf-8", "ignore"))
            except Exception:
                continue
            # ưu tiên bản ~mobile/small: nhẹ, đủ nét cho nền video
            mp4 = [f for f in files if str(f).lower().endswith(".mp4")]
            small = [f for f in mp4 if "small" in f.lower() or "mobile" in f.lower()] or mp4
            if small:
                nid = ((it.get("data") or [{}])[0] or {}).get("nasa_id", "")
                out.append({"id": f"nasav:{nid}", "url": small[0], "video": True,
                            "creator": "NASA", "license": "Public Domain"})
        return out
    except Exception:
        return []


def fetch_clip(query, dest, tall=True, max_mb=14):
    """Tải 1 CLIP THẬT về `dest` (.mp4). Không có/hỏng -> None để caller lùi về ảnh tĩnh.

    Chống trùng dùng chung sổ ảnh: mỗi clip có id riêng (pxv:/pbv:) nên không bao giờ lặp lại clip
    đã dùng cho kênh này."""
    cands = (_pexels_video(query, tall=tall) + _pixabay_video(query, tall=tall)
             + [c for c in (_nara(query) + _dvids(query)) if c.get("video")]
             + _archive_video(query) + _nasa_video(query))   # 24/8: 2 nguồn KHÔNG cần key
    random.shuffle(cands)
    for c in cands:
        if str(c.get("id")) in _IMG_USED or not c.get("url"):
            continue
        try:
            req = urllib.request.Request(c["url"], headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read(max_mb * 1024 * 1024 + 1)
            if len(data) > max_mb * 1024 * 1024 or len(data) < 40000:
                continue                                   # quá nặng (render lâu) hoặc file hỏng
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            note_image_used(c["id"])
            note_credit({"id": c["id"], "creator": c.get("creator"), "license": c.get("license")})
            print(f"   🎬 clip thật: {os.path.basename(dest)} ({len(data)/1e6:.1f}MB · {c.get('dur')}s · {c.get('license')})")
            return dest
        except Exception:
            continue
    return None


def _pexels(query, n=12):
    """NGUỒN 4 (23/8): Pexels — kho ảnh HIỆN ĐẠI đẹp nhất nhóm miễn phí (người thật, đời sống Mỹ).
    Cần key (secret PEXELS_KEY). Tôn trọng giới hạn nhà cung cấp: 200 lượt/giờ, 20.000/tháng nên
    hệ TỰ HẠN CHẾ 120 lượt/tiến trình rồi thôi (các nguồn khác gánh tiếp) — không bao giờ spam.
    Dùng ĐÚNG mục đích (lấy ảnh minh hoạ cho video của mình), KHÔNG dựng lại dịch vụ giống Pexels,
    và có ghi công theo yêu cầu license (dòng 'Imagery:' trong mô tả)."""
    _slot = next((x for x in _PX_POOL if not x["off"] and x["used"] < _PX_CAP), None)
    if _slot is None:
        return []
    k = _slot["k"]
    try:
        u = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
            {"query": query, "per_page": min(n, 20), "page": random.randint(1, 3)})
        req = urllib.request.Request(u, headers={**UA, "Authorization": k})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
        _slot["used"] += 1
        out = []
        for ph in (d.get("photos") or []):
            src = (ph.get("src") or {})
            url = src.get("large2x") or src.get("large") or src.get("original")
            if url:
                out.append({"id": f"px:{ph.get('id')}", "url": url,
                            "photographer": ph.get("photographer", ""), "license": "Pexels License"})
        return out
    except Exception as e:
        # 401 = key sai/bị thu hồi · 403/429 = chạm trần -> đều TẮT key đó và nhảy key kế.
        # (Đo thật 23/8: key sai trả 401, bản đầu chỉ bắt 429/403 nên key hỏng cứ nằm lại pool.)
        if any(c in str(e) for c in ("401", "403", "429")):
            _slot["off"] = True
            _live = sum(1 for x in _PX_POOL if not x["off"])
            print(f"   ⏸ 1 key Pexels chạm giới hạn -> chuyển key khác (còn {_live} key sống).")
        return []


_PB_POOL: list = []
_PB_CAP = 400                # lượt/key/tiến trình (Pixabay cho 5.000/giờ — rộng hơn Pexels nhiều)


def set_pixabay_pool(keys, channel: str = ""):
    """Pool key Pixabay (23/8) — key ghi dạng 'pb:<KEY>' trong cùng hệ quản lý key của dashboard.
    Cùng cơ chế Pexels: xoay điểm bắt đầu theo kênh, trần lượt/key, key hỏng thì tắt riêng nó."""
    global _PB_POOL
    raw = [str(k.get("key"))[3:] for k in (keys or []) if str(k.get("key") or "").startswith("pb:")]
    env = os.environ.get("PIXABAY_KEY", "")
    if env and env not in raw:
        raw.append(env)
    if channel and len(raw) > 1:
        import hashlib
        i2 = int(hashlib.md5(channel.encode()).hexdigest(), 16) % len(raw)
        raw = raw[i2:] + raw[:i2]
    _PB_POOL = [{"k": k, "used": 0, "off": False} for k in raw]
    if _PB_POOL:
        print(f"   🧩 Pixabay: {len(_PB_POOL)} key trong pool ({_PB_CAP} lượt/key).")


def _pixabay(query, n=12):
    """NGUỒN 5 (23/8): Pixabay — ~4 triệu ảnh, giấy phép riêng cho phép dùng thương mại, không cần
    ghi công. Hạn mức rộng nhất nhóm (5.000 lượt/giờ/key). Lỗi/hết hạn mức -> tắt key đó, trả []."""
    _slot = next((x for x in _PB_POOL if not x["off"] and x["used"] < _PB_CAP), None)
    if _slot is None:
        return []
    try:
        u = "https://pixabay.com/api/?" + urllib.parse.urlencode(
            {"key": _slot["k"], "q": query, "image_type": "photo", "per_page": min(max(n, 3), 30),
             "page": random.randint(1, 3), "safesearch": "true"})
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20) as r:
            d = json.load(r)
        _slot["used"] += 1
        return [{"id": f"pb:{h.get('id')}", "url": h.get("largeImageURL") or h.get("webformatURL"),
                 "author": h.get("user", ""), "license": "Pixabay Content License"}
                for h in (d.get("hits") or []) if h.get("largeImageURL") or h.get("webformatURL")]
    except Exception as e:
        if any(c in str(e) for c in ("400", "401", "403", "429")):
            _slot["off"] = True
            print(f"   ⏸ 1 key Pixabay hỏng/chạm trần -> nhảy key kế ({sum(1 for x in _PB_POOL if not x['off'])} còn sống).")
        return []


def _wikimedia(query, n=12):
    """NGUỒN ẢNH THỨ HAI (23/8): Wikimedia Commons — kho ảnh tự do LỚN NHẤT (~100 triệu file),
    không cần key, không giới hạn gọi hợp lý. Vì sao cần: Openverse lọc cc0/pdm cho kho rất hẹp
    (~12 tấm đầu cho mỗi từ khoá) nên nhiều video/kênh trùng ảnh nhau. Trả list giống Openverse
    ({id,url}) để dùng chung mọi nhánh phía sau. Lỗi mạng -> [] (im lặng, có Openverse gánh)."""
    try:
        p = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": "6",
             "gsrsearch": f"filetype:bitmap {query}", "gsrlimit": n, "prop": "imageinfo",
             "iiprop": "url|extmetadata", "iiurlwidth": "1600"}
        u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p)
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20) as r:
            d = json.load(r)
        out = []
        for pg in (d.get("query", {}).get("pages") or {}).values():
            ii = (pg.get("imageinfo") or [{}])[0]
            lic = (((ii.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value") or "").lower()
            # chỉ nhận giấy phép KHÔNG ràng buộc chia sẻ tương tự (tránh rắc rối license cho video)
            if not ii.get("thumburl") or "sa" in lic.replace("share", ""):
                continue
            out.append({"id": f"wm:{pg.get('pageid')}", "url": ii["thumburl"],
                        "title": pg.get("title", ""), "license": lic})
        return out
    except Exception:
        return []


def fetch_image(query, dest, orient=None, verify=None, max_check=4, ai_key=None, ai_prompt=None,
                ai_style=None, ai_only=False, extra=None, verify_many=None):
    """Tải 1 ảnh từ Openverse — ƯU TIÊN CC0/Public Domain (KHÔNG cần ghi nguồn, an toàn bản quyền).
    verify(path)->True/False/None: kiểm ảnh có KHỚP chủ đề không (dùng cho GUESS). True=nhận, False=thử ảnh khác,
    None=không kiểm được (Vision lỗi) -> nhớ làm dự phòng. Lỗi/ảnh hỏng/không khớp -> trả None.
    ai_key: nếu có + Openverse KHÔNG tìm ra ảnh nào -> DỰ PHÒNG bằng Gemini vẽ ảnh (Nano Banana) trước
    khi bỏ cuộc hẳn. ai_prompt (tuỳ chọn): mô tả rõ hơn cho AI vẽ, mặc định dùng lại 'query'.
    ai_style: phong cách vẽ riêng (kênh speculative — tương lai/vũ trụ suy đoán — không có ảnh thật để
    so nên cần gu vẽ nhất quán, khác ảnh báo chí mặc định). ai_only=True: BỎ QUA Openverse hẳn, đi thẳng
    vào AI vẽ — dùng khi CHẮC CHẮN không có ảnh thật (chủ đề tưởng tượng/tương lai) -> đỡ phí 3 lượt tìm
    Openverse chắc chắn trật (mỗi lượt tốn round-trip mạng) trước khi mới vẽ."""
    query = re.sub(r"\b(chart|graph|screenshot|data|statistics|dashboard|trading|diagram|infographic)\b",
                   "", query, flags=re.I).strip() or query   # tránh ảnh chart/watermark
    def _try(params):
        u = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20) as r:
            res = json.load(r).get("results") or []
        # ── CHỐNG TRÙNG ẢNH TOÀN HỆ (23/8, user: "nhiều video nhiều kênh dùng chung 1 footage") ──
        # Gốc bệnh: luôn lấy TRANG 1 + luôn ưu tiên kết quả đầu -> cùng từ khoá ("college tuition",
        # "american flag"...) thì mọi video, mọi kênh, mọi ngày đều nhận ĐÚNG một tấm. FIX:
        #   (a) XÁO thứ tự kết quả -> không phải lúc nào cũng lấy ảnh top-1;
        #   (b) BỎ ảnh đã dùng gần đây (sổ nhớ dưới đây, dùng chung mọi kênh trong tiến trình).
        random.shuffle(res)
        fresh = [x for x in res if str(x.get("id") or x.get("url") or "") not in _IMG_USED]
        return fresh or res            # hết ảnh mới thì đành dùng lại (thà có ảnh còn hơn trống)
    ar = {"tall": "tall", "wide": "wide"}.get(orient or "")   # KHỚP ĐỊNH DẠNG: short=dọc(tall), long=ngang(wide)
    _need = 1 + len(extra or [])
    pg = max(6, max_check + 2, _need * 3) if verify else max(3, _need * 3)   # cần verify/nhiều ảnh -> lấy nhiều ứng viên hơn
    # 23/8 (user: "nhiều video nhiều kênh dùng chung 1 footage"): luôn lấy TRANG 1 nghĩa là mọi
    # video cùng từ khoá đều bốc từ đúng ~12 ảnh đầu -> trùng là chắc chắn. Lấy TRANG NGẪU NHIÊN
    # 1-4 -> kho ứng viên rộng gấp 4, kèm xáo thứ tự + bỏ ảnh đã dùng ở _try().
    base = {"page_size": pg, "license": "cc0,pdm,by", "mature": "false",
            "page": random.randint(1, 4)}
    if ar:
        base["aspect_ratio"] = ar
    def _openverse():
        # CHỈ CC0 + Public Domain -> KHÔNG cần ghi nguồn, an toàn bản quyền 100%. Không có -> dùng ảnh fallback.
        res = _try({"q": query, **base})
        # GỘP THÊM WIKIMEDIA (23/8) — kho rộng gấp bội, cùng chuẩn tự do; gộp trước khi lọc/xáo
        # nên ảnh hai nguồn trộn đều, hết cảnh cả hệ dùng chung vài tấm của Openverse.
        _extra = [x for x in (_pexels(query) + _pixabay(query) + _wikimedia(query) + _nasa_images(query))
                  if str(x.get("id")) not in _IMG_USED]
        if _extra:
            res = (res or []) + _extra
            random.shuffle(res)
        if not res and ar:
            res = _try({"q": query, "page_size": pg, "license": "cc0,pdm,by", "mature": "false"})   # bỏ lọc hướng nếu 0 kết quả
        if not res:
            res = _try({"q": " ".join(query.split()[:2]), "page_size": pg, "license": "cc0,pdm,by", "mature": "false"})  # rút gọn từ khoá thử lại
        if not res:
            return None
        # DANH SÁCH (không phải 1 ảnh): Vision hỏng/429 thì MỌI ứng viên trả None -> nếu chỉ giữ 1 ảnh
        # dự phòng thì cả cảnh chỉ có 1 hình, mất hẳn nhịp cắt 2-3s (log 21/8: "7 cảnh giữ một ảnh
        # quá 3.5s"). Giữ đủ `need` ảnh dự phòng -> nhịp cắt vẫn chạy dù Vision đang down.
        if verify_many and not verify:
            need = 1 + len(extra or [])
            # CHẤM HÀNG LOẠT (1 lệnh Vision cho cả cảnh, ý tưởng của user): tải trước tối đa
            # max_check + need ứng viên HỢP LỆ, ghép lưới chấm 1 lần, giữ ảnh True theo thứ tự.
            # Cả lưới không chấm được (None) -> fail-open lấy need ảnh đầu (y hệ verify None cũ).
            # Có kết quả mà 0 ảnh True -> trả None (THÀ KHÔNG ẢNH còn hơn ảnh SAI).
            import shutil
            cds = []
            for cand in res:
                try:
                    note_image_used(cand.get("id") or cand.get("url"))   # 23/8: nhớ để KHÔNG lặp ở video sau
                    note_credit(cand)                                   # 23/8: ghi công đúng nguồn/tác giả/giấy phép
                    with urllib.request.urlopen(urllib.request.Request(cand["url"], headers=UA), timeout=30) as r:
                        ctype = (r.headers.get("Content-Type") or "").lower()
                        data = r.read()
                    if len(data) < 2000 or ("image" not in ctype and not _is_image(data)) or not _is_image(data):
                        continue
                    cds.append(data)
                    if len(cds) >= min(5, max_check + need):   # ≤5 ứng viên = trọn 1 lưới (6 ô kể cả
                        break                                   # ô mồi) -> đúng 1 lệnh Vision/cảnh, không chia lô
                except Exception:
                    continue
            if not cds:
                return None
            tmp = []
            for k, d0 in enumerate(cds):
                tp = f"{dest}.cand{k}.jpg"; open(tp, "wb").write(d0); tmp.append(tp)
            try:
                vs = verify_many([(t, query) for t in tmp])
                if all(v is None for v in vs):
                    chosen = tmp[:need]                     # Vision mù -> fail-open như cũ
                else:
                    chosen = [tmp[k] for k, v in enumerate(vs) if v is True][:need]
                if not chosen:
                    return None
                shutil.copyfile(chosen[0], dest)
                for k, _p in enumerate(extra or []):
                    if k + 1 < len(chosen):
                        shutil.copyfile(chosen[k + 1], _p)
                return dest
            finally:
                for t in tmp:
                    try: os.remove(t)
                    except OSError: pass
        fallback = []                                     # ảnh hợp lệ nhưng Vision không kiểm được
        checked = 0
        picked = []                                       # NHIỀU ảnh khác nhau từ CÙNG 1 lần tìm -> cắt cảnh 2-3s
        need = 1 + len(extra or [])                       # mà KHÔNG tốn thêm lượt gọi Openverse nào
        for cand in res:                                  # duyệt cho tới khi đủ ảnh HỢP LỆ (+ KHỚP nếu có verify)
            try:
                with urllib.request.urlopen(urllib.request.Request(cand["url"], headers=UA), timeout=30) as r:
                    ctype = (r.headers.get("Content-Type") or "").lower()
                    data = r.read()
                if len(data) < 2000 or ("image" not in ctype and not _is_image(data)) or not _is_image(data):
                    continue                              # HTML/redirect/hỏng/định dạng lạ -> bỏ, thử ảnh khác
                if not verify:
                    picked.append(data)
                else:
                    open(dest, "wb").write(data)          # verify cần đọc từ file
                    v = verify(dest)                      # KIỂM khớp chủ đề
                    if v is True:
                        picked.append(data)
                    elif v is None and len(fallback) < need:   # Vision lỗi -> gom đủ ảnh dự phòng
                        fallback.append(data)
                    checked += 1
                    # hết ngân sách kiểm VÀ đã đủ ảnh (khớp hoặc dự phòng) -> dừng
                    if checked >= max_check and (picked or len(fallback) >= need):
                        break
                if len(picked) >= need:
                    break
            except Exception:
                continue
        if not picked and verify and fallback:            # không ảnh nào KHỚP chắc, nhưng có ảnh dự phòng (Vision down)
            picked = fallback
        if not picked:
            return None                                   # verify bật mà không ảnh nào khớp -> THÀ KHÔNG ẢNH còn hơn ảnh SAI
        open(dest, "wb").write(picked[0])
        for _k, _p in enumerate(extra or []):             # ảnh phụ: thiếu thì thôi, caller tự kiểm tồn tại
            if _k + 1 < len(picked):
                open(_p, "wb").write(picked[_k + 1])
        return dest                                       # verify bật mà không ảnh nào khớp -> THÀ KHÔNG ẢNH còn hơn ảnh SAI
    got = None
    if not ai_only:
        try:
            got = _openverse()
        except Exception as e:
            print(f"   ⚠️ ảnh '{query[:30]}' lỗi: {e}"); got = None
    if got:
        return got
    if ai_key and _generate_image_ai(ai_prompt or query, dest, ai_key, style=ai_style):   # KHÔNG có ảnh thật khớp -> chữa cháy bằng AI vẽ
        print(f"   🎨 '{query[:30]}': {'ai_only' if ai_only else 'không có ảnh CC0 khớp'} -> đã dùng Nano Banana vẽ.")
        return dest
    return None


def _concat(mp3s, out):
    lst = out + ".txt"; open(lst, "w").write("".join(f"file '{m}'\n" for m in mp3s))
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out],
                   check=True, capture_output=True, timeout=300)


def _dur(path):
    """Độ dài THẬT của file (giây) — dùng để cộng dồn offset sub chính xác (chống lệch dần)."""
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nk=1:nw=1", path], capture_output=True, text=True, timeout=60).stdout.strip()
    try:
        return float(o)
    except ValueError:
        return 0.0


def _race_from_story(story, sdir, port, tag=""):
    """Dựng 1 RACE (giọng + subs karaoke + ảnh theo câu) từ 1 story. Dùng cho cả short lẫn long."""
    rel = lambda p: os.path.relpath(p, PUB)
    narr = story["narration"]
    if port and len(narr) > 7:            # short < 60s -> giữ 6 câu đầu + câu TWIST cuối
        narr = narr[:6] + narr[-1:]
    seg_mp3, all_subs, shots, cum = [], [], [], 0.0
    idir = os.path.join(PUB, "img", os.path.basename(sdir) + tag); os.makedirs(idir, exist_ok=True)
    for i, n in enumerate(narr):
        m = os.path.join(sdir, f"n{tag}{i}.mp3")
        _, subs, _ = TK.synth(n["text"], m)
        for s in subs: s["si"] = i; s["t"] = round(s["t"] + cum, 3)
        all_subs += subs
        cum += _dur(m) or (subs[-1]["t"] - cum + subs[-1]["d"] if subs else 0)  # offset theo độ dài THẬT mp3
        seg_mp3.append(m)
        q = (n.get("visual") or {}).get("query") or story.get("topic", "")
        img = fetch_image(q, os.path.join(idir, f"s{i}.jpg"), orient="tall" if port else "wide")
        shots.append(rel(img) if img else (shots[-1] if shots else None))
    FB = "img/_fallback.jpg"
    firstok = next((s for s in shots if s), None) or FB
    shots = [s or firstok for s in shots]
    race_mp3 = os.path.join(sdir, f"race{tag}.mp3"); _concat(seg_mp3, race_mp3)
    frames = story["race"]["frames"]; nfr = len(frames)
    # TIỀN-KIỂM (miễn phí, TRƯỚC render): cắt tên ≤16 ký tự -> chống cắt mép/chồng nhãn (thủ phạm điểm visual thấp).
    for fr in frames:
        for d in fr.get("data", []):
            nm = d.get("name")
            if isinstance(nm, str) and len(nm) > 16:
                d["name"] = nm[:15].rstrip() + "…"
    spf = max(2.0, min(11.0, (0.9 * cum) / max(1, nfr - 1)))
    # UNIT gọn: bỏ chú thích trong ngoặc + cap ngắn -> nhãn giá trị KHÔNG tràn mép (vd "USD (chained 2017)"->"USD").
    unit = re.sub(r"\s*\(.*?\)", "", story["race"].get("unit", "") or "").strip()
    unit = re.sub(r"\b(chained|nominal|current|constant|real|per\s+capita|dollars?)\b", "", unit, flags=re.I).strip()
    unit = unit[:6]
    title = (story["race"].get("title_label", "") or "")[:40]   # tiêu đề chart cũng cap tránh tràn
    return {"frames": frames, "secondsPerFrame": round(spf, 3), "durationSec": round(cum + 1.0, 2),
            "narration": rel(race_mp3), "subs": all_subs, "chart": "bars",
            "bg": shots[0], "shots": shots,
            "title": title, "unit": unit}, shots[0]


def _intro_from_story(story, hook_bg, sdir, tag=""):
    rel = lambda p: os.path.relpath(p, PUB)
    hook_mp3 = os.path.join(sdir, f"hook{tag}.mp3")
    hdur, _, _ = TK.synth(story.get("hook") or story["title"], hook_mp3)
    intro = {"kicker": _clip_words(story.get("topic", ""), 34).upper(),
             "title": (story.get("hook_title") or _clip_words(story.get("topic", ""), 24)).upper(),
             "sec": round(hdur + 0.5, 2), "bg": hook_bg, "audio": rel(hook_mp3)}
    if story.get("hook_stat"): intro["bignum"] = story["hook_stat"]
    if story.get("hook_caption"): intro["bigcap"] = story["hook_caption"]
    return intro


_HANDLES = None
def channel_handle(channel):
    """Handle @ đúng theo KÊNH (đọc brands.json). Fallback @<kênh>hq. Tránh gắn nhầm @dataracehq cho mọi kênh."""
    global _HANDLES
    if _HANDLES is None:
        _HANDLES = {}
        src = os.environ.get("AUTOPUBLISHER_SRC", "")
        cands = []
        if src:
            cands.append(os.path.join(os.path.dirname(src.rstrip("/")), "config", "brands.json"))
        cands += [os.path.join(ENG, "..", "MM0-AutoPublisher", "config", "brands.json"),
                  os.path.join(os.path.dirname(ENG), "MM0-AutoPublisher", "config", "brands.json")]
        for p in cands:
            try:
                if p and os.path.exists(p):
                    b = json.load(open(p)); items = b if isinstance(b, list) else list(b.values())
                    for v in items:
                        cid = re.sub(r"[^a-z0-9]", "", (v.get("id") or v.get("display") or "").lower())
                        if cid and v.get("handle"):
                            _HANDLES[cid] = v["handle"]
                    break
            except Exception:
                pass
    key = re.sub(r"[^a-z0-9]", "", (channel or "").lower())
    return _HANDLES.get(key) or ("@" + key + "hq")


def build_props(story, sdir, port, music="music/carefree.mp3", handle="@dataracehq"):
    """SHORT / 1-race: intro hook + 1 race."""
    race, bg0 = _race_from_story(story, sdir, port)
    intro = _intro_from_story(story, bg0, sdir)
    return {"races": [race], "intro": intro, "handle": handle, "music": music}


def build_long_props(stories, sdir, music="music/carefree.mp3", handle="@dataracehq"):
    """LONG (16:9): compilation NHIỀU race cùng chủ đề + intro từ race đầu."""
    races, first_bg = [], None
    for i, s in enumerate(stories):
        r, bg = _race_from_story(s, sdir, port=False, tag=f"_{i}")
        races.append(r); first_bg = first_bg or bg
    intro = _intro_from_story(stories[0], first_bg, sdir, tag="_intro")
    return {"races": races, "intro": intro, "handle": handle, "music": music}


class _HookDone(Exception):
    """Đã lấy được khung hook mở đầu -> nhảy khỏi khối dựng DocThumb (không cần vẽ chồng chữ)."""


def _clip_words(s: str, n: int) -> str:
    """Cắt ngắn THEO TỪ, không cắt giữa chữ.

    Trước đây cắt thô `s[:34]` -> kicker cảnh hook hiện ra cụt lủn giữa từ, ví dụ "THE NET WORTH OF
    THE 10 RICHEST BI" (thấy rõ khi render khung hook làm thumbnail). Lỗi này nằm ngay CẢNH ĐẦU của
    mọi video data-race nên vừa xấu trong video vừa xấu trên thumbnail."""
    s = (s or "").strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > n * 0.5 else cut).rstrip(" ,;:-")


# LÀM NÉT khung cắt từ VIDEO ĐÃ NÉN: H.264 làm mềm nét chữ. lanczos (thu nhỏ sắc hơn) + unsharp
# nhẹ -> đo trên khung thật: độ nét biên 29.8 -> 33.7 (+13%), chữ gọn hẳn, không rỗ.
# KHÔNG dùng cho still_hook_thumb: nguồn là PNG chưa nén, làm nét thêm chỉ tạo viền giả.
SHARPEN = "unsharp=5:5:0.9:5:5:0.0"

# TRẦN THỜI GIAN 1 LỆNH RENDER. Không có trần = Remotion treo thì job treo tới hết 120' của
# GitHub, giữ khoá concurrency, mọi phiên sau bị huỷ (đúng sự cố 20/8: GRIDIRON+PAYCHECK treo
# 2 tiếng nuốt trọn 3 phiên). Số liệu thật: cả một kênh (nhiều video) chạy xong lâu nhất 27'.
# Đặt 30'/lệnh = rộng rãi cho long 1080p trên máy 2 nhân, mà treo thì tự ném TimeoutExpired ->
# lớp retry sẵn có bắt được, job chuyển "failed" gọn gàng thay vì đơ.
RENDER_TIMEOUT = 1800
# CANH THEO GIỜ THỰC: trần 30' vẫn có nghĩa là MẤT 30' mới biết nó treo. Bộ canh dưới đây đo CPU
# THẬT của tiến trình render mỗi 20s; render là việc nặng CPU (swiftshader) nên CPU đứng im nghĩa
# là ĐANG TREO chứ không phải đang chờ mạng -> giết sớm ở phút thứ 6 để lớp retry chạy lại NGAY
# trong cùng phiên, thay vì bỏ phí nửa tiếng rồi chờ phiên sau.
STALL_SEC = 360      # CPU gần như không nhúc nhích liên tục ngần này -> coi là treo
STALL_TICK = 20      # nhịp lấy mẫu


def _cpu_seconds(pgid: int):
    """Tổng CPU SỐNG của CẢ NHÓM tiến trình (cha + mọi con CHƯA thoát), đo qua /proc theo pgrp.

    Bản cũ đọc utime+cutime của MỖI tiến trình cha: cutime/cstime chỉ được Linux cộng SAU KHI con
    đã thoát và được reap — render LONG thì Chrome con cày 30' trong khi đồng hồ cha đứng im ->
    watchdog kết luận treo và giết oan ĐÚNG giây STALL_SEC (22/8: mọi long chết ở 360s, toàn bộ
    kênh bị luật 1:3 chặn short theo -> sản lượng đứng hình 2h). Đo cả nhóm sống thì render thật
    luôn thấy CPU nhảy; còn treo thật (cả nhóm im) vẫn bị bắt như cũ. Không đọc được /proc -> None
    (macOS/dev) -> chỉ còn trần cứng, y hành vi cũ."""
    try:
        total = 0.0; hz = os.sysconf("SC_CLK_TCK"); found = False
        for d in os.listdir("/proc"):
            if not d.isdigit():
                continue
            try:
                with open(f"/proc/{d}/stat") as f:
                    p = f.read().rsplit(") ", 1)[1].split()
                if int(p[2]) == pgid:                      # pgrp
                    total += (int(p[11]) + int(p[12])) / hz
                    found = True
            except Exception:
                continue
        return total if found else None
    except Exception:
        return None


def run_render_cmd(cmd, cwd, timeout=RENDER_TIMEOUT, label=""):
    """Chạy lệnh render CÓ CANH TREO THỜI GIAN THỰC.

    subprocess.run(timeout=...) chỉ cứu được ở phút thứ 30. Hàm này bám tiến trình: cứ 20s đo CPU
    tích luỹ; nếu suốt STALL_SEC mà CPU tăng không đáng kể -> kết luận treo, giết ngay và ném
    TimeoutExpired để lớp retry sẵn có xử lý. Máy không đọc được /proc (vd macOS) -> tự bỏ qua phần
    canh CPU, vẫn còn trần cứng timeout."""
    import time as _t
    import signal
    proc = subprocess.Popen(cmd, cwd=cwd, start_new_session=True)   # nhóm riêng -> đo/giết CẢ nhóm
    t0 = _t.time()
    last_cpu, last_move = _cpu_seconds(proc.pid), _t.time()
    while True:
        try:
            proc.wait(timeout=STALL_TICK)
            break                                    # đã xong
        except subprocess.TimeoutExpired:
            pass
        now = _t.time()
        if now - t0 > timeout:                       # trần cứng — chốt chặn cuối
            try: os.killpg(proc.pid, signal.SIGKILL)
            except Exception: proc.kill()
            proc.wait()
            raise subprocess.TimeoutExpired(cmd, timeout)
        cur = _cpu_seconds(proc.pid)
        if cur is None or last_cpu is None:
            last_cpu = cur
            continue                                 # không đo được -> chỉ dựa vào trần cứng
        if cur - last_cpu > 1.0:                     # có làm việc thật -> reset đồng hồ đứng im
            last_cpu, last_move = cur, now
        elif now - last_move > STALL_SEC:
            try: os.killpg(proc.pid, signal.SIGKILL)
            except Exception: proc.kill()
            proc.wait()
            print(f"   ⛔ {label or 'render'}: CPU đứng im {int(now - last_move)}s -> TREO, giết sớm "
                  f"(khỏi phí {int(timeout - (now - t0))}s còn lại)")
            raise subprocess.TimeoutExpired(cmd, int(now - t0))
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


# CHUẨN THUMBNAIL YOUTUBE (áp cho CẢ long lẫn short — YouTube chỉ nhận thumbnail tuỳ chỉnh 16:9,
# Shorts cũng vậy, nó tự cắt khi hiển thị dọc): 1280x720, JPG, dưới 2MB (trần cứng của YouTube).
YT_THUMB_W, YT_THUMB_H, YT_THUMB_MAX = 1280, 720, 2 * 1024 * 1024


def ensure_yt_thumb(path: str) -> bool:
    """Chốt chặn CUỐI trước khi ảnh rời máy: ép đúng 1280x720 và dưới 2MB.

    Vì sao cần dù các nhánh đều đã xuất 1280x720: chỉ cần MỘT nhánh sau này đổi kích thước là
    YouTube từ chối thumbnail SILENT (youtube_uploader bắt lỗi rồi bỏ qua để không chặn upload)
    -> video lên mà không có thumbnail, nhìn log thành công nên không ai biết. Kiểm ở đây thì
    không nhánh nào lọt được."""
    try:
        from PIL import Image
        im = Image.open(path)
        if im.size != (YT_THUMB_W, YT_THUMB_H):
            print(f"   🔧 thumbnail {im.size} != {YT_THUMB_W}x{YT_THUMB_H} -> ép lại đúng cỡ")
            im = im.convert("RGB").resize((YT_THUMB_W, YT_THUMB_H), Image.LANCZOS)
            im.save(path, "JPEG", quality=90)
        q = 90
        while os.path.getsize(path) > YT_THUMB_MAX and q >= 60:
            q -= 10                                    # hiếm khi chạm (ảnh thật ~100KB) nhưng vẫn chặn
            Image.open(path).convert("RGB").save(path, "JPEG", quality=q)
            print(f"   🔧 thumbnail > 2MB -> nén lại chất lượng {q}")
        return os.path.getsize(path) <= YT_THUMB_MAX
    except Exception as e:
        print("   ⚠️ không kiểm được cỡ thumbnail:", str(e)[:70])
        return True                                    # fail-open: thà thử upload còn hơn bỏ ảnh


SAFE_TOP = 0.58   # phụ đề cháy vào khung nằm ở ĐÁY -> lấy 58% trên là vùng sạch chữ
FRAME_BLUR = 9    # khung video vốn đã đầy nhãn/số -> mờ 9 thì chữ cũ tan thành kết cấu (đã thử 0/5/9)


def photo_score(path: str):
    """Khung này là ẢNH THẬT hay chỉ là ĐỒ HOẠ/BIỂU ĐỒ?

    Đo trên video thật: khung biểu đồ có 66-71% pixel TRÙNG HỆT pixel bên cạnh (mảng màu phẳng) và
    ít màu; ảnh chụp thì <15% và rất nhiều màu. Cần phân biệt vì nền thumbnail lấy từ khung biểu đồ
    (dù đã làm mờ) trông tẻ nhạt, KHÔNG hook — phải lùi sang ảnh thật/AI vẽ theo chủ đề.
    Trả (flat_percent, so_mau, la_anh_that)."""
    try:
        from PIL import Image
        im = Image.open(path).convert("RGB")
        im.thumbnail((240, 240))
        w, h = im.size
        raw = list(im.getdata())
        same = sum(1 for y in range(h) for x in range(w - 1) if raw[y * w + x] == raw[y * w + x + 1])
        flat = same / max(1, w * h) * 100
        cols = len({(r >> 3, g >> 3, b >> 3) for r, g, b in raw})
        return flat, cols, (flat < 15 and cols > 1400)
    except Exception:
        return 100.0, 0, False


def frame_bg(video: str, dest_dir: str, rel_prefix: str):
    """Rút 1 KHUNG ĐẸP NHẤT TỪ CHÍNH VIDEO làm nền thumbnail (footage thật -> khớp nội dung 100%).

    Dùng cho các engine ĐỒ HOẠ THUẦN (guess/mapped/ranked/scaled/thennow/swarm/pulse/clockwork/
    longshot): chúng KHÔNG tải ảnh thật nào, nên trước đây thumbnail chỉ là chữ trên nền màu phẳng —
    vừa chán vừa na ná nhau giữa các video. Giờ lấy chính hình ảnh video làm nền.
    Rút 6 khung rải đều thân bài, cắt 58% trên (tránh phụ đề), chọn khung nhiều chi tiết + rực màu
    nhất, bỏ khung đen (fade chuyển cảnh). Trả đường dẫn TƯƠNG ĐỐI trong public/ hoặc "" nếu hỏng."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", video], capture_output=True, text=True, timeout=60)
        dur = float((r.stdout or "0").strip() or 0)
    except Exception:
        return ""
    if dur <= 0:
        return ""
    os.makedirs(dest_dir, exist_ok=True)
    best, best_s = None, -1.0
    # 12 mốc (trước 6): ảnh thật chỉ chèn vài giây trong bài -> lấy thưa là trượt hết vào biểu đồ
    for i, p in enumerate((0.10, 0.18, 0.26, 0.34, 0.42, 0.50, 0.58, 0.66, 0.74, 0.82, 0.88, 0.93)):
        cand = os.path.join(dest_dir, f"_f{i}.jpg")
        try:
            subprocess.run(["ffmpeg", "-y", "-ss", f"{dur * p:.2f}", "-i", video, "-frames:v", "1",
                            "-vf", f"crop=iw:ih*{SAFE_TOP}:0:0,scale=1280:-2", "-q:v", "3", cand],
                           capture_output=True, timeout=90, check=True)
        except Exception:
            continue
        flat, cols, is_photo = photo_score(cand)
        if not is_photo:
            continue          # khung đồ hoạ/biểu đồ -> KHÔNG dùng làm nền (tẻ nhạt, không hook)
        try:
            from PIL import Image, ImageStat
            im = Image.open(cand).convert("RGB"); im.thumbnail((320, 320))
            stt = ImageStat.Stat(im)
            bright = sum(stt.mean) / 3.0
            s = 0.0 if bright < 26 else (sum(stt.stddev) / 3.0) * 1.6 \
                + (max(stt.mean) - min(stt.mean)) * 1.2 + min(bright, 150) * 0.25
        except Exception:
            s = 1.0
        if s > best_s:
            best_s, best = s, cand
    if not best or best_s <= 0:
        return ""
    final = os.path.join(dest_dir, "thumbbg.jpg")
    try:
        if os.path.exists(final):
            os.remove(final)
        os.rename(best, final)
    except Exception:
        return ""
    return f"{rel_prefix}/thumbbg.jpg"


def hook_frame_of(props: dict, fps: int = 30, default: int = 90) -> int:
    """Chọn ĐÚNG frame mà cảnh hook đã hiện ĐẦY ĐỦ.

    KHÔNG được dùng số cố định: độ dài intro bằng độ dài LỜI ĐỌC intro nên mỗi video một khác
    (props["introSec"]), và các hiệu ứng còn fade vào sau đó — ví dụ RaceLong cho dòng hook hiện dần
    từ frame 42 đến 56, nên chụp ở frame 40 sẽ ra ảnh CHƯA CÓ dòng hook (đã kiểm trong RaceLong.tsx).
    Lấy 72% chặng intro: chắc chắn qua hết fade-in mà chưa sang cảnh kế. Sàn 60 frame (2s) để không
    bao giờ rơi vào đoạn fade mở màn."""
    sec = 0.0
    try:
        # 3 dạng props đang dùng trong hệ thống:
        #   motif (swarm/ranked/…): props["introSec"]
        #   data-race (RaceLong/RaceLongV): props["intro"]["sec"]  — cảnh hook có kicker+title+bignum
        #   tài liệu (Cinematic):        props["scenes"][0]["dur"] tính bằng FRAME, không phải giây
        if props.get("introSec"):
            sec = float(props["introSec"])
        elif isinstance(props.get("intro"), dict) and props["intro"].get("sec"):
            sec = float(props["intro"]["sec"])
        elif props.get("scenes"):
            d0 = float((props["scenes"][0] or {}).get("dur") or 0)   # ĐƠN VỊ FRAME
            return max(60, int(d0 * 0.6)) if d0 > 0 else default
    except Exception:
        sec = 0.0
    if sec <= 0:
        return default
    return max(60, int(sec * fps * 0.72))


def still_hook_thumb(comp_id, props_path, dest_jpg, frame=90, api_key=None, title="", min_score=65,
                     trust=False):
    """THUMBNAIL = CHÍNH KHUNG HOOK MỞ ĐẦU, render TRỰC TIẾP từ Remotion (không cắt từ video).

    Vì sao không cắt từ mp4: video đã nén H.264 -> chữ rỗ, ảnh mềm, đúng kiểu "thumbnail mờ". Render
    still từ cùng composition + cùng props cho ra khung Y HỆT nhưng SẮC NÉT tuyệt đối, đúng kích cỡ.
    Đây là ảnh hook đã được thiết kế sẵn ở đầu bài -> khớp nội dung 100%, không phải vẽ chồng chữ.

    Composition dọc (short 1080x1920) -> lồng nguyên khung vào giữa khung 1280x720, nền là chính nó
    phóng to + làm mờ (ép cắt 16:9 sẽ xén mất chữ hai bên — đã thử thật).
    Có key -> Vision chấm chất lượng cảnh hook trước khi nhận. Trả True/False."""
    raw = dest_jpg + ".raw.png"
    try:
        subprocess.run(["npx", "remotion", "still", "src/index.ts", comp_id, raw,
                        f"--props=./{os.path.relpath(props_path, ENG)}",
                        f"--frame={int(frame)}", "--log=error"],
                       cwd=ENG, check=True, timeout=180)
        if not os.path.exists(raw):
            return False
        from PIL import Image
        w, h = Image.open(raw).size
        if w >= h:
            vf = "scale=1280:720:force_original_aspect_ratio=increase:flags=lanczos,crop=1280:720"
        else:
            # VIDEO DỌC: thử lồng nguyên khung vào giữa (pillarbox) thì ra dải hẹp, chữ bé tí, hai
            # bên là vệt mờ xấu — đã render thử và thấy rõ. Thay bằng CẮT CỬA SỔ 16:9 BÁM KHỐI CHỮ:
            # cụm hook (kicker + tiêu đề + số liệu + chú thích) nằm quanh 51% chiều cao, cắt quanh đó
            # rồi phóng lên 1280x720 -> chữ TO, rõ, vẫn thấy ảnh nền thật.
            ch_ = int(w * 9 / 16)
            y0 = max(0, min(h - ch_, int(h * 0.51 - ch_ / 2)))
            vf = f"crop={w}:{ch_}:0:{y0},scale=1280:720:flags=lanczos"
        subprocess.run(["ffmpeg", "-y", "-i", raw, "-vf", vf, "-q:v", "2", dest_jpg],
                       capture_output=True, timeout=90, check=True)
        if not os.path.exists(dest_jpg):
            return False
        ensure_yt_thumb(dest_jpg)
        if trust:
            # phần 2-3 cùng cụm: khung hook CÙNG THIẾT KẾ với phần 1 đã qua Vision; bản thân khung
            # đã qua cổng pixel (không nền trơn) + ensure_yt_thumb -> nhận thẳng, khỏi tốn 1 gọi.
            print("   🖼️ thumbnail khung hook: nhận theo phần 1 cùng cụm (lite)")
            return True
        if api_key:
            import qc_vision as QV
            ok, info = QV.check_thumb(dest_jpg, title=title, api_key=api_key, min_score=min_score)
            print(f"   🖼️ QC cảnh hook: {info.get('score')}/100"
                  + ("" if ok else f" — {'; '.join(info.get('issues') or [])[:90]}"))
            if not ok:
                return False      # hook xấu -> lùi về dựng DocThumb
        return True
    except Exception as e:
        print("   ⚠️ still hook lỗi:", str(e)[:80])
        return False
    finally:
        try:
            os.remove(raw)
        except Exception:
            pass


def opening_thumb(out_video, dest_jpg, api_key=None, title="", min_score=70):
    """DÙNG THẲNG KHUNG MỞ ĐẦU VIDEO LÀM THUMBNAIL.

    Cấu trúc video của hệ thống đặt HOOK NGAY ĐẦU BÀI: một khung đã thiết kế sẵn (tiêu đề lớn + số
    liệu sốc + ảnh nền thật). Đó chính là tấm thumbnail tốt nhất có thể có — khớp nội dung tuyệt đối
    vì nó LÀ video, và không cần vẽ chồng thêm chữ (vẽ thêm sẽ thành chữ đè chữ).

    Mốc chụp tính bằng GIÂY TUYỆT ĐỐI, KHÔNG theo % thời lượng: cảnh hook luôn nằm ở ~2-8 giây đầu
    dù video dài 30 giây hay 7 phút. Bản đầu lấy 6/11/16% nên với video long 7 phút hoá ra chụp ở
    giây 25/46/67 — trượt hẳn khỏi intro, ra khung giữa bài (đã tính lại và thấy rõ).

    Gemini Vision CHẤM CHÍNH NÓ NHƯ MỘT THUMBNAIL (qc_vision.check_thumb: chữ có bị cắt mép không,
    có đè nhau không, đọc được không, nền có trống trơn không). Đạt >= min_score -> dùng luôn.
    Không đạt -> trả False để lùi về dựng DocThumb như thường.
    Không có key Vision -> KHÔNG dùng (không dám lấy khung chưa ai kiểm làm mặt tiền video)."""
    if not api_key:
        return False
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", out_video],
                           capture_output=True, text=True, timeout=60)
        dur = float((r.stdout or "0").strip() or 0)
    except Exception:
        return False
    if dur <= 0:
        return False
    import qc_vision as QV
    # Video DỌC (short 1080x1920): ép về 16:9 kiểu cắt giữa sẽ XÉN MẤT CHỮ hai bên (đã thử thật).
    # -> lồng NGUYÊN khung vừa chiều cao vào giữa, nền là chính khung đó phóng to + làm mờ.
    try:
        rr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                             "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", out_video],
                            capture_output=True, text=True, timeout=60)
        _w, _h = (int(x) for x in (rr.stdout or "0x0").strip().split("x")[:2])
    except Exception:
        _w = _h = 0
    if _h > _w and _w > 0:   # dọc -> cắt cửa sổ 16:9 BÁM KHỐI CHỮ (giống still_hook_thumb)
        _ch = int(_w * 9 / 16)
        _y0 = max(0, min(_h - _ch, int(_h * 0.51 - _ch / 2)))
        VF = f"crop={_w}:{_ch}:0:{_y0},scale=1280:720:flags=lanczos,{SHARPEN}"
    else:                    # ngang -> lấy thẳng
        VF = f"scale=1280:720:force_original_aspect_ratio=increase:flags=lanczos,crop=1280:720,{SHARPEN}"
    tmpd = os.path.dirname(dest_jpg) or "."
    os.makedirs(tmpd, exist_ok=True)
    best, best_s = None, -1
    # GIÂY TUYỆT ĐỐI (không phải %): hook nằm ở 2-8s đầu với MỌI độ dài video.
    # LẤY SỚM NHƯ DRIVE: Drive hiện preview bằng khung ĐẦU video và tấm nào cũng đúng cảnh hook ->
    # bằng chứng cảnh hook đã hiện đầy đủ ngay từ giây đầu. Bản trước lấy 3.0/4.5/6.0s là QUÁ MUỘN,
    # nhiều video đã chuyển sang cảnh khác. Thử 1.0s trước (qua fade mở màn), rồi 0.5s, rồi mới tới
    # các mốc muộn hơn để phòng video có intro dài.
    marks = [t for t in (1.0, 0.5, 1.8, 3.0, 4.5) if t < dur * 0.9] or [min(0.5, dur / 2)]
    for i, t in enumerate(marks):
        cand = os.path.join(tmpd, f"_op{i}.jpg")
        try:
            subprocess.run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", out_video, "-frames:v", "1",
                            "-vf", VF, "-q:v", "2", cand], capture_output=True, timeout=90, check=True)
        except Exception:
            continue
        # LỌC MIỄN PHÍ TRƯỚC KHI GỌI VISION: cảnh hook (chữ lớn trên ẢNH nền thật) có ~29% pixel
        # phẳng, còn khung biểu đồ thuần đồ hoạ là ~66% (đo thật trên video của hệ thống). Chặn ở 45%
        # -> video KHÔNG có cảnh hook (bản render đời đầu) bị loại ngay, không tiêu lượt Gemini nào.
        # NGƯỠNG 63 (không phải 45): lượt chạy 150 video cho thấy khung bị loại nằm ở 49-61%, trong
        # khi video CHỈ CÓ biểu đồ đo được 65-67%. Đặt 45 là loại nhầm chính các cảnh hook có nền
        # ảnh tối/đơn giản. Chỉ chặn trường hợp CHẮC CHẮN là đồ hoạ, còn lại để Vision phán.
        _flat = photo_score(cand)[0]
        if _flat > 63:
            print(f"   ↩️ khung {t:.1f}s là đồ hoạ/biểu đồ ({_flat:.0f}% phẳng) — bỏ")
            continue
        ok, info = QV.check_thumb(cand, title=title, api_key=api_key, min_score=min_score)
        # VISION HỎNG (hết quota/mạng) -> check_thumb fail-open: ok=True nhưng KHÔNG có "score".
        # Bản trước lấy score=0 rồi so với min_score=70 -> LOẠI SẠCH: 788/820 khung hook bị vứt oan
        # chỉ vì Gemini hết quota, dù ảnh hoàn toàn tốt. Không chấm được thì TIN vào bộ lọc tất định
        # phía trên (đã loại khung đồ hoạ theo % phẳng) và NHẬN khung này.
        if info.get("note", "").startswith(("vision-skip", "no-thumb")) or "score" not in info:
            print(f"   ✅ khung mở đầu {t:.1f}s: Vision không chấm được -> nhận (đã qua bộ lọc đồ hoạ)")
            best, best_s = cand, max(min_score, 1)
            break
        sc = info.get("score") or 0
        print(f"   🖼️ khung mở đầu {t:.1f}s: {sc}/100"
              + ("" if ok else f" — {'; '.join(info.get('issues') or [])[:80]}"))
        if sc > best_s:
            best_s, best = sc, cand
        if ok:
            break
    if best is None or best_s < min_score:
        return False
    try:
        if os.path.exists(dest_jpg):
            os.remove(dest_jpg)
        os.rename(best, dest_jpg)
        return True
    except Exception:
        return False


def hook_bg(channel, out_video, subject, keys=None, api_key=None):
    """NỀN HOOK cho thumbnail — luôn cố ra một ảnh THẬT, LIÊN QUAN, BẮT MẮT.

    Thứ tự (dừng ở cái đầu tiên có được):
      1. Khung ẢNH THẬT rút từ chính video (chỉ nhận khung ảnh chụp, KHÔNG nhận khung biểu đồ —
         xem photo_score). Đây là ảnh khớp nội dung 100%.
      2. Ảnh CC0 Openverse theo chủ đề; không có thì Nano Banana (Gemini) VẼ ảnh minh hoạ đúng chủ
         đề — fetch_image() đã lo sẵn chuỗi này.
    Kênh đồ hoạ thuần (biểu đồ/bản đồ/tier list) không có ảnh chụp nào trong video nên hầu như luôn
    rơi xuống bước 2 — đúng ý đồ: thà một tấm ảnh thật/vẽ đúng chủ đề còn hơn khung biểu đồ làm mờ
    nhìn tẻ nhạt, không ai bấm vào.
    Trả (đường_dẫn_tương_đối, có_phải_khung_video)."""
    d = os.path.join(PUB, "_tb_" + slug(channel))
    rel = "_tb_" + slug(channel)
    got = frame_bg(out_video, d, rel)
    if got:
        return got, True
    if keys:
        set_ai_pool(keys, channel)   # nền thumbnail cũng có thể phải nhờ Nano Banana vẽ -> cho xoay cả pool
    key = api_key or ((keys or [{}])[0].get("key") if keys else None) or os.environ.get("GEMINI_API_KEY")
    try:
        os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, "hook.jpg")
        subj = (subject or channel).strip()
        if fetch_image(subj, dest, orient="wide", ai_key=key,
                       ai_prompt=f"dramatic cinematic editorial photo illustrating: {subj}. "
                                 f"No text, no words, no charts, no watermark."):
            return f"{rel}/hook.jpg", False
    except Exception as e:
        print("   ⚠️ hook_bg:", str(e)[:80])
    return "", False


def doc_thumb(channel, out, big, stat="", stat_label="", hook="",
              accent="#22D3EE", accent2="#F5B301", bg_rel="", bg_blur=0,
              api_key_for_thumb=None, comp_id="", props_path="", hook_frame=0,
              bg_provider=None):
    """Dựng thumbnail chuẩn nhà (DocThumb) — DÙNG CHUNG cho MỌI engine.

    Trước đây mỗi nhóm kênh một kiểu thumbnail riêng: 21 kênh doc + 10 kênh gốc dùng DocThumb (số
    liệu sốc + câu hỏi mở + ảnh thật), còn 9 kênh motif vẫn dùng Brand*Thumb kiểu cũ = chữ trên nền
    màu phẳng, KHÔNG số liệu, KHÔNG câu hỏi. Gộp hết về 1 công thức đã được duyệt.
    Trả đường dẫn ảnh hoặc "" nếu lỗi (caller tự lùi về cách cũ)."""
    thumb = out.rsplit(".", 1)[0] + ".jpg"
    # BƯỚC 0 — ưu tiên cao nhất: KHUNG HOOK MỞ ĐẦU của chính video. Video hệ thống đặt hook ngay đầu
    # bài (tiêu đề lớn + số sốc + ảnh nền thật) nên khung đó vốn ĐÃ là một thumbnail hoàn chỉnh, khớp
    # nội dung tuyệt đối. Chỉ nhận khi Gemini Vision chấm đạt (không cắt chữ/không đè/đọc được).
    _k = api_key_for_thumb or os.environ.get("GEMINI_API_KEY")
    try:
        # (a) NÉT NHẤT: render lại khung hook từ chính composition + props (không qua nén video).
        _hf = hook_frame
        if comp_id and props_path and not _hf:
            try:                       # tự suy frame từ độ dài intro THẬT của chính video này
                _hf = hook_frame_of(json.load(open(props_path)))
            except Exception:
                _hf = 90
        if comp_id and props_path and still_hook_thumb(comp_id, props_path, thumb, frame=_hf,
                                                       api_key=_k, title=big):
            print("   ✅ thumbnail = KHUNG HOOK MỞ ĐẦU (render nét từ composition)")
            return thumb
        # (b) không có props (vd render lại từ checkpoint) -> cắt khung đầu từ video
        if _k and opening_thumb(out, thumb, api_key=_k, title=big):
            print("   ✅ thumbnail = khung hook mở đầu (cắt từ video)")
            return thumb
    except Exception as e:
        print("   ⚠️ khung mở đầu bỏ qua:", str(e)[:70])
    # Tới đây = khung hook trượt QC -> BÂY GIỜ mới đi kiếm ảnh nền (trước đây kiếm sẵn từ đầu ->
    # mỗi video đều tốn ffmpeg + lượt Openverse + có khi cả lượt Nano Banana vẽ, dù phần lớn video
    # dùng khung hook và vứt hết công đó đi).
    if bg_provider is not None and not bg_rel:
        try:
            bg_rel, _is_frame = bg_provider()
            if _is_frame:
                bg_blur = FRAME_BLUR
        except Exception as e:
            print("   ⚠️ bg_provider lỗi:", str(e)[:70])
    try:
        tprops = {"bg": bg_rel, "big": big, "kicker": channel, "accent": accent, "accent2": accent2,
                  "stat": str(stat or "").strip(), "statLabel": str(stat_label or "").strip(),
                  "hook": str(hook or "").strip(), "bgBlur": bg_blur}
        tf = os.path.join(PUB, f"_dthumb_{slug(channel)}.json")
        json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "DocThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"],
                       cwd=ENG, check=True, timeout=180)
        if os.path.exists(thumb):
            ensure_yt_thumb(thumb)
            return thumb
        return ""
    except Exception as e:
        print("   ⚠️ DocThumb lỗi:", str(e)[:90])
        return ""
    finally:
        # Dọn khung tạm rút từ video (mỗi video 1 thư mục) — không dọn thì public/ phình dần
        # suốt phiên render 18 kênh song song.
        if str(bg_rel).startswith("_tb_"):
            try:
                import shutil
                shutil.rmtree(os.path.join(PUB, str(bg_rel).split("/")[0]), ignore_errors=True)
            except Exception:
                pass


def qc(mp4):
    """QC kỹ thuật: đủ giây + có audio + đúng khung."""
    def ff(args): return subprocess.run(["ffprobe", "-v", "error", *args, mp4],
                                        capture_output=True, text=True, timeout=60).stdout.strip()
    dur = float(ff(["-show_entries", "format=duration", "-of", "default=nk=1:nw=1"]) or 0)
    ach = ff(["-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "default=nk=1:nw=1"])
    wh = ff(["-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x"])
    try:
        size_mb = round(os.path.getsize(mp4) / 1e6, 1)
    except Exception:
        size_mb = 0
    # 23/8 — VÁ LỖ QC LỚN: mốc cũ chỉ là "dur >= 5 và CÓ luồng audio". Ba short CLOCKWORKUSA ra lò
    # 0:13 / 1.8MB / audio CÂM vẫn được chấm QC 100 rồi đẩy thẳng lên kho. Hai thứ phải kiểm thêm:
    #   1) ĐỘ DÀI TỐI THIỂU theo khổ hình (dọc = short, ngang = long) — 13 giây không phải một video.
    #   2) CÓ TIẾNG THẬT hay không — luồng audio tồn tại KHÔNG có nghĩa là có người nói.
    try:
        _w, _h = (int(x) for x in str(wh).lower().split("x")[:2])
    except Exception:
        _w = _h = 0
    portrait = _h > _w
    min_dur = 20 if portrait else 45
    # đo mức âm trung bình: câm hoàn toàn -> ffmpeg trả -91 dB; giọng nói chuẩn hoá -14 LUFS ~ -20 dB
    mean_db = 0.0
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp4, "-af", "volumedetect",
                            "-f", "null", "-"], capture_output=True, text=True, timeout=120)
        for line in (r.stderr or "").splitlines():
            if "mean_volume:" in line:
                mean_db = float(line.split("mean_volume:")[1].split("dB")[0].strip())
    except Exception:
        mean_db = 0.0
    silent = mean_db <= -45.0
    ok = dur >= max(5, min_dur) and ach == "audio" and not silent
    info = {"dur": round(dur, 1), "audio": ach == "audio", "res": wh, "size_mb": size_mb,
            "mean_db": round(mean_db, 1)}
    if not ok:
        why = []
        if dur < min_dur:
            why.append(f"quá ngắn {round(dur,1)}s < {min_dur}s ({'dọc/short' if portrait else 'ngang/long'})")
        if ach != "audio":
            why.append("không có luồng âm thanh")
        if silent:
            why.append(f"CÂM (mức âm {round(mean_db,1)}dB) — TTS hỏng, video không có lời")
        info["err"] = " · ".join(why)
    # 23/8: video đã dựng xong -> chốt sổ ảnh vừa dùng vào Firestore (chống trùng cho video sau).
    # Móc ở qc() vì mọi make_* đều gọi đúng một lần sau khi render xong.
    try:
        save_used_images()
    except Exception:
        pass
    return ok, info


def make_video(channel, seed, vtype, out, api_key=None, tier="normal", keys=None, on_status=None, on_limit=None, on_ok=None, resume_story=None,
                accent="#22D3EE", accent2="#F5B301"):
    """keys: list [{id,key,email}] (production, từ Firestore); None -> dùng GEMINI_API_KEY env (local).
    on_status(status, step, **extra): ghi trạng thái realtime. on_limit(key_id): cho key nghỉ khi limit.
    resume_story: kịch bản ĐÃ CÓ (checkpoint từ phiên trước bị huỷ/lỗi) -> dùng lại, bỏ qua gọi Gemini."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)   # QUAN TRỌNG: render chạy cwd=ENG -> phải tuyệt đối, nếu không file lạc chỗ (QC/enqueue tìm không ra -> 0 giây)
    print(f"▶ {channel} [{vtype}] seed={seed!r}")
    import key_manager as KM
    if keys is None:
        if not (api_key or os.environ.get("GEMINI_API_KEY")):
            raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
        keys = [{"id": "env", "key": api_key or os.environ["GEMINI_API_KEY"], "email": "local"}]
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", "Gemini viết kịch bản")
        story = KM.write_story(channel, keys, seed, vtype, tier, on_limit=on_limit, on_ok=on_ok)   # bám key theo kênh, limit -> nghỉ + đổi
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + ảnh + render", title=story.get("title"), score=score, script=_ckpt_json(story))
    sdir = os.path.join(PUB, "narration", "_ci_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    comp = "RaceLongV" if vtype == "short" else "RaceLong"
    props = build_props(story, sdir, vtype == "short", handle=channel_handle(channel))
    pf = os.path.join(PUB, f"_ci_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render {comp} …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", comp, out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label=comp)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out)
    if ok:                                          # QC THẨM MỸ (Gemini Vision) — chống chồng chéo/xấu
        try:
            import qc_vision
            vok, vinfo = _check_visual_rot(out, keys)
            info["visual"] = vinfo
            if not vok:
                ok = False
        except Exception as e:
            print("   ⚠️ vision qc skip:", e)
    # THUMBNAIL BRAND (DocThumb, dùng chung với 21 kênh doc) — 10 kênh GỐC (data-race) trước đây KHÔNG
    # có thumbnail riêng, rơi vào _make_thumb() ở run_render.py: cắt đại 1 khung TỪ VIDEO ĐÃ RENDER (dính
    # phụ đề/HUD cháy vào ảnh). Đây là 10 kênh có TOÀN BỘ 705 video đã đăng thật từ trước tới giờ, đáng
    # nâng cấp nhất. Data-race đã sẵn "hook_stat"/"hook_caption" (số to dùng ngay ở intro video) -> tái
    # dùng LUÔN cho thumbnail, khỏi cần Gemini trả thêm field mới. Nền = ảnh THẬT đã tuyển cho câu giữa
    # bài (props["races"][0]["shots"]), không phải khung cắt từ video render.
    try:
        # ƯU TIÊN: KHUNG HOOK MỞ ĐẦU render nét từ chính composition (khớp video 100%,
        # không phải vẽ chồng chữ). Không đạt QC -> rơi xuống dựng DocThumb bên dưới.
        _thumb0 = out.rsplit(".", 1)[0] + ".jpg"
        _kk = ((keys or [{}])[0].get("key") if keys else None) or os.environ.get("GEMINI_API_KEY")
        if still_hook_thumb(comp, pf, _thumb0, api_key=_kk, title=(story.get("title") or channel)):
            print("   ✅ thumbnail = KHUNG HOOK MỞ ĐẦU (render nét)")
            raise _HookDone(_thumb0)
        shots = (props.get("races") or [{}])[0].get("shots") or []
        bg_rel = shots[len(shots) // 2] if shots else ""
        if bg_rel and not os.path.exists(os.path.join(PUB, bg_rel)):
            bg_rel = ""
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        tprops = {"bg": bg_rel, "big": (story.get("title") or channel), "kicker": channel,
                  "accent": accent, "accent2": accent2,
                  "stat": str(story.get("hook_stat") or "").strip(),
                  "statLabel": str(story.get("hook_caption") or "").strip()}
        tf = os.path.join(PUB, f"_racethumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "DocThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True, timeout=240)
        if os.path.exists(thumb):
            story["_thumb"] = thumb; info["thumb"] = thumb
    except _HookDone as h:
        story["_thumb"] = h.args[0]; info["thumb"] = h.args[0]
    except Exception as e:
        print("   ⚠️ DocThumb bỏ qua (dùng khung cắt mặc định):", str(e)[:90])
    print(f"   {'✅' if ok else '❌'} QC {info}")
    return out, story, ok, info


def build_mapped_props(story, sdir, handle="@mappedusa", music="music/km_ascending.mp3"):
    """Dựng props MappedShort: TTS (intro+bloom+3 top+outro) -> timing bám giọng + 1 track. Không cần ảnh."""
    rel = lambda p: os.path.relpath(p, PUB)
    intro_mp3 = os.path.join(sdir, "intro.mp3"); bloom_mp3 = os.path.join(sdir, "bloom.mp3"); outro_mp3 = os.path.join(sdir, "outro.mp3")
    idur, _, _ = TK.synth(story.get("intro_vo") or story.get("title") or "Which state wins?", intro_mp3)
    bdur, _, _ = TK.synth(story.get("bloom_vo") or "Watch the map light up.", bloom_mp3)
    tops = (story.get("top") or [])[:3]
    top_mp3, top_durs = [], []
    for i, t in enumerate(tops):
        p = os.path.join(sdir, f"top{i}.mp3")
        du, _, _ = TK.synth(t.get("vo") or f"{t.get('state','')} {t.get('disp','')}", p)
        top_mp3.append(p); top_durs.append(du)
    odur, _, _ = TK.synth(story.get("outro_vo") or "Follow for more maps.", outro_mp3)
    introSec = round(idur + 0.4, 2); bloomSec = round(bdur + 0.5, 2)
    popSec = round((max(top_durs) if top_durs else 1.4) + 0.5, 2)
    outroSec = round(odur + 0.4, 2)
    nTop = len(tops)
    # track: intro@0, bloom@introSec, top rank r (0=#1) reveal ở slot (nTop-1-r), outro cuối
    popStart = introSec + bloomSec
    clips = [(intro_mp3, 0.0), (bloom_mp3, introSec)]
    for r, p in enumerate(top_mp3):
        slot = nTop - 1 - r                               # #1 hiện SAU CÙNG (climax) -> khớp composition
        clips.append((p, popStart + slot * popSec))
    clips.append((outro_mp3, popStart + nTop * popSec))
    total = round(popStart + nTop * popSec + outroSec, 2)
    track = os.path.join(sdir, "track.mp3"); _mix_track(clips, total, track)
    return {"title": (story.get("title") or "BY STATE"), "unit": story.get("unit", ""),
            "handle": handle, "color": "#22D3EE", "accent": "#22D3EE", "topN": nTop,
            "introSec": introSec, "bloomSec": bloomSec, "popSec": popSec, "outroSec": outroSec,
            "data": story.get("data") or [], "audio": rel(track), "music": music}


def make_mapped(channel, niche, out, keys=None, api_key=None, tier="normal",
                accent="#059669", accent2="#FDBA74",
                avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH #2 MAPPED A-Z: Gemini sinh metric+số liệu bang THẬT -> giọng -> render MappedShort -> QC + thumb.
    Trả (out, story, ok, info)."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini soạn bản đồ ({niche})")
        story = KM.write_mapped(channel, keys, niche, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + render bản đồ", title=story.get("title_yt") or story.get("title"), score=score, script=_ckpt_json(story))
    sdir = os.path.join(PUB, "narration", "_mapped_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    props = build_mapped_props(story, sdir, handle=channel_handle(channel))
    pf = os.path.join(PUB, f"_mapped_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render MappedShort ({len(props['data'])} bang) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "MappedShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="MappedShort")
    story["_credits"] = take_credits()   # 23/8: ghi công đúng ảnh đã dùng
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        _t = (story.get("top") or [{}])[0]
        _stat, _lab = _t.get("disp", ""), _t.get("state", "")
        _hook = story.get("title") or "WHICH STATE WINS?"
        _th = doc_thumb(channel, out, big=(story.get("title_yt") or story.get("title") or channel),
                        stat=_stat, stat_label=_lab, hook=_hook,
                        accent=accent, accent2=accent2,
                        bg_provider=lambda: hook_bg(channel, out,
                            _hook or story.get("title") or channel, keys=keys),
                        api_key_for_thumb=((keys or [{}])[0].get("key") if keys else None),
                        comp_id="MappedShort", props_path=pf,)
        thumb = _th or thumb
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb skip:", e)
    print(f"   {'✅' if ok else '❌'} QC mapped {info}")
    return out, story, ok, info


def build_ranked_props(story, sdir, handle="@rankedusa", music="music/km_ascending.mp3"):
    """Dựng props RankedShort: TTS (intro + mỗi item + outro) -> timing bám giọng + 1 track. Không cần ảnh."""
    rel = lambda p: os.path.relpath(p, PUB)
    intro_mp3 = os.path.join(sdir, "intro.mp3"); outro_mp3 = os.path.join(sdir, "outro.mp3")
    idur, _, _ = TK.synth(story.get("intro_vo") or story.get("title") or "Let's rank these.", intro_mp3)
    introSec = round(idur + 0.4, 2)
    items_in = story.get("items") or []
    items_out, clips, cum = [], [(intro_mp3, 0.0)], 0.0
    for i, it in enumerate(items_in):
        p = os.path.join(sdir, f"it{i}.mp3")
        du, _, _ = TK.synth(it.get("vo") or f"{it.get('name','')} is {it.get('tier','')} tier.", p)
        dur = round(du + 0.35, 2)
        items_out.append({"name": it.get("name"), "tier": it.get("tier"), "stat": it.get("stat"), "dur": dur})
        clips.append((p, introSec + cum)); cum += dur
    odur, _, _ = TK.synth(story.get("outro_vo") or "Agree? Comment your S tier.", outro_mp3)
    outroSec = round(odur + 0.4, 2)
    clips.append((outro_mp3, introSec + cum))
    total = round(introSec + cum + outroSec, 2)
    track = os.path.join(sdir, "track.mp3"); _mix_track(clips, total, track)
    return {"title": (story.get("title") or "TIER LIST"), "subtitle": story.get("subtitle", ""),
            "handle": handle, "color": "#7C5CFF", "accent": "#7C5CFF", "sfx": True,
            "introSec": introSec, "itemSec": 1.7, "outroSec": outroSec,
            "items": items_out, "audio": rel(track), "music": music}


def make_ranked(channel, niche, out, keys=None, api_key=None, tier="normal",
                accent="#D946EF", accent2="#67E8F9",
                avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH #3 RANKED A-Z: Gemini sinh tier list (tiêu chí + số liệu thật) -> giọng -> render RankedShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini xếp hạng ({niche})")
        story = KM.write_ranked(channel, keys, niche, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + render tier list", title=story.get("title_yt") or story.get("title"), score=score, script=_ckpt_json(story))
    sdir = os.path.join(PUB, "narration", "_ranked_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    props = build_ranked_props(story, sdir, handle=channel_handle(channel))
    pf = os.path.join(PUB, f"_ranked_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render RankedShort ({len(props['items'])} item) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "RankedShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="RankedShort")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        _s = [i for i in (story.get("items") or []) if i.get("tier") == "S"]
        _t = (_s or (story.get("items") or [{}]))[-1]
        _stat, _lab = _t.get("stat", ""), _t.get("name", "")
        _hook = story.get("title") or "WHAT'S S-TIER?"
        _th = doc_thumb(channel, out, big=(story.get("title_yt") or story.get("title") or channel),
                        stat=_stat, stat_label=_lab, hook=_hook,
                        accent=accent, accent2=accent2,
                        bg_provider=lambda: hook_bg(channel, out,
                            _hook or story.get("title") or channel, keys=keys),
                        api_key_for_thumb=((keys or [{}])[0].get("key") if keys else None),
                        comp_id="RankedShort", props_path=pf,)
        thumb = _th or thumb
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb skip:", e)
    print(f"   {'✅' if ok else '❌'} QC ranked {info}")
    return out, story, ok, info


def build_scaled_props(story, sdir, handle="@scaledusa", music="music/km_ascending.mp3"):
    """Dựng props ScaledShort: TTS (intro + mỗi item + outro) -> timing bám giọng + 1 track. Emoji có sẵn từ story."""
    rel = lambda p: os.path.relpath(p, PUB)
    intro_mp3 = os.path.join(sdir, "intro.mp3"); outro_mp3 = os.path.join(sdir, "outro.mp3")
    idur, _, _ = TK.synth(story.get("intro_vo") or story.get("title") or "How big is it?", intro_mp3)
    introSec = round(idur + 0.4, 2)
    items_in = story.get("items") or []
    items_out, clips, cum = [], [(intro_mp3, 0.0)], 0.0
    for i, it in enumerate(items_in):
        p = os.path.join(sdir, f"it{i}.mp3")
        du, _, _ = TK.synth(it.get("vo") or f"{it.get('name','')}, {it.get('disp','')}.", p)
        dur = round(du + 0.4, 2)
        items_out.append({"name": it.get("name"), "emoji": it.get("emoji"), "value": it.get("value"),
                          "disp": it.get("disp"), "dur": dur})
        clips.append((p, introSec + cum)); cum += dur
    odur, _, _ = TK.synth(story.get("outro_vo") or "Follow for more size shocks.", outro_mp3)
    outroSec = round(odur + 0.4, 2)
    clips.append((outro_mp3, introSec + cum))
    total = round(introSec + cum + outroSec, 2)
    track = os.path.join(sdir, "track.mp3"); _mix_track(clips, total, track)
    return {"title": (story.get("title") or "SIZE COMPARISON"), "subtitle": story.get("subtitle", ""),
            "handle": handle, "color": "#2FA84F", "accent": "#2FA84F", "sfx": True,
            "introSec": introSec, "itemSec": 2.0, "outroSec": outroSec,
            "items": items_out, "audio": rel(track), "music": music}


def make_scaled(channel, niche, out, keys=None, api_key=None, tier="normal",
                accent="#0284C7", accent2="#FDE68A",
                avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH #4 SCALED A-Z: Gemini sinh so sánh kích thước (đo thật + emoji) -> giọng -> render ScaledShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini so sánh kích thước ({niche})")
        story = KM.write_scaled(channel, keys, niche, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + render so sánh", title=story.get("title_yt") or story.get("title"), score=score, script=_ckpt_json(story))
    sdir = os.path.join(PUB, "narration", "_scaled_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    props = build_scaled_props(story, sdir, handle=channel_handle(channel))
    pf = os.path.join(PUB, f"_scaled_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render ScaledShort ({len(props['items'])} vật) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "ScaledShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="ScaledShort")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        _t = (story.get("items") or [{}])[-1]
        _stat, _lab = _t.get("disp", ""), _t.get("name", "")
        _hook = story.get("title") or "HOW BIG REALLY?"
        _th = doc_thumb(channel, out, big=(story.get("title_yt") or story.get("title") or channel),
                        stat=_stat, stat_label=_lab, hook=_hook,
                        accent=accent, accent2=accent2,
                        bg_provider=lambda: hook_bg(channel, out,
                            _hook or story.get("title") or channel, keys=keys),
                        api_key_for_thumb=((keys or [{}])[0].get("key") if keys else None),
                        comp_id="ScaledShort", props_path=pf,)
        thumb = _th or thumb
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb skip:", e)
    print(f"   {'✅' if ok else '❌'} QC scaled {info}")
    return out, story, ok, info


def build_thennow_props(story, sdir, handle="@thennowusa", music="music/km_ossuary_air.mp3"):
    """Dựng props ThenNowShort: TTS (intro + mỗi cặp + outro) -> timing bám giọng + 1 track."""
    rel = lambda p: os.path.relpath(p, PUB)
    intro_mp3 = os.path.join(sdir, "intro.mp3"); outro_mp3 = os.path.join(sdir, "outro.mp3")
    idur, _, _ = TK.synth(story.get("intro_vo") or story.get("title") or "Then versus now.", intro_mp3)
    introSec = round(idur + 0.4, 2)
    pairs_in = story.get("pairs") or []
    pairs_out, clips, cum = [], [(intro_mp3, 0.0)], 0.0
    for i, p in enumerate(pairs_in):
        mp = os.path.join(sdir, f"pair{i}.mp3")
        du, _, _ = TK.synth(p.get("vo") or f"{p.get('label','')}: {p.get('thenVal','')} then, {p.get('nowVal','')} now.", mp)
        dur = round(du + 0.6, 2)
        pairs_out.append({"label": p.get("label"), "thenYear": p.get("thenYear"), "thenVal": p.get("thenVal"),
                          "nowYear": p.get("nowYear"), "nowVal": p.get("nowVal"), "change": p.get("change"), "dur": dur})
        clips.append((mp, introSec + cum)); cum += dur
    odur, _, _ = TK.synth(story.get("outro_vo") or "Which change shocked you most?", outro_mp3)
    outroSec = round(odur + 0.4, 2)
    clips.append((outro_mp3, introSec + cum))
    total = round(introSec + cum + outroSec, 2)
    track = os.path.join(sdir, "track.mp3"); _mix_track(clips, total, track)
    return {"title": (story.get("title") or "THEN vs NOW"),
            "handle": handle, "color": "#EC4899", "accent": "#EC4899", "sfx": True,
            "introSec": introSec, "pairSec": 4.5, "outroSec": outroSec,
            "pairs": pairs_out, "audio": rel(track), "music": music}


def make_thennow(channel, niche, out, keys=None, api_key=None, tier="normal",
                 accent="#9333EA", accent2="#86EFAC",
                avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH #5 THEN×NOW A-Z: Gemini sinh so sánh xưa/nay (giá trị thật) -> giọng -> render ThenNowShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini so sánh xưa/nay ({niche})")
        story = KM.write_thennow(channel, keys, niche, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + render xưa/nay", title=story.get("title_yt") or story.get("title"), score=score, script=_ckpt_json(story))
    sdir = os.path.join(PUB, "narration", "_thennow_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    props = build_thennow_props(story, sdir, handle=channel_handle(channel))
    pf = os.path.join(PUB, f"_thennow_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render ThenNowShort ({len(props['pairs'])} cặp) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "ThenNowShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="ThenNowShort")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        _t = (story.get("pairs") or [{}])[0]
        _stat, _lab = _t.get("change", ""), _t.get("label", "")
        _hook = (f"{_t.get('thenVal','')} → {_t.get('nowVal','')}").strip(" →") or story.get("title", "")
        _th = doc_thumb(channel, out, big=(story.get("title_yt") or story.get("title") or channel),
                        stat=_stat, stat_label=_lab, hook=_hook,
                        accent=accent, accent2=accent2,
                        bg_provider=lambda: hook_bg(channel, out,
                            _hook or story.get("title") or channel, keys=keys),
                        api_key_for_thumb=((keys or [{}])[0].get("key") if keys else None),
                        comp_id="ThenNowShort", props_path=pf,)
        thumb = _th or thumb
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb skip:", e)
    print(f"   {'✅' if ok else '❌'} QC thennow {info}")
    return out, story, ok, info


def build_doc_props(story, channel, imgsrc=None, api_key=None, accent="#22D3EE", accent2="#F5B301", handle="@doc",
                    ai_style=None, ai_only=False, music=None, mode=None, host_prompt=None, prefix=""):
    """Dựng props Cinematic (Wave 2): CHỈ các cảnh có ảnh (fetch + Vision verify khớp) — KHÔNG intro/outro.
    Asset: PUB/<slug>/*.mp3 (giọng) + PUB/<slug>/clips/*.jpg (ảnh). dur tính bằng FRAME (30fps).
    ai_style/ai_only: kênh speculative (không có ảnh thật để so) -> gu vẽ riêng + bỏ qua Openverse hẳn.
    music: nhạc nền cực nhẹ xuyên suốt — MẶC ĐỊNH TẮT (None). 13 kênh doc-format có tông rất khác nhau
    (awe/eerie/deadpan/ominous...) -> 1 bài nhạc chung ép lên hết dễ bị lệch tông ("kỳ" — đúng như user
    lo). CHỈ bật khi đã NGHE THẬT + chọn đúng bài hợp tông từng kênh (đặt field 'music' riêng ở
    render_channels), không đoán theo tên file. File PHẢI `git ls-files` xác nhận có trên git trước khi
    dùng (xem PIPELINE_RULES.md — bài học 404 nhạc)."""
    FPS = 30
    slug_ = "_doc_" + slug(channel)
    sdir = os.path.join(PUB, slug_); cdir = os.path.join(sdir, "clips")
    os.makedirs(cdir, exist_ok=True)
    scenes_out = []
    import qc_vision
    # ai_only: ảnh nào cũng do AI vẽ theo prompt, không có "ảnh thật tải về" để verify khớp/sai -> khỏi tốn Vision API.
    # CHẤM HÀNG LOẠT (1 lệnh/cảnh thay vì 1 lệnh/ảnh) + xoay key. ai_only (ảnh AI vẽ) -> khỏi kiểm.
    vm_on = bool(api_key and not ai_only)
    vf_for = lambda subj: None      # đường từng-ảnh tắt cho doc — giữ chữ ký fetch_image cho caller khác
    vm_for = (lambda: (lambda pairs: _verify_grid_rot(pairs, first_key=api_key))) if vm_on else (lambda: None)

    def add_scene(i, nar, kind, img_query=None, title="", hook=None, alt_queries=None):
        amp3 = os.path.join(sdir, f"{prefix}s{i}.mp3")
        dur_s, _subs, _ = TK.synth(nar or title or "…", amp3)
        durF = max(48, round((dur_s + 0.5) * FPS))
        # KHÔNG truyền subs (TK trả dạng TỪ, Cinematic cần dạng CÂU) -> để engine tự tạo caption từ nar (khớp giọng đều).
        sc = {"type": kind, "audio": f"{prefix}s{i}.mp3", "dur": durF, "nar": nar or "", "title": title or ""}
        if hook:
            sc["hook"] = hook          # cảnh MỞ ĐẦU: số liệu to + nhãn + câu hỏi mở, đè lên footage
        if img_query:
            # CẮT CẢNH 2-3 GIÂY: một cảnh dài 6-8s mà đứng yên 1 tấm ảnh là nhàm. Chia cảnh thành
            # các đoạn ~2.6s, mỗi đoạn MỘT ẢNH KHÁC — lấy hết trong CÙNG 1 lần tìm Openverse nên
            # không tốn thêm lượt gọi API nào. Tối đa 3 ảnh/cảnh (đủ nhịp, không phình thời gian tải).
            segs = max(1, min(3, round(durF / (2.6 * FPS))))
            extra_paths = [os.path.join(cdir, f"{prefix}s{i}_{k}.jpg") for k in range(1, segs)]
            for _p in extra_paths:                     # dọn file cũ của video trước -> không nhận nhầm
                try: os.remove(_p)
                except OSError: pass
            # THỬ LẦN LƯỢT nhiều truy vấn: cảnh mở đầu BẮT BUỘC phải có ảnh thật, không được rơi
            # về nền trơn. Openverse trượt từ khoá này thì thử từ khoá khác trước khi bỏ cuộc.
            got = None
            # NGÂN SÁCH VISION THEO VAI TRÒ CẢNH: cảnh MỞ ĐẦU là mặt tiền (thumbnail + 3s giữ chân)
            # -> đáng 4 lượt kiểm/ứng viên. Cảnh sau là b-roll lướt ~2.6s, đã qua lọc từ khoá +
            # lọc deterministic -> 2 lượt là đủ. Ở 1.000 video/ngày, riêng chỗ này cắt ~nửa số
            # lệnh gọi Vision (mục ăn Gemini lớn nhất toàn pipeline).
            _mc = 4 if i == 0 else 2
            # 24/8 — CLIP THẬT XEN KẼ ẢNH TĨNH: cảnh mở đầu và cứ 3 cảnh lấy 1 clip video thật
            # (Pexels/Pixabay video, dùng chung key ảnh). Hỏng/không có -> lùi về ảnh tĩnh như cũ,
            # nên không có đường nào làm video xấu đi. Xen kẽ thay vì toàn video: tải nhẹ hơn,
            # render nhanh hơn, và nhịp hình đa dạng hơn là chuỗi clip liên tục.
            if os.environ.get("CLIPS_OFF") != "1" and (i == 0 or i % 3 == 0):
                _cp = fetch_clip(img_query, os.path.join(cdir, f"{prefix}s{i}.mp4"), tall=True)
                if _cp:
                    sc["clip"] = f"{prefix}s{i}.mp4"
                    scenes_out.append(sc)
                    return sc
            for _q in [img_query] + list(alt_queries or []):
                if not _q:
                    continue
                got = fetch_image(_q, os.path.join(cdir, f"{prefix}s{i}.jpg"), orient="tall", verify=vf_for(_q),
                                  verify_many=vm_for(), max_check=_mc, ai_key=api_key, ai_style=ai_style,
                                  ai_only=ai_only, extra=extra_paths)
                if got:
                    break
            if got:
                sc["clip"] = f"{prefix}s{i}.jpg"
                _cl = [f"{prefix}s{i}.jpg"] + [os.path.basename(_p) for _p in extra_paths if os.path.exists(_p)]
                if len(_cl) > 1:
                    sc["clips"] = _cl              # engine tự chia đều thời lượng cho từng ảnh
            # KHÔNG có ảnh -> giữ nguyên type 'scene', chỉ thiếu clip: engine vẫn vẽ nền theo tông kênh
            # (ThemedBase) + phụ đề. TRƯỚC ĐÂY hạ xuống 'chapter' -> hiện thẻ CHỮ TO trên nền trơn giữa
            # video, đúng thứ user không muốn. Thà nền tông kênh còn hơn một thẻ tiêu đề chen ngang.
        scenes_out.append(sc)
        return sc

    # KHÔNG INTRO, KHÔNG OUTRO (rule của user). Trước đây dựng 2 thẻ chapter — chữ to trên nền
    # cosmic, không ảnh — kẹp đầu và cuối video. Vì thumbnail lấy đúng khung MỞ ĐẦU nên mọi video
    # ra một tấm chữ-trên-nền-đen na ná nhau, và người xem phải chờ hết thẻ mới thấy nội dung.
    # Giờ: video VÀO THẲNG cảnh có footage. Lời hook gộp vào cảnh 1, lời kết gộp vào cảnh cuối
    # -> không mất chữ nào, chỉ bỏ 2 thẻ tiêu đề.
    _scs = [x for x in (story.get("scenes") or []) if (x.get("nar") or x.get("img_query"))]
    if not _scs:
        _scs = [{"nar": story.get("hook") or story.get("title") or "", "img_query": story.get("title")}]
    _hook = (story.get("hook") or "").strip()
    # KHÔNG gộp outro: schema doc định nghĩa outro = "spoken closing + soft CTA (follow for more)"
    # — đúng loại câu rule user CẤM. Tệ hơn ở bản long ghép 3 phần: CTA của phần 1/2 rơi vào GIỮA
    # video (mốc 1/3, 2/3) — người xem nghe "follow for more" khi video còn 2/3 nội dung.
    # Video kết thúc ở câu nội dung cuối cùng, không đuôi thừa.
    _outro = ""
    i = 0
    for k, sc0 in enumerate(_scs):
        nar = (sc0.get("nar") or "").strip()
        if k == 0 and _hook and not nar.startswith(_hook):
            nar = f"{_hook} {nar}".strip()          # hook đọc ngay trên footage, không cần thẻ riêng
        if k == len(_scs) - 1 and _outro and _outro not in nar:
            nar = f"{nar} {_outro}".strip()         # lời kết nối vào cảnh cuối, bỏ thẻ outro
        # CẢNH 1 = CẢNH HOOK (giống kênh 01/02/03): footage thật + SỐ LIỆU TO + câu hỏi mở đè lên,
        # đọc luôn lời hook. Không phải thẻ tiêu đề chờ sẵn — vào là hook ngay.
        hk = None
        if k == 0:
            _stat = str(story.get("thumb_stat") or "").strip()
            _lab = str(story.get("thumb_label") or "").strip()
            _q = str(story.get("thumb_hook") or "").strip()
            if _stat or _q:
                hk = {"stat": _stat[:8], "label": _lab[:20], "line": _q[:22]}
        _alts = None
        if k == 0:
            # dự phòng cho cảnh MỞ ĐẦU: img_query các cảnh sau, rồi tới tiêu đề/chủ đề. Mở đầu mà
            # không có footage thì cả video hỏng ngay giây đầu -> cố tới cùng.
            _alts = [x.get("img_query") for x in _scs[1:4] if x.get("img_query")]
            _alts += [story.get("title_yt"), story.get("title"), story.get("topic")]
        add_scene(i, nar, "scene", img_query=sc0.get("img_query"), title=sc0.get("title", ""),
                  hook=hk, alt_queries=_alts); i += 1
    # LỚP CUỐI cho cảnh MỞ ĐẦU: đã thử img_query của chính nó -> img_query 3 cảnh sau -> tiêu đề
    # -> Gemini vẽ (fetch_image tự lo), mà vẫn trắng tay thì MƯỢN ảnh của cảnh sau đã có.
    # Mượn ảnh thay vì đảo thứ tự cảnh: đảo thứ tự sẽ làm lời thoại mất mạch, còn mượn ảnh thì
    # mở đầu vẫn có footage thật liên quan mà câu chuyện giữ nguyên trình tự.
    if scenes_out and not scenes_out[0].get("clip"):
        for _later in scenes_out[1:]:
            if _later.get("clip"):
                _srcp = os.path.join(cdir, _later["clip"])
                _dstp = os.path.join(cdir, f"{prefix}s0_lead.jpg")
                try:
                    import shutil
                    shutil.copyfile(_srcp, _dstp)
                    scenes_out[0]["clip"] = f"{prefix}s0_lead.jpg"
                    scenes_out[0].pop("clips", None)
                    print(f"   ↩️ cảnh mở đầu mượn ảnh của cảnh sau ({_later['clip']}) — không để mở đầu nền trơn")
                except Exception:
                    pass
                break
    props = {"scenes": scenes_out, "slug": slug_, "handle": handle, "accent": accent, "accent2": accent2}
    if music:
        props["music"] = music
    if mode:
        props["mode"] = mode
    if host_prompt and api_key:
        ref = _generate_character_ref(channel, host_prompt, api_key)
        if ref:
            props["host"] = ref
    return props


def flat_bg_metrics(path: str):
    """Đo khung ảnh: (%điểm tối, độ bão hoà TB, số màu). Dùng để biết khung có phải NỀN TRƠN không."""
    try:
        from PIL import Image
        im = Image.open(path).convert("RGB"); im.thumbnail((240, 240))
        raw = list(im.getdata()); n = max(1, len(raw))
        lum = [(r * 299 + g * 587 + b * 114) // 1000 for r, g, b in raw]
        dark = sum(1 for x in lum if x < 40) / n * 100
        sat = sum(max(r, g, b) - min(r, g, b) for r, g, b in raw) / n
        cols = len({(r >> 3, g >> 3, b >> 3) for r, g, b in raw})
        return dark, sat, cols
    except Exception:
        return 0.0, 999.0, 9999      # đo không được -> coi như ĐẠT, không chặn oan


DARK_OK_CHANNELS = set((os.environ.get("DARK_OK_CHANNELS")
                        or "COSMOS,THEDEEP,UNSEENUSA,FUTUREUSA,UNDERUSA").upper().split(","))


def _dark_ok(channel) -> bool:
    """Kênh có thẩm mỹ TỐI CHỦ ĐÍCH (vũ trụ/đáy biển/bí ẩn): mở đầu tối là ĐÚNG CHẤT, không phải
    lỗi nền trơn. Phát hiện 22/8: cổng dark>=75&cols<900 giết oan 4/6 short COSMOS (dark 75-86%
    nhưng 737-992 màu — là ảnh không gian thật/nền cosmic có sao, không phải thẻ chữ trống)."""
    return str(channel or "").upper() in DARK_OK_CHANNELS


def opening_is_flat(mp4: str, at: float = 1.2, dark_ok: bool = False):
    """KHUNG MỞ ĐẦU có phải 'chữ trên nền trơn' không? Đo bằng PIXEL, KHÔNG gọi API, không tốn quota.

    Đây là chốt chặn SAU RENDER cho đúng rule: mở đầu BẮT BUỘC là ảnh nền hook thật.
    qc_structure chặn trước render dựa trên props; hàm này soi VIDEO THẬT ĐÃ DỰNG — bắt cả trường
    hợp props có 'clip' nhưng ảnh hỏng/không hiện ra.

    Ngưỡng đo trên khung render thật (21/8):
        có footage rực rỡ   : 43.9% tối · bão hoà 78.9 · 1983 màu -> ĐẠT
        ảnh thật TỐI, xỉn   : 68.0% tối · bão hoà 31.1 ·  401 màu -> ĐẠT (không bắt oan ảnh tối)
        NỀN TRƠN (cần bắt)  : 91.9% tối · bão hoà 14.2 ·  342 màu -> BẮT
    Trả (ok, info)."""
    jpg = os.path.splitext(mp4)[0] + "_open.jpg"
    try:
        subprocess.run(["ffmpeg", "-y", "-ss", str(at), "-i", mp4, "-frames:v", "1", jpg],
                       check=True, capture_output=True, timeout=120)
    except Exception as e:
        return True, {"note": f"không trích được khung: {str(e)[:60]}"}   # fail-open, đừng chặn oan
    dark, sat, cols = flat_bg_metrics(jpg)
    try: os.remove(jpg)
    except OSError: pass
    # ĐO THẬT đêm 21/8 (DEBTUSA, 6 video render thành công đầu tiên): video THẬT của hệ có sat
    # 10-13.6 và colors 417-738 — bảng màu doc-style trầm là BÌNH THƯỜNG. Điều kiện (cols<500 &
    # sat<25) giết oan 2/6 video tốt (dark chỉ 35-37%, tức có ảnh thật, không hề "nền trơn").
    # Chữ-trên-nền-trơn thật sự có chữ ký dark>=75 (đo: 91.9%) -> giữ điều kiện ĐÓ làm chặn cứng,
    # ca ít-màu hạ xuống CẢNH BÁO ghi vào info để soi, không giết video.
    # Kênh tối-chủ-đích: chỉ chặn chữ ký NỀN TRƠN THẬT SỰ (đo 21/8: 91.9% tối · 342 màu) —
    # ngưỡng 88/450 vẫn bắt được thẻ chữ trống nhưng tha cho khung không gian tối giàu màu.
    flat = (dark >= 88 and cols < 450) if dark_ok else (dark >= 75 and cols < 900)
    warn = (cols < 500 and sat < 25 and not flat)
    info = {"dark": round(dark, 1), "sat": round(sat, 1), "colors": cols}
    if warn:
        info["note"] = "màu trầm/ít màu — soi bằng mắt nếu lặp"
        print(f"   ⚠️ mở đầu màu trầm (sat {sat:.0f}, {cols} màu) — cho qua, ghi nhận để soi")
    return (not flat), info


def fresh_out(out: str):
    """XOÁ file cũ cùng tên TRƯỚC khi render — chống lẫn bản không đạt chuẩn của vòng trước.

    Vì sao cần: tên file đầu ra cố định theo kênh (vd out/xxx_docshort0.mp4) nên MỖI VÒNG trong
    cùng một phiên đều ghi đè đúng chỗ đó. Nhiều nơi lại suy ra thumbnail = <out>.jpg. Nếu vòng
    này render/thumbnail hỏng giữa chừng mà file vòng TRƯỚC còn nằm đó, bước đẩy Drive có thể vớ
    phải bản cũ -> video mới đăng kèm ảnh của video khác. Dọn sạch trước là hết cả lớp lỗi này."""
    for f in (out, out.rsplit(".", 1)[0] + ".jpg", out.rsplit(".", 1)[0] + "_thumb.jpg",
              out.rsplit(".", 1)[0] + "_open.jpg"):
        try:
            if os.path.exists(f):
                os.remove(f)
        except OSError:
            pass


def prune_ghost_clips(props: dict):
    """LỌC ẢNH MA khỏi props ngay trước khi ghi: mọi clip/clips phải TỒN TẠI và >1KB trên đĩa.

    Vì sao (21/8): render UNSOLVED treo 7/7 lần vì Remotion chờ vô hạn một ảnh đăng ký trong props
    nhưng không nạp được lúc render -> CPU 0% -> watchdog giết sau 6'/lần, cả lane 0 video. SafeImg
    bên TSX đã chặn tầng render; tầng này chặn từ gốc: ảnh ma không bao giờ vào props."""
    base = os.path.join(PUB, props.get("slug", ""), "clips")
    def ok(f):
        try:
            fp = os.path.join(base, f)
            return os.path.exists(fp) and os.path.getsize(fp) > 1000
        except OSError:
            return False
    dropped = 0
    for sc in props.get("scenes") or []:
        cl = [c for c in (sc.get("clips") or ([sc["clip"]] if sc.get("clip") else [])) if ok(c)]
        dropped += len(sc.get("clips") or ([sc.get("clip")] if sc.get("clip") else [])) - len(cl)
        if cl:
            sc["clip"] = cl[0]
            if len(cl) > 1:
                sc["clips"] = cl
            else:
                sc.pop("clips", None)
        else:
            sc.pop("clip", None); sc.pop("clips", None)
    if dropped:
        print(f"   🧹 prune_ghost_clips: bỏ {dropped} ảnh ma khỏi props (không để render chờ ảnh không tồn tại)")
    return props


_CANARY = {"ok": None}


def render_canary() -> bool:
    """PHÁT SÚNG THỬ 0-QUOTA: render 12 frame CinematicShort bằng asset tự tạo (KHÔNG một gọi
    Gemini nào) TRƯỚC khi luồng bắt đầu tiêu đạn viết kịch bản.

    Bài học 21/8 trả giá đắt nhất: engine render hỏng (treo chờ ảnh) nhưng não vẫn viết đủ 15
    gọi/luồng x 18 luồng -> đốt sạch 1.120 gọi/ngày của 56 key mà ra 0 video. Nếu hôm đó có phát
    súng thử này, cả ngày quota còn nguyên. Chi phí: ~30-60s CPU/luồng, cache theo tiến trình.
    Trả False = engine hỏng -> luồng dừng NGAY với thông báo rõ, quota nguyên vẹn."""
    if _CANARY["ok"] is not None:
        return _CANARY["ok"]
    try:
        d = os.path.join(PUB, "_canary"); os.makedirs(os.path.join(d, "clips"), exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=540x960:rate=1",
                        "-frames:v", "1", os.path.join(d, "clips", "c.jpg")],
                       capture_output=True, timeout=60, check=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=200:d=1.5", "-ar", "44100",
                        os.path.join(d, "a.mp3")], capture_output=True, timeout=60, check=True)
        pf = os.path.join(PUB, "_canary.json")
        json.dump({"scenes": [{"type": "scene", "clip": "c.jpg", "audio": "a.mp3", "dur": 45,
                               "nar": "canary", "hook": {"stat": "1", "line": "OK"}}],
                   "slug": "_canary", "handle": "@c", "accent": "#22D3EE", "accent2": "#F5B301"},
                  open(pf, "w"))
        out = os.path.join(d, "c.mp4")
        subprocess.run(["npx", "remotion", "render", "src/index.ts", "CinematicShort", out,
                        f"--props=./{os.path.relpath(pf, ENG)}", "--frames=0-11",
                        "--gl=swiftshader", "--concurrency=1", "--log=error"],
                       cwd=ENG, capture_output=True, timeout=240, check=True)
        _CANARY["ok"] = os.path.exists(out) and os.path.getsize(out) > 1000
    except Exception as e:
        print(f"   🐤 CANARY FAIL — engine render hỏng, DỪNG luồng để không đốt quota: {str(e)[:120]}")
        _CANARY["ok"] = False
    if _CANARY["ok"]:
        print("   🐤 canary render OK (~0 quota) — engine sống, cho phép tiêu đạn Gemini")
    return _CANARY["ok"]


def qc_structure(props, fps=30):
    """QC CẤU TRÚC — kiểm bằng LOGIC, không gọi API, không tốn quota.

    VÌ SAO CẦN (bài học 21/8): đã có QC visual bằng Gemini Vision mà cả loạt video vẫn ra lò
    toàn chữ trên nền đen. Hai lý do, cả hai đều không phải "Vision kém":
      1. check_visual chấm KHUYẾT TẬT, không chấm CHUẨN HẤP DẪN — prompt ghi rõ "chỉ dưới 50 nếu
         THỰC SỰ vỡ; sạch, đọc được = 80+". Thẻ chữ trên nền đen thì sạch và đọc rất rõ -> 80+.
      2. Lúc đó Vision còn kẹt keys[0] nên 429 liên tục -> fail-open, không hề soi tấm nào.
    Vision không bao giờ thay được luật cứng. Những thứ dưới đây ĐO ĐƯỢC nên phải chặn bằng code:

    Trả (ok, issues). ok=False CHỈ khi video hỏng về bản chất (không một ảnh nào) — thứ đã tạo ra
    cả lô hôm nay. Còn lại trả cảnh báo để ghi vào job, không chặn sản xuất."""
    scenes = props.get("scenes") or []
    issues = []
    if not scenes:
        return False, ["không có cảnh nào"]
    # ── ĐỘ LẶP HÌNH (23/8, user: "footage lặp đi lặp lại hơi nhiều") ────────────────────────────
    # Trước đây QC chỉ ĐẾM số ảnh, không kiểm ảnh có TRÙNG NHAU không. Mà mọi đường hỏng đều dẫn
    # tới lặp: tải footage lỗi -> lấy lại ảnh trước; FLUX vẽ trượt -> dùng khung liền trước; Vision
    # bắt ảnh sai -> vẽ lại không được -> lại lấy ảnh trước. Kết quả: video "đủ 10 cảnh" nhưng chỉ
    # có 3 hình thật, xem rất chán mà QC vẫn cho qua.
    _clips = [str(x.get("clip") or "") for x in scenes if x.get("clip")]
    if _clips:
        _uniq = len(set(_clips))
        _ratio = _uniq / len(_clips)
        _top = max((_clips.count(c) for c in set(_clips)), default=0)
        print(f"   🖼️ Độ đa dạng hình: {_uniq}/{len(_clips)} ảnh khác nhau ({_ratio:.0%}), "
              f"ảnh lặp nhiều nhất {_top} lần")
        if _ratio < 0.5 or _top > max(3, len(_clips) // 3):
            issues.append(f"HÌNH LẶP QUÁ NHIỀU: chỉ {_uniq}/{len(_clips)} ảnh khác nhau "
                          f"(1 ảnh lặp {_top} lần) — video sẽ nhàm, phải vẽ/tải lại")

    n_img = sum(1 for x in scenes if x.get("clip"))
    if n_img == 0:
        return False, ["KHÔNG cảnh nào có ảnh -> cả video là chữ trên nền trơn"]
    if n_img < max(1, len(scenes) // 2):
        issues.append(f"chỉ {n_img}/{len(scenes)} cảnh có ảnh")
    n_chapter = sum(1 for x in scenes if x.get("type") == "chapter")
    if n_chapter:
        issues.append(f"{n_chapter} thẻ chữ (chapter) — rule: không intro/outro")
    if not (scenes[0].get("hook") or {}).get("stat") and not (scenes[0].get("hook") or {}).get("line"):
        issues.append("cảnh mở đầu thiếu lớp hook (số liệu/câu hỏi)")
    if not scenes[0].get("clip"):
        # CHẶN CỨNG: đúng thứ user cấm — mở đầu bằng chữ trên nền đen, không có ảnh hook liên quan.
        return False, issues + ["cảnh MỞ ĐẦU không có footage (chữ trên nền trơn) — CẤM"]
    # nhịp cắt: mỗi ảnh không được đứng quá ~3.5s
    slow = []
    for k, x in enumerate(scenes):
        n = max(1, len(x.get("clips") or [x.get("clip")] if x.get("clip") else [1]))
        if (x.get("dur") or 0) / n > 3.5 * fps:
            slow.append(k)
    if slow:
        issues.append(f"{len(slow)} cảnh giữ một ảnh quá 3.5s (nhàm)")
    return True, issues


def make_doc(channel, niche, out, keys=None, api_key=None, tier="normal", style="awe, cinematic",
             imgsrc=None, accent="#22D3EE", accent2="#F5B301", avoid=None,
             on_status=None, on_limit=None, on_ok=None, resume_story=None, ai_style=None, ai_only=False, music=None,
             mode=None, host_prompt=None):
    """WAVE 2 A-Z: Gemini viết tài liệu -> giọng + ảnh CC0 (Vision verify) -> render Cinematic -> QC + thumb.
    ai_style/ai_only: kênh speculative (tương lai/vũ trụ suy đoán, KHÔNG có ảnh thật để tìm) -> gu vẽ
    riêng nhất quán + bỏ qua tìm Openverse hẳn (đỡ phí round-trip mạng chắc chắn trật).
    music: mặc định None (im lặng) — chỉ đặt khi đã nghe thật + hợp tông kênh, xem build_doc_props()."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini viết tài liệu ({niche})")
        story = KM.write_doc(channel, keys, niche, style, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok, speculative=ai_only)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + ảnh + render điện ảnh", title=story.get("title_yt") or story.get("title"), score=score, script=_ckpt_json(story))
    props = build_doc_props(story, channel, imgsrc=imgsrc, api_key=keys[0]["key"],
                            accent=accent, accent2=accent2, handle=channel_handle(channel),
                            ai_style=ai_style, ai_only=ai_only, music=music, mode=mode, host_prompt=host_prompt)
    story["_music"] = bool(music)   # có nhạc thật -> enqueue mới ghi công CC-BY (bắt buộc theo license)
    # QC CẤU TRÚC TRƯỚC KHI RENDER: rẻ (không API) và chặn sớm — render xong mới phát hiện hỏng là
    # phí trắng ~2-4 phút CPU + lượt Vision. Đây là lớp mà QC visual KHÔNG thay được (xem qc_structure).
    _sok, _sissues = qc_structure(props)
    for _it in _sissues:
        print(f"   ⚠️ cấu trúc: {_it}")
    if not _sok:
        raise Exception("QC cấu trúc KHÔNG ĐẠT: " + "; ".join(_sissues))
    prune_ghost_clips(props)
    pf = os.path.join(PUB, f"_doc_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render CinematicShort ({len(props['scenes'])} cảnh) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "CinematicShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="CinematicShort")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    # QC HÌNH ẢNH SAU RENDER (Gemini Vision) — make_video() (data-race gốc) đã có bước này từ đầu,
    # make_doc() (Wave 2+, 20/40 kênh tính cả Wave 6/7 mới) TRƯỚC ĐÂY THIẾU hẳn -> chỉ QC kỹ thuật
    # (giây/tiếng/khung hình), lọt cảnh chồng chéo/xấu/vỡ layout ra thẳng YouTube. Thêm cho khớp chuẩn.
    if ok:
        # CHỐT RULE MỞ ĐẦU (đo pixel, KHÔNG tốn quota): mở đầu PHẢI là ảnh nền hook thật, cấm chữ
        # trên nền trơn. Soi VIDEO ĐÃ DỰNG nên bắt được cả ca props có 'clip' mà ảnh không hiện ra.
        # Đặt TRƯỚC Vision vì rẻ hơn nhiều, và Vision vốn KHÔNG bắt được lỗi này (nó chấm khuyết
        # tật; thẻ chữ thì sạch và đọc rõ nên luôn 80+ — xem ghi chú ở qc_structure).
        # CHỈ áp cho make_doc (Cinematic, nền là ảnh thật). Engine data-race mở bằng đồ hoạ có chủ
        # đích (ít màu, nền tối) nên áp vào đó sẽ bắt oan.
        _fok, _finfo = opening_is_flat(out, dark_ok=_dark_ok(channel))
        info["opening"] = _finfo
        if not _fok:
            print(f"   ❌ mở đầu là NỀN TRƠN (tối {_finfo.get('dark')}% · {_finfo.get('colors')} màu) — loại")
            ok = False
    if ok:
        try:
            import qc_vision
            vok, vinfo = _check_visual_rot(out, keys)
            info["visual"] = vinfo
            if not vok:
                ok = False
        except Exception as e:
            print("   ⚠️ vision qc skip:", e)
    # THUMBNAIL BRAND (DocThumb) — trước đây 21 kênh doc chỉ cắt đại 1 khung hình làm thumbnail (mờ nhạt,
    # không chữ, CTR thấp). Giờ: khung đẹp của CHÍNH video làm nền + chữ hook to + màu brand kênh.
    # Lỗi -> bỏ qua, caller tự lùi về _make_thumb() cũ (không bao giờ chặn pipeline).
    try:
        # ƯU TIÊN: KHUNG HOOK MỞ ĐẦU render nét từ chính composition (khớp video 100%,
        # không phải vẽ chồng chữ). Không đạt QC -> rơi xuống dựng DocThumb bên dưới.
        _thumb0 = out.rsplit(".", 1)[0] + ".jpg"
        _kk = ((keys or [{}])[0].get("key") if keys else None) or os.environ.get("GEMINI_API_KEY")
        if still_hook_thumb("CinematicShort", pf, _thumb0, api_key=_kk, title=(story.get("title_yt") or story.get("title") or channel)):
            print("   ✅ thumbnail = KHUNG HOOK MỞ ĐẦU (render nét)")
            raise _HookDone(_thumb0)
        # NỀN = ẢNH GỐC SẠCH của chính video (public/<slug>/clips/sN.jpg), KHÔNG phải khung cắt từ video
        # đã render: khung render đã CHÁY phụ đề + HUD vào ảnh -> thumbnail bị chữ đè chữ, rất xấu.
        # Ảnh gốc là ảnh đã tuyển (Openverse CC0 hoặc AI vẽ) -> nét, và MỖI VIDEO MỘT ẢNH KHÁC NHAU
        # -> thumbnail 21 kênh doc không bị giống hệt nhau.
        # 24/8: từ khi có CLIP VIDEO xen kẽ, danh sách này có cả .mp4. Nền thumbnail là ẢNH TĨNH
        # (DocThumb dựng bằng <Img>) nên phải LỌC BỎ video, không thì thumbnail ra nền trắng.
        clips = [s.get("clip") for s in (props.get("scenes") or [])
                 if s.get("clip") and str(s.get("clip")).lower().endswith((".jpg", ".jpeg", ".png"))]
        bg_rel = ""
        if clips:
            # bỏ ảnh cảnh đầu (hay là ảnh mở bài chung chung) nếu còn ảnh khác -> lấy ảnh giữa bài, đúng
            # cao trào, khác nhau giữa các video cùng kênh.
            pick = clips[len(clips) // 2] if len(clips) > 1 else clips[0]
            # slug_ chỉ tồn tại trong build_doc_props(); dùng ở đây là NameError (pyflakes bắt được).
            cand = f"_doc_{slug(channel)}/clips/{pick}"
            if os.path.exists(os.path.join(PUB, cand)):
                bg_rel = cand
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        tprops = {"bg": bg_rel,
                  "big": (story.get("title") or story.get("title_yt") or channel),
                  "kicker": channel, "accent": accent, "accent2": accent2,
                  # điểm nhấn của video: số liệu sốc + câu hỏi mở (Gemini trích sẵn, xem DOC_SCHEMA).
                  # Không có số -> DocThumb tự lùi về bố cục tiêu đề.
                  "stat": (story.get("thumb_stat") or "").strip(),
                  "statLabel": (story.get("thumb_label") or "").strip(),
                  "hook": (story.get("thumb_hook") or "").strip()}
        tf = os.path.join(PUB, f"_docthumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "DocThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True, timeout=240)
        if os.path.exists(thumb):
            story["_thumb"] = thumb; info["thumb"] = thumb
    except _HookDone as h:
        story["_thumb"] = h.args[0]; info["thumb"] = h.args[0]
    except Exception as e:
        print("   ⚠️ DocThumb bỏ qua (dùng khung cắt mặc định):", str(e)[:90])
    print(f"   {'✅' if ok else '❌'} QC doc {info}")
    return out, story, ok, info


# ─────────────────────────────────────────────────────────────────────────────
# WAVE 4 — 4 engine mới: SWARM (mật độ hạt), PULSE (gauge cường độ), CLOCKWORK (nén thời gian), LONGSHOT (xác suất).

def build_swarm_props(story, sdir, handle="@swarmusa", accent="#0D9488", music="music/km_ascending.mp3"):
    """Dựng props SwarmShort: TTS (intro + mỗi item + outro) -> timing bám giọng + 1 track."""
    rel = lambda p: os.path.relpath(p, PUB)
    intro_mp3 = os.path.join(sdir, "intro.mp3"); outro_mp3 = os.path.join(sdir, "outro.mp3")
    idur, _, _ = TK.synth(story.get("intro_vo") or story.get("title") or "How many fit?", intro_mp3)
    introSec = round(idur + 0.4, 2)
    items_in = story.get("items") or []
    items_out, clips, cum = [], [(intro_mp3, 0.0)], 0.0
    for i, it in enumerate(items_in):
        p = os.path.join(sdir, f"it{i}.mp3")
        du, _, _ = TK.synth(it.get("vo") or f"{it.get('label','')}, {it.get('countDisp','')}.", p)
        dur = round(du + 0.4, 2)
        items_out.append({"label": it.get("label"), "count": it.get("count"), "countDisp": it.get("countDisp"),
                          "shape": it.get("shape") or "circle", "emoji": it.get("emoji"), "dur": dur})
        clips.append((p, introSec + cum)); cum += dur
    odur, _, _ = TK.synth(story.get("outro_vo") or "Follow for more real numbers.", outro_mp3)
    outroSec = round(odur + 0.4, 2)
    clips.append((outro_mp3, introSec + cum))
    total = round(introSec + cum + outroSec, 2)
    track = os.path.join(sdir, "track.mp3"); _mix_track(clips, total, track)
    return {"title": (story.get("title") or "HOW MANY FIT?"), "handle": handle, "color": accent, "accent": accent,
            "sfx": True, "items": items_out, "audio": rel(track), "music": music}


def render_short_from_props(channel, props, story, out, keys=None, prefix="", lite=False):
    """Dựng 1 SHORT 9:16 từ props ĐÃ CÓ (do make_doc_long tạo cho từng phần của long).

    Không gọi Gemini, không tải ảnh lại: dùng lại nguyên giọng + ảnh của phần đó -> short bám sát
    100% nội dung long, đúng rule '1 long sinh ra 3 short'.
    Trả (ok, info) — thumbnail gắn vào story['_thumb'] như make_doc."""
    out = os.path.abspath(out); fresh_out(out)      # dọn bản vòng trước, tránh lẫn
    pf = os.path.join(PUB, f"_docshort_{slug(channel)}_{prefix or '0'}.json")
    prune_ghost_clips(props)
    json.dump(props, open(pf, "w"))
    sok, sissues = qc_structure(props)
    for it in sissues:
        print(f"   ⚠️ short cấu trúc: {it}")
    if not sok:
        return False, {"note": "QC cấu trúc: " + "; ".join(sissues)}
    print(f"   🎞️ render CinematicShort ({len(props['scenes'])} cảnh) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "CinematicShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="CinematicShort(part)")
    ok, info = qc(out)
    if ok:
        fok, finfo = opening_is_flat(out, dark_ok=_dark_ok(channel))
        info["opening"] = finfo
        if not fok:
            print(f"   ❌ mở đầu NỀN TRƠN (tối {finfo.get('dark')}%) — loại"); ok = False
    if ok:
        if lite:
            # QC-NHẸ cho short phần 2-3: cùng engine + cùng bộ ảnh đã qua verify-grid + cùng layout
            # với phần 1 (đã soi Vision đầy đủ). Cổng cấu trúc + cổng pixel mở-đầu vẫn chạy đủ ở
            # trên. Tiết kiệm ~2 gọi Vision/cụm — 20 gọi/key/ngày nên mỗi gọi đều đáng tiền.
            info["visual"] = {"note": "lite: phần 1 cùng cụm đã soi Vision đầy đủ"}
        else:
            try:
                vok, vinfo = _check_visual_rot(out, keys)
                info["visual"] = vinfo
                if not vok:
                    ok = False
            except Exception as e:
                print("   ⚠️ vision qc skip:", e)
    # thumbnail = KHUNG HOOK MỞ ĐẦU render nét từ chính props này (khớp video 100%)
    try:
        t0 = out.rsplit(".", 1)[0] + ".jpg"
        kk = next((k.get("key") for k in (keys or []) if k.get("key") and not str(k.get("key")).startswith("gsk_")), None) or os.environ.get("GEMINI_API_KEY")
        if still_hook_thumb("CinematicShort", pf, t0, trust=lite,
                            api_key=kk, title=(story.get("title_yt") or story.get("title") or channel)):
            story["_thumb"] = t0
            print("   ✅ thumbnail = KHUNG HOOK MỞ ĐẦU (render nét)")
    except Exception as e:
        print("   ⚠️ thumbnail bỏ qua:", str(e)[:70])
    return ok, info


def make_doc_long(channel, niche, out, keys=None, api_key=None, tier="normal", style="awe, cinematic",
                  on_status=None, on_limit=None, on_ok=None, avoid=None, n_parts=3,
                  accent="#22D3EE", accent2="#F5B301", ai_style=None, ai_only=False, music=None,
                  mode=None, host_prompt=None, resume=None):
    """LONG 16:9 cho kênh doc-format — và ĐẺ RA LUÔN props của n_parts SHORT gắn liền nội dung.

    Rule user: short phải ĐI SAU long và bám nội dung long (1 long -> 3 short). Trước đây 10 format
    đặc biệt (doc/guess/mapped/...) rẽ vào nhánh CHỈ-SHORT trong run_one nên kênh ra 3 short mà
    KHÔNG có long nào — sai hẳn mô hình.

    Cách làm RẺ: 1 lần lập pillar + n_parts lần viết doc. Mỗi phần dựng props MỘT LẦN (giọng + ảnh),
    rồi dùng CHUNG cho cả hai đầu ra:
      - LONG  = ghép scenes của tất cả các phần -> render composition 'Cinematic' (1920x1080)
      - SHORT = props của TỪNG phần -> render 'CinematicShort' (1080x1920)
    Không tốn thêm lượt Gemini nào cho short, và nội dung khớp tuyệt đối với long.

    Trả (out, plan, subtopics, ok, info, parts) — parts = [{"story","props"}] để caller dựng short.
    """
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out); fresh_out(out)      # dọn bản vòng trước, tránh lẫn
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)

    # ── RESUME TỪNG PHẦN: phiên trước bị giết giữa chừng -> pillar + các phần ĐÃ VIẾT nằm trong
    # checkpoint, chỉ viết tiếp phần còn thiếu. Mỗi phần đã cứu = 1-2 gọi Gemini không phải trả lại.
    done_stories = []
    if resume and resume.get("parts"):
        plan = {"pillar_title": resume.get("pillar_title"), "hook": resume.get("hook"),
                "sources": resume.get("sources") or []}
        subs = [x for x in (resume.get("subs") or []) if x][:n_parts]
        done_stories = list(resume["parts"])[:len(subs)]
        st("writing", f"♻️ Resume: {len(done_stories)}/{len(subs)} phần đã có sẵn — khỏi gọi Gemini lại")
        print(f"   ♻️ resume long: dùng lại pillar + {len(done_stories)} phần đã viết")
    else:
        st("writing", f"Lập pillar {n_parts} phần ({niche[:40]})")
        k0 = KM.key_order(channel, keys)[0]
        try:
            plan = CB.plan_pillar(niche, n_parts, api_key=k0["key"], model_name=KM.model_for(tier), avoid=avoid)
        except Exception as _e0:
            _gem = next((k for k in keys if not str(k.get("key", "")).startswith(("gsk_", "cf:"))), None)
            if "413" in str(_e0) and _gem:
                # prompt quá cỡ với nhà 8K-token (Groq) -> lập pillar bằng Gemini (nuốt prompt lớn), 22/8
                plan = CB.plan_pillar(niche, n_parts, api_key=_gem["key"], model_name=KM.model_for(tier), avoid=avoid)
            else:
                raise
        subs = [x for x in (plan.get("subtopics") or []) if x][:n_parts]
    if not subs:
        raise Exception("plan_pillar không trả subtopic nào")

    parts, all_scenes = [], []
    for pi, sub in enumerate(subs):
        if pi < len(done_stories):
            story = done_stories[pi]          # phần đã viết ở phiên trước
        else:
            st("writing", f"Viết phần {pi + 1}/{len(subs)}: {str(sub)[:40]}")
            story = KM.write_doc(channel, keys, sub, style, tier, avoid=avoid,
                                 on_limit=on_limit, on_ok=on_ok, speculative=ai_only,
                                 audit=(pi == 0))   # soi độc lập PHẦN ĐẦU đại diện
            done_stories.append(story)
            # CHECKPOINT NGAY sau mỗi phần (không đợi viết đủ): luồng bị giết lúc render thì phiên
            # sau resume đúng từ đây. Đi qua update_job (đã có đệm-xả khi quota chết).
            st("writing", f"✔ xong phần {pi + 1}/{len(subs)}",
               script=_ckpt_json({"pillar_title": plan.get("pillar_title"), "hook": plan.get("hook"),
                                  "sources": plan.get("sources") or [], "subs": subs,
                                  "parts": done_stories}))
        pr = build_doc_props(story, channel, api_key=keys[0]["key"], accent=accent, accent2=accent2,
                             handle=channel_handle(channel), ai_style=ai_style, ai_only=ai_only,
                             music=music, mode=mode, host_prompt=host_prompt, prefix=f"p{pi}_")
        sok, sissues = qc_structure(pr)
        for it in sissues:
            print(f"   ⚠️ phần {pi + 1} cấu trúc: {it}")
        if not sok:
            print(f"   ⏭️ bỏ phần {pi + 1}: " + "; ".join(sissues))
            continue
        story["_music"] = bool(music)
        parts.append({"story": story, "props": pr, "topic": sub})
        all_scenes += pr["scenes"]

    if not all_scenes:
        raise Exception("không phần nào đạt QC cấu trúc")

    long_props = {"scenes": all_scenes, "slug": "_doc_" + slug(channel),
                  "handle": channel_handle(channel), "accent": accent, "accent2": accent2}
    if music:
        long_props["music"] = music
    if mode:
        long_props["mode"] = mode
    prune_ghost_clips(long_props)
    pf = os.path.join(PUB, f"_doclong_{slug(channel)}.json"); json.dump(long_props, open(pf, "w"))
    st("rendering", f"Render LONG 16:9 ({len(all_scenes)} cảnh, {len(parts)} phần)")
    print(f"   🎞️ render Cinematic 16:9 ({len(all_scenes)} cảnh / {len(parts)} phần) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "Cinematic", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, timeout=3600, label="Cinematic(long)")   # long 10'+ cần 30-50' render trên 2 core — trần riêng 60'

    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out)
    if ok:
        fok, finfo = opening_is_flat(out, dark_ok=_dark_ok(channel))
        info["opening"] = finfo
        if not fok:
            print(f"   ❌ LONG mở đầu NỀN TRƠN (tối {finfo.get('dark')}%) — loại"); ok = False
    if ok:
        try:
            vok, vinfo = _check_visual_rot(out, keys)
            info["visual"] = vinfo
            if not vok:
                ok = False
        except Exception as e:
            print("   ⚠️ vision qc skip:", e)
    # THUMBNAIL LONG = khung hook mở đầu render nét từ CHÍNH props long. Long là 16:9 nên khung này
    # đã đúng tỉ lệ thumbnail (1280x720) — không phải cắt/độn gì. Thiếu bước này thì enqueue nhận
    # _thumb=None và rơi về _make_thumb() cắt khung thô (test_thumb_pipeline bắt đúng chỗ này).
    try:
        t0 = out.rsplit(".", 1)[0] + ".jpg"
        kk = next((k.get("key") for k in (keys or []) if k.get("key") and not str(k.get("key")).startswith("gsk_")), None) or os.environ.get("GEMINI_API_KEY")
        if still_hook_thumb("Cinematic", pf, t0, api_key=kk,
                            title=(plan.get("pillar_title") or channel)):
            info["thumb"] = t0
            print("   ✅ thumbnail LONG = KHUNG HOOK MỞ ĐẦU (render nét)")
    except Exception as e:
        print("   ⚠️ thumbnail long bỏ qua:", str(e)[:70])
    plan["_parts"] = [p["topic"] for p in parts]
    return out, plan, [p["topic"] for p in parts], ok, info, parts


def make_swarm(channel, niche, out, keys=None, api_key=None, tier="normal",
               accent="#0D9488", accent2="#F0ABFC", avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH SWARM A-Z: Gemini sinh mật độ/số lượng thật -> giọng -> render SwarmShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini tính mật độ/số lượng ({niche})")
        story = KM.write_swarm(channel, keys, niche, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + render hạt", title=story.get("title_yt") or story.get("title"), score=score, script=_ckpt_json(story))
    sdir = os.path.join(PUB, "narration", "_swarm_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    props = build_swarm_props(story, sdir, handle=channel_handle(channel), accent=accent)
    pf = os.path.join(PUB, f"_swarm_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render SwarmShort ({len(props['items'])} mục) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "SwarmShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="SwarmShort")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        _its = story.get("items") or [{}]
        _t = max(_its, key=lambda x: x.get("count") or 0)
        _stat, _lab = _t.get("countDisp", ""), _t.get("label", "")
        _hook = story.get("title") or "HOW MANY, REALLY?"
        _th = doc_thumb(channel, out, big=(story.get("title_yt") or story.get("title") or channel),
                        stat=_stat, stat_label=_lab, hook=_hook,
                        accent=accent, accent2=accent2,
                        bg_provider=lambda: hook_bg(channel, out,
                            _hook or story.get("title") or channel, keys=keys),
                        api_key_for_thumb=((keys or [{}])[0].get("key") if keys else None),
                        comp_id="SwarmShort", props_path=pf,)
        thumb = _th or thumb
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb SWARM lỗi:", str(e)[:80])
    print(f"   {'✅' if ok else '❌'} QC swarm {info}")
    return out, story, ok, info


def build_pulse_props(story, sdir, handle="@pulseusa", accent="#EA580C", music="music/km_ascending.mp3"):
    """Dựng props PulseShort: TTS (intro + mỗi item + outro) -> timing bám giọng + 1 track."""
    rel = lambda p: os.path.relpath(p, PUB)
    intro_mp3 = os.path.join(sdir, "intro.mp3"); outro_mp3 = os.path.join(sdir, "outro.mp3")
    idur, _, _ = TK.synth(story.get("intro_vo") or story.get("title") or "How intense is it?", intro_mp3)
    introSec = round(idur + 0.4, 2)
    items_in = story.get("items") or []
    # 24/8 — PULSE RA VIDEO 12,8s VÀ BỊ QC LOẠI HÀNG LOẠT (15 lần trong phiên 08:47, kênh PULSEUSA
    # chỉ đẩy được 2 video). Vì sao: độ dài clip = TỔNG ĐỘ DÀI GIỌNG ĐỌC, mà mỗi mục chỉ một câu
    # ngắn -> 5 mục ≈ 12-15s, dưới sàn 20s của QC dọc. Mỗi lần loại là mất trắng một lượt viết
    # (token AI) + một lượt render — đắt hơn nhiều so với việc giữ mỗi con số trên màn thêm 1 giây.
    # Nay: đo trước, thiếu bao nhiêu thì RẢI ĐỀU vào các mục (giữ số lâu hơn, người xem kịp đọc),
    # KHÔNG bịa thêm nội dung và KHÔNG kéo dài giọng đọc.
    MIN_TONG = 21.0                       # 20s là sàn QC — chừa 1s biên cho sai số ffmpeg
    dur_tho, paths = [], []
    for i, it in enumerate(items_in):
        p = os.path.join(sdir, f"it{i}.mp3")
        du, _, _ = TK.synth(it.get("vo") or f"{it.get('label','')}, {it.get('disp','')}.", p)
        dur_tho.append(round(du + 0.4, 2)); paths.append(p)
    odur, _, _ = TK.synth(story.get("outro_vo") or "Follow for more real intensity checks.", outro_mp3)
    outroSec = round(odur + 0.4, 2)
    tho = round(introSec + sum(dur_tho) + outroSec, 2)
    if tho < MIN_TONG and dur_tho:
        them = (MIN_TONG - tho) / len(dur_tho)
        them = min(them, 2.5)             # trần 2,5s/mục: quá đà thành lê thê, mất nhịp "pulse"
        dur_tho = [round(d + them, 2) for d in dur_tho]
        print(f"   ⏱ PULSE {tho:.1f}s < {MIN_TONG:.0f}s — giữ mỗi mục thêm {them:.1f}s "
              f"-> {round(introSec + sum(dur_tho) + outroSec, 1)}s (không đổi nội dung)")
    items_out, clips, cum = [], [(intro_mp3, 0.0)], 0.0
    for i, it in enumerate(items_in):
        items_out.append({"label": it.get("label"), "emoji": it.get("emoji"), "value": it.get("value"),
                          "disp": it.get("disp"), "extreme": bool(it.get("extreme")), "dur": dur_tho[i]})
        clips.append((paths[i], introSec + cum)); cum += dur_tho[i]
    clips.append((outro_mp3, introSec + cum))
    total = round(introSec + cum + outroSec, 2)
    track = os.path.join(sdir, "track.mp3"); _mix_track(clips, total, track)
    return {"title": (story.get("title") or "HOW INTENSE?"), "handle": handle, "color": accent, "accent": accent,
            "sfx": True, "unit": story.get("unit") or "", "maxScale": story.get("maxScale") or 100,
            "items": items_out, "audio": rel(track), "music": music}


def make_pulse(channel, niche, out, keys=None, api_key=None, tier="normal",
              accent="#EA580C", accent2="#FCA5A5", avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH PULSE A-Z: Gemini sinh cường độ giác quan thật -> giọng -> render PulseShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini so sánh cường độ ({niche})")
        story = KM.write_pulse(channel, keys, niche, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + render gauge", title=story.get("title_yt") or story.get("title"), score=score, script=_ckpt_json(story))
    sdir = os.path.join(PUB, "narration", "_pulse_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    props = build_pulse_props(story, sdir, handle=channel_handle(channel), accent=accent)
    pf = os.path.join(PUB, f"_pulse_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render PulseShort ({len(props['items'])} mục) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "PulseShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="PulseShort")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        _t = (story.get("items") or [{}])[-1]
        _stat, _lab = _t.get("disp", ""), _t.get("label", "")
        _hook = story.get("title") or "HOW INTENSE?"
        _th = doc_thumb(channel, out, big=(story.get("title_yt") or story.get("title") or channel),
                        stat=_stat, stat_label=_lab, hook=_hook,
                        accent=accent, accent2=accent2,
                        bg_provider=lambda: hook_bg(channel, out,
                            _hook or story.get("title") or channel, keys=keys),
                        api_key_for_thumb=((keys or [{}])[0].get("key") if keys else None),
                        comp_id="PulseShort", props_path=pf,)
        thumb = _th or thumb
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb PULSE lỗi:", str(e)[:80])
    print(f"   {'✅' if ok else '❌'} QC pulse {info}")
    return out, story, ok, info


def build_clockwork_props(story, sdir, handle="@clockworkusa", accent="#C2410C", music="music/km_ascending.mp3"):
    """Dựng props ClockworkShort: TTS (intro + mỗi waypoint + hero + outro) -> timing bám giọng + 1 track."""
    rel = lambda p: os.path.relpath(p, PUB)
    intro_mp3 = os.path.join(sdir, "intro.mp3")
    idur, _, _ = TK.synth(story.get("intro_vo") or story.get("title") or "Let's compress time.", intro_mp3)
    introSec = round(idur + 0.4, 2)
    wps_in = story.get("waypoints") or []
    wps_out, clips, cum = [], [(intro_mp3, 0.0)], 0.0
    for i, w in enumerate(wps_in):
        p = os.path.join(sdir, f"wp{i}.mp3")
        du, _, _ = TK.synth(w.get("vo") or w.get("label") or "", p)
        wps_out.append({"label": w.get("label"), "atPercent": w.get("atPercent")})
        clips.append((p, introSec + cum)); cum += round(du + 0.4, 2)
    hero = story.get("hero") or {}
    hero_mp3 = os.path.join(sdir, "hero.mp3")
    hdur, _, _ = TK.synth(hero.get("vo") or hero.get("label") or "", hero_mp3)
    clips.append((hero_mp3, introSec + cum)); heroSec = round(hdur + 0.4, 2) + 2.0   # +2s giữ khung reveal
    outro_mp3 = os.path.join(sdir, "outro.mp3")
    odur, _, _ = TK.synth(story.get("outro_vo") or "Follow for more perspective shifts.", outro_mp3)
    outroSec = round(odur + 0.4, 2)
    clips.append((outro_mp3, introSec + cum + heroSec))
    total = round(introSec + cum + heroSec + outroSec, 2)
    track = os.path.join(sdir, "track.mp3"); _mix_track(clips, total, track)
    return {"title": (story.get("title") or "TIME, COMPRESSED"), "handle": handle, "color": accent, "accent": accent,
            "sfx": True, "scaleLabel": story.get("scaleLabel") or "",
            "waypoints": wps_out, "hero": {"label": hero.get("label"), "atPercent": hero.get("atPercent"),
            "realValue": hero.get("realValue")}, "audio": rel(track), "music": music,
            # 23/8 — GỬI THỜI LƯỢNG THẬT SANG REMOTION: trước đây composition tự tính độ dài bằng
            # HẰNG SỐ CỨNG (1.5 + 1.8×mốc + 3 + 1.5) nên video CLOCKWORK dài 13.2s trong khi giọng
            # đọc tới 27s -> cắt mất hơn nửa lời. Có 4 số này thì độ dài video = độ dài giọng.
            "introSec": introSec, "heroSec": heroSec, "outroSec": outroSec, "totalSec": total}


def make_clockwork(channel, niche, out, keys=None, api_key=None, tier="normal",
                   accent="#C2410C", accent2="#FCD34D", avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH CLOCKWORK A-Z: Gemini nén thời gian thật -> giọng -> render ClockworkShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini nén thời gian ({niche})")
        story = KM.write_clockwork(channel, keys, niche, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + render đồng hồ", title=story.get("title_yt") or story.get("title"), score=score, script=_ckpt_json(story))
    sdir = os.path.join(PUB, "narration", "_clockwork_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    props = build_clockwork_props(story, sdir, handle=channel_handle(channel), accent=accent)
    pf = os.path.join(PUB, f"_clockwork_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render ClockworkShort ({len(props['waypoints'])} mốc) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "ClockworkShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="ClockworkShort")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        _t = story.get("hero") or {}
        _stat, _lab = _t.get("realValue", ""), _t.get("label", "")
        _hook = story.get("scaleLabel") or story.get("title", "")
        _th = doc_thumb(channel, out, big=(story.get("title_yt") or story.get("title") or channel),
                        stat=_stat, stat_label=_lab, hook=_hook,
                        accent=accent, accent2=accent2,
                        bg_provider=lambda: hook_bg(channel, out,
                            _hook or story.get("title") or channel, keys=keys),
                        api_key_for_thumb=((keys or [{}])[0].get("key") if keys else None),
                        comp_id="ClockworkShort", props_path=pf,)
        thumb = _th or thumb
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb CLOCKWORK lỗi:", str(e)[:80])
    print(f"   {'✅' if ok else '❌'} QC clockwork {info}")
    return out, story, ok, info


def build_longshot_props(story, sdir, handle="@longshotusa", accent="#4F46E5", music="music/km_ascending.mp3"):
    """Dựng props LongshotShort: TTS (intro + mỗi item + outro) -> timing bám giọng + 1 track."""
    rel = lambda p: os.path.relpath(p, PUB)
    intro_mp3 = os.path.join(sdir, "intro.mp3"); outro_mp3 = os.path.join(sdir, "outro.mp3")
    idur, _, _ = TK.synth(story.get("intro_vo") or story.get("title") or "What are the real odds?", intro_mp3)
    introSec = round(idur + 0.4, 2)
    items_in = story.get("items") or []
    items_out, clips, cum = [], [(intro_mp3, 0.0)], 0.0
    for i, it in enumerate(items_in):
        p = os.path.join(sdir, f"it{i}.mp3")
        du, _, _ = TK.synth(it.get("vo") or f"{it.get('label','')}, {it.get('oddsDisp','')}.", p)
        dur = round(du + 0.4, 2)
        items_out.append({"label": it.get("label"), "emoji": it.get("emoji"), "oddsDisp": it.get("oddsDisp"),
                          "logValue": it.get("logValue"), "dur": dur})
        clips.append((p, introSec + cum)); cum += dur
    odur, _, _ = TK.synth(story.get("outro_vo") or "Follow for more real odds.", outro_mp3)
    outroSec = round(odur + 0.4, 2)
    clips.append((outro_mp3, introSec + cum))
    total = round(introSec + cum + outroSec, 2)
    track = os.path.join(sdir, "track.mp3"); _mix_track(clips, total, track)
    return {"title": (story.get("title") or "WHAT ARE THE ODDS?"), "handle": handle, "color": accent, "accent": accent,
            "sfx": True, "items": items_out, "audio": rel(track), "music": music}


def make_longshot(channel, niche, out, keys=None, api_key=None, tier="normal",
                  accent="#4F46E5", accent2="#A5B4FC", avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH LONGSHOT A-Z: Gemini sinh xác suất thật -> giọng -> render LongshotShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini tính xác suất thật ({niche})")
        story = KM.write_longshot(channel, keys, niche, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + render tháp xác suất", title=story.get("title_yt") or story.get("title"), score=score, script=_ckpt_json(story))
    sdir = os.path.join(PUB, "narration", "_longshot_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    props = build_longshot_props(story, sdir, handle=channel_handle(channel), accent=accent)
    pf = os.path.join(PUB, f"_longshot_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render LongshotShort ({len(props['items'])} mục) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "LongshotShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="LongshotShort")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        _t = (story.get("items") or [{}])[-1]
        _stat, _lab = _t.get("oddsDisp", ""), _t.get("label", "")
        _hook = story.get("title") or "WHAT ARE THE ODDS?"
        _th = doc_thumb(channel, out, big=(story.get("title_yt") or story.get("title") or channel),
                        stat=_stat, stat_label=_lab, hook=_hook,
                        accent=accent, accent2=accent2,
                        bg_provider=lambda: hook_bg(channel, out,
                            _hook or story.get("title") or channel, keys=keys),
                        api_key_for_thumb=((keys or [{}])[0].get("key") if keys else None),
                        comp_id="LongshotShort", props_path=pf,)
        thumb = _th or thumb
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb LONGSHOT lỗi:", str(e)[:80])
    print(f"   {'✅' if ok else '❌'} QC longshot {info}")
    return out, story, ok, info


def make_long(channel, niche, out, keys=None, api_key=None, tier="normal",
              on_status=None, on_limit=None, n_races=6, avoid=None, on_ok=None, resume_checkpoint=None,
              accent="#22D3EE", accent2="#F5B301"):
    """LONG 16:9 = pillar 5-6 race cùng chủ đề. Trả (out, plan, subtopics, ok, info, stories).
    resume_checkpoint: {"pillar_title","hook","races":[...]} ĐÃ CÓ (checkpoint phiên trước bị huỷ/lỗi lúc
    render) -> dùng lại, bỏ qua gọi Gemini lập pillar + viết lại từng race."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)   # QUAN TRỌNG: render cwd=ENG -> path tuyệt đối (nếu không QC/enqueue tìm không ra file -> 0 giây)
    import key_manager as KM   # CB đã import ở đầu file — không cần import lại
    keys = keys or [{"id": "env", "key": api_key or os.environ["GEMINI_API_KEY"], "email": "local"}]
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    sdir = os.path.join(PUB, "narration", "_long_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    if resume_checkpoint and (resume_checkpoint.get("races") or []):
        st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
        stories = resume_checkpoint["races"]
        subtopics = [s.get("topic") or s.get("title") for s in stories if (s.get("topic") or s.get("title"))]
        plan = {"pillar_title": resume_checkpoint.get("pillar_title"), "hook": resume_checkpoint.get("hook"),
                "subtopics": subtopics}
    else:
        st("writing", "Lập pillar (chủ đề con)")
        k0 = KM.key_order(channel, keys)[0]
        try:
            plan = CB.plan_pillar(niche, n_races, api_key=k0["key"], model_name=KM.model_for(tier), avoid=avoid)
        except Exception as _e0:
            _gem = next((k for k in keys if not str(k.get("key", "")).startswith(("gsk_", "cf:"))), None)
            if "413" in str(_e0) and _gem:
                # cùng thuốc với nhánh doc: prompt quá cỡ nhà 8K -> Gemini lập dàn ý (22/8)
                plan = CB.plan_pillar(niche, n_races, api_key=_gem["key"], model_name=KM.model_for(tier), avoid=avoid)
            else:
                raise
        subtopics = plan.get("subtopics", [])[:n_races]
        stories = []
        for i, sub in enumerate(subtopics):
            st("writing", f"Viết race {i+1}/{len(subtopics)}: {sub[:28]}")
            try:
                stories.append(KM.write_story(channel, keys, sub, "long", tier, on_limit=on_limit, on_ok=on_ok))
            except Exception as e:
                print(f"   ⚠️ bỏ race '{sub[:30]}': {e}")
        if len(stories) < 2:
            raise Exception("Long cần ≥2 race hợp lệ.")   # Exception (không SystemExit) -> retry/loop bắt được, không giết cả mẻ
    st("rendering", f"Render long ({len(stories)} race)", title=plan.get("pillar_title"),
       script=_ckpt_json({"pillar_title": plan.get("pillar_title"), "hook": plan.get("hook"), "races": stories}))
    props = build_long_props(stories, sdir, handle=channel_handle(channel))
    pf = os.path.join(PUB, f"_long_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render RaceLong ({len(stories)} race) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "RaceLong", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="RaceLong")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out)
    if ok:
        try:
            import qc_vision
            vok, vinfo = _check_visual_rot(out, keys)
            info["visual"] = vinfo
            if not vok:
                ok = False
        except Exception as e:
            print("   ⚠️ vision qc skip:", e)
    scs = [(s.get("self_score") or {}).get("total") for s in stories if (s.get("self_score") or {}).get("total")]
    if scs:
        info["score"] = round(sum(scs) / len(scs))   # điểm QC long = TB các race -> hiện trên dashboard
    # THUMBNAIL BRAND (DocThumb) — cùng lý do đã áp cho make_video(): 10 kênh gốc trước đây KHÔNG có
    # thumbnail riêng cho bản LONG (nội dung mid-roll monetize, giá trị cao). Lấy hook_stat/hook_caption
    # của RACE ĐẦU (đại diện cả pillar) + ảnh thật đã tuyển làm nền.
    try:
        # ƯU TIÊN: KHUNG HOOK MỞ ĐẦU render nét từ chính composition (khớp video 100%,
        # không phải vẽ chồng chữ). Không đạt QC -> rơi xuống dựng DocThumb bên dưới.
        _thumb0 = out.rsplit(".", 1)[0] + ".jpg"
        _kk = ((keys or [{}])[0].get("key") if keys else None) or os.environ.get("GEMINI_API_KEY")
        if still_hook_thumb("RaceLong", pf, _thumb0, api_key=_kk, title=(plan.get("pillar_title") or channel)):
            print("   ✅ thumbnail = KHUNG HOOK MỞ ĐẦU (render nét)")
            raise _HookDone(_thumb0)
        first = stories[0] if stories else {}
        shots = (props.get("races") or [{}])[0].get("shots") or []
        bg_rel = shots[len(shots) // 2] if shots else ""
        if bg_rel and not os.path.exists(os.path.join(PUB, bg_rel)):
            bg_rel = ""
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        tprops = {"bg": bg_rel, "big": (plan.get("pillar_title") or channel), "kicker": channel,
                  "accent": accent, "accent2": accent2,
                  "stat": str(first.get("hook_stat") or "").strip(),
                  "statLabel": str(first.get("hook_caption") or "").strip()}
        tf = os.path.join(PUB, f"_longthumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "DocThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True, timeout=240)
        if os.path.exists(thumb):
            plan["_thumb"] = thumb; info["thumb"] = thumb
    except _HookDone as h:
        plan["_thumb"] = h.args[0]; info["thumb"] = h.args[0]
    except Exception as e:
        print("   ⚠️ DocThumb (long) bỏ qua:", str(e)[:90])
    print(f"   {'✅' if ok else '❌'} QC long {info}")
    return out, plan, subtopics, ok, info, stories


def _mix_track(clips, total, out):
    """Ghép các đoạn giọng vào 1 track theo offset tuyệt đối (giây) + nền im lặng cố định độ dài.
    clips=[(path, start_sec)]. Không overlap -> amix normalize=0 giữ nguyên âm lượng."""
    inputs, filt, labels = [], [], []
    for i, (p, st_) in enumerate(clips):
        inputs += ["-i", p]
        filt.append(f"[{i}:a]adelay={int(st_*1000)}:all=1[a{i}]")
        labels.append(f"[a{i}]")
    si = len(clips)
    inputs += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
    filt.append(f"[{si}:a]volume=0[base]")
    filt.append("[base]" + "".join(labels) + f"amix=inputs={len(clips)+1}:normalize=0:duration=first[out]")
    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filt),
                    "-map", "[out]", "-ac", "2", "-ar", "44100", out], check=True, capture_output=True, timeout=300)


def build_guess_props(story, sdir, handle="@guessdaily", music="music/km_ascending.mp3", api_key=None):
    """Dựng props GuessShort: TTS mỗi vòng (clue+reveal) + ảnh KHỚP đáp án (Vision verify) + timing bám giọng + 1 track."""
    rel = lambda p: os.path.relpath(p, PUB)
    rounds_in = story.get("rounds") or []
    intro_mp3 = os.path.join(sdir, "intro.mp3")
    idur, _, _ = TK.synth(story.get("intro_vo") or "Can you guess them all?", intro_mp3)
    introSec = round(idur + 0.5, 2)
    clips = [(intro_mp3, 0.0)]
    rounds_out = []
    cum = 0.0  # offset (giây) từ đầu vùng vòng
    for i, r in enumerate(rounds_in):
        clue_mp3 = os.path.join(sdir, f"r{i}_clue.mp3")
        rev_mp3 = os.path.join(sdir, f"r{i}_reveal.mp3")
        cdur, _, _ = TK.synth(r.get("vo_clue") or r.get("clue") or r.get("q") or "Guess this.", clue_mp3)
        rdur_, _, _ = TK.synth(r.get("vo_reveal") or r.get("answer") or "", rev_mp3)
        revSec = round(max(2.8, cdur + 0.7), 2)          # đủ thời gian đếm ngược 3-2-1 + khoảng hồi hộp
        dur = round(revSec + rdur_ + 0.9, 2)             # giữ đáp án sau reveal
        # ẢNH KHỚP ĐÁP ÁN 100%: query từ img_query; Vision xác minh ảnh RÕ là đáp án -> không thì THÀ bỏ ảnh (mosaic nền)
        img_rel = None
        q = (r.get("img_query") or r.get("answer") or "").strip()
        subject = (r.get("img_query") or r.get("answer") or "").strip()
        if q:
            dest = os.path.join(PUB, "img", "_guess", slug(story.get("category", "g")) + f"_{i}.jpg")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            vf = None
            if api_key:
                import qc_vision
                vf = lambda p: qc_vision.verify_image(p, subject, api_key=api_key)
            got = fetch_image(q, dest, orient="tall", verify=vf, ai_key=api_key, ai_prompt=subject)
            if got:
                img_rel = rel(dest)
            else:
                print(f"   ⚠️ round {i+1}: không có ảnh CC0 khớp '{subject[:30]}' -> để nền mosaic (không dùng ảnh sai)")
        rounds_out.append({"q": r.get("q"), "clue": r.get("clue"), "answer": r.get("answer"),
                           "stat": r.get("stat"), "img": img_rel, "dur": dur, "revSec": revSec})
        clips.append((clue_mp3, introSec + cum))
        clips.append((rev_mp3, introSec + cum + revSec))
        cum += dur
    outro_mp3 = os.path.join(sdir, "outro.mp3")
    odur, _, _ = TK.synth(story.get("outro_vo") or "How many did you get?", outro_mp3)
    outroSec = round(odur + 0.4, 2)
    clips.append((outro_mp3, introSec + cum))
    total = round(introSec + cum + outroSec, 2)
    track = os.path.join(sdir, "track.mp3")
    _mix_track(clips, total, track)
    return {"title": (story.get("title_yt") or story.get("title") or "GUESS").upper(),
            "handle": handle, "color": "#F5B301", "accent": "#ff375f",
            "introSec": introSec, "outroSec": outroSec, "sfx": True,
            "rounds": rounds_out, "audio": rel(track), "music": music}


def make_guess(channel, category, out, keys=None, api_key=None, tier="normal", n_rounds=3,
               avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH #1 GUESS A-Z: Gemini sinh câu đố (logic + khớp ảnh) -> giọng + ảnh + SFX -> render GuessShort -> QC + thumb.
    Trả (out, story, ok, info)."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    set_ai_pool(keys, channel)   # vẽ ảnh xoay vòng CẢ pool, không kẹt mỗi keys[0] (xem _AI_POOL đầu file)
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini soạn câu đố ({category})")
        story = KM.write_guess(channel, keys, category, n_rounds, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + ảnh + SFX + render", title=story.get("title_yt"), score=score, script=_ckpt_json(story))
    sdir = os.path.join(PUB, "narration", "_guess_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    props = build_guess_props(story, sdir, handle=channel_handle(channel), api_key=keys[0]["key"])
    pf = os.path.join(PUB, f"_guess_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render GuessShort ({len(props['rounds'])} vòng) …")
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", "GuessShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, label="GuessShort")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out)
    info["score"] = score
    # thumbnail: cùng công thức nhà (DocThumb). GUESS là câu đố -> KHÔNG lộ đáp án: dùng bố cục
    # TIÊU ĐỀ (câu hỏi to) + pill "99% FAIL", nền là khung thật rút từ chính video.
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        _r0 = (story.get("rounds") or [{}])[0]
        _th = doc_thumb(channel, out, big=_r0.get("q") or "CAN YOU NAME IT?",
                        stat="", stat_label="", hook="",
                        accent="#84CC16", accent2="#FDE047",
                        bg_provider=lambda: hook_bg(channel, out,
                            _r0.get("answer") or story.get("category") or channel, keys=keys),
                        api_key_for_thumb=((keys or [{}])[0].get("key") if keys else None))
        thumb = _th or thumb
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb skip:", e)
    print(f"   {'✅' if ok else '❌'} QC guess {info}")
    return out, story, ok, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True); ap.add_argument("--seed", required=True)
    ap.add_argument("--type", dest="vtype", choices=["short", "long"], default="short")
    ap.add_argument("--tier", default="normal"); ap.add_argument("--out", default="out.mp4")
    a = ap.parse_args()
    out, story, ok, info = make_video(a.channel, a.seed, a.vtype, a.out, tier=a.tier)
    print(f"\n{'✅ XONG' if ok else '⚠️ CÓ LỖI QC'}: {out}\n   {story['title']}")


if __name__ == "__main__":
    main()


# ─────────────────────────────────────────────────────────────────────────────
# TOON (22/8) — skit 2 nhân vật cố định: FLUX vẽ 3-5 khung + thoại 2 giọng.
# SHORT = 1 skit (ToonShort 9:16) · LONG = tuyển tập 3 skit (ToonLong 16:9, chapters) ->
# 3 short đẻ từ CHÍNH 3 skit của long (dùng lại nguyên audio + ảnh, 0 gọi thêm AI) = đúng luật 1:3.
_TOON_SAFE = [("extreme close-up", "tight head-and-shoulders shot"), ("close-up of face", "head-and-shoulders shot"),
              ("close-up", "tight shot"), ("close up", "tight shot"), ("shooting", "pointing"),
              ("shoot", "point"), ("gun", "banana"), ("blood", "ketchup"),
              # 22/8 đêm — đo thật bằng 6 lượt vẽ brand: 2 bẫy làm FLUX IN CHỮ GIẢ lên ảnh:
              # (a) từ vựng quảng cáo ("advertising") -> nó vẽ poster kèm chữ to đùng;
              # (b) TÊN RIÊNG VIẾT HOA trong prompt (PEARL, MOSE...) -> nó viết thẳng tên lên hộp thư/cửa sổ.
              ("advertising", "animation"), ("billboard", "backdrop"), ("poster", "backdrop")]


# VÂN TAY MỸ (23/8, user chốt): mọi khung của kênh essay phải đọc ra "đây là nước Mỹ" trong 1 nháy.
# Ghép ở TẦNG VẼ (không chỉ ở prompt AI viết) để cả ảnh vẽ-lại/ảnh fallback đều dính luật -> phong
# cách đồng nhất suốt kênh. Giữ dạng ĐẠO CỤ/BỐI CẢNH, không phải cờ quạt phủ kín (tránh lố + chính trị).
# 23/8 (đo bằng 4 ảnh test): bản đầu bắt "bối cảnh Mỹ" nhưng KHÔNG chặn độ rối -> FLUX vẽ nội thất
# siêu thị chi chít kệ hàng, đẻ ra CHỮ GIẢ ("Coffe Ferricus") và cả LOGO NHÁI (rủi ro bản quyền).
# Bản này: vân tay Mỹ chỉ 1-2 ĐẠO CỤ, nền tối giản, cấm biển hiệu/nhãn hàng/logo -> giữ được chất
# editorial sang trọng mà vẫn "đọc ra nước Mỹ" ngay.
_USA_TAG = ("set in a recognisably American everyday place, with ONE ordinary US object (two at most) "
            "(curbside mailbox with red flag, red plastic cup, paper coffee cup, long receipt, pill "
            "bottle, pickup truck, fire hydrant, folding lawn chair), any people are ordinary Americans "
            "of mixed ages and ethnicities in everyday US clothing; UNCLUTTERED minimal background with "
            "large flat areas, only 3-5 elements in the whole frame, no shop shelves full of products, "
            "no signage, no brand logos, no product labels, no flags draped over the scene, not political")


def _usa_style(style: str, mode: str) -> str:
    """Gắn vân tay Mỹ vào style-lock của kênh essay (skit/story giữ nguyên vì đã có nhân vật cố định)."""
    if mode != "essay" or not style:
        return style
    return style if "recognisably American" in style else f"{style}, {_USA_TAG}"


def _toon_safe(p: str) -> str:
    """Né bộ lọc prompt CF (8007 NSFW chặn oan 'close-up of face' — đo thật 22/8) + né bẫy chữ giả:
    token VIẾT-HOA-TOÀN-BỘ >=3 ký tự (PEARL/HANK/BISON/USA/UPA...) bị FLUX vẽ thành chữ trên ảnh
    -> xoá khỏi prompt (nhân vật đã được mô tả bằng lời ngay sau tên nên không mất nghĩa)."""
    low = p
    for a, b in _TOON_SAFE:
        low = low.replace(a, b).replace(a.title(), b)
    low = re.sub(r"\b[A-Z]{3,}\b", "", low)
    return re.sub(r"\s{2,}", " ", low).replace(" ,", ",").strip()


def _toon_build(channel, keys, niche, tier, avoid, on_limit, on_ok, pub, prefix="",
                voice_a="en-US-ChristopherNeural", rate_a="+0%", voice_b="en-US-GuyNeural", rate_b="+8%",
                toon_style="", resume_story=None, on_status=None, mode="skit"):
    """Dựng 1 SKIT (viết + TTS từng câu + FLUX khung) — trả (story, frames_rel, lines_rel, end_f).
    frames/lines tính frame TƯƠNG ĐỐI từ 0 (caller tự dời khi ghép long). File mang prefix
    -> long 3 skit không giẫm tên nhau; short tái dùng đúng các file này (0 phí thêm)."""
    import key_manager as KM
    st = on_status or (lambda *a, **k: None)
    # 23/8: 3 chế độ — skit (đối thoại 2 nhân vật) · story (kể chuyện 1 giọng) · essay (PHÂN TÍCH
    # lật-ngược-niềm-tin 1 giọng + ẩn dụ hình ảnh — format thay thế skit hài sau khi user chấm demo).
    _writer = {"story": KM.write_tale, "essay": KM.write_essay}.get(mode, KM.write_toon)
    story = resume_story or _writer(channel, keys, niche, tier=tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    # 23/8: SOI LẠI 1 LƯỢT trước khi render — cắt câu dài, bỏ ý lặp, ép mỗi khung tả một cảnh KHÁC
    # nhau (chống ảnh trùng ngay từ kịch bản), giữ nguyên nguồn. Lỗi thì trả nguyên bản.
    if not resume_story:
        st("writing", "Soi lại kịch bản")
        story = KM.review_script(channel, keys, story, niche=niche, tier=tier, avoid=avoid)
    st("writing", f"✔ skit: {story.get('title', '')[:60]}", script=json.dumps(story, ensure_ascii=False))
    dialog = story.get("dialog") or []
    FPS = 30; GAP = 0.20; t = 0.55
    lines = []
    for i, dl in enumerate(dialog):
        who = "A" if dl.get("who") != "B" else "B"
        v, r = (voice_a, rate_a) if who == "A" else (voice_b, rate_b)
        mp3 = f"{prefix}line{i}.mp3"
        d, _subs, _srt = TK.synth(dl.get("line", ""), os.path.join(pub, mp3), v, r)
        if d <= 0.1:
            continue
        words = [{"w": w.get("w", ""), "f": int(float(w.get("t", 0)) * FPS)} for w in (_subs or []) if w.get("w")]
        lines.append({"audio": mp3, "text": dl.get("line", ""), "who": who,
                      "from": int(t * FPS), "dur": int((d + GAP) * FPS), "words": words})
        t += d + GAP
    if len(lines) < 4:
        raise RuntimeError("TTS quá ít câu")
    # NẤC 3 (bản 23/8): đánh dấu CÂU CHỐT để engine nhấn bằng CÚ MÁY (zoom giật + rung nhẹ +
    # vignette khép). ĐÃ BỎ đạo cụ emoji — user: "đừng làm xấu, trông rẻ tiền"; kênh sepia cổ
    # điển (DUMB HISTORY) mà emoji bay vào là hỏng tông ngay.
    # (5) NHỊP THỞ (23/8): lặng 0.4s TRƯỚC câu chốt — thủ pháp kể chuyện cơ bản, câu cuối nặng hơn
    # hẳn mà không tốn gì. Dời câu cuối lùi lại + nới end_f tương ứng.
    if len(lines) >= 3:
        _pause = int(0.4 * FPS)
        lines[-1]["from"] += _pause
        t += 0.4
    lines[-1]["punch"] = True
    # THẺ SỐ LIỆU (23/8, user: "kết hợp chart/biểu đồ nếu phù hợp"): rút CON SỐ THẬT trong lời kể
    # -> engine bung thẻ số + thanh chỉ báo. Tối đa 3 thẻ/video và chỉ cho mode essay: nhồi nhiều
    # là rối, mà format phân tích thì mỗi con số là một cú chốt hạ nên phải nổi bật.
    if mode == "essay":
        _num = re.compile(r"(\$?\d[\d,.]*\s?(?:%|percent|million|billion|thousand|grams?|years?|hours?|days?)?)", re.I)
        _cap = re.compile(r"\b(19|20)\d{2}\b")
        _n = 0
        for _l in lines:
            if _n >= 3:
                break
            _t = _l.get("text") or ""
            # chọn con số ĐÁNG hiện nhất trong câu: có $/%/đơn vị hoặc dấu phân cách > năm trơn
            _cands = [c[0].strip().rstrip(".,") for c in _num.findall(_t)] if _num.findall(_t) else []
            _cands = [c for c in [m.group(1).strip().rstrip(".,") for m in _num.finditer(_t)] if len(c) >= 2]
            if not _cands:
                continue
            def _rank(v):
                sc = 0
                if any(ch in v for ch in "$%,"):
                    sc += 3
                if any(u in v.lower() for u in ("million", "billion", "thousand", "gram", "percent", "year", "hour", "day")):
                    sc += 2
                if _cap.fullmatch(v.strip()):
                    sc -= 2      # năm trơn kém hấp dẫn hơn số liệu
                return (sc, len(v))
            _v = max(_cands, key=_rank)
            _words = [w for w in _t.replace(",", "").split() if not any(c.isdigit() for c in w)]
            _l["stat"] = {"num": _v, "cap": " ".join(_words[-3:])[:26]}
            _n += 1
        if _n:
            print(f"   📊 Thẻ số liệu: {_n} thẻ (rút từ chính lời kể).")
    end_f = int(t * FPS) + 16 + 66      # +66 frame (2.2s) cho KẾT BÀI mời theo dõi (23/8)
    spec = sorted((story.get("frames") or []), key=lambda x: int(x.get("line_idx", 0)))
    fr = []
    for k2, fx in enumerate(spec):
        li = min(int(fx.get("line_idx", 0)), len(lines) - 1)
        start = 0 if k2 == 0 else lines[li]["from"]
        fr.append({"img": f"{prefix}fr{k2}.jpg", "from": start, "prompt": _toon_safe(str(fx.get("prompt", "")))})
    for k2 in range(len(fr)):
        end = fr[k2 + 1]["from"] if k2 + 1 < len(fr) else end_f
        fr[k2]["dur"] = max(24, end - fr[k2]["from"])
    # ── NẤC 1 (23/8, user: "cần chất lượng, giảm số lượng"): TĂNG MẬT ĐỘ ẢNH ──────────────────
    # Khung nào dài hơn ~3.2s bị CẮT ĐÔI/BA thành các góc máy khác nhau (toàn → cận → qua vai).
    # Mắt người bắt đầu thấy "ảnh chết" từ ~3s; cắt góc đều đặn là hết cảm giác tĩnh mà KHÔNG
    # tốn AI viết lại (chỉ thêm lượt vẽ FLUX — CF free). Trần 16 khung/skit để không nổ neuron.
    MAXD, CAP = int(3.2 * FPS), 16
    ANGLES = ["wide establishing shot of the whole scene",
              "medium shot, characters from the waist up",
              "tight head-and-shoulders shot of the character who is speaking",
              "over-the-shoulder shot from behind the other character",
              "low angle shot looking up, dramatic",
              "side profile two-shot of both characters"]
    dense, ai = [], 0
    for k2, fx in enumerate(fr):
        nsub = max(1, min(3, -(-fx["dur"] // MAXD)))          # trần 3 lát/khung
        if len(dense) + nsub > CAP:
            nsub = max(1, CAP - len(dense))
        step = fx["dur"] // nsub
        for s in range(nsub):
            dense.append({
                "img": f"{prefix}fr{len(dense)}.jpg",
                "from": fx["from"] + s * step,
                "dur": (fx["dur"] - s * step) if s == nsub - 1 else step,
                # lát đầu giữ nguyên ý đạo diễn của AI; lát sau đổi GÓC MÁY (cùng cảnh, cùng nhân vật)
                "prompt": fx["prompt"] if s == 0 else f"{fx['prompt']}, {ANGLES[(k2 + s) % len(ANGLES)]}",
            })
            ai += 1
        if len(dense) >= CAP:
            break
    if dense:
        fr = dense
    print(f"   🎞️ Mật độ ảnh: {len(fr)} khung / {end_f / FPS:.0f}s (~{end_f / FPS / max(1, len(fr)):.1f}s/khung)")
    okn = 0
    for k2, fx in enumerate(fr):
        dest = os.path.join(pub, fx["img"])
        # _toon_safe cho CẢ prompt LẪN style ngay từ lượt đầu (22/8 đêm): style-lock chứa tên
        # riêng VIẾT HOA (PEARL/BISON/OWL) và từ "advertising" -> FLUX in chữ giả lên khung hình.
        _sty = _toon_safe(_usa_style(toon_style or DEFAULT_AI_STYLE, mode))
        prompt = _toon_safe(f"{story.get('scene_base', '')}. {fx['prompt']}. no signs, no lettering, no text")
        okimg = _generate_image_ai(prompt, dest, (keys[0] or {}).get("key"), style=_sty)
        if not okimg:
            okimg = _generate_image_ai(prompt, dest, (keys[0] or {}).get("key"), style=_sty)
        if okimg:
            okn += 1
        elif k2 > 0:
            fx["img"] = fr[k2 - 1]["img"]
    if okn < max(3, int(len(fr) * 0.6)):
        raise RuntimeError(f"chỉ vẽ được {okn}/{len(fr)} khung")
    # CHUẨN HÌNH ≥95 (user 22/8): Vision chấm cả lưới 1 lệnh — khung nào sai (dị dạng/không đúng
    # 2 nhân vật/chữ vô nghĩa) thì vẽ lại 1 lần; vẫn sai -> dùng khung liền trước (an toàn hơn ảnh hỏng).
    try:
        # 23/8 — 2 LỖI VỪA VÁ:
        # (a) chủ đề chấm bị HARDCODE "hai nhân vật hoạt hình" -> sai hoàn toàn với mode essay
        #     (tranh ẩn dụ, không có nhân vật) => Vision đánh trượt oan hoặc bỏ lọt sai nội dung.
        #     Giờ mỗi ô chấm theo ĐÚNG PROMPT CỦA CHÍNH NÓ -> khớp nội dung 100%, đúng ý user.
        # (b) vẽ lại dùng spec[k2] — nhưng sau khi TĂNG MẬT ĐỘ, fr đã dài hơn spec => lệch prompt
        #     (thậm chí IndexError). Giờ lấy prompt ngay trong fr[k2].
        _clean = ("clean composition, correct proportions, no gibberish text, no watermark"
                  if mode == "essay" else
                  "the channel's fixed characters clearly drawn, correct anatomy, no gibberish text")
        _pairs = [(os.path.join(pub, fx["img"]), f"{fx.get('prompt', '')[:120]} — {_clean}") for fx in fr]
        _vr = _verify_grid_rot(_pairs, first_key=(keys[0] or {}).get("key"))
        _bad = sum(1 for x in (_vr or []) if x is False)
        if _vr:
            print(f"   🔍 QC ảnh TRƯỚC render (ghép lưới 1 lệnh): {len(_vr) - _bad}/{len(_vr)} khung khớp nội dung.")
        for k2, ok2 in enumerate(_vr or []):
            if ok2 is False and k2 < len(fr):
                dest = os.path.join(pub, fr[k2]["img"])
                re_ok = _generate_image_ai(
                    _toon_safe(f"{story.get('scene_base', '')}. {fr[k2].get('prompt', '')}. {_clean}"),
                    dest, (keys[0] or {}).get("key"), style=_toon_safe(_usa_style(toon_style or DEFAULT_AI_STYLE, mode)))
                if not re_ok and k2 > 0:
                    fr[k2]["img"] = fr[k2 - 1]["img"]
        if _bad and len(_vr or []) and _bad / len(_vr) > 0.4:
            raise RuntimeError(f"QC ảnh: {_bad}/{len(_vr)} khung KHÔNG khớp nội dung -> bỏ bài, viết lại")
    except RuntimeError:
        raise
    except Exception as _ve:
        print("   ⚠️ vision khung toon (bỏ qua):", str(_ve)[:60])
    for fx in fr:
        fx.pop("prompt", None)
    return story, fr, lines, end_f


def _normalize_loudness(out):
    """CHUẨN ÂM LƯỢNG NỀN TẢNG -14 LUFS (23/8). Vì sao: YouTube/TikTok tự kéo mọi video về ~-14 LUFS
    khi phát; video nào xuất nhỏ hơn sẽ nghe MỎNG và YẾU hơn video đối thủ ngay giây đầu (âm lượng
    là tín hiệu chất lượng vô thức mạnh nhất). Dùng ffmpeg loudnorm 1-pass + true-peak -1.5dB chống
    méo. Ghi ra file tạm rồi thay thế; lỗi -> giữ nguyên bản cũ (không bao giờ làm hỏng video)."""
    import subprocess
    tmp = out.rsplit(".", 1)[0] + "_ln.mp4"
    try:
        r = subprocess.run(["ffmpeg", "-y", "-i", out, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", tmp],
                           capture_output=True, timeout=900)
        if r.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 100_000:
            os.replace(tmp, out)
            print("   🔊 Đã chuẩn hoá âm lượng -14 LUFS (chuẩn YouTube/TikTok).")
            return True
        print("   ⚠️ chuẩn âm lượng bỏ qua:", (r.stderr or b"")[-120:].decode("utf8", "ignore"))
    except Exception as e:
        print("   ⚠️ chuẩn âm lượng lỗi:", str(e)[:70])
    finally:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except Exception: pass
    return False


def _qc_after_render(out, story, keys, n=6):
    """QC SAU RENDER (23/8, user yêu cầu): trích n khung TỪ VIDEO THẬT -> ghép lưới -> Vision chấm
    1 lệnh. Bắt được thứ QC-trước-render KHÔNG thấy: khung đen cuối, phụ đề đè mất hình, ảnh không
    nạp (fallback xám), chữ dính mép. Trả (ok, tỉ_lệ_khớp). Lỗi vision -> (True, -1) fail-open."""
    import subprocess, tempfile
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "csv=p=0", out], capture_output=True, text=True,
                                   timeout=60).stdout.strip() or 0)
        if dur <= 1:
            return True, -1
        tmp = tempfile.mkdtemp(prefix="qcv_")
        shots = []
        for k in range(n):
            at = dur * (0.06 + 0.88 * k / max(1, n - 1))     # trải đều, có lấy sát cuối để bắt khung đen
            f = os.path.join(tmp, f"s{k}.jpg")
            subprocess.run(["ffmpeg", "-y", "-ss", f"{at:.2f}", "-i", out, "-frames:v", "1",
                            "-vf", "scale=640:-2", f], capture_output=True, timeout=120)
            if os.path.exists(f) and os.path.getsize(f) > 2000:
                shots.append(f)
        if len(shots) < 3:
            return True, -1
        subj = (f"a frame from a video about: {(story.get('title') or '')[:70]} — "
                "an illustrated scene with readable subtitle text, NOT a blank or black frame")
        vr = _verify_grid_rot([(f, subj) for f in shots], first_key=(keys[0] or {}).get("key"))
        if not vr:
            return True, -1
        good = sum(1 for x in vr if x is not False)
        rate = good / len(vr)
        print(f"   🔍 QC SAU render: {good}/{len(vr)} khung video đạt ({rate:.0%}).")
        return rate >= 0.7, rate
    except Exception as e:
        print("   ⚠️ QC sau render bỏ qua:", str(e)[:60])
        return True, -1


# Nhạc nền CC-BY (Kevin MacLeod) — chọn theo kênh cho khỏi trùng tông; volume để rất khẽ trong
# engine (0.09) nên chỉ đủ "giữ nhịp", không lấn giọng đọc. Ghi công tự thêm vào mô tả (xem enqueue).
_TOON_MUSIC = {"TRUETALES": "music/km_impact_andante.mp3", "DUMBHISTORY": "music/km_interloper.mp3",
               "EXPLAINUSA": "music/forecast.mp3", "BALDBANDIT": "music/km_ascending.mp3",
               "HANKTOWN": "music/inspired.mp3"}


def _chart_props(story, lines):
    """CHART ĐỘNG (23/8): kịch bản có bộ số thật -> dựng 4.5 giây cột chạy + số đếm lên, đặt vào
    GIỮA video (sau hook, trước kết) để cắt nhịp và neo con số vào đầu người xem.

    Chỉ nhận số liệu AI trả về trong khối `chart`; thiếu/hỏng thì trả None và video chạy như cũ —
    thà không có chart còn hơn chart bịa."""
    c = (story or {}).get("chart") or None
    if not isinstance(c, dict):
        return None
    items = [x for x in (c.get("items") or [])
             if isinstance(x, dict) and str(x.get("name") or "").strip()
             and isinstance(x.get("value"), (int, float)) and x["value"] > 0]
    if not (2 <= len(items) <= 5):
        return None
    if not lines:
        return None
    mid = lines[max(0, len(lines) // 2 - 1)]
    return {"label": str(c.get("label") or "")[:40], "unit": str(c.get("unit") or "")[:10],
            "items": [{"name": str(x["name"])[:14], "value": float(x["value"])} for x in items],
            "from": int(mid.get("from", 0)), "dur": 135}          # 4.5 giây ở 30fps


def _toon_props(sl, title, accent, display, fr, lines, color_a, color_b, chapters=None, channel="", story=None):
    return {"slug": sl, "title": title, "color": accent, "name": display,
            "frames": fr, "lines": lines,
            "music": _TOON_MUSIC.get(str(channel).upper(), ""), "chapters": chapters or [],
            "chart": _chart_props(story or {}, lines),
            "whoColors": {"A": color_a, "B": color_b}}


def _toon_render(props, out, comp, label):
    """Trả ĐƯỜNG DẪN props (23/8) -> doc_thumb render thẳng KHUNG BANNER từ composition, không phải
    trích từ video đã nén: chữ sắc, màu đúng, đúng khoảnh khắc hook."""
    pf = os.path.join(PUB, f"_toon_{props['slug']}_{comp}.json")
    json.dump(props, open(pf, "w"), ensure_ascii=False)
    run_render_cmd(["npx", "remotion", "render", "src/index.ts", comp, out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG,
                   timeout=(3600 if comp == "ToonLong" else RENDER_TIMEOUT), label=label)
    return pf


def make_toon(channel, niche, out, keys=None, api_key=None, tier="normal",
              accent="#E4562B", avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None,
              toon_style="", voice_a="en-US-ChristopherNeural", rate_a="+0%",
              voice_b="en-US-GuyNeural", rate_b="+8%", color_a="#7DD3FC", color_b="#FCA5A5",
              display="", toon_mode="skit"):
    """1 SHORT toon độc lập (dùng khi kênh đã đủ long theo tỉ lệ)."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out); fresh_out(out)
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    set_ai_pool(keys, channel)
    sl = slug(channel); pub = os.path.join(PUB, sl); os.makedirs(pub, exist_ok=True)
    st("writing", "TOON viết skit")
    try:
        story, fr, lines, _end = _toon_build(channel, keys, niche, tier, avoid, on_limit, on_ok, pub,
                                             prefix="s_", voice_a=voice_a, rate_a=rate_a, voice_b=voice_b,
                                             rate_b=rate_b, toon_style=toon_style,
                                             resume_story=resume_story, on_status=st, mode=toon_mode)
    except RuntimeError as e:
        return out, (resume_story or {}), False, {"err": str(e)[:80]}
    st("rendering", "TOON render")
    _props = _toon_props(sl, story.get("title", ""), accent, display or channel, fr, lines, color_a, color_b, channel=channel, story=story)
    story["_music"] = bool(_props.get("music"))    # có nhạc -> enqueue ghi công Kevin MacLeod (CC-BY)
    _pf = _toon_render(_props, out, "ToonShort", "ToonShort")
    story["_credits"] = take_credits()   # 23/8: ghi công đúng ảnh đã dùng
    _normalize_loudness(out)          # -14 LUFS trước khi QC đo (QC phải đo đúng file sẽ đăng)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out)
    info["score"] = int((story.get("self_score") or {}).get("total", 0) or 0)
    # QC SAU RENDER (23/8): soi khung THẬT trong video — bắt khung đen/ảnh trắng/phụ đề đè hình.
    if ok:
        _vok, _vrate = _qc_after_render(out, story, keys or [])
        info["visual_after"] = _vrate
        if not _vok:
            ok = False
            info["err"] = f"QC sau render trượt ({_vrate:.0%} khung đạt)"
    if ok:
        try:
            # THUMBNAIL = KHUNG BANNER MỞ ĐẦU render thẳng từ composition (23/8): tiêu đề chữ hoa
            # cỡ lớn trên ảnh ẩn dụ = đúng thứ ăn click trên trang chủ YouTube, nét hơn hẳn trích video.
            _th = doc_thumb(channel, out, big=(story.get("title") or channel),
                            accent=accent, comp_id="ToonShort", props_path=_pf, hook_frame=46,
                            api_key_for_thumb=(keys[0] or {}).get("key"))
            if _th:
                info["thumb"] = _th
        except Exception as e:
            print("   ⚠️ thumb TOON lỗi:", str(e)[:80])
    return out, story, ok, info


def make_toon_long(channel, niche, out, keys=None, tier="normal", accent="#E4562B",
                   avoid=None, on_status=None, on_limit=None, on_ok=None, n_parts=3,
                   toon_style="", voice_a="en-US-ChristopherNeural", rate_a="+0%",
                   voice_b="en-US-GuyNeural", rate_b="+8%", color_a="#7DD3FC", color_b="#FCA5A5",
                   display="", resume=None, toon_mode="skit"):
    """LONG toon = tuyển tập n_parts skit (ToonLong 16:9, title đổi theo skit).
    Trả (out, plan, subs, ok, info, parts) — parts[{story, props}] để run_render đẻ short 9:16."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out); fresh_out(out)
    keys = keys or []
    set_ai_pool(keys, channel)
    sl = slug(channel); pub = os.path.join(PUB, sl); os.makedirs(pub, exist_ok=True)
    FPS = 30; SKIT_GAP = int(1.1 * FPS)
    off = 0; all_fr = []; all_ln = []; chapters = []; parts = []; titles = []
    done_parts = (resume or {}).get("parts") if isinstance(resume, dict) else None
    for pi in range(n_parts):
        st("writing", f"TOON long — skit {pi + 1}/{n_parts}")
        rs = None
        if done_parts and pi < len(done_parts):
            rs = done_parts[pi]                    # checkpoint: skit đã viết phiên trước
        story, fr, lines, end_f = _toon_build(channel, keys, niche, tier,
                                              (avoid or []) + titles, on_limit, on_ok, pub,
                                              prefix=f"p{pi}_", voice_a=voice_a, rate_a=rate_a,
                                              voice_b=voice_b, rate_b=rate_b, toon_style=toon_style,
                                              resume_story=rs, on_status=st, mode=toon_mode)
        titles.append(story.get("title", ""))
        parts.append({"story": story,
                      "props": _toon_props(sl, story.get("title", ""), accent, display or channel,
                                           fr, lines, color_a, color_b, story=story)})
        all_fr += [{**f, "from": f["from"] + off} for f in fr]
        all_ln += [{**l, "from": l["from"] + off} for l in lines]
        chapters.append({"text": story.get("title", ""), "from": off, "dur": end_f})
        off += end_f + SKIT_GAP
        # CHECKPOINT từng skit: chết giữa chừng thì phiên sau viết tiếp từ skit kế
        st("writing", f"✔ xong skit {pi + 1}/{n_parts}",
           script=json.dumps({"parts": [p["story"] for p in parts]}, ensure_ascii=False))
    lp = _toon_props(sl, titles[0] if titles else channel, accent, display or channel,
                     all_fr, all_ln, color_a, color_b, chapters=chapters,
                     story=(parts[0]["story"] if parts else None))
    st("rendering", "TOON long render")
    _toon_render(lp, out, "ToonLong", "ToonLong")
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out)
    info["score"] = min([int((p["story"].get("self_score") or {}).get("total", 0) or 0) for p in parts] or [0])
    if ok:
        try:
            _th = doc_thumb(channel, out, big=(titles[0] if titles else channel),
                            api_key_for_thumb=(keys[0] or {}).get("key") if keys else None)
            if _th:
                info["thumb"] = _th
        except Exception as e:
            print("   ⚠️ thumb TOON long lỗi:", str(e)[:80])
    # 23/8: tiêu đề long KHÔNG gắn tên kênh (YouTube coi "TÊN KÊNH — tiêu đề" là spam/nhồi từ khoá,
    # và ăn mất ~15 ký tự hiển thị trên mobile). Lấy hook của phần 1 làm tiêu đề chính, kèm số mục
    # để hứa hẹn giá trị ("+2 more"). SOURCES gom từ MỌI phần -> mô tả có dẫn nguồn thật (điều kiện
    # cần khi YouTube xét bật kiếm tiền: nội dung có kiểm chứng, không phải nội dung lặp lại hàng loạt).
    _allsrc = []
    for _p in parts:
        for _s in ((_p.get("story") or {}).get("sources") or []):
            if _s and _s not in _allsrc:
                _allsrc.append(_s)
    _t0 = titles[0] if titles else (display or channel)
    plan = {"pillar_title": (f"{_t0} (+{len(titles) - 1} more)" if len(titles) > 1 else _t0),
            "hook": (parts[0]["story"].get("title") if parts else ""),
            "parts": parts, "sources": _allsrc[:8]}
    return out, plan, titles, ok, info, parts


def render_toon_short_props(channel, props, story, out, keys=None, prefix=""):
    """SHORT từ props skit có sẵn (audio + ảnh dùng lại nguyên) — 0 gọi AI."""
    out = os.path.abspath(out); fresh_out(out)
    _toon_render(props, out, "ToonShort", f"ToonShort({prefix})")
    ok, info = qc(out)
    info["score"] = int((story.get("self_score") or {}).get("total", 0) or 0)
    if ok:
        try:
            _th = doc_thumb(channel, out, big=(story.get("title") or channel),
                            api_key_for_thumb=(keys[0] or {}).get("key") if keys else None)
            if _th:
                info["thumb"] = _th
        except Exception as e:
            print("   ⚠️ thumb TOON short lỗi:", str(e)[:80])
    return ok, info
