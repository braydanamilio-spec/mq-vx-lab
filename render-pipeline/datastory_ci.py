"""
datastory_ci.py — DRIVER A-Z: Gemini viết -> giọng(hook+narration)+karaoke -> ảnh theo câu
-> render RaceLong(V) -> QC. Portable (chạy được trên GitHub Actions).

Local test:
    export GEMINI_API_KEY=xxx
    python datastory_ci.py --channel DATARACE --type short --seed "US billionaire tax" --out out.mp4
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, urllib.parse, urllib.request
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


def _generate_image_ai(prompt, dest, api_key, model="gemini-2.5-flash-image", style=None) -> bool:
    """DỰ PHÒNG khi Openverse KHÔNG có ảnh CC0 khớp: nhờ Gemini VẼ ảnh minh hoạ (Nano Banana).
    Quota TÁCH RIÊNG khỏi quota viết kịch bản (model khác nhau) -> dùng thoải mái, không đụng key đang
    viết chữ. ~500 ảnh/ngày/key free, không cần thẻ. Lỗi/an toàn nội dung/hết quota -> trả False,
    caller tự lùi về fallback cũ (mosaic/cosmic bg) — KHÔNG BAO GIỜ làm crash pipeline.
    style: phong cách vẽ (vd "cinematic sci-fi concept art") — mặc định ảnh báo chí thật, đổi cho kênh
    speculative (tương lai/vũ trụ suy đoán) nơi KHÔNG có ảnh thật để so nên cần 1 gu vẽ riêng, nhất quán."""
    if not api_key:
        return False
    try:
        from google import genai as genai2
        client = genai2.Client(api_key=api_key)
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
            return False
        open(dest, "wb").write(data)
        return True
    except Exception as e:
        print(f"   ⚠️ Nano Banana '{prompt[:30]}' lỗi: {str(e)[:100]}"); return False


def fetch_image(query, dest, orient=None, verify=None, max_check=4, ai_key=None, ai_prompt=None,
                ai_style=None, ai_only=False):
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
            return json.load(r).get("results") or []
    ar = {"tall": "tall", "wide": "wide"}.get(orient or "")   # KHỚP ĐỊNH DẠNG: short=dọc(tall), long=ngang(wide)
    pg = max(6, max_check + 2) if verify else 3               # cần verify -> lấy nhiều ứng viên hơn để chọn ảnh KHỚP
    base = {"page_size": pg, "license": "cc0,pdm", "mature": "false"}
    if ar:
        base["aspect_ratio"] = ar
    def _openverse():
        # CHỈ CC0 + Public Domain -> KHÔNG cần ghi nguồn, an toàn bản quyền 100%. Không có -> dùng ảnh fallback.
        res = _try({"q": query, **base})
        if not res and ar:
            res = _try({"q": query, "page_size": pg, "license": "cc0,pdm", "mature": "false"})   # bỏ lọc hướng nếu 0 kết quả
        if not res:
            res = _try({"q": " ".join(query.split()[:2]), "page_size": pg, "license": "cc0,pdm", "mature": "false"})  # rút gọn từ khoá thử lại
        if not res:
            return None
        fallback = None                                   # ảnh hợp lệ nhưng Vision không kiểm được -> dùng nếu không có ảnh KHỚP
        checked = 0
        for cand in res:                                  # duyệt cho tới khi ra 1 ảnh HỢP LỆ (+ KHỚP nếu có verify)
            try:
                with urllib.request.urlopen(urllib.request.Request(cand["url"], headers=UA), timeout=30) as r:
                    ctype = (r.headers.get("Content-Type") or "").lower()
                    data = r.read()
                if len(data) < 2000 or ("image" not in ctype and not _is_image(data)) or not _is_image(data):
                    continue                              # HTML/redirect/hỏng/định dạng lạ -> bỏ, thử ảnh khác
                open(dest, "wb").write(data)
                if not verify:
                    return dest
                v = verify(dest)                          # KIỂM khớp chủ đề
                if v is True:
                    return dest
                if v is None and fallback is None:        # Vision lỗi -> giữ ảnh đầu tiên làm dự phòng
                    fallback = data
                checked += 1
                if checked >= max_check:
                    break
            except Exception:
                continue
        if verify and fallback is not None:               # không ảnh nào KHỚP chắc, nhưng có ảnh dự phòng (Vision down)
            open(dest, "wb").write(fallback); return dest
        return None                                       # verify bật mà không ảnh nào khớp -> THÀ KHÔNG ẢNH còn hơn ảnh SAI
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
                   check=True, capture_output=True)


def _dur(path):
    """Độ dài THẬT của file (giây) — dùng để cộng dồn offset sub chính xác (chống lệch dần)."""
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nk=1:nw=1", path], capture_output=True, text=True).stdout.strip()
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
    intro = {"kicker": (story.get("topic", "")[:34]).upper(),
             "title": (story.get("hook_title") or story.get("topic", "")[:24]).upper(),
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


def qc(mp4):
    """QC kỹ thuật: đủ giây + có audio + đúng khung."""
    def ff(args): return subprocess.run(["ffprobe", "-v", "error", *args, mp4],
                                        capture_output=True, text=True).stdout.strip()
    dur = float(ff(["-show_entries", "format=duration", "-of", "default=nk=1:nw=1"]) or 0)
    ach = ff(["-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "default=nk=1:nw=1"])
    wh = ff(["-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x"])
    ok = dur >= 5 and ach == "audio"
    try:
        size_mb = round(os.path.getsize(mp4) / 1e6, 1)
    except Exception:
        size_mb = 0
    return ok, {"dur": round(dur, 1), "audio": ach == "audio", "res": wh, "size_mb": size_mb}


def make_video(channel, seed, vtype, out, api_key=None, tier="normal", keys=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", comp, out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out)
    if ok:                                          # QC THẨM MỸ (Gemini Vision) — chống chồng chéo/xấu
        try:
            import qc_vision
            vok, vinfo = qc_vision.check_visual(out, api_key=keys[0]["key"])
            info["visual"] = vinfo
            if not vok:
                ok = False
        except Exception as e:
            print("   ⚠️ vision qc skip:", e)
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
                avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH #2 MAPPED A-Z: Gemini sinh metric+số liệu bang THẬT -> giọng -> render MappedShort -> QC + thumb.
    Trả (out, story, ok, info)."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "MappedShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        big = (story.get("title") or "WHICH STATE\nWINS?").upper()
        tprops = {"kind": "thumb", "bigLine": big, "topLine": "#1 will shock you"}
        tf = os.path.join(PUB, f"_mappedthumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "MappedThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True)
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
                avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH #3 RANKED A-Z: Gemini sinh tier list (tiêu chí + số liệu thật) -> giọng -> render RankedShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "RankedShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        big = (story.get("title") or "WHAT'S\nS-TIER?").upper()
        tprops = {"kind": "thumb", "bigLine": big, "topLine": "you'll rage 😤"}
        tf = os.path.join(PUB, f"_rankedthumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "RankedThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True)
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
                avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH #4 SCALED A-Z: Gemini sinh so sánh kích thước (đo thật + emoji) -> giọng -> render ScaledShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "ScaledShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        big = (story.get("title") or "HOW BIG\nREALLY?").upper()
        tprops = {"kind": "thumb", "bigLine": big, "topLine": "you won't believe it"}
        tf = os.path.join(PUB, f"_scaledthumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "ScaledThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True)
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
                 avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH #5 THEN×NOW A-Z: Gemini sinh so sánh xưa/nay (giá trị thật) -> giọng -> render ThenNowShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "ThenNowShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        big = (story.get("title") or "THEN vs\nNOW").upper()
        tprops = {"kind": "thumb", "bigLine": big, "topLine": "the change is wild"}
        tf = os.path.join(PUB, f"_thennowthumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "ThenNowThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True)
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb skip:", e)
    print(f"   {'✅' if ok else '❌'} QC thennow {info}")
    return out, story, ok, info


def build_doc_props(story, channel, imgsrc=None, api_key=None, accent="#22D3EE", accent2="#F5B301", handle="@doc",
                    ai_style=None, ai_only=False, music=None):
    """Dựng props Cinematic (Wave 2): intro chapter + cảnh ảnh (fetch + Vision verify khớp) + outro chapter.
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
    vf_for = (lambda subj: (lambda p: qc_vision.verify_image(p, subj, api_key=api_key))) if (api_key and not ai_only) else (lambda subj: None)

    def add_scene(i, nar, kind, img_query=None, title=""):
        amp3 = os.path.join(sdir, f"s{i}.mp3")
        dur_s, _subs, _ = TK.synth(nar or title or "…", amp3)
        durF = max(48, round((dur_s + 0.5) * FPS))
        # KHÔNG truyền subs (TK trả dạng TỪ, Cinematic cần dạng CÂU) -> để engine tự tạo caption từ nar (khớp giọng đều).
        sc = {"type": kind, "audio": f"s{i}.mp3", "dur": durF, "nar": nar or "", "title": title or ""}
        if kind != "chapter" and img_query:
            got = fetch_image(img_query, os.path.join(cdir, f"s{i}.jpg"), orient="tall", verify=vf_for(img_query),
                              ai_key=api_key, ai_style=ai_style, ai_only=ai_only)
            if got:
                sc["clip"] = f"s{i}.jpg"
            else:
                sc["type"] = "chapter"; sc["title"] = title or (story.get("title") or "")  # không ảnh khớp -> cosmic bg (không dùng ảnh sai)
        scenes_out.append(sc)

    i = 0
    add_scene(i, story.get("hook") or story.get("title"), "chapter", title=story.get("title")); i += 1
    for s in (story.get("scenes") or []):
        add_scene(i, s.get("nar"), "scene", img_query=s.get("img_query"), title=s.get("title", "")); i += 1
    add_scene(i, story.get("outro") or "Follow for more.", "chapter", title=""); i += 1
    props = {"scenes": scenes_out, "slug": slug_, "handle": handle, "accent": accent, "accent2": accent2}
    if music:
        props["music"] = music
    return props


