"""
run_render.py — PIPELINE (GitHub Actions cron). RULE CHẠY:
  1. Đọc render_config (bật/tắt), gemini_keys, render_channels từ Firestore.
  2. Với MỖI kênh: tạo job -> Gemini viết (bám key kênh) -> render -> QC -> đẩy Drive (enqueue).
  3. Ghi trạng thái REALTIME vào render_jobs -> tab 🎬 Render Studio hiện live.

Env: OWNER_UID (uid chủ), GOOGLE_APPLICATION_CREDENTIALS, FIREBASE_PROJECT_ID,
     AUTOPUBLISHER_SRC (đường dẫn tới MM0-AutoPublisher/src để enqueue). FORCE=1 để chạy dù đang tắt.
"""
from __future__ import annotations
import os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firestore_bridge as FB
import datastory_ci as DS

OWNER = os.environ.get("OWNER_UID")


def enqueue_drive(channel, out, story, vtype) -> bool:
    """Đẩy video + sidecar lên Drive _QUEUE qua enqueue.py của AutoPublisher (nếu có)."""
    try:
        src = os.environ.get("AUTOPUBLISHER_SRC")
        if src and src not in sys.path:
            sys.path.insert(0, src)
        from enqueue import enqueue
        enqueue(channel=channel, video=out, vtype=vtype,
                topic=story.get("topic") or story.get("title"),
                title=story.get("title"), description=story.get("description"),
                hashtags=story.get("hashtags"), tags=story.get("tags"))
        return True
    except Exception as e:
        print("   ⚠️ enqueue lỗi (giữ artifact):", e); return False


def run_one(ch, keys, n_shorts=3):
    """1 kênh/ngày: 1 LONG (pillar 5-6 race) + n_shorts SHORT dọc (viết lại từ chủ đề con)."""
    channel = ch.get("name"); tier = ch.get("tier", "normal"); niche = ch.get("niche") or channel
    cool = lambda kid: FB.cool_key(kid)
    os.makedirs("out", exist_ok=True)
    # ---- LONG ----
    ljob = FB.new_job(OWNER, channel, "long")
    lst = lambda s, step, **x: FB.update_job(ljob, status=s, step=step, **x)
    subtopics = []
    try:
        lout = os.path.join("out", DS.slug(channel) + "_long.mp4")
        _, plan, subtopics, ok, info = DS.make_long(channel, niche, lout, keys=keys, tier=tier, on_status=lst, on_limit=cool)
        if ok:
            enqueue_drive(channel, lout, {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"),
                                          "description": plan.get("hook", "")}, "long")
            lst("done", "Long đã đẩy Drive", title=plan.get("pillar_title"))
        else:
            lst("failed", f"QC long trượt: {info}")
    except Exception as e:
        traceback.print_exc(); lst("failed", str(e)[:140])
    # ---- SHORTS (viết LẠI cho 9:16 từ 2-3 chủ đề con của long) ----
    for i, sub in enumerate(subtopics[:n_shorts]):
        sjob = FB.new_job(OWNER, channel, "short")
        sst = lambda s, step, **x: FB.update_job(sjob, status=s, step=step, **x)
        try:
            sout = os.path.join("out", DS.slug(channel) + f"_short{i}.mp4")
            _, story, sok, sinfo = DS.make_video(channel, sub, "short", sout, keys=keys, tier=tier, on_status=sst, on_limit=cool)
            if sok:
                enqueue_drive(channel, sout, story, "short")
                sst("done", "Short đã đẩy Drive", title=story.get("title"),
                    score=(story.get("self_score") or {}).get("total"))
            else:
                sst("failed", f"QC short trượt: {sinfo}")
        except Exception as e:
            traceback.print_exc(); sst("failed", str(e)[:120])
    print(f"   ✅ {channel}: xong long + {min(n_shorts, len(subtopics))} short")


def main():
    if not OWNER:
        raise SystemExit("❌ Thiếu OWNER_UID (uid chủ — set ở workflow).")
    cfg = FB.read_config(OWNER)
    if not cfg.get("enabled") and os.environ.get("FORCE") != "1":
        print("⏸ Pipeline đang TẮT — bật ở tab Render Studio, hoặc chạy FORCE=1."); return
    keys = FB.read_keys(OWNER)
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key — thêm ở tab 🎬 Render Studio.")
    channels = [c for c in FB.read_channels(OWNER) if c.get("name")]
    if not channels:
        print("⚠️ Chưa cấu hình kênh render nào (thêm ở tab Render Studio)."); return
    print(f"▶ Pipeline: {len(channels)} kênh · {len(keys)} key")
    for ch in channels:
        run_one(ch, keys)
    print("✅ Xong tất cả.")


if __name__ == "__main__":
    main()
