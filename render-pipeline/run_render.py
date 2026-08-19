"""
run_render.py — PIPELINE (GitHub Actions cron). RULE CHẠY:
  1. Đọc render_config (bật/tắt), gemini_keys, render_channels từ Firestore.
  2. Với MỖI kênh: tạo job -> Gemini viết (bám key kênh) -> render -> QC -> đẩy Drive (enqueue).
  3. Ghi trạng thái REALTIME vào render_jobs -> tab 🎬 Render Studio hiện live.

Env: OWNER_UID (uid chủ), GOOGLE_APPLICATION_CREDENTIALS, FIREBASE_PROJECT_ID,
     AUTOPUBLISHER_SRC (đường dẫn tới MM0-AutoPublisher/src để enqueue). FORCE=1 để chạy dù đang tắt.
"""
from __future__ import annotations
import os, sys, traceback, subprocess, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firestore_bridge as FB
import datastory_ci as DS

OWNER = os.environ.get("OWNER_UID")
PVER = os.environ.get("PIPELINE_VERSION", "v2")   # phiên bản pipeline (fix handle/tràn/che/hướng ảnh) -> dọn thông minh chỉ xóa bản CŨ
# AN TOÀN: render là làm DỰ TRỮ (kho), upload là pipeline riêng. Mỗi kênh giữ tối đa N video dự trữ
# (khi target=0) -> KHÔNG render vô hạn làm phình Drive. Chỉnh ở render_config.reserve_long/short.
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
                              "-of", "default=nk=1:nw=1", video], capture_output=True, text=True).stdout.strip()
        try:
            at = max(1.0, float(dur) * 0.62)
        except ValueError:
            at = 3.0
        thumb = os.path.splitext(video)[0] + "_thumb.jpg"
        subprocess.run(["ffmpeg", "-y", "-ss", str(at), "-i", video, "-frames:v", "1",
                        "-vf", "scale=1280:-1", thumb], check=True, capture_output=True)
        return thumb if os.path.exists(thumb) else None
    except Exception as e:
        print("   ⚠️ thumbnail lỗi:", str(e)[:80]); return None


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

    # ── FORMAT ĐẶC BIỆT (short-only, motif riêng): GUESS / MAPPED ── route sang make_guess/make_mapped.
    fmt = (ch.get("format") or "").lower()
    if fmt in ("guess", "mapped", "ranked", "scaled", "thennow", "doc"):
        short_target = int(ch.get("short_target", 0) or 0) or RESERVE_SHORT
        need = max(0, short_target - FB.count_done(OWNER, channel, "short"))
        n = min(int(ch.get("n_shorts", n_shorts) or 3) or 3, need)
        if n <= 0:
            print(f"🎯 {channel}: đủ target {fmt} — bỏ qua."); return
        cat = niche   # ⚠️ KHÔNG dùng ch.get("category") — field đó giờ chứa mã YouTube category SỐ ("24"/"27"/"28",
                      # dashboard tự set cho brand kit), KHÔNG phải gợi ý chủ đề. Đụng nhầm = Gemini nhận "24" làm niche.
        avoid = FB.recent_topics(OWNER, channel)
        made_here = []
        for i in range(n):
            if _stopped():
                print(f"   ⛔ {channel}: dừng — bỏ {n - i} clip còn lại."); break
            job = FB.new_job(OWNER, channel, "short", pver=PVER)
            jst = lambda s, step, **x: FB.update_job(job, status=s, step=step, **x)
            out = os.path.join("out", DS.slug(channel) + f"_{fmt}{i}.mp4")
            story = ok = info = None; err = None
            for att in (1, 2):
                try:
                    if att > 1: jst("running", f"🔧 Tự thử lại {fmt}…")
                    if fmt == "doc":     # Wave 2 tài liệu: truyền style/accent riêng của kênh
                        _, story, ok, info = DS.make_doc(channel, cat, out, keys=keys, tier=tier,
                                                         style=ch.get("style", "awe, cinematic"),
                                                         accent=ch.get("accent", "#22D3EE"), accent2=ch.get("accent2", "#F5B301"),
                                                         avoid=(avoid + made_here), on_status=jst, on_limit=cool, on_ok=okcb)
                    else:
                        mk = {"guess": DS.make_guess, "mapped": DS.make_mapped, "ranked": DS.make_ranked,
                              "scaled": DS.make_scaled, "thennow": DS.make_thennow}[fmt]
                        _, story, ok, info = mk(channel, cat, out, keys=keys, tier=tier,
                                                avoid=(avoid + made_here), on_status=jst, on_limit=cool, on_ok=okcb)
                    err = None; break
                except Exception as e:
                    err = e; traceback.print_exc(); print(f"   🔧 {fmt.upper()} {channel}#{i} lỗi lần {att}: {str(e)[:100]}")
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
                    description=story.get("description", ""), hashtags=story.get("hashtags") or [], tags=story.get("tags") or [],  # cho auto-enqueue đăng đủ metadata
                    score=(story.get("self_score") or {}).get("total"),
                    dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0), res=(info or {}).get("res", ""),
                    drive_id=did or "", drive_account=acc, preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else "")); R["done"] += 1; R["done_short"] = R.get("done_short", 0) + 1
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
        for attempt, nr in enumerate([4, 2], start=1):
            try:
                avoid = FB.recent_topics(OWNER, channel)      # chủ đề đã dùng -> tránh trùng
                lout = os.path.join("out", DS.slug(channel) + "_long.mp4")
                if attempt > 1:
                    lst("running", f"🔧 Tự thử lại nhẹ hơn ({nr} race)…")
                _, plan, subtopics, ok, info = DS.make_long(channel, niche, lout, keys=keys, tier=tier,
                                                            on_status=lst, on_limit=cool, avoid=avoid, n_races=nr, on_ok=okcb)
                last_err = None; break
            except Exception as e:
                last_err = e; traceback.print_exc()
                print(f"   🔧 LONG {channel} lỗi lần {attempt} ({nr} race): {str(e)[:120]}")
        try:
            if subtopics:
                FB.save_topics(OWNER, channel, subtopics)     # ghi vào ngân hàng chủ đề
            if last_err is not None and _is_ratelimit(last_err):
                lst("ratelimited", "⏳ hết quota tạm — thử lại sau"); R["rl"] = R.get("rl", 0) + 1   # KHÔNG tính Lỗi
            elif last_err is not None:
                lst("failed", f"Tự thử lại vẫn lỗi: {str(last_err)[:120]}"); R["fails"].append(f"{channel} LONG: {str(last_err)[:100]}")
            elif ok:
                eq = enqueue_drive(channel, lout, {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"),
                                                   "description": plan.get("hook", "")}, "long")
                did = (eq or {}).get("id"); acc = (eq or {}).get("account", "")
                lst("done", "Long đã đẩy Drive" if did else "Long xong (chưa đẩy Drive)", title=plan.get("pillar_title"),
                    score=(info or {}).get("score"),
                    dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0), res=(info or {}).get("res", ""),
                    drive_id=did or "", drive_account=acc, preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else "")); R["done"] += 1; R["done_long"] = R.get("done_long", 0) + 1
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
    for i, sub in enumerate(subtopics[:n_shorts]):
        if _stopped():   # ⛔ đã xong clip trước -> ngừng, KHÔNG bắt đầu clip mới (tiết kiệm, không dở dang).
            print(f"   ⛔ {channel}: dừng theo yêu cầu — xong clip hiện tại, bỏ {n_shorts - i} short còn lại."); break
        sjob = FB.new_job(OWNER, channel, "short", pver=PVER)
        sst = lambda s, step, **x: FB.update_job(sjob, status=s, step=step, **x)
        story = sok = sinfo = None; serr = None
        for satt in (1, 2):                                # SELF-HEAL: thử lại 1 lần nếu lỗi
            try:
                sout = os.path.join("out", DS.slug(channel) + f"_short{i}.mp4")
                if satt > 1:
                    sst("running", "🔧 Tự thử lại short…")
                _, story, sok, sinfo = DS.make_video(channel, sub, "short", sout, keys=keys, tier=tier, on_status=sst, on_limit=cool, on_ok=okcb)
                serr = None; break
            except Exception as e:
                serr = e; traceback.print_exc(); print(f"   🔧 SHORT {channel}#{i} lỗi lần {satt}: {str(e)[:100]}")
        if serr is not None and _is_ratelimit(serr):
            sst("ratelimited", "⏳ hết quota tạm — thử lại sau"); R["rl"] = R.get("rl", 0) + 1   # KHÔNG tính Lỗi
        elif serr is not None:
            sst("failed", f"Tự thử lại vẫn lỗi: {str(serr)[:110]}"); R["fails"].append(f"{channel} SHORT {i}: {str(serr)[:100]}")
        elif sok:
            eq = enqueue_drive(channel, sout, story, "short")
            did = (eq or {}).get("id"); acc = (eq or {}).get("account", "")
            sst("done", "Short đã đẩy Drive" if did else "Short xong (chưa đẩy Drive)", title=story.get("title"),
                description=story.get("description", ""), hashtags=story.get("hashtags") or [], tags=story.get("tags") or [],  # cho auto-enqueue
                score=(story.get("self_score") or {}).get("total"),
                dur=(sinfo or {}).get("dur", 0), size_mb=(sinfo or {}).get("size_mb", 0), res=(sinfo or {}).get("res", ""),
                drive_id=did or "", drive_account=acc, preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else "")); R["done"] += 1; R["done_short"] = R.get("done_short", 0) + 1
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