def make_doc(channel, niche, out, keys=None, api_key=None, tier="normal", style="awe, cinematic",
             imgsrc=None, accent="#22D3EE", accent2="#F5B301", avoid=None,
             on_status=None, on_limit=None, on_ok=None, resume_story=None, ai_style=None, ai_only=False, music=None):
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
    if resume_story:
        story = resume_story; st("writing", "♻️ Dùng lại kịch bản đã lưu (khỏi gọi Gemini lại)")
    else:
        st("writing", f"Gemini viết tài liệu ({niche})")
        story = KM.write_doc(channel, keys, niche, style, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok, speculative=ai_only)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + ảnh + render điện ảnh", title=story.get("title_yt") or story.get("title"), score=score, script=_ckpt_json(story))
    props = build_doc_props(story, channel, imgsrc=imgsrc, api_key=keys[0]["key"],
                            accent=accent, accent2=accent2, handle=channel_handle(channel),
                            ai_style=ai_style, ai_only=ai_only, music=music)
    pf = os.path.join(PUB, f"_doc_{slug(channel)}.json"); json.dump(props, open(pf, "w"))
    print(f"   🎞️ render CinematicShort ({len(props['scenes'])} cảnh) …")
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "CinematicShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
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


def make_swarm(channel, niche, out, keys=None, api_key=None, tier="normal",
               accent="#0D9488", avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH SWARM A-Z: Gemini sinh mật độ/số lượng thật -> giọng -> render SwarmShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "SwarmShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        big = (story.get("title") or "HOW MANY?").upper()
        tprops = {"kind": "thumb", "bigLine": big, "topLine": "the real number"}
        tf = os.path.join(PUB, f"_swarmthumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "SwarmThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True)
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
    items_out, clips, cum = [], [(intro_mp3, 0.0)], 0.0
    for i, it in enumerate(items_in):
        p = os.path.join(sdir, f"it{i}.mp3")
        du, _, _ = TK.synth(it.get("vo") or f"{it.get('label','')}, {it.get('disp','')}.", p)
        dur = round(du + 0.4, 2)
        items_out.append({"label": it.get("label"), "emoji": it.get("emoji"), "value": it.get("value"),
                          "disp": it.get("disp"), "extreme": bool(it.get("extreme")), "dur": dur})
        clips.append((p, introSec + cum)); cum += dur
    odur, _, _ = TK.synth(story.get("outro_vo") or "Follow for more real intensity checks.", outro_mp3)
    outroSec = round(odur + 0.4, 2)
    clips.append((outro_mp3, introSec + cum))
    total = round(introSec + cum + outroSec, 2)
    track = os.path.join(sdir, "track.mp3"); _mix_track(clips, total, track)
    return {"title": (story.get("title") or "HOW INTENSE?"), "handle": handle, "color": accent, "accent": accent,
            "sfx": True, "unit": story.get("unit") or "", "maxScale": story.get("maxScale") or 100,
            "items": items_out, "audio": rel(track), "music": music}


def make_pulse(channel, niche, out, keys=None, api_key=None, tier="normal",
              accent="#EA580C", avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH PULSE A-Z: Gemini sinh cường độ giác quan thật -> giọng -> render PulseShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "PulseShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        big = (story.get("title") or "HOW INTENSE?").upper()
        tprops = {"kind": "thumb", "bigLine": big, "topLine": "redline this"}
        tf = os.path.join(PUB, f"_pulsethumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "PulseThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True)
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
            "realValue": hero.get("realValue")}, "audio": rel(track), "music": music}


