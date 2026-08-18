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


def fetch_image(query, dest, orient=None, verify=None, max_check=4):
    """Tải 1 ảnh từ Openverse — ƯU TIÊN CC0/Public Domain (KHÔNG cần ghi nguồn, an toàn bản quyền).
    verify(path)->True/False/None: kiểm ảnh có KHỚP chủ đề không (dùng cho GUESS). True=nhận, False=thử ảnh khác,
    None=không kiểm được (Vision lỗi) -> nhớ làm dự phòng. Lỗi/ảnh hỏng/không khớp -> trả None."""
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
    try:
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
    except Exception as e:
        print(f"   ⚠️ ảnh '{query[:30]}' lỗi: {e}"); return None


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


def make_video(channel, seed, vtype, out, api_key=None, tier="normal", keys=None, on_status=None, on_limit=None, on_ok=None):
    """keys: list [{id,key,email}] (production, từ Firestore); None -> dùng GEMINI_API_KEY env (local).
    on_status(status, step, **extra): ghi trạng thái realtime. on_limit(key_id): cho key nghỉ khi limit."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)   # QUAN TRỌNG: render chạy cwd=ENG -> phải tuyệt đối, nếu không file lạc chỗ (QC/enqueue tìm không ra -> 0 giây)
    print(f"▶ {channel} [{vtype}] seed={seed!r}")
    import key_manager as KM
    if keys is None:
        if not (api_key or os.environ.get("GEMINI_API_KEY")):
            raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
        keys = [{"id": "env", "key": api_key or os.environ["GEMINI_API_KEY"], "email": "local"}]
    st("writing", "Gemini viết kịch bản")
    story = KM.write_story(channel, keys, seed, vtype, tier, on_limit=on_limit, on_ok=on_ok)   # bám key theo kênh, limit -> nghỉ + đổi
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + ảnh + render", title=story.get("title"), score=score)
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
                avoid=None, on_status=None, on_limit=None, on_ok=None):
    """KÊNH #2 MAPPED A-Z: Gemini sinh metric+số liệu bang THẬT -> giọng -> render MappedShort -> QC + thumb.
    Trả (out, story, ok, info)."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    st("writing", f"Gemini soạn bản đồ ({niche})")
    story = KM.write_mapped(channel, keys, niche, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + render bản đồ", title=story.get("title_yt") or story.get("title"), score=score)
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


def make_long(channel, niche, out, keys=None, api_key=None, tier="normal",
              on_status=None, on_limit=None, n_races=6, avoid=None, on_ok=None):
    """LONG 16:9 = pillar 5-6 race cùng chủ đề. Trả (out, plan, subtopics, ok, info)."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)   # QUAN TRỌNG: render cwd=ENG -> path tuyệt đối (nếu không QC/enqueue tìm không ra file -> 0 giây)
    import key_manager as KM
    import content_brain as CB
    keys = keys or [{"id": "env", "key": api_key or os.environ["GEMINI_API_KEY"], "email": "local"}]
    st("writing", "Lập pillar (chủ đề con)")
    k0 = KM.key_order(channel, keys)[0]
    plan = CB.plan_pillar(niche, n_races, api_key=k0["key"], model_name=KM.model_for(tier), avoid=avoid)
    subtopics = plan.get("subtopics", [])[:n_races]
    sdir = os.path.join(PUB, "narration", "_long_" + slug(channel)); os.makedirs(sdir, exist_ok=True)
    stories = []
    for i, sub in enumerate(subtopics):
        st("writing", f"Viết race {i+1}/{len(subtopics)}: {sub[:28]}")
        try:
            stories.append(KM.write_story(channel, keys, sub, "long", tier, on_limit=on_limit, on_ok=on_ok))
        except Exception as e:
            print(f"   ⚠️ bỏ race '{sub[:30]}': {e}")
    if len(stories) < 2:
        raise Exception("Long cần ≥2 race hợp lệ.")   # Exception (không SystemExit) -> retry/loop bắt được, không giết cả mẻ
    st("rendering", f"Render long ({len(stories)} race)", title=plan.get("pillar_title"))
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
    return out, plan, subtopics, ok, info


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
            got = fetch_image(q, dest, orient="tall", verify=vf)
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
               avoid=None, on_status=None, on_limit=None, on_ok=None):
    """KÊNH #1 GUESS A-Z: Gemini sinh câu đố (logic + khớp ảnh) -> giọng + ảnh + SFX -> render GuessShort -> QC + thumb.
    Trả (out, story, ok, info)."""
    st = on_status or (lambda *a, **k: None)
    out = os.path.abspath(out)
    import key_manager as KM
    keys = keys or [{"id": "env", "key": api_key or os.environ.get("GEMINI_API_KEY", ""), "email": "local"}]
    if not keys[0]["key"]:
        raise SystemExit("❌ Chưa có GEMINI_API_KEY / key nào")
    st("writing", f"Gemini soạn câu đố ({category})")
    story = KM.write_guess(channel, keys, category, n_rounds, tier, avoid=avoid, on_limit=on_limit, on_ok=on_ok)
    score = (story.get("self_score") or {}).get("total")
    st("rendering", "Giọng + ảnh + SFX + render", title=story.get("title_yt"), score=score)
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
