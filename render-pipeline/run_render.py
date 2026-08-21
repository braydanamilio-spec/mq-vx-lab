"""
run_render.py — PIPELINE (GitHub Actions cron). RULE CHẠY:
  1. Đọc render_config (bật/tắt), gemini_keys, render_channels từ Firestore.
  2. Với MỖI kênh: tạo job -> Gemini viết (bám key kênh) -> render -> QC -> đẩy Drive (enqueue).
  3. Ghi trạng thái REALTIME vào render_jobs -> tab 🎬 Render Studio hiện live.

Env: OWNER_UID (uid chủ), GOOGLE_APPLICATION_CREDENTIALS, FIREBASE_PROJECT_ID,
     AUTOPUBLISHER_SRC (đường dẫn tới MM0-AutoPublisher/src để enqueue). FORCE=1 để chạy dù đang tắt.
"""
from __future__ import annotations
import os, sys, traceback, subprocess, re, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firestore_bridge as FB
import datastory_ci as DS

OWNER = os.environ.get("OWNER_UID")
PVER = os.environ.get("PIPELINE_VERSION", "v2")   # phiên bản pipeline (fix handle/tràn/che/hướng ảnh) -> dọn thông minh chỉ xóa bản CŨ
# AN TOÀN: render là làm DỰ TRỮ (kho), upload là pipeline riêng. Mỗi kênh giữ tối đa N video dự trữ
# (khi target=0) -> KHÔNG render vô hạn làm phình Drive. Chỉnh ở render_config.reserve_long/short.
# NGHỈ GIỮA 2 PHIÊN: trước để 30' -> máy đứng không suốt nửa tiếng sau mỗi phiên dù đã xong việc.
# GitHub concurrency (group mm0-render-cron, cancel-in-progress:false) ĐÃ bảo đảm không bao giờ có
# 2 phiên render chạy đè — lượt mới xếp hàng chờ lượt cũ xong. Nên chỉ cần sàn nghỉ này là đủ.
SESSION_GAP_MIN = 12
RESERVE_LONG = 10
RESERVE_SHORT = 30
DRIVE_SAFETY_PCT = 0.90   # kho ≥90% đầy -> ngừng render mẻ này (tránh phình + lỗi ghi khi hết chỗ)


def _is_ratelimit(err) -> bool:
    """True nếu lỗi do HẾT QUOTA/rate-limit (TẠM) -> KHÔNG tính 'Lỗi', vòng/phiên sau tự thử lại (dùng key còn quota)."""
    s = str(err).lower()
    return ("hết quota" in s or "đều hết" in s or "quota" in s or "429" in s
            or "resource_exhausted" in s or "rate limit" in s or "ratelimit" in s or "per minute" in s)


def _make_thumb(video):
    """Trích 1 khung ĐẸP (giữa-cuối, lúc bars cao/số lớn) làm thumbnail — dùng cho YouTube + gallery."""
    try:
        dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "default=nk=1:nw=1", video], capture_output=True, text=True, timeout=60).stdout.strip()
        try:
            at = max(1.0, float(dur) * 0.62)
        except ValueError:
            at = 3.0
        thumb = os.path.splitext(video)[0] + "_thumb.jpg"
        # ÉP ĐÚNG 1280x720. Bản cũ dùng scale=1280:-1 (cao TỰ TÍNH) -> với short 1080x1920 ra
        # 1280x2276, YouTube TỪ CHỐI thumbnail mà youtube_uploader lại nuốt lỗi để không chặn
        # upload -> video lên KHÔNG có thumbnail, log vẫn báo thành công nên không ai biết.
        # Khung dọc thì đặt vừa vào giữa, hai bên lấp bằng chính nó phóng to + làm mờ (đẹp hơn
        # viền đen, không méo hình như kéo giãn).
        vf = ("split[a][b];"
              "[a]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=20:2[bg];"
              "[b]scale=1280:720:force_original_aspect_ratio=decrease[fg];"
              "[bg][fg]overlay=(W-w)/2:(H-h)/2")
        subprocess.run(["ffmpeg", "-y", "-ss", str(at), "-i", video, "-frames:v", "1",
                        "-filter_complex", vf, thumb], check=True, capture_output=True, timeout=300)
        if not os.path.exists(thumb):
            return None
        DS.ensure_yt_thumb(thumb)       # chốt chặn cuối: đúng cỡ + dưới 2MB
        return thumb
    except Exception as e:
        print("   ⚠️ thumbnail lỗi:", str(e)[:80]); return None


def _script_json(d, cap=300_000):
    """JSON kịch bản chi tiết (lời thoại/scene/số liệu) kèm vào job LÚC 'done' -> lưu ở Firestore (project B),
    TÁCH KHỎI Drive -> nếu 1 tài khoản Drive bị khoá/mất TRƯỚC KHI đăng, kịch bản vẫn còn -> render lại
    MIỄN PHÍ + NHANH (khỏi gọi lại Gemini). Rẻ: mỗi video vài KB, cả 1GiB free tier dư sức chứa hàng vạn video."""
    try:
        s = json.dumps(d, ensure_ascii=False, default=str)
        return s[:cap] if len(s) > cap else s
    except Exception:
        return ""


def _desc_src(story) -> str:
    """Mô tả + DẪN NGUỒN. Kênh data-race đã ghi nguồn từ đầu (xem enqueue_drive), nhưng đường kênh
    doc/motif (30/40 kênh) TRƯỚC ĐÂY chỉ đăng description trần -> video nêu đầy số liệu/mốc/vụ án mà
    KHÔNG có nguồn nào. Với kênh dữ liệu/tài liệu, dẫn nguồn vừa là chất lượng, vừa là bằng chứng
    'nội dung giáo dục, có kiểm chứng' khi YouTube xét bật kiếm tiền, vừa là chỗ dựa nếu bị report
    thông tin sai. Gemini trả 'sources' trong DOC_SCHEMA (bắt buộc nêu tổ chức + báo cáo + năm THẬT)."""
    desc = (story.get("description") or "").strip()
    srcs = [s for s in (story.get("sources") or []) if isinstance(s, str) and s.strip()]
    if srcs:
        desc += "\n\nSources: " + " · ".join(s.strip() for s in srcs[:4])
    return desc


def enqueue_drive(channel, out, story, vtype) -> bool:
    """Đẩy video + sidecar (+ thumbnail) lên Drive _QUEUE qua enqueue.py của AutoPublisher (nếu có)."""
    try:
        # ĐẶT TÊN FILE = KÊNH__tiêu-đề (để search được cả trong Drive lẫn kho tổng, biết ngay của kênh nào).
        _title = story.get("title") or story.get("topic") or vtype
        _safe = re.sub(r"[^A-Za-z0-9]+", "-", f"{channel}__{_title}").strip("-")[:80]
        _new = os.path.join(os.path.dirname(out), _safe + os.path.splitext(out)[1])
        if _new != out and not os.path.exists(_new):
            try:
                os.rename(out, _new); out = _new
            except Exception:
                pass
        src = os.environ.get("AUTOPUBLISHER_SRC")
        if src and src not in sys.path:
            sys.path.insert(0, src)
        from enqueue import enqueue
        # GHI NGUỒN NHẠC (Kevin MacLeod CC-BY) + nguồn số liệu -> tránh claim bản quyền, đúng chính sách.
        desc = (story.get("description") or "")
        srcs = story.get("sources") or []
        if srcs:
            desc += "\n\nSources: " + " · ".join(srcs[:3])
        desc += "\n\nMusic: Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 3.0"
        created = enqueue(channel=channel, video=out, vtype=vtype,
                          topic=story.get("topic") or story.get("title"),
                          title=story.get("title"), description=desc,
                          hashtags=story.get("hashtags"), tags=story.get("tags"),
                          thumbnail=(story.get("_thumb") if (story.get("_thumb") and os.path.exists(story.get("_thumb"))) else _make_thumb(out)))   # thumb brand (GUESS/MAPPED) nếu có, không thì trích khung
        return created or None                     # trả cả {id, account} -> lưu vào job để XEM/stream trên web
    except SystemExit as e:
        # enqueue.py dùng raise SystemExit khi kênh THIẾU trong channels.yaml. SystemExit kế thừa
        # BaseException chứ KHÔNG phải Exception -> "except Exception" bên dưới KHÔNG bắt được, nó
        # xuyên thẳng lên và GIẾT CẢ KÊNH giữa chừng: video vừa render xong (QC 96 điểm) bị vứt,
        # job kẹt mãi ở trạng thái "qc" vì không kịp ghi done/failed, mà GitHub vẫn báo success nên
        # không ai thấy. Ngày 20/8: 27/40 kênh thiếu trong channels.yaml -> mất TOÀN BỘ video của
        # chúng suốt nhiều tuần. Bắt riêng ở đây để một kênh lỗi cấu hình không kéo sập cả phiên.
        print(f"   ❌ enqueue TỪ CHỐI kênh {channel}: {e}")
        print(f"      -> thêm '{channel}' vào MM0-AutoPublisher/config/channels.yaml rồi render lại.")
        return None
    except Exception as e:
        print("   ⚠️ enqueue lỗi (giữ artifact):", e); return None