def make_clockwork(channel, niche, out, keys=None, api_key=None, tier="normal",
                   accent="#C2410C", avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH CLOCKWORK A-Z: Gemini nén thời gian thật -> giọng -> render ClockworkShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "ClockworkShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        big = (story.get("title") or "TIME COMPRESSED").upper()
        tprops = {"kind": "thumb", "bigLine": big, "topLine": "you won't believe it"}
        tf = os.path.join(PUB, f"_clockworkthumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "ClockworkThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True)
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
                  accent="#4F46E5", avoid=None, on_status=None, on_limit=None, on_ok=None, resume_story=None):
    """KÊNH LONGSHOT A-Z: Gemini sinh xác suất thật -> giọng -> render LongshotShort -> QC + thumb."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "LongshotShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out); info["score"] = score
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        big = (story.get("title") or "REAL ODDS").upper()
        tprops = {"kind": "thumb", "bigLine": big, "topLine": "the real odds"}
        tf = os.path.join(PUB, f"_longshotthumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "LongshotThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True)
        info["thumb"] = thumb
    except Exception as e:
        print("   ⚠️ thumb LONGSHOT lỗi:", str(e)[:80])
    print(f"   {'✅' if ok else '❌'} QC longshot {info}")
    return out, story, ok, info


def make_long(channel, niche, out, keys=None, api_key=None, tier="normal",
              on_status=None, on_limit=None, n_races=6, avoid=None, on_ok=None, resume_checkpoint=None):
    """LONG 16:9 = pillar 5-6 race cùng chủ đề. Trả (out, plan, subtopics, ok, info, stories).
    resume_checkpoint: {"pillar_title","hook","races":[...]} ĐÃ CÓ (checkpoint phiên trước bị huỷ/lỗi lúc
    render) -> dùng lại, bỏ qua gọi Gemini lập pillar + viết lại từng race."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)   # QUAN TRỌNG: render cwd=ENG -> path tuyệt đối (nếu không QC/enqueue tìm không ra file -> 0 giây)
    import key_manager as KM
    import content_brain as CB
    keys = keys or [{"id": "env", "key": api_key or os.environ["GEMINI_API_KEY"], "email": "local"}]
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
        plan = CB.plan_pillar(niche, n_races, api_key=k0["key"], model_name=KM.model_for(tier), avoid=avoid)
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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "RaceLong", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out)
    if ok:
        try:
            import qc_vision
            vok, vinfo = qc_vision.check_visual(out, api_key=keys[0]["key"])
            info["visual"] = vinfo
            if not vok:
                ok = False
        except Exception as e:
            print("   ⚠️ vision qc skip:", e)
    scs = [(s.get("self_score") or {}).get("total") for s in stories if (s.get("self_score") or {}).get("total")]
    if scs:
        info["score"] = round(sum(scs) / len(scs))   # điểm QC long = TB các race -> hiện trên dashboard
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
                    "-map", "[out]", "-ac", "2", "-ar", "44100", out], check=True, capture_output=True)


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
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "GuessShort", out,
                    f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
                    "--concurrency=2", "--log=error"], cwd=ENG, check=True)
    st("qc", "Kiểm tra chất lượng")
    ok, info = qc(out)
    info["score"] = score
    # thumbnail đi kèm (GuessThumb): câu hỏi to + mảnh ghép
    try:
        thumb = out.rsplit(".", 1)[0] + ".jpg"
        tprops = {"kind": "thumb", "bigLine": (story.get("rounds") or [{}])[0].get("q", "CAN YOU\nNAME IT?").upper(),
                  "topLine": "99% FAIL 👀"}
        tf = os.path.join(PUB, f"_guessthumb_{slug(channel)}.json"); json.dump(tprops, open(tf, "w"))
        subprocess.run(["npx", "remotion", "still", "src/index.ts", "GuessThumb", thumb,
                        f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"], cwd=ENG, check=True)
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
