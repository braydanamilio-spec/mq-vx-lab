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
        # GHI NGUỒN NHẠC (Kevin MacLeod CC-BY) + nguồn số liệu -> tránh claim bản quyền, đúng chính sách.
        desc = (story.get("description") or "")
        srcs = story.get("sources") or []
        if srcs:
            desc += "\n\nSources: " + " · ".join(srcs[:3])
        desc += "\n\nMusic: Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 3.0"
        created = enqueue(channel=channel, video=out, vtype=vtype,
                          topic=story.get("topic") or story.get("title"),
                          title=story.get("title"), description=desc,
                          hashtags=story.get("hashtags"), tags=story.get("tags"))
        return (created or {}).get("id")          # trả Drive file id -> lưu vào job để XEM trên web
    except Exception as e:
        print("   ⚠️ enqueue lỗi (giữ artifact):", e); return None


def run_one(ch, keys, n_shorts=3, report=None):
    """1 kênh/ngày: 1 LONG (pillar 5-6 race) + n_shorts SHORT dọc (viết lại từ chủ đề con)."""
    channel = ch.get("name"); tier = ch.get("tier", "normal"); niche = ch.get("niche") or channel
    cool = lambda kid: FB.cool_key(kid)
    R = report if report is not None else {"done": 0, "fails": []}
    os.makedirs("out", exist_ok=True)
    # ---- LONG ----
    ljob = FB.new_job(OWNER, channel, "long")
    lst = lambda s, step, **x: FB.update_job(ljob, status=s, step=step, **x)
    subtopics = []
    try:
        avoid = FB.recent_topics(OWNER, channel)          # chủ đề đã dùng -> tránh trùng
        lout = os.path.join("out", DS.slug(channel) + "_long.mp4")
        _, plan, subtopics, ok, info = DS.make_long(channel, niche, lout, keys=keys, tier=tier,
                                                    on_status=lst, on_limit=cool, avoid=avoid)
        if subtopics:
            FB.save_topics(OWNER, channel, subtopics)     # ghi vào ngân hàng chủ đề
        if ok:
            did = enqueue_drive(channel, lout, {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"),
                                                "description": plan.get("hook", "")}, "long")
            lst("done", "Long đã đẩy Drive" if did else "Long xong (chưa đẩy Drive)", title=plan.get("pillar_title"),
                drive_id=did or "", preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else "")); R["done"] += 1
        else:
            lst("failed", f"QC long trượt: {info}"); R["fails"].append(f"{channel} LONG: QC trượt {info}")
    except Exception as e:
        traceback.print_exc(); lst("failed", str(e)[:140]); R["fails"].append(f"{channel} LONG: {str(e)[:100]}")
    # ---- SHORTS (viết LẠI cho 9:16 từ 2-3 chủ đề con của long) ----
    for i, sub in enumerate(subtopics[:n_shorts]):
        sjob = FB.new_job(OWNER, channel, "short")
        sst = lambda s, step, **x: FB.update_job(sjob, status=s, step=step, **x)
        try:
            sout = os.path.join("out", DS.slug(channel) + f"_short{i}.mp4")
            _, story, sok, sinfo = DS.make_video(channel, sub, "short", sout, keys=keys, tier=tier, on_status=sst, on_limit=cool)
            if sok:
                did = enqueue_drive(channel, sout, story, "short")
                sst("done", "Short đã đẩy Drive" if did else "Short xong (chưa đẩy Drive)", title=story.get("title"),
                    score=(story.get("self_score") or {}).get("total"),
                    drive_id=did or "", preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else "")); R["done"] += 1
            else:
                sst("failed", f"QC short trượt: {sinfo}"); R["fails"].append(f"{channel} SHORT {i}: QC trượt")
        except Exception as e:
            traceback.print_exc(); sst("failed", str(e)[:120]); R["fails"].append(f"{channel} SHORT {i}: {str(e)[:100]}")
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
    report = {"done": 0, "fails": []}
    for ch in channels:
        run_one(ch, keys, report=report)
    print(f"✅ Xong: {report['done']} video · {len(report['fails'])} lỗi.")
    # EMAIL CẢNH BÁO — chống spam: CHỈ gửi khi CÓ LỖI, gộp 1 email cho cả lần chạy.
    if report["fails"]:
        try:
            import alert_email
            body = (f"MM0 Render Factory — {len(report['fails'])} job LỖI (đã xong {report['done']}):\n\n"
                    + "\n".join("• " + f for f in report["fails"])
                    + "\n\nXem chi tiết: https://mm0-auto-publisher.web.app/#render")
            alert_email.send_alert(f"⚠️ MM0 Render: {len(report['fails'])} job lỗi", body)
        except Exception as e:
            print(f"   ⚠️ email lỗi: {e}")


if __name__ == "__main__":
    main()