def run_one(ch, keys, n_shorts=3, report=None):
    """1 kênh theo TEMPLATE của kênh: make_long (1 long pillar) + n_shorts SHORT dọc.
    Đọc ch['make_long'] (mặc định True) và ch['n_shorts'] (mặc định 3) do dashboard đặt."""
    channel = ch.get("name"); tier = ch.get("tier", "normal"); niche = ch.get("niche") or channel
    # FEEDBACK LOOP: video ĐÃ ĐĂNG xem nhiều -> gợi ý Gemini bám GU khán giả thật (KHÔNG lặp chủ đề, chỉ học phong cách).
    # Rỗng tới khi user kết nối YouTube + có video đăng thật -> tự động có tác dụng khi đó, không cần sửa gì thêm.
    try:
        _perf = FB.top_titles(OWNER, channel, n=8)
        if _perf:
            niche = niche + ("\n\nTOP PERFORMING videos on this channel so far (real audience data) — "
                              "lean into what STYLE/ANGLE resonates here, but pick a genuinely NEW topic, "
                              "never repeat one of these: " + "; ".join(_perf))
    except Exception:
        pass
    # TREND SCOUT (trend_scout.py, quét title kênh lớn tham khảo -> Gemini tự tóm gu viết) -> KHÔNG copy
    # chủ đề, chỉ học công thức hook/twist. Rỗng tới khi trend_scout.py chạy lần đầu (bình thường).
    try:
        _trends = FB.read_trend_scout(OWNER, channel)
        if _trends:
            niche = niche + ("\n\nSTYLE PATTERNS from top channels in this space (learn the ANGLE/HOOK "
                              "technique, never copy a topic): " + " | ".join(_trends))
    except Exception:
        pass
    cool = lambda kid, mins=90: FB.cool_key(kid, mins)   # giới hạn PHÚT -> nghỉ ngắn; quota NGÀY -> 90'
    _marked = set()   # key viết OK lúc dùng thật -> đánh dấu SỐNG 1 lần/run (khỏi health-check riêng, đỡ tốn)
    def okcb(kid):
        if kid and kid not in _marked:
            _marked.add(kid)
            try: FB.mark_key_alive(kid, True, "ok (dùng thật)", used=True)   # stamp last_used -> lần sau ưu tiên key lâu chưa xài
            except Exception: pass
    R = report if report is not None else {"done": 0, "fails": []}
    def _stopped():   # nút ⛔ Dừng: kiểm GIỮA các clip -> clip đang render vẫn xong (không hư), rồi mới ngừng.
        try: return bool(FB.read_config(OWNER).get("stop"))
        except Exception: return False
    os.makedirs("out", exist_ok=True)

    # GIỌNG ĐỌC RIÊNG TỪNG KÊNH (chống "nội dung hàng loạt" — xem tts_karaoke.set_voice).
    # Đặt 1 lần ở đây -> mọi TK.synth() trong cả phiên của kênh này tự dùng đúng giọng.
    try:
        import tts_karaoke as _TK
        _TK.set_voice(ch.get("voice"), ch.get("voice_rate"))
    except Exception:
        pass

    # ── FORMAT ĐẶC BIỆT (short-only, motif riêng): GUESS / MAPPED ── route sang make_guess/make_mapped.
    fmt = (ch.get("format") or "").lower()
    if fmt in ("guess", "mapped", "ranked", "scaled", "thennow", "doc", "swarm", "pulse", "clockwork", "longshot"):
        short_target = int(ch.get("short_target", 0) or 0) or RESERVE_SHORT
        need = max(0, short_target - FB.count_done(OWNER, channel, "short"))
        n = min(int(ch.get("n_shorts", n_shorts) or 3) or 3, need)
        if n <= 0:
            print(f"🎯 {channel}: đủ target {fmt} — bỏ qua."); return
        cat = niche   # ⚠️ KHÔNG dùng ch.get("category") — field đó giờ chứa mã YouTube category SỐ ("24"/"27"/"28",
                      # dashboard tự set cho brand kit), KHÔNG phải gợi ý chủ đề. Đụng nhầm = Gemini nhận "24" làm niche.
        avoid = FB.recent_topics(OWNER, channel)
        made_here = []
        resumed = FB.find_resumable(OWNER, channel, "short")   # CHECKPOINT: job cũ lỗi/treo nhưng còn kịch bản -> dùng lại 1 lần
        for i in range(n):
            if _stopped():
                print(f"   ⛔ {channel}: dừng — bỏ {n - i} clip còn lại."); break
            job = FB.new_job(OWNER, channel, "short", pver=PVER)
            jst = lambda s, step, **x: FB.update_job(job, status=s, step=step, **x)
            out = os.path.join("out", DS.slug(channel) + f"_{fmt}{i}.mp4")
            story = ok = info = None; err = None
            resume_story = (resumed or {}).get("story")   # chỉ dùng cho clip ĐẦU (i=0) rồi tiêu luôn, clip sau viết mới bình thường
            for att in (1, 2):
                try:
                    if att > 1: jst("running", f"🔧 Tự thử lại {fmt}…"); resume_story = None   # thử lại lần 2 -> KHÔNG dùng lại kịch bản resume (lỗi có thể do chính nó)
                    _, story, ok, info = _dispatch_short(ch, fmt, cat, out, keys, tier, jst, cool, okcb,
                                                         resume_story=resume_story, avoid=(avoid + made_here))
                    err = None; break
                except (Exception, SystemExit) as e:
                    # BẮT CẢ SystemExit: key_manager/datastory_ci ném SystemExit khi hết Gemini key
                    # ("Chưa có Gemini key nào"). SystemExit kế thừa BaseException nên "except
                    # Exception" KHÔNG bắt -> nó xuyên lên giết cả kênh giữa chừng, để job ma kẹt ở
                    # "writing"/"qc" mà GitHub vẫn báo success (đúng lỗi đã gặp với enqueue 20/8).
                    err = e; traceback.print_exc(); print(f"   🔧 {fmt.upper()} {channel}#{i} lỗi lần {att}: {str(e)[:100]}")
            if resumed:   # dù ok hay lỗi -> đã THỬ dùng checkpoint này rồi, không đưa cho clip kế/phiên sau nữa (tránh lặp vô hạn 1 kịch bản lỗi)
                FB.clear_resumed(resumed["job_id"]); resumed = None
            if err is not None and _is_ratelimit(err):
                jst("ratelimited", "⏳ hết quota tạm — thử lại sau"); R["rl"] = R.get("rl", 0) + 1
            elif err is not None:
                jst("failed", f"Tự thử lại vẫn lỗi: {str(err)[:110]}"); R["fails"].append(f"{channel} {fmt} {i}: {str(err)[:100]}")
            elif ok:
                story["title"] = story.get("title_yt") or story.get("title")   # YT title + tên file dùng bản punchy
                if info and info.get("thumb"): story["_thumb"] = info["thumb"]  # thumb brand đẹp
                # tránh trùng lần sau: nhớ đáp án (guess) / metric (mapped)
                made_here += [r.get("answer") for r in (story.get("rounds") or []) if r.get("answer")] or [story.get("title", "")]
                eq = enqueue_drive(channel, out, story, "short")
                did = (eq or {}).get("id"); acc = (eq or {}).get("account", "")
                jst("done", "Đã đẩy Drive" if did else "Xong (chưa đẩy Drive)", title=story.get("title"),
                    description=_desc_src(story), hashtags=story.get("hashtags") or [], tags=story.get("tags") or [],  # cho auto-enqueue đăng đủ metadata
                    score=(story.get("self_score") or {}).get("total"),
                    dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0), res=(info or {}).get("res", ""),
                    drive_id=did or "", drive_account=acc, thumb_id=(eq or {}).get("thumb_id", ""), preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""),
                    script=_script_json({k: v for k, v in story.items() if k != "_thumb"})); R["done"] += 1; R["done_short"] = R.get("done_short", 0) + 1
            else:
                jst("failed", f"QC {fmt} trượt: {info}"); R["fails"].append(f"{channel} {fmt} {i}: QC trượt")
        if made_here:
            try: FB.save_topics(OWNER, channel, [str(x) for x in made_here if x])
            except Exception: pass
        print(f"   ✅ {channel}: xong {fmt} ({R['done']} clip)"); return

    do_long = ch.get("make_long", True)
    n_shorts = int(ch.get("n_shorts", n_shorts) or 0)
    # MỤC TIÊU/DỰ TRỮ số video/kênh: target>0 = mục tiêu người đặt; target=0 = mức DỰ TRỮ AN TOÀN (khỏi phình vô hạn).
    long_target = int(ch.get("long_target", 0) or 0) or RESERVE_LONG
    short_target = int(ch.get("short_target", 0) or 0) or RESERVE_SHORT
    if do_long and FB.count_done(OWNER, channel, "long") >= long_target:
        do_long = False; print(f"🎯 {channel}: đủ {long_target} long (dự trữ) — bỏ qua long.")
    n_shorts = max(0, min(n_shorts, short_target - FB.count_done(OWNER, channel, "short")))
    if not do_long and n_shorts <= 0:      # ĐỦ CẢ long+short -> thoát NGAY (không gọi Gemini) -> made=0 SẠCH (phân biệt với lỗi quota)
        print(f"🎯 {channel}: đủ target (long+short) — không làm gì thêm."); return
    subtopics = []
    if do_long:
        # ---- LONG ---- SELF-HEAL: render lỗi -> tự thử lại NHẸ hơn (4 race -> 2).
        ljob = FB.new_job(OWNER, channel, "long", pver=PVER)
        lst = lambda s, step, **x: FB.update_job(ljob, status=s, step=step, **x)
        plan = ok = info = None; last_err = None
        resumed_long = FB.find_resumable(OWNER, channel, "long")   # CHECKPOINT: phiên trước lỗi/treo nhưng còn kịch bản
        for attempt, nr in enumerate([4, 2], start=1):
            try:
                avoid = FB.recent_topics(OWNER, channel)      # chủ đề đã dùng -> tránh trùng
                lout = os.path.join("out", DS.slug(channel) + "_long.mp4")
                rck = None
                if attempt == 1 and resumed_long:
                    rck = resumed_long["story"]   # chỉ dùng lần 1; lần 2 (thử nhẹ hơn) viết mới bình thường
                elif attempt > 1:
                    lst("running", f"🔧 Tự thử lại nhẹ hơn ({nr} race)…")
                _, plan, subtopics, ok, info, stories = DS.make_long(channel, niche, lout, keys=keys, tier=tier,
                                                            on_status=lst, on_limit=cool, avoid=avoid, n_races=nr, on_ok=okcb,
                                                            resume_checkpoint=rck,
                                                            accent=ch.get("accent", "#22D3EE"), accent2=ch.get("accent2", "#F5B301"))
                last_err = None; break
            except (Exception, SystemExit) as e:
                last_err = e; traceback.print_exc()
                print(f"   🔧 LONG {channel} lỗi lần {attempt} ({nr} race): {str(e)[:120]}")
        if resumed_long:
            FB.clear_resumed(resumed_long["job_id"])
        try:
            if subtopics:
                FB.save_topics(OWNER, channel, subtopics)     # ghi vào ngân hàng chủ đề
            if last_err is not None and _is_ratelimit(last_err):
                lst("ratelimited", "⏳ hết quota tạm — thử lại sau"); R["rl"] = R.get("rl", 0) + 1   # KHÔNG tính Lỗi
            elif last_err is not None:
                lst("failed", f"Tự thử lại vẫn lỗi: {str(last_err)[:120]}"); R["fails"].append(f"{channel} LONG: {str(last_err)[:100]}")
            elif ok:
                # _thumb PHẢI đi kèm: trước đây chỗ này dựng dict MỚI từ plan nên bỏ rơi plan["_thumb"]
                # -> enqueue_drive không thấy thumbnail, lùi về _make_thumb() cắt khung thô. Nghĩa là
                # MỌI video long đăng lên đều mất tấm thumbnail hook vừa dựng công phu.
                eq = enqueue_drive(channel, lout, {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"),
                                                   "description": plan.get("hook", ""),
                                                   "sources": plan.get("sources") or [],
                                                   "_thumb": plan.get("_thumb") or (info or {}).get("thumb")}, "long")
                did = (eq or {}).get("id"); acc = (eq or {}).get("account", "")
                lst("done", "Long đã đẩy Drive" if did else "Long xong (chưa đẩy Drive)", title=plan.get("pillar_title"),
                    score=(info or {}).get("score"),
                    dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0), res=(info or {}).get("res", ""),
                    drive_id=did or "", drive_account=acc, thumb_id=(eq or {}).get("thumb_id", ""), preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""),
                    script=_script_json({"pillar_title": plan.get("pillar_title"), "hook": plan.get("hook"), "races": stories})); R["done"] += 1; R["done_long"] = R.get("done_long", 0) + 1
            else:
                lst("failed", f"QC long trượt: {info}"); R["fails"].append(f"{channel} LONG: QC trượt {info}")
        except Exception as e:
            traceback.print_exc(); lst("failed", str(e)[:140]); R["fails"].append(f"{channel} LONG: {str(e)[:100]}")
    else:
        # TEMPLATE "chỉ short": lấy subtopics KHÔNG render long (rẻ, nhanh).
        try:
            import content_brain as CB, key_manager as KM
            k0 = KM.key_order(channel, keys)[0]
            plan = CB.plan_pillar(niche, max(n_shorts, 3), api_key=k0["key"], model_name=KM.model_for(tier),
                                  avoid=FB.recent_topics(OWNER, channel))
            subtopics = (plan.get("subtopics") or [])[:max(n_shorts, 3)]
            if subtopics:
                FB.save_topics(OWNER, channel, subtopics)
        except Exception as e:
            traceback.print_exc(); R["fails"].append(f"{channel} PLAN: {str(e)[:100]}")
    # ---- SHORTS (viết LẠI cho 9:16 từ 2-3 chủ đề con) ----
    resumed_short = FB.find_resumable(OWNER, channel, "short")   # CHECKPOINT: phiên trước lỗi/treo nhưng còn kịch bản
    for i, sub in enumerate(subtopics[:n_shorts]):
        if _stopped():   # ⛔ đã xong clip trước -> ngừng, KHÔNG bắt đầu clip mới (tiết kiệm, không dở dang).
            print(f"   ⛔ {channel}: dừng theo yêu cầu — xong clip hiện tại, bỏ {n_shorts - i} short còn lại."); break
        sjob = FB.new_job(OWNER, channel, "short", pver=PVER)
        sst = lambda s, step, **x: FB.update_job(sjob, status=s, step=step, **x)
        story = sok = sinfo = None; serr = None
        resume_story = (resumed_short or {}).get("story")   # chỉ short ĐẦU tiên dùng, các short sau viết mới bình thường (chủ đề khác)
        for satt in (1, 2):                                # SELF-HEAL: thử lại 1 lần nếu lỗi
            try:
                sout = os.path.join("out", DS.slug(channel) + f"_short{i}.mp4")
                if satt > 1:
                    sst("running", "🔧 Tự thử lại short…"); resume_story = None
                _, story, sok, sinfo = DS.make_video(channel, sub, "short", sout, keys=keys, tier=tier, on_status=sst, on_limit=cool, on_ok=okcb, resume_story=resume_story,
                                                      accent=ch.get("accent", "#22D3EE"), accent2=ch.get("accent2", "#F5B301"))
                serr = None; break
            except (Exception, SystemExit) as e:
                serr = e; traceback.print_exc(); print(f"   🔧 SHORT {channel}#{i} lỗi lần {satt}: {str(e)[:100]}")
        if resumed_short:
            FB.clear_resumed(resumed_short["job_id"]); resumed_short = None
        if serr is not None and _is_ratelimit(serr):
            sst("ratelimited", "⏳ hết quota tạm — thử lại sau"); R["rl"] = R.get("rl", 0) + 1   # KHÔNG tính Lỗi
        elif serr is not None:
            sst("failed", f"Tự thử lại vẫn lỗi: {str(serr)[:110]}"); R["fails"].append(f"{channel} SHORT {i}: {str(serr)[:100]}")
        elif sok:
            eq = enqueue_drive(channel, sout, story, "short")
            did = (eq or {}).get("id"); acc = (eq or {}).get("account", "")
            sst("done", "Short đã đẩy Drive" if did else "Short xong (chưa đẩy Drive)", title=story.get("title"),
                description=_desc_src(story), hashtags=story.get("hashtags") or [], tags=story.get("tags") or [],  # cho auto-enqueue
                score=(story.get("self_score") or {}).get("total"),
                dur=(sinfo or {}).get("dur", 0), size_mb=(sinfo or {}).get("size_mb", 0), res=(sinfo or {}).get("res", ""),
                drive_id=did or "", drive_account=acc, thumb_id=(eq or {}).get("thumb_id", ""), preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""),
                script=_script_json({k: v for k, v in story.items() if k != "_thumb"})); R["done"] += 1; R["done_short"] = R.get("done_short", 0) + 1
        else:
            sst("failed", f"QC short trượt: {sinfo}"); R["fails"].append(f"{channel} SHORT {i}: QC trượt")
    print(f"   ✅ {channel}: xong long + {min(n_shorts, len(subtopics))} short")