def process_requests(keys, report):
    """YÊU CẦU RENDER LẠI (nút 🔄): render lại đúng chủ đề -> đẩy Drive -> BỎ bản cũ (thay thế)."""
    for req in FB.read_render_requests(OWNER):
        ch = req.get("channel"); typ = req.get("type", "short"); seed = req.get("seed", "")
        if not (ch and seed):
            FB.mark_request_done(req["id"], "thiếu thông tin"); continue
        FB.mark_request_status(req["id"], "processing")   # KHÓA hủy: đã bắt đầu render lại
        job = FB.new_job(OWNER, ch, typ, pver=PVER)
        st = lambda s, step, **x: FB.update_job(job, status=s, step=step, **x)
        cool = lambda kid, mins=90: FB.cool_key(kid, mins)   # giới hạn PHÚT -> nghỉ ngắn; quota NGÀY -> 90'
        try:
            st("running", f"🔄 Render lại: {seed[:40]}")
            out = os.path.join("out", DS.slug(ch) + "_rr.mp4")
            if typ == "long":
                _, plan, _subs, ok, info = DS.make_long(ch, seed, out, keys=keys, on_status=st, on_limit=cool, n_races=4)
                story = {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"), "description": plan.get("hook", "")}
            else:
                _, story, ok, info = DS.make_video(ch, seed, "short", out, keys=keys, on_status=st, on_limit=cool)
            if ok:
                eq = enqueue_drive(ch, out, story, typ)
                did = (eq or {}).get("id"); acc = (eq or {}).get("account", "")
                _trash_old(req.get("replace_account"), req.get("replace_id"))
                FB.delete_jobs_by_drive(OWNER, req.get("replace_id"))   # dọn job cũ (bản đã bị thay thế)
                st("done", "Render lại xong — đã thay thế bản cũ", title=story.get("title"),
                   dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0), res=(info or {}).get("res", ""),
                   drive_id=did or "", drive_account=acc, preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""))
                report["done"] += 1; FB.mark_request_done(req["id"], "done")
            else:
                st("failed", f"Render lại QC trượt: {info}"); FB.mark_request_done(req["id"], "qc-trượt")
        except Exception as e:
            traceback.print_exc(); st("failed", str(e)[:120]); FB.mark_request_done(req["id"], "lỗi")


