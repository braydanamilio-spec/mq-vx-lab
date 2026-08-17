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
                          thumbnail=_make_thumb(out))   # trích khung từ video -> thumbnail YouTube + gallery
        return created or None                     # trả cả {id, account} -> lưu vào job để XEM/stream trên web
    except Exception as e:
        print("   ⚠️ enqueue lỗi (giữ artifact):", e); return None


def run_one(ch, keys, n_shorts=3, report=None):
    """1 kênh theo TEMPLATE của kênh: make_long (1 long pillar) + n_shorts SHORT dọc.
    Đọc ch['make_long'] (mặc định True) và ch['n_shorts'] (mặc định 3) do dashboard đặt."""
    channel = ch.get("name"); tier = ch.get("tier", "normal"); niche = ch.get("niche") or channel
    cool = lambda kid: FB.cool_key(kid)
    _marked = set()   # key viết OK lúc dùng thật -> đánh dấu SỐNG 1 lần/run (khỏi health-check riêng, đỡ tốn)
    def okcb(kid):
        if kid and kid not in _marked:
            _marked.add(kid)
            try: FB.mark_key_alive(kid, True, "ok (dùng thật)")
            except Exception: pass
    R = report if report is not None else {"done": 0, "fails": []}
    os.makedirs("out", exist_ok=True)
    do_long = ch.get("make_long", True)
    n_shorts = int(ch.get("n_shorts", n_shorts) or 0)
    # MỤC TIÊU số video/kênh (0 = không giới hạn): đủ rồi thì bỏ qua, khỏi làm dư.
    long_target = int(ch.get("long_target", 0) or 0)
    short_target = int(ch.get("short_target", 0) or 0)
    if do_long and long_target and FB.count_done(OWNER, channel, "long") >= long_target:
        do_long = False; print(f"🎯 {channel}: đủ {long_target} long — bỏ qua long.")
    if short_target:
        n_shorts = max(0, min(n_shorts, short_target - FB.count_done(OWNER, channel, "short")))
    subtopics = []
    if do_long:
        # ---- LONG ---- SELF-HEAL: render lỗi -> tự thử lại NHẸ hơn (4 race -> 2).
        ljob = FB.new_job(OWNER, channel, "long")
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
            if last_err is not None:
                lst("failed", f"Tự thử lại vẫn lỗi: {str(last_err)[:120]}"); R["fails"].append(f"{channel} LONG: {str(last_err)[:100]}")
            elif ok:
                info = enqueue_drive(channel, lout, {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"),
                                                     "description": plan.get("hook", "")}, "long")
                did = (info or {}).get("id"); acc = (info or {}).get("account", "")
                lst("done", "Long đã đẩy Drive" if did else "Long xong (chưa đẩy Drive)", title=plan.get("pillar_title"),
                    drive_id=did or "", drive_account=acc, preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else "")); R["done"] += 1
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
        sjob = FB.new_job(OWNER, channel, "short")
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
        if serr is not None:
            sst("failed", f"Tự thử lại vẫn lỗi: {str(serr)[:110]}"); R["fails"].append(f"{channel} SHORT {i}: {str(serr)[:100]}")
        elif sok:
            info = enqueue_drive(channel, sout, story, "short")
            did = (info or {}).get("id"); acc = (info or {}).get("account", "")
            sst("done", "Short đã đẩy Drive" if did else "Short xong (chưa đẩy Drive)", title=story.get("title"),
                score=(story.get("self_score") or {}).get("total"),
                drive_id=did or "", drive_account=acc, preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else "")); R["done"] += 1
        else:
            sst("failed", f"QC short trượt: {sinfo}"); R["fails"].append(f"{channel} SHORT {i}: QC trượt")
    print(f"   ✅ {channel}: xong long + {min(n_shorts, len(subtopics))} short")


def main():
    if not OWNER:
        raise SystemExit("❌ Thiếu OWNER_UID (uid chủ — set ở workflow).")
    cfg = FB.read_config(OWNER)
    # NHỊP 30': chỉ chạy khi có lệnh "Render ngay" (run_now) HOẶC đúng giờ mẻ đêm (18h UTC).
    from datetime import datetime, timezone, timedelta
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    run_now = bool(cfg.get("run_now"))
    is_nightly = datetime.now(timezone.utc).hour == 18
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
    max_run = int(cfg.get("max_per_run", 0) or 0)   # 0 = không giới hạn; >0 = dừng sau N video/lần
    FB.set_config(OWNER, {"stop": None})             # xoá cờ dừng cũ khi bắt đầu run mới
    print(f"▶ Pipeline: {len(channels)} kênh · {len(keys)} key" + (f" · tối đa {max_run} video" if max_run else ""))
    report = {"done": 0, "fails": []}
    for ch in channels:
        if FB.read_config(OWNER).get("stop"):        # ⛔ nút Dừng ngay trên dashboard
            FB.set_config(OWNER, {"stop": None}); print("⛔ Dừng theo yêu cầu — ngưng các kênh còn lại."); break
        run_one(ch, keys, report=report)
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


if __name__ == "__main__":
    main()