def _trash_old(account_name, file_id):
    """Đưa file CŨ vào thùng rác Drive (render lại -> thay thế đúng bản đó)."""
    if not (account_name and file_id):
        return False
    try:
        src = os.environ.get("AUTOPUBLISHER_SRC")
        if src and src not in sys.path:
            sys.path.insert(0, src)
        import storage as ST
        for a in ST.pool_accounts():
            if a.get("name") == account_name:
                ST.account_drive(a).svc.files().update(fileId=file_id, body={"trashed": True}).execute()
                print(f"   🗑 đã bỏ bản cũ {file_id} (kho {account_name})"); return True
    except Exception as e:
        print("   ⚠️ bỏ bản cũ lỗi:", str(e)[:90])
    return False


def _dispatch_short(ch, fmt, cat, out, keys, tier, jst, cool, okcb, resume_story=None, avoid=None):
    """ĐỊNH TUYẾN SHORT theo format của kênh — NGUỒN DUY NHẤT, dùng chung cho cả render thường
    (run_one) lẫn render lại (process_requests, nút 🔄).

    TRƯỚC ĐÂY process_requests LUÔN gọi DS.make_video (engine data-race) bất kể kênh format gì ->
    bấm 🔄 trên 30/40 kênh (doc + motif + wave4) render RA SAI ENGINE hoàn toàn, mất luôn
    accent/style/mode/host_prompt của kênh. Gộp về 1 hàm để 2 đường đi không bao giờ lệch nhau nữa.
    """
    avoid = avoid or []
    if fmt == "doc":     # Wave 2 tài liệu: truyền style/accent riêng của kênh
        return DS.make_doc(ch.get("name"), cat, out, keys=keys, tier=tier,
                           style=ch.get("style", "awe, cinematic"),
                           accent=ch.get("accent", "#22D3EE"), accent2=ch.get("accent2", "#F5B301"),
                           avoid=avoid, on_status=jst, on_limit=cool, on_ok=okcb, resume_story=resume_story,
                           ai_style=ch.get("ai_style"), ai_only=bool(ch.get("ai_only")),
                           music=ch.get("music"),
                           mode=ch.get("mode"), host_prompt=ch.get("host_prompt"))
    # 8 engine đồ hoạ dưới đây nay cũng dựng thumbnail DocThumb (số liệu sốc + câu hỏi mở + nền là
    # KHUNG THẬT rút từ chính video) -> phải truyền accent2 thật, nếu không số liệu 9 kênh sẽ cùng
    # một màu mặc định = nhìn như hàng loạt.
    if fmt in ("swarm", "pulse", "clockwork", "longshot"):   # Wave 4: 1 accent riêng/kênh
        mk4 = {"swarm": DS.make_swarm, "pulse": DS.make_pulse,
               "clockwork": DS.make_clockwork, "longshot": DS.make_longshot}[fmt]
        _defacc = {"swarm": "#0D9488", "pulse": "#EA580C", "clockwork": "#C2410C", "longshot": "#4F46E5"}[fmt]
        _def2 = {"swarm": "#F0ABFC", "pulse": "#FCA5A5", "clockwork": "#FCD34D", "longshot": "#A5B4FC"}[fmt]
        return mk4(ch.get("name"), cat, out, keys=keys, tier=tier, accent=ch.get("accent", _defacc),
                   accent2=ch.get("accent2", _def2),
                   avoid=avoid, on_status=jst, on_limit=cool, on_ok=okcb, resume_story=resume_story)
    if fmt in ("guess", "mapped", "ranked", "scaled", "thennow"):
        mk = {"guess": DS.make_guess, "mapped": DS.make_mapped, "ranked": DS.make_ranked,
              "scaled": DS.make_scaled, "thennow": DS.make_thennow}[fmt]
        if fmt == "guess":                                   # GUESS chưa nhận accent (bố cục câu đố riêng)
            return mk(ch.get("name"), cat, out, keys=keys, tier=tier,
                      avoid=avoid, on_status=jst, on_limit=cool, on_ok=okcb, resume_story=resume_story)
        _da = {"mapped": "#059669", "ranked": "#D946EF", "scaled": "#0284C7", "thennow": "#9333EA"}[fmt]
        _d2 = {"mapped": "#FDBA74", "ranked": "#67E8F9", "scaled": "#FDE68A", "thennow": "#86EFAC"}[fmt]
        return mk(ch.get("name"), cat, out, keys=keys, tier=tier,
                  accent=ch.get("accent", _da), accent2=ch.get("accent2", _d2),
                  avoid=avoid, on_status=jst, on_limit=cool, on_ok=okcb, resume_story=resume_story)
    # format trống = 10 kênh GỐC data-race
    return DS.make_video(ch.get("name"), cat, "short", out, keys=keys, tier=tier,
                         on_status=jst, on_limit=cool, on_ok=okcb, resume_story=resume_story,
                         accent=ch.get("accent", "#22D3EE"), accent2=ch.get("accent2", "#F5B301"))