def main():
    if not OWNER:
        raise SystemExit("❌ Thiếu OWNER_UID (uid chủ — set ở workflow).")
    cfg = FB.read_config(OWNER)
    # NHỊP 30': chỉ chạy khi có lệnh "Render ngay" (run_now) HOẶC đúng giờ mẻ đêm (18h UTC).
    from datetime import datetime, timezone, timedelta
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    run_now = bool(cfg.get("run_now"))
    is_nightly = (datetime.now(timezone.utc).hour in (cfg.get("batch_hours") or [0, 4, 8, 12, 16, 20])
                  and datetime.now(timezone.utc).minute < 25)   # GIỜ MẺ (mặc định mỗi 6h): chưa đủ target -> phiên mới tự chạy suốt ngày
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
            # tới giờ cố định tiếp theo là lãng phí. Sàn tối thiểu session_gap_min (mặc định 30') chống trigger dồn
            # dập nếu check active lỗi. Chỉnh session_gap_min ở render_config nếu muốn thưa hơn.
            last = cfg.get("last_session_at", ""); gap_min = int(cfg.get("session_gap_min", 30) or 30); recently = False
            if last:
                try:
                    elapsed_min = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 60
                    recently = (elapsed_min < gap_min) or FB.has_active_render(OWNER)
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
    last = cfg.get("last_session_at", ""); gap_min = int(cfg.get("session_gap_min", 30) or 30); recently = False
    if last:
        try:
            elapsed_min = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 60
            recently = (elapsed_min < gap_min) or FB.has_active_render(OWNER)
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
    channels = [c["name"] for c in all_ch if not c.get("paused")]   # ⏸ kênh PAUSE -> KHÔNG vào matrix (không làm mẻ mới)
    n_paused = len(all_ch) - len(channels)
    print(f"▶ {len(channels)} kênh -> render SONG SONG." + (f" (⏸ {n_paused} kênh đang pause, bỏ qua)" if n_paused else ""))
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