def process_requests(keys, report):
    """YÊU CẦU RENDER LẠI (nút 🔄): render lại đúng chủ đề -> đẩy Drive -> BỎ bản cũ (thay thế).

    DÙNG LẠI KỊCH BẢN ĐÃ LƯU của chính video cũ (get_script_by_drive) -> KHỎI gọi Gemini: đúng
    mục đích "giữ kịch bản để sau có vấn đề thì render lại được" (không tốn quota, ra ĐÚNG nội
    dung cũ). Không có kịch bản (video render trước 19/8, chưa có tính năng) -> viết mới như cũ.
    Và định tuyến engine qua _dispatch_short theo format THẬT của kênh (trước đây luôn ép
    make_video = engine data-race -> bấm 🔄 ở 30/40 kênh ra sai engine + mất accent/style/mode).
    """
    chans = {(c.get("name") or "").upper(): c for c in FB.read_channels(OWNER)}
    for req in FB.read_render_requests(OWNER):
        ch = req.get("channel"); typ = req.get("type", "short"); seed = req.get("seed", "")
        if not (ch and seed):
            FB.mark_request_done(req["id"], "thiếu thông tin"); continue
        FB.mark_request_status(req["id"], "processing")   # KHÓA hủy: đã bắt đầu render lại
        cfg = chans.get(str(ch).upper()) or {"name": ch}
        fmt = (cfg.get("format") or "").lower()
        job = FB.new_job(OWNER, ch, typ, pver=PVER)
        st = lambda s, step, **x: FB.update_job(job, status=s, step=step, **x)
        cool = lambda kid, mins=90: FB.cool_key(kid, mins)   # giới hạn PHÚT -> nghỉ ngắn; quota NGÀY -> 90'
        try:
            # GIỌNG RIÊNG của kênh (giống run_one) — thiếu bước này thì bản render lại đọc giọng
            # mặc định, khác hẳn các video còn lại của kênh.
            try:
                import tts_karaoke as _TK
                _TK.set_voice(cfg.get("voice"), cfg.get("voice_rate"))
            except Exception:
                pass
            old = FB.get_script_by_drive(OWNER, req.get("replace_id"))
            st("running", ("♻️ Render lại (dùng kịch bản cũ): " if old else "🔄 Render lại: ") + seed[:40])
            out = os.path.join("out", DS.slug(ch) + "_rr.mp4")
            if typ == "long":
                _, plan, _subs, ok, info, _stories = DS.make_long(
                    ch, seed, out, keys=keys, on_status=st, on_limit=cool, n_races=4,
                    resume_checkpoint=(old if isinstance(old, dict) and old.get("races") else None),
                    accent=cfg.get("accent", "#22D3EE"), accent2=cfg.get("accent2", "#F5B301"))
                story = {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"), "description": plan.get("hook", "")}
                script = _script_json({"pillar_title": plan.get("pillar_title"), "hook": plan.get("hook"), "races": _stories})
            else:
                _, story, ok, info = _dispatch_short(
                    cfg, fmt, seed, out, keys, cfg.get("tier", "normal"), st, cool, None,
                    resume_story=(old if isinstance(old, dict) and not old.get("races") else None))
                script = _script_json({k: v for k, v in story.items() if k != "_thumb"})
            if ok:
                if info and info.get("thumb"): story["_thumb"] = info["thumb"]   # thumbnail DocThumb đẹp (giống run_one)
                eq = enqueue_drive(ch, out, story, typ)
                did = (eq or {}).get("id"); acc = (eq or {}).get("account", "")
                _trash_old(req.get("replace_account"), req.get("replace_id"))
                FB.delete_jobs_by_drive(OWNER, req.get("replace_id"))   # dọn job cũ (bản đã bị thay thế)
                st("done", "Render lại xong — đã thay thế bản cũ", title=story.get("title"),
                   dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0), res=(info or {}).get("res", ""),
                   drive_id=did or "", drive_account=acc, thumb_id=(eq or {}).get("thumb_id", ""), preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""),
                   script=script)
                report["done"] += 1; FB.mark_request_done(req["id"], "done")
            else:
                st("failed", f"Render lại QC trượt: {info}"); FB.mark_request_done(req["id"], "qc-trượt")
        except (Exception, SystemExit) as e:
            traceback.print_exc(); st("failed", str(e)[:120]); FB.mark_request_done(req["id"], "lỗi")


def main():
    if not OWNER:
        raise SystemExit("❌ Thiếu OWNER_UID (uid chủ — set ở workflow).")
    cfg = FB.read_config(OWNER)
    # 🔎 Trend Scout "Quét ngay" từ dashboard: lồng vào ĐÚNG nhịp poll 30' đã có sẵn -> KHÔNG tạo Actions run mới.
    if cfg.get("trend_scout_run_now"):
        FB.set_config(OWNER, {"trend_scout_run_now": None})
        print("🔎 Nhận lệnh 'Quét trend ngay' từ dashboard.")
        try:
            import trend_scout
            trend_scout.main()
        except BaseException as e:
            print(f"⚠️ trend_scout lỗi (bỏ qua, không ảnh hưởng render): {e}")
    # NHỊP 30': chỉ chạy khi có lệnh "Render ngay" (run_now) HOẶC đúng giờ mẻ đêm (18h UTC).
    from datetime import datetime, timezone, timedelta
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    run_now = bool(cfg.get("run_now"))
    # 20/8: cron khai báo mỗi 10' nhưng GitHub Actions THỰC TẾ hay trễ 30-50' (nghẽn nền tảng, quan sát
    # nhiều lần đêm nay) -> cửa sổ cũ minute<25 bị TRƯỢT HẲN mẻ 04h UTC (lần chạy trước 03:55, lần sau
    # 04:28, đều ngoài [xx:00,xx:25)). Nới lên minute<55 (gần hết giờ) để chịu được độ trễ lịch thực tế,
    # vẫn an toàn không lấn giờ mẻ kế (batch_hours cách nhau ít nhất 4h).
    is_nightly = (datetime.now(timezone.utc).hour in (cfg.get("batch_hours") or [0, 4, 8, 12, 16, 20])
                  and datetime.now(timezone.utc).minute < 55)
    if event == "schedule" and not run_now and not is_nightly:
        print("⏭ Nhịp kiểm 30' — không có lệnh Render ngay, bỏ qua (free)."); return
    if run_now:
        FB.set_config(OWNER, {"run_now": None, "run_now_done_at": datetime.now(timezone.utc).isoformat()})
        print("⚡ Nhận lệnh 'Render ngay' từ dashboard.")
    if not cfg.get("enabled") and os.environ.get("FORCE") != "1" and not run_now:
        print("⏸ Pipeline đang TẮT — bật ở tab Render Studio, hoặc bấm Render ngay."); return
    keys = FB.read_keys(OWNER)
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key — thêm ở tab 🎬 Render Studio.")
    # HEALTH CHECK — TIẾT KIỆM: mỗi key tối đa 1 lần/~20h (tránh spam list_models -> limit + tốn quota).
    # Key nào đã check trong 20h (kể cả tự-đánh-dấu-sống lúc VIẾT thật) -> BỎ QUA.
    import content_brain as CB
    dead_keys = []
    fresh = (datetime.now(timezone.utc) - timedelta(hours=20)).isoformat()
    for k in FB.read_keys(OWNER, include_cooling=True):
        if k.get("last_checked") and k["last_checked"] > fresh:
            continue                 # còn tươi -> khỏi test lại, đỡ tốn
        alive, reason = CB.test_key(k["key"])
        if alive is None:            # KHÔNG chắc (lỗi tạm) -> giữ trạng thái cũ, tránh báo chết OAN
            print(f"   … key {k.get('email') or k['id']}: {reason}")
            continue
        FB.mark_key_alive(k["id"], alive, reason)
        if not alive:
            dead_keys.append(f"{k.get('email') or k['id']} — {reason[:70]}")
    if dead_keys:
        print(f"⚠️ {len(dead_keys)} Gemini key CHẾT: {dead_keys}")
    channels = [c for c in FB.read_channels(OWNER) if c.get("name")]
    if not channels:
        print("⚠️ Chưa cấu hình kênh render nào (thêm ở tab Render Studio)."); return
    # AN TOÀN dự trữ (chỉnh được ở dashboard): mức giữ mỗi kênh khi target=0.
    global RESERVE_LONG, RESERVE_SHORT
    RESERVE_LONG = int(cfg.get("reserve_long", RESERVE_LONG) or RESERVE_LONG)
    RESERVE_SHORT = int(cfg.get("reserve_short", RESERVE_SHORT) or RESERVE_SHORT)
    # ---- GUARD KHO GẦN ĐẦY: render là làm DỰ TRỮ, nhưng kho đầy thì NGỪNG (tránh phình + lỗi ghi khi hết chỗ) ----
    safety_pct = float(cfg.get("drive_safety_pct", DRIVE_SAFETY_PCT) or DRIVE_SAFETY_PCT)
    used, cap = FB.drive_usage(OWNER)
    if cap and used / cap >= safety_pct:
        note = (f"⛔ Kho Drive {used/cap*100:.0f}% đầy (ngưỡng an toàn {safety_pct*100:.0f}%) — NGỪNG render mẻ này "
                f"để tránh phình/lỗi. Thêm tài khoản Drive (Storage→Connect) hoặc upload+dọn bớt rồi chạy lại.")
        print(note)
        FB.set_config(OWNER, {"last_safety_stop": note, "last_safety_at": datetime.now(timezone.utc).isoformat()})
        try:
            import alert_email; alert_email.send_alert("⛔ MM0 Render dừng: kho Drive gần đầy", note)
        except Exception: pass
        return
    FB.set_config(OWNER, {"last_safety_stop": None})   # kho ổn -> xoá cảnh báo cũ
    max_run = int(cfg.get("max_per_run", 0) or 0)   # 0 = không giới hạn; >0 = dừng sau N video/lần
    FB.set_config(OWNER, {"stop": None})             # xoá cờ dừng cũ khi bắt đầu run mới
    print(f"▶ Pipeline: {len(channels)} kênh · {len(keys)} key" + (f" · tối đa {max_run} video" if max_run else ""))
    report = {"done": 0, "fails": []}
    process_requests(keys, report)   # 🔄 xử lý yêu cầu render lại (thay thế bản cũ) TRƯỚC
    for ch in channels:
        if FB.read_config(OWNER).get("stop"):        # ⛔ nút Dừng ngay trên dashboard
            FB.set_config(OWNER, {"stop": None}); print("⛔ Dừng theo yêu cầu — ngưng các kênh còn lại."); break
        try:
            run_one(ch, keys, report=report)         # 1 kênh lỗi (kể cả SystemExit) KHÔNG được giết cả mẻ
        except BaseException as e:
            traceback.print_exc(); report["fails"].append(f"{ch.get('name')}: {str(e)[:120]}")
        if max_run and report["done"] >= max_run:
            print(f"🎯 Đạt {max_run} video/lần chạy — dừng."); break
    print(f"✅ Xong: {report['done']} video · {len(report['fails'])} lỗi.")
    # EMAIL CẢNH BÁO — chống spam: CHỈ gửi khi CÓ LỖI, gộp 1 email cho cả lần chạy.
    if report["fails"] or dead_keys:
        try:
            import alert_email
            lines = []
            if dead_keys:
                lines.append(f"🔴 {len(dead_keys)} Gemini key CHẾT (cần thay/xoá): " + ", ".join(dead_keys))
            lines += ["❌ " + f for f in report["fails"]]
            body = (f"MM0 Render Factory — {report['done']} video xong:\n\n" + "\n".join(lines)
                    + "\n\nXem chi tiết: https://mm0-auto-publisher.web.app/#render")
            alert_email.send_alert(f"⚠️ MM0 Render: {len(report['fails'])} lỗi · {len(dead_keys)} key chết", body)
        except Exception as e:
            print(f"   ⚠️ email lỗi: {e}")


def gate_mode():
    """KIỂM NHANH (read-only, nhẹ) có nên chạy mẻ này không -> workflow bỏ qua setup nặng lúc nhịp 30' (free)."""
    from datetime import datetime, timezone
    run = "false"
    if OWNER:
        try:
            cfg = FB.read_config(OWNER)
            event = os.environ.get("GITHUB_EVENT_NAME", "")
            run_now = bool(cfg.get("run_now"))
            enabled = bool(cfg.get("enabled")) or os.environ.get("FORCE") == "1"
            # MỞ PHIÊN MỚI ngay khi phiên trước XONG HẲN (còn job active ở B thì chưa) — KHÔNG còn ép đúng giờ cố định
            # (0/4/8/12/16/20 UTC): với round-cap, phiên tự xong sớm (10 long/30 short/kênh) rồi để trống luồng
            # tới giờ cố định tiếp theo là lãng phí. Chỉnh session_gap_min ở render_config nếu muốn thưa hơn.
            #
            # ⚠️ ĐỪNG THÊM LẠI has_active_render() VÀO ĐÂY (đã gỡ 20/8).
            # Nó đọc render_jobs để đoán "có phiên đang chạy không" — nhưng đó là SUY ĐOÁN từ dữ liệu
            # có thể sai (job ma do tiến trình chết đột ngột), và MỌI lần dây chuyền đứng hôm nay đều
            # do nó: 39 job ma khoá cổng 6 tiếng, rồi 10 job ma khoá thêm 5 tiếng nữa. Vá bằng cách
            # rút mốc phát hiện job chết xuống 30' thì lại sinh lỗi mới: health_guardian giết nhầm 15
            # job đang render khoẻ mạnh.
            # Việc chặn chồng phiên KHÔNG cần suy đoán: GitHub concurrency (group mm0-render-cron,
            # cancel-in-progress:false) BẢO ĐẢM ở tầng hạ tầng rằng lượt mới xếp hàng chờ lượt cũ xong.
            # Cổng này chỉ cần giữ đúng một việc: sàn nghỉ tối thiểu giữa 2 phiên.
            last = cfg.get("last_session_at", ""); gap_min = int(cfg.get("session_gap_min", SESSION_GAP_MIN) or SESSION_GAP_MIN); recently = False
            if last:
                try:
                    elapsed_min = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 60
                    recently = elapsed_min < gap_min
                except Exception: recently = False
            batch_ok = not recently
            if ((event != "schedule") or run_now or batch_ok) and (enabled or run_now):
                run = "true"
        except Exception:
            traceback.print_exc()
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"run={run}\n")
    print(f"GATE run={run}")


# Mốc bản vá xoay key vẽ ảnh (commit "Ve anh AI + Vision QC xoay vong 56 key"). Video của kênh
# ai_only tạo TRƯỚC mốc này ra đời khi MỌI lời gọi vẽ ảnh đều 429 -> mọi cảnh bị hạ xuống thẻ chữ
# nền cosmic, không có ảnh nào. Đo thật: 0 ảnh vẽ được / 209 lần lỗi (21/8) và 0/158 (20/8).
AI_IMG_FIXED_AT = "2026-08-21T12:30:00+00:00"
SWEEP_PER_SESSION = 12      # trần mỗi phiên: render lại vẫn tốn thời gian, không để nó nuốt cả mẻ mới


def sweep_ai_quality(all_ch, cfg):
    """Xếp hàng render lại cho video KHÔNG ĐẠT CHUẨN của các kênh vẽ ảnh AI.

    Chỉ TẠO YÊU CẦU, không tự render: process_requests ở đầu phiên kế sẽ dựng lại từ kịch bản đã
    lưu (không tốn quota Gemini viết bài, ra đúng nội dung cũ), đẩy Drive rồi BỎ bản cũ vào thùng
    rác + xoá bản ghi job -> phần dọn dẹp nằm sẵn trong luồng đó.
    Rải tối đa SWEEP_PER_SESSION mỗi phiên cho tới hết, rồi tự tắt bằng cờ trong config."""
    if cfg.get("ai_img_sweep_done"):
        return
    # MỌI kênh doc-format đều dính, không riêng kênh vẽ AI: bản cũ dựng 2 thẻ chữ (intro/outro),
    # cảnh mở đầu không có footage, và mỗi cảnh đứng yên 1 ảnh 6-8s. ai_only nặng nhất (0 ảnh nào)
    # nhưng kênh doc thường cũng không đạt chuẩn DATARACE -> quét hết.
    targets = [c for c in all_ch
               if c.get("name") and (c.get("ai_only") or (c.get("format") or "").lower() == "doc")]
    if not targets:
        FB.set_config(OWNER, {"ai_img_sweep_done": True}); return
    pending = {r.get("replace_id") for r in FB.read_render_requests(OWNER) if r.get("replace_id")}
    made, seen_any = 0, False
    for c in targets:
        if made >= SWEEP_PER_SESSION:
            break
        for j in FB.find_done_before(OWNER, c["name"], "short", AI_IMG_FIXED_AT,
                                     limit=SWEEP_PER_SESSION - made):
            seen_any = True
            did = j.get("drive_id") or ""
            if did and did in pending:
                continue
            rid = FB.new_render_request(OWNER, c["name"], j.get("type") or "short",
                                        j.get("title") or j.get("topic") or "",
                                        did, j.get("drive_account") or "")
            FB.mark_job_requeued(j["id"], rid)
            made += 1
            if made >= SWEEP_PER_SESSION:
                break
    if made:
        print(f"   ♻️ Xếp render lại {made} video chưa đạt chuẩn (kênh doc-format) — phiên sau xử lý.")
    elif not seen_any:
        FB.set_config(OWNER, {"ai_img_sweep_done": True})
        print("   ✅ Đã xử lý xong toàn bộ video tồn chưa đạt chuẩn.")


def plan_mode():
    """ĐIỀU PHỐI (matrix 10 luồng): gating + health-check + re-render — CHẠY 1 LẦN — rồi xuất danh sách kênh
    cho các job render song song. Các job render KHÔNG lặp health-check/re-render (đỡ tốn API)."""
    import json
    from datetime import datetime, timezone, timedelta
    def out_channels(lst):
        payload = json.dumps(lst)
        gh = os.environ.get("GITHUB_OUTPUT")
        if gh:
            with open(gh, "a") as f:
                f.write(f"channels={payload}\n")
        print(f"PLAN channels={payload}")
    if not OWNER:
        out_channels([]); raise SystemExit("❌ Thiếu OWNER_UID.")
    cfg = FB.read_config(OWNER)
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    run_now = bool(cfg.get("run_now"))
    # MỞ PHIÊN MỚI ngay khi phiên trước XONG HẲN — xem giải thích đầy đủ trong gate_mode().
    last = cfg.get("last_session_at", ""); gap_min = int(cfg.get("session_gap_min", SESSION_GAP_MIN) or SESSION_GAP_MIN); recently = False
    if last:
        try:
            elapsed_min = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 60
            recently = elapsed_min < gap_min
        except Exception: recently = False
    if event == "schedule" and not run_now and recently:
        print("⏭ Nhịp kiểm — phiên gần đây còn trong hạn nghỉ, bỏ qua (free)."); return out_channels([])
    FB.set_config(OWNER, {"last_session_at": datetime.now(timezone.utc).isoformat()})   # đánh dấu phiên bắt đầu -> chống trùng
    if run_now:
        FB.set_config(OWNER, {"run_now": None, "run_now_done_at": datetime.now(timezone.utc).isoformat()})
        print("⚡ Nhận lệnh 'Render ngay'.")
    if not cfg.get("enabled") and os.environ.get("FORCE") != "1" and not run_now:
        print("⏸ Pipeline TẮT — bật ở Render Studio hoặc bấm Render ngay."); return out_channels([])
    all_keys = FB.read_keys(OWNER, include_cooling=True)   # TẤT CẢ (kể cả chết/cooling) -> health-check test hết
    if not all_keys:
        print("❌ Chưa có Gemini key."); return out_channels([])
    # HEALTH CHECK (throttled 20h) — chỉ ở plan, 10 luồng không lặp. Chạy TRƯỚC khi lọc key sống -> key vừa hồi được nhận lại.
    import content_brain as CB
    now_iso = datetime.now(timezone.utc).isoformat()
    force_health = bool(cfg.get("force_health"))   # nút "Kiểm key NGAY" -> bỏ qua giới hạn, test LẠI HẾT (kể cả chết hẳn)
    fresh = (datetime.now(timezone.utc) - timedelta(hours=20)).isoformat()
    perm_fresh = (datetime.now(timezone.utc) - timedelta(hours=int(cfg.get("perm_recheck_hours", 168) or 168))).isoformat()  # chết hẳn: test lại mỗi ~7 ngày (phòng check NHẦM / Google mở lại)
    dead = []
    import time as _t
    _PERM = ("denied", "suspended", "invalid", "permission", "forbidden", "401", "not valid", "unregistered")
    MAX_CHECK = int(cfg.get("health_max_per_cycle", 12) or 12)   # test tối đa N key/mẻ (rải qua nhiều mẻ) -> KHÔNG dội cả loạt = chống burst
    tested = 0
    for k in all_keys:
        # CHẾT HẲN -> KHÔNG test mỗi mẻ (đỡ phí), NHƯNG vẫn test lại HIẾM (mỗi ~7 ngày) -> phòng check nhầm / Google mở khoá lại -> không mất oan.
        if k.get("dead_kind") == "permanent" and not force_health and (k.get("last_checked", "") or "") > perm_fresh:
            continue
        if k.get("dead_kind") != "permanent" and k.get("last_checked") and k["last_checked"] > fresh and not force_health:
            continue
        if tested >= MAX_CHECK and not force_health:
            break                                       # đủ N/mẻ -> phần còn lại để mẻ SAU (health-check rải đều, không spam)
        if tested:
            _t.sleep(0.5)                               # GIÃN giữa mỗi test -> không burst -> tránh dội server/bị coi spam
        alive, reason = CB.test_key(k["key"])
        tested += 1
        if alive is None:
            continue
        kind = "permanent" if (not alive and any(s in (reason or "").lower() for s in _PERM)) else ""
        FB.mark_key_alive(k["id"], alive, reason, kind=kind)
        if not alive:
            dead.append(f"{k.get('email') or k['id']} — {reason[:70]}{' [CHẾT HẲN]' if kind else ''}")
    if dead:
        print(f"⚠️ {len(dead)} Gemini key CHẾT: {dead}")
    if force_health:
        try: FB.set_config(OWNER, {"force_health": None, "force_health_done_at": now_iso})   # đã kiểm xong -> tắt cờ
        except Exception: pass
    # CẢNH BÁO KEY CHẾT — 2 MỨC: ⚠️ >warn_h (72h, THEO DÕI, có thể còn tự mở) · 🔴 >repl_h (7 ngày, THAY NGAY, chết hẳn).
    warn_h = int(cfg.get("dead_key_warn_hours", 72) or 72)
    repl_h = int(cfg.get("dead_key_replace_hours", 168) or 168)
    warn_cut = (datetime.now(timezone.utc) - timedelta(hours=warn_h)).isoformat()
    repl_cut = (datetime.now(timezone.utc) - timedelta(hours=repl_h)).isoformat()
    dead_all = [(k.get("email") or k["id"], k.get("dead_since", ""))
                for k in FB.read_keys(OWNER, include_cooling=True)
                if k.get("alive") is False and k.get("dead_since")]
    repl = [x for x in dead_all if x[1] < repl_cut]                     # chết > repl_h
    warn = [x for x in dead_all if repl_cut <= x[1] < warn_cut]         # chết trong [warn_h, repl_h)
    FB.set_config(OWNER, {"stale_keys_warn": [e for e, _ in warn],
                          "stale_keys_replace": [e for e, _ in repl], "stale_keys_at": now_iso})
    if warn or repl:
        parts = []
        if repl:
            parts.append(f"🔴 {len(repl)} key CHẾT quá {repl_h // 24} ngày — THAY NGAY (project chết hẳn):\n"
                         + "\n".join(f"  • {e} (chết từ {d[:16]})" for e, d in repl))
        if warn:
            parts.append(f"⚠️ {len(warn)} key chết quá {warn_h}h — THEO DÕI (có thể còn tự mở lại):\n"
                         + "\n".join(f"  • {e} (chết từ {d[:16]})" for e, d in warn))
        msg = "\n\n".join(parts) + "\n\nQuản lý key: https://mm0-auto-publisher.web.app/#render (tab Render → Key API)."
        print(msg)
        subj = (f"🔴 MM0: {len(repl)} key cần THAY NGAY" if repl else f"⚠️ MM0: {len(warn)} key chết >{warn_h}h theo dõi")
        try:
            import alert_email; alert_email.send_alert(subj, msg)
        except Exception:
            pass
    keys = FB.read_keys(OWNER)   # key SỐNG dùng được (sau health-check -> gồm key vừa hồi)
    if not keys:
        note = "⚠️ KHÔNG còn Gemini key SỐNG nào — thêm/thay key ở Render Studio."
        print(note)
        try:
            import alert_email; alert_email.send_alert("⚠️ MM0 Render dừng: hết key Gemini sống", note)
        except Exception:
            pass
        return out_channels([])
    global RESERVE_LONG, RESERVE_SHORT
    RESERVE_LONG = int(cfg.get("reserve_long", RESERVE_LONG) or RESERVE_LONG)
    RESERVE_SHORT = int(cfg.get("reserve_short", RESERVE_SHORT) or RESERVE_SHORT)
    # ĐỒNG BỘ dung lượng THẬT mọi kho -> storage_accounts.used. TIẾT KIỆM: chỉ ~1 lần/20h (không mỗi phiên) — 37 ghi Firestore.
    _sync_fresh = (datetime.now(timezone.utc) - timedelta(hours=20)).isoformat()
    if (cfg.get("usage_synced_at") or "") > _sync_fresh:
        pass   # đã sync trong 20h -> bỏ qua (dùng nút 🔄 Đồng bộ dung lượng trên dashboard nếu cần ngay)
    else:
      try:
        # storage.py nằm trong repo AutoPublisher (checkout vào _autopublisher/src) -> PHẢI nạp path
        # trước khi import. Thiếu dòng này thì plan_mode chết ngay "No module named 'storage'" và
        # NGUYÊN khâu đồng bộ dung lượng kho không bao giờ chạy -> storage_accounts.used đứng yên,
        # guard "kho gần đầy" chấm trên số cũ. (Lỗi âm thầm vì đã bọc try/except.)
        _src = os.environ.get("AUTOPUBLISHER_SRC")
        if _src and _src not in sys.path:
            sys.path.insert(0, _src)
        import storage as ST
        synced = 0
        for acc in ST.pool_accounts():
            if acc.get("owner") and acc["owner"] != OWNER:
                continue
            try:
                stt = ST.account_status(acc)
                FB.update_storage_used(OWNER, acc["name"], stt.get("used", 0), acc.get("cap_gb"))
                synced += 1
            except Exception:
                pass
        FB.set_config(OWNER, {"usage_synced_at": datetime.now(timezone.utc).isoformat()})
        print(f"   💾 Đã đồng bộ dung lượng thật {synced} kho.")
      except Exception as e:
        print(f"   ⚠️ Sync dung lượng kho lỗi: {e}")
    # GUARD KHO GẦN ĐẦY (tính tổng cả 33 kho, dùng số VỪA sync).
    safety_pct = float(cfg.get("drive_safety_pct", DRIVE_SAFETY_PCT) or DRIVE_SAFETY_PCT)
    used, cap = FB.drive_usage(OWNER)
    if cap and used / cap >= safety_pct:
        note = (f"⛔ Kho Drive {used/cap*100:.0f}% đầy (ngưỡng {safety_pct*100:.0f}%) — NGỪNG render mẻ này. "
                f"Thêm tài khoản Drive hoặc upload+dọn bớt rồi chạy lại.")
        print(note)
        FB.set_config(OWNER, {"last_safety_stop": note, "last_safety_at": datetime.now(timezone.utc).isoformat()})
        try:
            import alert_email; alert_email.send_alert("⛔ MM0 Render dừng: kho Drive gần đầy", note)
        except Exception:
            pass
        return out_channels([])
    FB.set_config(OWNER, {"last_safety_stop": None, "stop": None})   # kho ổn + xoá cờ dừng cũ
    try:
        process_requests(keys, {"done": 0, "fails": []})   # 🔄 render lại (thay bản cũ) — 1 lần ở plan
    except Exception:
        traceback.print_exc()
    all_ch = [c for c in FB.read_channels(OWNER) if c.get("name")]
    try:
        sweep_ai_quality(all_ch, cfg)   # xếp render lại các video ra đời khi bước vẽ ảnh AI còn hỏng
    except Exception:
        traceback.print_exc()
    channels = [c["name"] for c in all_ch if not c.get("paused")]   # ⏸ kênh PAUSE -> KHÔNG vào matrix (không làm mẻ mới)
    # XÁO THỨ TỰ mỗi phiên: Firestore trả channels theo ID tài liệu (~alphabet cố định) -> KHÔNG xáo thì cùng nhóm
    # đầu bảng chữ cái LUÔN vào 18 slot đầu (ưu tiên), nhóm cuối LUÔN bị đẩy xuống chờ mỗi phiên -> thiên vị có hệ
    # thống. Xáo ngẫu nhiên -> mỗi phiên 1 nhóm khác được ưu tiên, công bằng thật sự về lâu dài.
    random.shuffle(channels)
    n_paused = len(all_ch) - len(channels)
    # 20/8: comment ở trên ("18 slot đầu") LUÔN giả định matrix chỉ có tối đa MAX_MATRIX kênh/phiên — nhưng
    # code TRƯỚC ĐÂY gửi NGUYÊN list (không cắt) -> khi tổng kênh > max-parallel (18, YAML), GitHub KHÔNG bỏ
    # qua phần dư mà XẾP HÀNG chạy tiếp đợt 2/3 NỐI TIẾP trong CÙNG workflow run -> 1 "phiên" kéo dài
    # 7-10+ tiếng (40 kênh/18 = 3 đợt × ~3.5h) thay vì ~3.5h như thiết kế, giữ khoá concurrency quá lâu,
    # nuốt mất cơ hội của các mẻ 4h kế tiếp -> tổng video/ngày sụt hẳn dù không lỗi gì. Cắt về đúng
    # MAX_MATRIX (khớp max-parallel YAML) -> mỗi phiên LUÔN 1 đợt, xong đúng hạn, nhường lượt sòng phẳng
    # cho phiên sau (đã xáo ngẫu nhiên nên nhóm bị cắt lần này ưu tiên lần sau).
    MAX_MATRIX = 18   # PHẢI khớp strategy.max-parallel trong .github/workflows/render_cron.yml

    # CHỈ XẾP KÊNH CÒN VIỆC — 20/8: trước đây lấy đại 18 kênh mà KHÔNG xét kênh nào đã đủ chỉ tiêu.
    # Kênh đủ target vẫn được cấp 1 slot, job khởi động rồi thoát ngay -> nhìn dashboard thấy "đang
    # chạy 3" trong khi đã cấp 18 slot: phí 15 luồng mỗi phiên. Đếm phần CÒN THIẾU trước (count_done
    # dùng aggregation, ~1 read/kênh nên rẻ), bỏ kênh đã đủ, rồi ưu tiên kênh thiếu NHIỀU nhất.
    _by_ch = {c.get("name"): c for c in all_ch}
    need = []
    for nm in channels:
        c = _by_ch.get(nm) or {}
        lt = int(c.get("long_target", 0) or 0) or RESERVE_LONG
        stt = int(c.get("short_target", 0) or 0) or RESERVE_SHORT
        try:
            nl = max(0, lt - FB.count_done(OWNER, nm, "long")) if c.get("make_long", True) else 0
            ns = max(0, stt - FB.count_done(OWNER, nm, "short"))
        except Exception as e:
            print(f"   ⚠️ đếm {nm} lỗi ({str(e)[:50]}) -> vẫn cho vào hàng"); nl = ns = 1
        if nl + ns > 0:
            need.append((nl + ns, nm))
    n_full = len(channels) - len(need)
    if need:
        need.sort(key=lambda x: -x[0])            # thiếu nhiều -> làm trước, lấp đủ 18 slot
        channels = [nm for _, nm in need]
    else:
        print("🎯 Mọi kênh đã đủ chỉ tiêu — không mở phiên (khỏi đốt runner).")
        return out_channels([])
    if len(channels) > MAX_MATRIX:
        print(f"   ✂️ {len(channels)} kênh còn việc > {MAX_MATRIX} slot -> lấy {MAX_MATRIX} kênh thiếu nhiều nhất, phần còn lại ưu tiên phiên sau.")
        channels = channels[:MAX_MATRIX]
    print(f"▶ {len(channels)} kênh -> render SONG SONG."
          + (f" (⏸ {n_paused} pause)" if n_paused else "")
          + (f" (🎯 {n_full} kênh đã đủ chỉ tiêu, bỏ qua)" if n_full else ""))
    out_channels(channels)


def channel_mode(name):
    """RENDER 1 KÊNH (1 luồng của matrix). Đọc reserve + tôn trọng cờ Dừng (per-clip trong run_one)."""
    if not OWNER:
        raise SystemExit("❌ Thiếu OWNER_UID.")
    cfg = FB.read_config(OWNER)
    global RESERVE_LONG, RESERVE_SHORT
    RESERVE_LONG = int(cfg.get("reserve_long", RESERVE_LONG) or RESERVE_LONG)
    RESERVE_SHORT = int(cfg.get("reserve_short", RESERVE_SHORT) or RESERVE_SHORT)
    if cfg.get("stop"):
        print(f"⛔ Đang dừng — bỏ {name}."); return
    keys = FB.read_keys(OWNER)
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key.")
    one = FB.read_one_channel(OWNER, name)   # 1 read (không đọc cả 15 kênh)
    if not one:
        print(f"⚠️ Kênh {name} không còn (đã xóa) — bỏ."); return
    if one.get("paused"):
        print(f"⏸ {name}: đang PAUSE — bỏ qua (bấm ▶ Chạy để tiếp)."); return
    chs = [one]
    # STAGGER theo kênh (0-18s): 10 luồng KHÔNG gọi Gemini/Drive cùng 1 khoảnh khắc -> đỡ bị coi là burst/lạm dụng.
    import time
    delay = sum(ord(c) for c in name) % 18
    if delay:
        print(f"   ⏳ {name}: giãn {delay}s (chống burst song song)…"); time.sleep(delay)
    report = {"done": 0, "fails": [], "rl": 0}
    # VÒNG LẶP A-Z: làm LIÊN TỤC nhiều mẻ trong 1 phiên tới khi — ĐỦ TARGET / HẾT GIỜ (trừ hao) / HẾT QUOTA / KHO ĐẦY / bấm Dừng.
    budget_s = int(cfg.get("batch_budget_min", 210) or 210) * 60    # ngân sách mềm 1 phiên (mặc định 3.5h -> 6 phiên/ngày không chồng lấn)
    HARD_S = 330 * 60                                               # cứng: timeout workflow 350' - chừa ~20' buffer
    max_run = int(cfg.get("max_per_run", 0) or 0)                   # 0 = ∞ (vòng lặp tự giới hạn theo target/quota/giờ); >0 = trần cứng/kênh/phiên
    # ROUND CAP (xoay vòng công bằng): mỗi kênh làm TỐI ĐA round_long/round_short video RỒI NHƯỜNG SLOT (không cắt ngang —
    # check SAU khi run_one() hoàn tất trọn video). Mặc định 10 long/30 short -> phiên xong sớm hơn, kênh khác kịp có lượt.
    # 0 = không giới hạn round (giữ hành vi cũ, chạy tới hết target/giờ/quota).
    _rl, _rs = cfg.get("round_long"), cfg.get("round_short")        # None (chưa set) = mặc định 10/30; 0 = anh chọn "không giới hạn"
    round_long = int(_rl) if _rl is not None else 10
    round_short = int(_rs) if _rs is not None else 30
    MAX_EMPTY = int(cfg.get("empty_retry", 4) or 4)                 # số vòng LIỀN ra 0 video (do rate-limit) rồi mới chịu ngừng -> quota cạn thật
    start = time.monotonic(); rounds = 0; last_dur = 0; empty_streak = 0
    while True:
        rounds += 1
        remain = min(budget_s, HARD_S) - (time.monotonic() - start)
        need = max(last_dur * 1.3, 20 * 60)    # TRỪ HAO: ước tính mẻ tới = mẻ vừa rồi ×1.3 (tối thiểu 20')
        if rounds > 1 and remain < need:       # còn ít giờ hơn 1 mẻ -> DỪNG, để phiên SAU làm (tránh bị timeout giết giữa chừng = phí)
            print(f"   ⏱ {name}: còn {remain/60:.0f}' < ước tính {need/60:.0f}'/mẻ → DỪNG, phiên sau tự làm tiếp (tránh treo/phí)."); break
        if FB.read_config(OWNER).get("stop"):
            print(f"   ⛔ {name}: có lệnh Dừng → ngừng."); break
        one = FB.read_one_channel(OWNER, name)   # 1 READ/vòng (thay vì 15): bắt PAUSE + đổi target kịp, tiết kiệm Firestore
        if not one:
            print(f"   ⚠️ {name}: kênh đã bị xóa → ngừng."); break
        if one.get("paused"):   # ⏸ PAUSE: clip hiện tại đã XONG (check ở đầu vòng sau) -> dừng, giữ nguyên tiến độ, KHÔNG cắt ngang
            print(f"   ⏸ {name}: đã PAUSE (đã làm xong clip đang dở + upload) → ngừng."); break
        chs = [one]
        before = report["done"]; before_rl = report.get("rl", 0); t0 = time.monotonic()
        try:
            run_one(chs[0], keys, report=report)
        except BaseException as e:
            traceback.print_exc()
            (report.__setitem__("rl", report.get("rl", 0) + 1) if _is_ratelimit(e) else report["fails"].append(f"{name} vòng {rounds}"))
        last_dur = time.monotonic() - t0
        made = report["done"] - before; rl = report.get("rl", 0) - before_rl
        if made > 0:
            empty_streak = 0
            if max_run and report["done"] >= max_run:
                print(f"   🎯 {name}: đạt trần {max_run} video/phiên → ngừng."); break
            dl, ds = report.get("done_long", 0), report.get("done_short", 0)
            if (round_long and dl >= round_long) or (round_short and ds >= round_short):
                print(f"   🔁 {name}: đạt round {dl} long/{ds} short (trần {round_long or '∞'}/{round_short or '∞'}) "
                      f"— video đang làm ĐÃ XONG, nhường slot cho kênh khác. Target còn thiếu sẽ tiếp ở lượt sau."); break
            continue
        # ---- made == 0 ----
        if rl == 0:                             # KHÔNG làm + KHÔNG dính rate-limit = ĐỦ TARGET (run_one thoát sớm) -> ngừng hẳn
            print(f"   🎯 {name}: đủ target (hoặc không còn việc) → ngừng."); break
        # made==0 VÌ RATE-LIMIT -> CHỜ rồi thử KEY KHÁC (còn quota) / per-minute reset -> KHÔNG bỏ kênh oan khi chưa đủ target
        empty_streak += 1
        if empty_streak >= MAX_EMPTY:
            print(f"   ⏹ {name}: {MAX_EMPTY} vòng liền dính rate-limit (quota cạn thật) → ngừng, phiên sau làm tiếp."); break
        wait = min(120, 40 * empty_streak)
        print(f"   ⏳ {name}: vòng {rounds} hết quota tạm → chờ {wait}s rồi thử KEY KHÁC (còn quota)…"); time.sleep(wait)
    print(f"✅ {name}: TỔNG {report['done']} video · {len(report['fails'])} lỗi (qua {rounds} vòng).")
    # GHI số request/key hôm nay -> theo dõi quota còn free + chia đều lần sau.
    try:
        import key_manager as KM
        from datetime import datetime as _dt, timezone as _tz
        reqs = KM.flush_requests(); today = _dt.now(_tz.utc).isoformat()[:10]
        for kid, cnt in reqs.items():
            FB.incr_key_requests(kid, cnt, today)
        if reqs:
            print(f"   📊 {name}: +{sum(reqs.values())} request lên {len(reqs)} key.")
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    if "--gate" in sys.argv:
        gate_mode()
    elif "--plan" in sys.argv:
        plan_mode()
    elif "--channel" in sys.argv:
        i = sys.argv.index("--channel")
        channel_mode(sys.argv[i + 1] if i + 1 < len(sys.argv) else "")
    else:
        main()   # tuần tự (fallback / chạy tay)
