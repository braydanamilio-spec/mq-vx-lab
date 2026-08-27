"""
run_render.py — PIPELINE (GitHub Actions cron). RULE CHẠY:
  1. Đọc render_config (bật/tắt), gemini_keys, render_channels từ Firestore.
  2. Với MỖI kênh: tạo job -> Gemini viết (bám key kênh) -> render -> QC -> đẩy Drive (enqueue).
  3. Ghi trạng thái REALTIME vào render_jobs -> tab 🎬 Render Studio hiện live.

Env: OWNER_UID (uid chủ), GOOGLE_APPLICATION_CREDENTIALS, FIREBASE_PROJECT_ID,
     AUTOPUBLISHER_SRC (đường dẫn tới MM0-AutoPublisher/src để enqueue). FORCE=1 để chạy dù đang tắt.
"""
from __future__ import annotations
import os, sys, traceback, subprocess, re, random, json, time

# MÁY TỰ KHAI NGĂN XẾP (25/8/2026). Phiên 08:55: 5 lane toon đứng im 25+ phút — không một bản ghi
# D1/Firestore nào, log GitHub thì không đọc được khi job đang chạy, thành ra chỉ còn cách ĐOÁN
# xem kẹt ở đâu (và đoán trượt 3 lần liên tiếp ở vụ plan). Từ nay khỏi đoán: cứ mỗi 10 phút,
# faulthandler in NGĂN XẾP THẬT của mọi thread vào stderr (vào thẳng log GitHub) — tiến trình
# vẫn chạy tiếp bình thường (exit=False), tốn 0 tài nguyên khi không kẹt. SIGTERM (bị chém
# timeout) cũng in ngăn xếp trước khi chết — biết chết ở dòng nào.
import faulthandler as _fh
import signal as _sg
_fh.dump_traceback_later(600, repeat=True, exit=False)
try:
    _fh.register(_sg.SIGTERM, all_threads=True, chain=True)
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firestore_bridge as FB
import datastory_ci as DS

OWNER = os.environ.get("OWNER_UID")
PVER = (os.environ.get('PIPELINE_VERSION') or 'v3')
# pver theo ENGINE THẬT của video, không phải theo ngày: v3 = chuẩn Cinematic mới (cảnh hook footage,
# không intro/outro, cắt 2-3s, SFX) — CHỈ engine doc/Cinematic đổi. Data-race/motif/wave4 KHÔNG đổi
# engine hôm 21/8 -> video mới của chúng vẫn "v2" như video cũ -> "Dọn bản cũ" không bao giờ coi
# video tốt của DATARACE là bản lỗi. Nhãn v3 chỉ dán lên thứ THẬT SỰ ra từ engine mới.
CLASSIC_PVER = "v2"


def _pv(fmt: str, cinematic: bool = False) -> str:
    return PVER if (cinematic or (fmt or "").lower() == "doc") else CLASSIC_PVER
   # phiên bản pipeline (fix handle/tràn/che/hướng ảnh) -> dọn thông minh chỉ xóa bản CŨ
# AN TOÀN: render là làm DỰ TRỮ (kho), upload là pipeline riêng. Mỗi kênh giữ tối đa N video dự trữ
# (khi target=0) -> KHÔNG render vô hạn làm phình Drive. Chỉnh ở render_config.reserve_long/short.
# NGHỈ GIỮA 2 PHIÊN: trước để 30' -> máy đứng không suốt nửa tiếng sau mỗi phiên dù đã xong việc.
# GitHub concurrency (group mm0-render-cron, cancel-in-progress:false) ĐÃ bảo đảm không bao giờ có
# 2 phiên render chạy đè — lượt mới xếp hàng chờ lượt cũ xong. Nên chỉ cần sàn nghỉ này là đủ.
# ── VAN ĐIỀU TIẾT PHIÊN — ĐẶT THEO NGÂN SÁCH, KHÔNG THEO SỐT RUỘT (26/8/2026) ─────────────
# Trước: 12 phút. Cron thức mỗi 10' nên phiên mở NỐI ĐUÔI liên tục — đo thật hôm qua **33 phiên
# trong 24h**, tức một phiên mỗi ~44 phút. Mà một phiên tiêu **4.219 lượt đọc** (đo bằng hiệu hai
# lần chốt sổ: 56.051 -> 60.270). 33 × 4.219 ≈ 139.000 lượt trên trần 50.000 ⇒ sổ chạm 120% từ
# 03:09Z và mọi thứ sau đó gãy: kênh không đọc được cấu hình, kho Drive không liệt kê được,
# "Không kho nào đủ chỗ" trên mọi lane.
#
# Tính ngược từ trần thay vì đoán:
#     50.000 lượt đọc/ngày
#   − 30% để dành cho khâu đăng · thống kê · health guardian · dashboard
#   = 35.000 cho render  ÷  4.219 lượt/phiên  ≈  8 phiên/ngày
#     24 giờ ÷ 8 phiên = 180 phút giữa hai phiên
#
# 8 phiên × 18 lane × ~3 video = ~430 video/ngày — thừa sức cho 50 kênh, mà KHÔNG bao giờ chạm trần.
# Muốn nhanh hơn thì phải giảm lượt đọc mỗi phiên trước, rồi mới hạ con số này.
SESSION_GAP_MIN = 180        # chỉ là ĐƯỜNG LÙI khi không đọc được sổ hạn mức
CHI_PHI_PHIEN_DOC = 4219     # lượt đọc Firestore một phiên 18 lane tiêu — ĐO THẬT, không đoán:
                             # hiệu hai lần chốt sổ liên tiếp 56.051 -> 60.270 (25-26/8).
                             # Đo lại con số này khi đổi số lane hoặc khi cắt bớt lượt đọc.
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


def _ks_long(plan, parts) -> dict:
    """KỊCH BẢN ĐỦ ĐỂ RENDER LẠI một video LONG (24/8 tối, anh hỏi "kịch bản đó có dùng để render
    được ko").

    Soi lại thì câu trả lời trước bản vá này là KHÔNG, với 2 trong 4 loại long:
      • long doc + long motif: chỉ lưu `[p["topic"] for p in parts]` — tức mấy CÁI TÊN chủ đề, không
        phải kịch bản. Mà `make_doc_long(resume=…)` cần `parts` là danh sách STORY DICT và cần thêm
        `subs`; đưa chuỗi vào chỗ dict là hoặc bỏ qua resume (viết mới, tốn Gemini) hoặc vỡ.
      • long toon: KHÔNG lưu gì cả — mất trắng, muốn làm lại phải viết mới từ đầu.
    Chỉ long DATARACE (`races`) và mọi SHORT là lưu đủ từ trước.

    Bốn trường dưới đây khớp đúng thứ `make_doc_long`/`make_toon_long` đọc ở nhánh resume. Nặng
    thêm vài KB/video — đổi lại render lại KHÔNG tốn một lượt gọi AI nào."""
    return {"pillar_title": plan.get("pillar_title"), "hook": plan.get("hook"),
            "sources": plan.get("sources") or [],
            "subs": [p.get("topic") for p in (parts or []) if p.get("topic")],
            "parts": [(p.get("story") or {}) for p in (parts or [])]}


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


import hashlib
from ten_chuan import lat as _lat, ten_file          # quy ước đặt tên: MỘT nguồn duy nhất

# ĐẾM SỐ LƯỢT HẾT HẠN MỨC ĐÃ TỰ XỬ LÝ (25/8/2026).
_DA_LUONG = {"n": 0}


def print_exc_gon() -> None:
    """Thay `print_exc_gon()`: lỗi ĐÃ LƯỜNG TRƯỚC và ĐÃ CÓ ĐƯỜNG XỬ LÝ thì in một dòng.

    Phiên 02:15 in 39 vệt Traceback 20 dòng, tất cả đều là `RateLimited: 429 rate limit daily
    (cloudflare)` — key CF cạn hạn mức ngày, hệ đổi key rồi làm tiếp bình thường, không mất video
    nào. Nhưng log thì trông như 39 lần sập: soi log mất thời gian vô ích, và một crash THẬT nằm
    lẫn giữa đống đó thì không ai thấy. Lỗi lạ vẫn in đủ stack như cũ — chỉ nén thứ đã biết cách chữa.
    Cuối phiên `bao_da_luong()` in tổng số lượt, để "im lặng" không thành "giấu"."""
    e = sys.exc_info()[1]
    if e is not None and (type(e).__name__ == "RateLimited" or "429 rate limit" in str(e)):
        _DA_LUONG["n"] += 1
        print(f"   ⏳ hết hạn mức: {str(e)[:130]} — đổi key rồi làm tiếp")
        return
    # 26/8 — CẠN TÀI NGUYÊN cũng là chuyện đã lường trước, không phải sập. Sau khi vá
    # `key_order(...)[0]`, `IndexError` biến mất nhưng chỗ bắt lỗi vẫn in NGUYÊN STACK cho
    # `RuntimeError: hết key viết dùng được` — 12 vệt Traceback một phiên cho đúng một tình
    # huống bình thường của hệ chạy trên hạn mức free. Cùng bài học với 588 dòng cảnh báo pool:
    # stack chỉ có ích khi không biết chuyện gì xảy ra; ở đây biết rõ rồi.
    _msg = str(e or "")
    if e is not None and any(t in _msg for t in
                             ("hết key viết dùng được", "pool vẽ ảnh CẠN SẠCH",
                              "KHÔNG CÒN KEY NÀO dùng được")):
        _DA_LUONG["n"] += 1
        print(f"   ⏳ {_msg[:130]}")
        return
    traceback.print_exc()


def bao_da_luong() -> None:
    if _DA_LUONG["n"]:
        print(f"   ⏳ TỔNG {_DA_LUONG['n']} lượt hết hạn mức key đã tự đổi key (không mất video nào).")


# KỊCH BẢN CỦA CẢ LANE -> cất thêm 2 KHO KHÁC lúc kết thúc. Xem _luu_kich_ban_du_phong().
_KB_PHIEN: list = []


def _luu_kich_ban_du_phong(channel: str) -> int:
    """Cất kịch bản của lane này sang 2 KHO DRIVE KHÁC (25/8/2026, anh hỏi: "nhỡ 1 driver có vấn đề").

    Hiện trạng thật trước bản này:
      • KỊCH BẢN có 2 bản — Firestore `render_jobs.script` và sidecar `.json` cạnh video. Hai hệ
        độc lập, nhưng bản trên Drive nằm ĐÚNG cái kho chứa video: kho đó chết là mất cả hai thứ
        cùng lúc, chỉ còn trông vào Firestore — mà Firestore chính là thứ hay cạn hạn mức nhất.
      • VIDEO chỉ có 1 bản. `storage.backup_account()` (kho lạnh) tồn tại nhưng **không ai gọi** —
        lại một tính năng chết câm.
    Không thể nhân đôi mọi video (72 kho × 14GB, nhân đôi là mất một nửa sức chứa). Nhưng kịch bản
    thì vài KB: cất thêm 2 nơi KHÁC là mất một kho vẫn dựng lại được toàn bộ video của kho đó,
    **không tốn một lượt gọi AI nào**.
    Gộp cả lane vào MỘT file (~18 file/phiên) thay vì mỗi video một file (~110).
    Trả số kho đã cất."""
    if not _KB_PHIEN:
        return 0
    try:
        import json as _j
        import tempfile as _tf
        from datetime import datetime as _d2, timezone as _tz2
        src = os.environ.get("AUTOPUBLISHER_SRC")
        if src and src not in sys.path:
            sys.path.insert(0, src)
        import storage as _ST
        accs = _ST.pool_accounts() or []
        if len(accs) < 2:
            return 0
        # Chọn 2 kho theo băm tên kênh -> rải đều, và gần như chắc chắn KHÁC kho đang giữ video
        # (video được rải theo băm + bộ đếm, xem storage.ranked_accounts).
        i = int(hashlib.sha1(str(channel).encode()).hexdigest(), 16) % len(accs)
        chon = [accs[i], accs[(i + len(accs) // 2) % len(accs)]]
        ten = (f"kb-{_lat(channel)}-"
               f"{_d2.now(_tz2.utc).strftime('%Y%m%d-%H%M%S')}.json")
        tam = os.path.join(_tf.gettempdir(), ten)
        with open(tam, "w", encoding="utf-8") as fh:
            _j.dump(_KB_PHIEN, fh, ensure_ascii=False)
        ok = 0
        for acc in chon:
            try:
                drv = _ST.account_drive(acc)
                store = drv.child_folder(acc["root"], "MM0-STORE")
                bdir = drv.child_folder(store, "_KICHBAN")
                drv.upload_file(bdir, tam, ten)
                ok += 1
            except Exception as e:
                print(f"   ⚠️ cất kịch bản dự phòng ở {acc.get('name')} hụt: {str(e)[:50]}")
        try:
            os.remove(tam)
        except OSError:
            pass
        if ok:
            print(f"   🧬 cất kịch bản {len(_KB_PHIEN)} video sang {ok} kho KHÁC "
                  f"(mất 1 kho vẫn dựng lại được, 0 lượt gọi AI).")
        _KB_PHIEN.clear()
        return ok
    except Exception as e:
        print(f"   ⚠️ không cất được kịch bản dự phòng ({str(e)[:60]})")
        return 0


def enqueue_drive(channel, out, story, vtype, seri: str = "", bo: str = "", script: str = "") -> bool:
    """Đẩy video + sidecar (+ thumbnail) lên Drive _QUEUE qua enqueue.py của AutoPublisher (nếu có).

    `seri` = mã cụm (dùng id job của bản LONG) · `bo` = vai trò trong cụm (L, S1, S2...)."""
    try:
        _safe = ten_file(channel, story, vtype, seri, bo)
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
        # CHỈ ghi công nhạc KHI VIDEO THẬT SỰ CÓ NHẠC. Nhạc nền mặc định TẮT (music=None, chỉ bật
        # cho kênh có cấu hình 'music') nhưng dòng này trước đây ghi VÔ ĐIỀU KIỆN -> phần lớn video
        # không hề có nhạc mà mô tả vẫn ghi công Kevin MacLeod. Mô tả sai sự thật là điểm trừ khi
        # YouTube xét kênh, và ghi công một license mình không dùng thì chẳng được gì.
        # 23/8: mở giấy phép ảnh sang CC-BY (kho rộng gấp 5) -> BẮT BUỘC ghi công theo license.
        # Ghi 1 dòng gọn, đúng yêu cầu attribution mà không làm rối mô tả.
        # GHI CÔNG ĐÚNG ẢNH ĐÃ DÙNG (23/8): CC-BY bắt buộc ghi tác giả; Pexels/Pixabay/NASA không bắt
        # buộc nhưng ghi vẫn hơn (minh bạch nguồn khi YouTube xét kiếm tiền). Không có sổ -> câu chung.
        _cr = story.get("_credits") or []
        desc += ("\n\nImagery: " + " | ".join(_cr[:8])) if _cr else \
                "\n\nImagery: Pexels · Pixabay · Wikimedia Commons · NASA · Openverse (free-license)."
        if story.get("_music"):
            desc += "\n\nMusic: Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 3.0"
        # #shorts NGAY TỪ LÚC ĐẨY KHO (24/8 tối). Log mọi phiên đều có dòng
        # "⚠️ Short nên có #shorts để YouTube phân loại đúng" — cảnh báo đúng, nhưng không đường nào
        # xử: `autotitle` chỉ thêm khi TỰ đặt lại tiêu đề, còn video có sẵn tiêu đề từ Gemini thì đi
        # thẳng qua. Thiếu thẻ này YouTube có thể xếp video dọc vào luồng thường -> mất hẳn kênh
        # phân phối Shorts. Thêm ở đây vì đây là chỗ DUY NHẤT mọi đường đẩy kho đi qua.
        _ht = list(story.get("hashtags") or [])
        if vtype != "long" and not any(str(h).lower().lstrip("#") == "shorts" for h in _ht):
            _ht = ["#shorts"] + _ht
        if vtype != "long" and "#shorts" not in desc.lower():
            desc = desc.rstrip() + "\n\n#shorts"
        created = enqueue(channel=channel, video=out, vtype=vtype,
                          topic=story.get("topic") or story.get("title"),
                          title=story.get("title"), description=desc,
                          hashtags=_ht, tags=story.get("tags"),
                          script=script or _script_json(
                              {k: v for k, v in (story or {}).items() if k != "_thumb"}),
                          thumbnail=(story.get("_thumb") if (story.get("_thumb") and os.path.exists(story.get("_thumb"))) else _make_thumb(out)))   # thumb brand (GUESS/MAPPED) nếu có, không thì trích khung
        # SỔ ĐẾM VIDEO ĐÃ LÊN KHO (23/8): 1 chỗ duy nhất mọi đường đẩy đều đi qua -> dashboard đọc
        # 1 doc là ra con số KHỚP với thư viện, hết cảnh "tổng 1755 mà kho 61".
        try:
            if created and created.get("id"):
                _ghi_nhan(channel, vtype)          # sổ phiên: giữ luật 1:3 kể cả khi Firestore câm
                FB.count_pushed(OWNER, created["id"], channel, vtype)
                _KB_PHIEN.append({"drive_id": created["id"], "channel": channel, "type": vtype,
                                  "title": (story or {}).get("title", ""),
                                  "script": script or _script_json(
                                      {k: v for k, v in (story or {}).items() if k != "_thumb"})})
                # 24/8 tối — HỒI QUY DO CHÍNH BẢN ĐỔI TÊN: trước đây tên file đầu ra cố định theo
                # kênh nên `fresh_out()` xoá đúng nó mỗi vòng, thư mục `out/` luôn chỉ có ~1 video.
                # Từ khi đổi sang tên chuẩn (mỗi video một tên riêng), `fresh_out` không còn khớp
                # -> video CŨ nằm lại. Mà workflow có bước `upload-artifact path: out/*.mp4` để cứu
                # video chưa đẩy được kho ⇒ mỗi lane bắt đầu nhét TOÀN BỘ video của mình lên
                # artifact (18 lane × ~8 video × ~40MB ≈ vài GB/phiên) dù chúng ĐÃ nằm an toàn trên
                # Drive. Đẩy kho xong thì bản trên đĩa hết nhiệm vụ -> xoá, chỉ giữ cái CHƯA đẩy
                # được (đúng ý nghĩa của bước backup).
                for _f in (out, os.path.splitext(out)[0] + ".jpg",
                           os.path.splitext(out)[0] + "_thumb.jpg"):
                    try:
                        if os.path.exists(_f):
                            os.remove(_f)
                    except OSError:
                        pass
        except Exception:
            pass
        # 27/8 — ĐÂY LÀ BẰNG CHỨNG DUY NHẤT ĐÁNG TIN RẰNG VIDEO ĐÃ RA LÒ.
        # Đẩy Drive xong nghĩa là: đã render, đã qua QC, đã có tệp thật nằm trong kho. Mọi mốc
        # sớm hơn đều có thể hỏng về sau. Nên chốt sổ đề tài ở ĐÚNG đây, thay vì rải lệnh ghi sổ
        # ở 6 chỗ trước QC như bản cũ (video trượt QC vẫn bị ghi là "đã làm").
        # Móc một chỗ thay vì sửa 8 điểm đẩy + 12 nhánh trượt: ít chỗ sai hơn hẳn, và điểm đẩy
        # mới thêm sau này tự động được chốt đúng.
        if created:
            try:
                _chot_chu_de(channel)
            except Exception:
                pass
        return created or None                     # trả cả {id, account} -> lưu vào job để XEM/stream trên web
    except SystemExit as e:
        # enqueue.py dùng raise SystemExit khi kênh THIẾU trong channels.yaml. SystemExit kế thừa
        # BaseException chứ KHÔNG phải Exception -> "except Exception" bên dưới KHÔNG bắt được, nó
        # xuyên thẳng lên và GIẾT CẢ KÊNH giữa chừng: video vừa render xong (QC 96 điểm) bị vứt,
        # job kẹt mãi ở trạng thái "qc" vì không kịp ghi done/failed, mà GitHub vẫn báo success nên
        # không ai thấy. Ngày 20/8: 27/40 kênh thiếu trong channels.yaml -> mất TOÀN BỘ video của
        # chúng suốt nhiều tuần. Bắt riêng ở đây để một kênh lỗi cấu hình không kéo sập cả phiên.
        # 27/8 — LỜI KHUYÊN PHẢI KHỚP LÝ DO, KHÔNG PHẢI MỘT CÂU DÁN CHUNG.
        #
        # `enqueue.py` ném `SystemExit` vì BỐN chuyện khác hẳn nhau (dòng 54/133/139/159), mà chỗ
        # này chỉ in đúng một câu "thêm kênh vào channels.yaml". Ba trong bốn lý do chẳng dính gì
        # tới channels.yaml — chúng đều là chuyện của HỒ KHO.
        # Nguy hiểm ở chỗ nó SAI CÙNG LÚC VỚI QUY MÔ LỚN: hồ kho chết (token hỏng hết / đầy / đọc
        # ra rỗng) thì CẢ 50 kênh cùng ném, cùng in câu đó. Người đọc log thấy 50 dòng bảo sửa
        # cấu hình kênh sẽ đi sửa cấu hình kênh — trong khi việc cần làm là nối lại kho hoặc dọn
        # chỗ. Một lời khuyên sai, nhân với 50, là mất cả buổi đi nhầm hướng.
        _m = str(e)
        if "channels.yaml" in _m:
            _khuyen = f"thêm '{channel}' vào MM0-AutoPublisher/config/channels.yaml rồi render lại."
        elif "đủ chỗ" in _m:
            _khuyen = ("HỒ KHO ĐẦY — không phải lỗi kênh. Dọn bớt video cũ (workflow 'Dọn'), "
                       "hoặc nối thêm tài khoản Drive ở dashboard → Storage → Connect.")
        elif "Chưa kết nối" in _m:
            _khuyen = ("KHÔNG ĐỌC RA KHO NÀO — không phải lỗi kênh. Có thể do chưa nối kho, hoặc "
                       "Firestore trả rỗng lúc đọc danh sách. Xem dòng '🧟'/'⛔' phía trên để biết "
                       "kho nào bị loại.")
        else:
            _khuyen = ("MỌI KHO ĐỀU ĐẨY HỎNG — không phải lỗi kênh. Xem lý do thật ở dòng "
                       "'⚠️ Upload vào kho:… lỗi' ngay phía trên; thường là token hỏng "
                       "(invalid_grant → nối lại kho) hoặc hạn mức Drive.")
        print(f"   ❌ enqueue TỪ CHỐI kênh {channel}: {e}")
        print(f"      -> {_khuyen}")
        return None
    except Exception as e:
        print("   ⚠️ enqueue lỗi (giữ artifact):", e); return None


def _lst_noi(channel, lst):
    """Bọc `lst` để MỌI lần đánh dấu 'failed' đều IN RA LOG, không chỉ ghi Firestore.

    27/8 — CAR RECALL dựng xong một long 7 chương (418,9 giây), QC ĐẠT, đã chuẩn hoá âm lượng
    -14 LUFS — rồi cả bộ bị vứt và lane nhường slot. Giữa dòng `🔊 âm lượng` và dòng `bộ gen-2
    không đạt` KHÔNG CÓ MỘT DÒNG NÀO. Em soi hết mọi nhánh bỏ cuộc trong `chay_bo` (hook trượt,
    short không dựng được, không ra short nào) — nhánh nào cũng có `print`, và log không có dòng
    nào trong số đó. Tức là công đã hoàn thành bị vứt qua một đường KHÔNG ĐỂ LẠI DẤU VẾT, và từ
    ngoài không có cách nào biết đường đó là đường nào.
    Gốc: `lst` là lambda chỉ ghi Firestore + gọi `_bo_chu_de`, KHÔNG in. Mười hai chỗ gọi
    `lst("failed", …)` vì thế đều câm. Bản ghi job trên dashboard có lý do, nhưng người đọc log
    thì không — mà log mới là thứ dùng để truy khi 18 lane chạy song song.
    Bọc tại nguồn thay vì rải `print` ra 12 chỗ: chỗ gọi thứ 13 thêm sau này tự động có tiếng.
    """
    def _bao(st, step, **x):
        if st == "failed":
            print(f"   ❌ {channel}: BỎ — {str(step)[:150]}", flush=True)
        return lst(st, step, **x)
    return _bao


SHORT_PER_LONG = 3        # RULE CỨNG: 1 long kèm đúng 3 short

# Sổ ĐẾM TRONG PHIÊN (RAM) — dùng khi Firestore không đọc được. Không có nó thì luật 1:3 chỉ đúng
# lúc quota khoẻ; đêm 23/8 quota cạn là tỉ lệ vọt lên 1:4.5 mà không ai hay.
_SESSION_MADE: dict = {}


def _ghi_nhan(channel: str, vtype: str):
    d = _SESSION_MADE.setdefault(channel, {"long": 0, "short": 0})
    d["long" if vtype == "long" else "short"] += 1


def _muc_tieu(ch, channel, vtype):
    """CHỈ TIÊU HIỆU LỰC của kênh — 24/8, sửa theo đúng ý vận hành.

    Trước đây `long_target`/`short_target` không đặt thì lấy RESERVE 10/30 làm TRẦN TRỌN ĐỜI. Mà
    10/30 cũng đúng bằng mẻ mỗi vòng (round_long/round_short) -> kênh làm xong ĐÚNG MỘT VÒNG là bị
    cho nghỉ vĩnh viễn, dù video đã đăng hết và kênh vẫn cần bài mới. Sai mô hình: 10/30 là MẺ MỖI
    VÒNG, không phải hạn ngạch cả đời.

    Nay:
      • Anh tự đặt chỉ tiêu trên dashboard (>0)  -> đó là TRẦN THẬT, đạt thì kênh nghỉ.
      • Không đặt (=0)                           -> KHÔNG có trần trọn đời: mỗi vòng mở thêm đúng
        một mẻ (đã-có + RESERVE), nên kênh luôn còn việc và luật 1:3 vẫn có mốc để so.
    Chặn phình kho là việc của DRIVE_SAFETY_PCT (kho ≥90% đầy thì ngừng), không phải của chỉ tiêu."""
    raw = int(ch.get(f"{vtype}_target", 0) or 0)
    if raw > 0:
        return raw
    da = FB.count_done(OWNER, channel, vtype)
    return da + (RESERVE_LONG if vtype == "long" else RESERVE_SHORT)


def _ratio_plan(channel, want_shorts, long_target):
    """LUẬT TỈ LỆ 1 LONG : 3 SHORT — tự chữa mọi kênh, bất kể cấu hình cũ.

    Vì sao cần dù luồng mới đã 'long trước, short sau': nhiều kênh ĐANG lệch sẵn từ thời code cũ
    (CRIMEUSA 0 long/3 short, EATSUSA 8 long/26 short), và kênh nào đặt make_long=False thì vĩnh
    viễn không có long. Chốt bằng SỐ ĐẾM THẬT thay vì tin cấu hình:
        short được phép tối đa = 3 x số long ĐÃ CÓ
    Hết chỗ short -> BẮT BUỘC làm long trước (kể cả make_long=False), tới khi đủ long_target.
    Trả (phải_làm_long, số_short_được_phép)."""
    if int(long_target or 0) <= 0:
        # KÊNH PILOT/SHORT-ONLY CHỦ ĐÍCH (long_target=0, vd TOON đang duyệt gu): không ép long,
        # short chạy theo short_target. Đủ duyệt thì dashboard đặt long_target>0 -> luật 1:3 siết lại.
        return False, int(want_shorts or 0)
    L = FB.count_done(OWNER, channel, "long")
    S = FB.count_done(OWNER, channel, "short")
    # 24/8 — LUẬT 1:3 PHẢI ĐÚNG NGAY CẢ KHI KHÔNG ĐẾM ĐƯỢC. Đêm 23/8 quota đọc cạn -> cầu dao trả
    # count_done = 0 cho mọi kênh -> `room` tính từ số 0 nên guard mất tác dụng, đo thật ra
    # 17 long / 77 short = 1:4.5 (vỡ luật). Nay đếm thêm SỐ LÀM TRONG CHÍNH PHIÊN NÀY (biến RAM,
    # không cần Firestore) và lấy mức CHẶT HƠN giữa hai cách tính.
    _ss = _SESSION_MADE.setdefault(channel, {"long": 0, "short": 0})
    L = max(L, _ss["long"])
    S = max(S, _ss["short"])
    room = max(0, SHORT_PER_LONG * L - S)          # chỗ trống theo tỉ lệ HIỆN TẠI
    need_long = (room <= 0) and (L < long_target)  # short đã kín -> phải thêm long mới mở được chỗ
    if need_long:
        room = max(room, SHORT_PER_LONG)           # long sắp làm xong sẽ mở thêm 3 chỗ
    # MINH BẠCH TỈ LỆ (22/8): in số thật để nhìn log là biết vì sao kênh này được làm N short —
    # tránh cảnh "dashboard hôm nay hiện 0 long · 8 short" gây tưởng vỡ luật trong khi đếm TÍCH LŨY
    # vẫn chuẩn (hoặc ngược lại: lộ ngay nếu count_done trả số sai).
    print(f"   ⚖️ {channel}: tích lũy long={L} short={S} -> short được phép {room}"
          + (" · PHẢI LÀM LONG trước" if need_long else ""))
    return need_long, max(0, min(int(want_shorts or 0), room))


# ── CHỐNG TRÙNG THEO CỤM NICHE (50 kênh) ────────────────────────────────────────────────────────
# recent_topics chỉ chống trùng TRONG một kênh. Nhưng nhiều kênh chung lãnh địa (VAULTUSA và
# LEDGERUSA đều tiền-bạc) có thể ra chủ đề gần giống nhau CÙNG NGÀY mà không ai hay — đúng
# "reused content" mà chính sách phạt, chỉ là rải trên 2 kênh. Cụm dưới đây gom các kênh giao
# lãnh địa; khi viết cho 1 kênh, avoid = chủ đề của CHÍNH nó (60) + của anh em cùng cụm (20/kênh,
# tối đa 3 kênh gần nhất trong cụm). Chi phí: +≤3 lượt đọc/luồng (đã có đệm _TOPICS_CACHE).
NICHE_CLUSTERS = [
    {"DATARACE", "MONEYMOVES", "BROKE", "PAYCHECK", "VAULTUSA", "LEDGERUSA", "DEBTUSA", "MARGINUSA", "PRICEDUSA"},
    {"STATEWARS", "MAPPEDUSA", "VERSUSUSA", "GRIDUSA"},
    {"BODYUSA", "INSIDE_YOU", "PULSEUSA"},
    {"CRIMEUSA", "FAKEUSA", "RULEDUSA", "UNSOLVED", "FILEUSA"},
    {"EATSUSA", "FARMUSA"},
    {"RIDEUSA", "HAULUSA", "SIGNALUSA", "MADEUSA", "BUILTUSA"},
    {"COSMOS", "FUTUREUSA", "THEDEEP", "UNDERUSA", "UNSEENUSA"},
    {"DISASTERUSA", "WILDUSA"},
    {"SCREENKINGS", "BRANDEDUSA", "POWERPLAY", "EMPIREUSA"},
    {"FIRSTUSA", "CLOCKWORKUSA", "THENNOWUSA", "RELICUSA"},
]


# 27/8 — SỔ CHỦ ĐỀ ĐÃ LÀM TRONG CHÍNH PHIÊN NÀY.
# Đo phiên đầu chạy được: 232 video ra lò nhưng CARRECALL 18 video chỉ 1 tiêu đề, và một loạt kênh
# 20 video chỉ 3-4 tiêu đề. Một bộ = 1 long + 3 short = 4 video từ MỘT câu chuyện, nên 20 video mà
# 3 tiêu đề nghĩa là các bộ trong cùng phiên chọn lại đúng chuyện vừa làm.
# Gốc: `_avoid_for` lấy chủ đề đã làm từ Firestore (`recent_topics`), mà Firestore luôn TRỄ hơn
# phiên đang chạy — bộ thứ hai không thể biết bộ thứ nhất vừa làm gì. Sổ RAM này lấp đúng khoảng
# trễ đó; không tốn lượt đọc nào.
_SESSION_TOPICS: dict = {}


def _nho_chu_de(channel: str, *tieu_de) -> None:
    """Ghi chủ đề vừa làm vào sổ phiên, để lượt sau của CHÍNH phiên này không chọn lại."""
    lo = _SESSION_TOPICS.setdefault(str(channel), [])
    for t in tieu_de:
        t = str(t or "").strip()
        if t and t not in lo:
            lo.append(t)


# ── SỔ ĐỀ TÀI: HAI TẦNG, VÀ CHỈ TẦNG BỀN MỚI ĐƯỢC COI LÀ "ĐÃ LÀM" (27/8) ───────────────────
# Anh nêu đúng yêu cầu: "nó phải biết được số video/kịch bản THỰC TẾ đã làm, không tính các
# clip không đạt hay đã xoá".
# Đo thì hiện tại KHÔNG như vậy. `FB.save_topics` được gọi ở 6 chỗ, và ít nhất 3 chỗ nằm TRƯỚC
# lệnh kiểm QC — ví dụ dòng 988 ghi sổ rồi dòng 989 mới `if not ok: return False`. Nghĩa là một
# video trượt QC vẫn được ghi vào sổ là "đã làm". Sổ cứ thế đầy dần những đề tài CHƯA TỪNG
# THÀNH VIDEO, và kênh tự từ chối làm lại chúng — càng chạy càng cạn đề tài mà kho vẫn còn.
#
# Hai tầng, hai nhiệm vụ khác nhau:
#   • SỔ PHIÊN (`_SESSION_TOPICS`, trong RAM) — ghi NGAY, để lượt sau của chính phiên này không
#     chọn lại. Không bền, và không cần bền.
#   • SỔ BỀN (Firestore/D1) — chỉ ghi khi video ĐÃ QUA QC VÀ ĐÃ ĐẨY DRIVE THÀNH CÔNG. Đây mới là
#     câu trả lời cho "đã làm bao nhiêu".
_CHO_GHI: dict = {}     # kênh -> đề tài đang chờ xác nhận thành video


def _hen_chu_de(channel: str, tieu_de) -> None:
    """Xếp hàng chờ: đề tài đã viết nhưng CHƯA biết có ra video không."""
    lo = _CHO_GHI.setdefault(str(channel), [])
    for t in (tieu_de if isinstance(tieu_de, (list, tuple)) else [tieu_de]):
        t = str(t or "").strip()
        if t and t not in lo:
            lo.append(t)
    _nho_chu_de(channel, *(tieu_de if isinstance(tieu_de, (list, tuple)) else [tieu_de]))


def _chot_chu_de(channel: str) -> int:
    """Video đã ra lò THẬT -> chuyển hàng chờ sang sổ bền. Gọi SAU khi đẩy Drive thành công."""
    lo = _CHO_GHI.pop(str(channel), [])
    if not lo:
        return 0
    try:
        FB.save_topics(OWNER, channel, lo)
    except Exception as e:
        print(f"   ⚠️ không chốt được sổ đề tài {channel} ({str(e)[:50]}) — sổ phiên vẫn giữ")
    return len(lo)


def _bo_chu_de(channel: str, ly_do: str = "") -> int:
    """Video KHÔNG ra lò (trượt QC / đẩy hụt) -> VỨT hàng chờ, không ghi sổ bền.
    Đề tài đó phải được phép làm lại ở phiên sau: nó chưa từng thành video."""
    lo = _CHO_GHI.pop(str(channel), [])
    if lo:
        print(f"   ↩️ {channel}: KHÔNG ghi sổ {len(lo)} đề tài — video không ra lò"
              + (f" ({ly_do[:50]})" if ly_do else "") + ". Phiên sau được làm lại.")
    return len(lo)


def _avoid_for(channel: str) -> list:
    """Danh sách chủ đề cần tránh = của kênh (60) + của các kênh CÙNG CỤM (20/kênh, ≤3 kênh).
    Cap ~120 mục để không phình prompt (tốn token đầu vào)."""
    # Sổ phiên đứng TRƯỚC: nó tươi nhất, và là thứ Firestore chưa kịp biết.
    out = list(_SESSION_TOPICS.get(str(channel), [])) + FB.recent_topics(OWNER, channel, n=60)
    for cl in NICHE_CLUSTERS:
        if channel in cl:
            sibs = sorted(x for x in cl if x != channel)[:3]
            for sb in sibs:
                try:
                    out = out + FB.recent_topics(OWNER, sb, n=20)
                except Exception:
                    pass
            break
    # KHỬ TRÙNG + CẮT GỌN trước khi cap: kênh anh em hay dùng chủ đề chạm nhau -> mục lặp nguyên
    # văn chỉ tốn token vô ích; tiêu đề dài quá 60 ký tự cắt bớt (đủ để model nhận diện chủ đề).
    out = list(dict.fromkeys(str(t)[:60] for t in out if t))
    return out[-120:]


# ══════════════════════════════════════════════════════════════════════════════════════════
# ĐỒNG HỒ TỪNG BƯỚC TRONG LANE (26/8/2026)
# ------------------------------------------------------------------------------------------
# Anh giao "tối ưu toàn bộ hệ thống". Bước đầu là ĐO — và hoá ra 50 phút bên trong mỗi lane là
# HỘP ĐEN: chỉ `plan` có mốc `⏱`, lane thì không. Thử tách bước bằng dấu thời gian của log cũng
# không được vì các dòng không theo khuôn cố định.
# Không đo được thì mọi "tối ưu" đều là đoán — đúng cái đã sai mấy lần đêm nay. Đồng hồ này rẻ
# (một phép trừ mỗi bước) và trả lời câu quan trọng nhất: trong 50 phút ấy thời gian đi đâu —
# viết kịch bản, vẽ ảnh, render, hay đẩy kho?
_DH: dict = {"moc": None, "tong": {}}


def dh_bat_dau(ten: str) -> None:
    import time as _t
    dh_ket_thuc()
    _DH["moc"] = (_t.monotonic(), ten)


def dh_ket_thuc() -> None:
    import time as _t
    if not _DH["moc"]:
        return
    t0, ten = _DH["moc"]
    _DH["tong"][ten] = _DH["tong"].get(ten, 0.0) + (_t.monotonic() - t0)
    _DH["moc"] = None


def dh_bao(nhan: str = "") -> str:
    dh_ket_thuc()
    t = sum(_DH["tong"].values())
    if t < 1:
        return ""
    phan = " · ".join(f"{k}={v/60:.0f}' ({v*100/t:.0f}%)"
                      for k, v in sorted(_DH["tong"].items(), key=lambda z: -z[1])[:6])
    return f"⏱ Thời gian lane{(' ' + nhan) if nhan else ''}: tổng {t/60:.0f}' — {phan}"


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
        # 26/8 — CAO ĐỘ BỊ BỎ RƠI SUỐT. `set_voice` nhận 3 tham số (giọng · tốc · CAO ĐỘ) và
        # chú thích của nó nói rõ cao độ là "đòn bẩy MẠNH NHẤT" để tách chất giọng, nhưng cả hai
        # điểm gọi đều chỉ truyền 2. Trường `voice_pitch` của kênh vì thế chưa từng có tác dụng —
        # cùng họ với `voice_tone` (ghi vào brand kit, không hàm nào đọc).
        _TK.set_voice(ch.get("voice"), ch.get("voice_rate"), ch.get("voice_pitch"))
    except Exception:
        pass

    # 🐤 PHÁT SÚNG THỬ trước khi tiêu đạn: engine render hỏng -> dừng luồng NGAY, quota còn nguyên
    # (bài học 21/8: não viết 15 gọi/luồng xong render mới chết -> đốt sạch 1.120 gọi/ngày, 0 video).
    if not DS.render_canary():
        R["fails"].append(f"{channel}: engine render hỏng (canary) — không đốt quota")
        return
    # ── FORMAT ĐẶC BIỆT (short-only, motif riêng): GUESS / MAPPED ── route sang make_guess/make_mapped.
    fmt = (ch.get("format") or "").lower()
    # 27/8 — DANH SÁCH NÀY LÀ CHỖ 17/50 KÊNH RƠI KHỎI PIPELINE GEN-2.
    #
    # Nhánh dưới là nơi DUY NHẤT gọi `_gen2_bo`. Nó gác bằng một danh sách ĐỊNH DẠNG viết tay,
    # và danh sách đó THIẾU `race` (7 kênh) lẫn `cinematic` (10 kênh). Nghĩa là 17 kênh thế hệ 2
    # CHƯA BAO GIỜ chạy pipeline gen-2 — chúng rơi thẳng xuống đường cũ (`datastory_ci`), đường
    # đi lấy ảnh Pexels làm nền và gọi Gemini viết kịch bản.
    # Bằng chứng khớp hoàn toàn: kênh AMERICA LOOKED UP có nguồn `bai_duoc_doc` (bảng Wikipedia
    # đọc nhiều nhất) nhưng video lại nói về TỈ LỆ KIỂM TOÁN THUẾ IRS, và tiêu đề là văn AI viết
    # ("Why Restaurants Get More IRS Audits Than Wall Street") chứ không sinh từ dữ liệu. Nền là
    # ảnh chụp sẵn hai người ngồi máy tính.
    # Cổng chặn "gen-2 không rơi xuống đường cũ" em thêm sáng nay nằm BÊN TRONG nhánh này, nên
    # nó không bao giờ được chạy cho 17 kênh đó — chặn một cánh cửa mà chúng không đi qua.
    #
    # Gốc sai là DÙNG ĐỊNH DẠNG ĐỂ QUYẾT ĐỊNH ĐƯỜNG CHẠY. Thứ quyết định phải là THẾ HỆ: kênh
    # thế hệ 2 thì đi đường gen-2, bất kể nó trình bày dưới dạng nào. Thêm hai tên vào danh sách
    # chỉ chữa hôm nay; hỏi `the_he` mới chữa cả mai — dạng mới thêm sau này tự động đi đúng.
    _g2 = str(ch.get("the_he") or "") == "2"
    if _g2 or fmt in ("guess", "mapped", "ranked", "scaled", "thennow", "doc", "swarm", "pulse", "clockwork", "longshot", "toon"):
        short_target = _muc_tieu(ch, channel, "short")
        need = max(0, short_target - FB.count_done(OWNER, channel, "short"))
        n = min(int(ch.get("n_shorts", n_shorts) or 3) or 3, need)
        _lt = _muc_tieu(ch, channel, "long")
        _need_long, n = _ratio_plan(channel, n, _lt)   # LUẬT 1 long : 3 short
        if n <= 0 and not _need_long:
            print(f"🎯 {channel}: đủ target {fmt} — bỏ qua."); return
        # ── LONG TRƯỚC, SHORT SAU (rule user: 1 long -> 3 short, short bám nội dung long) ──
        # Kênh doc-format trước đây rẽ thẳng vào nhánh CHỈ-SHORT nên ra "0 long · 3 short" — sai mô
        # hình. Giờ nếu kênh còn thiếu long thì dựng LONG trước, và 3 short được đẻ ra từ ĐÚNG các
        # phần của long đó (dùng lại giọng + ảnh, KHÔNG gọi thêm Gemini).
        # _need_long=True -> BẮT BUỘC làm long dù kênh đặt make_long=False (tỉ lệ đang lệch).
        if ch.get("make_long", True) or _need_long:
            if FB.count_done(OWNER, channel, "long") < _lt:
                if fmt == "toon":
                    if _toon_long_then_shorts(ch, keys, tier, niche, n, cool, okcb, R, _stopped):
                        return
                    print(f"   ↩️ {channel}: long toon không đạt — làm short rời phiên này.")
                elif str(ch.get("the_he") or "") == "2":
                    # THẾ HỆ 2: bộ = 1 long + 3 short, short là CÁC CHƯƠNG CỦA CHÍNH LONG ĐÓ
                    # (xem `the_he_2.chay_bo`). Phải đứng TRƯỚC nhánh `fmt == "doc"` và trước nhánh
                    # motif, vì gen-2 dùng lại đúng tên định dạng (ranked/scaled/…) nhưng nguồn nội
                    # dung khác hẳn — đi nhầm nhánh là gọi Gemini viết kịch bản, sai hẳn mô hình.
                    if _gen2_bo(ch, keys, cool, okcb, R, _stopped, n):
                        return
                    # 27/8 — KÊNH KHÔNG CÓ TRỤC XOAY THÌ ĐỪNG RƠI XUỐNG ĐƯỜNG DỰ PHÒNG.
                    # Đo thật lane SKYRIGHTNOW: 18 video trùng đúng một tiêu đề. Chuỗi nhân quả:
                    #   không có trục xoay -> chỉ dựng được 1 chương
                    #   -> long 30,8s, mà QC đòi long khổ ngang >= 45s -> LOẠI
                    #   -> "bộ gen-2 không đạt" -> rơi xuống làm SHORT RỜI
                    #   -> đường đó đặt tên video bằng TÊN KÊNH ('SKY RIGHT NOW') -> 18 cái trùng.
                    # Lặp 6 lượt trong một phiên vì mỗi lượt đều hỏng ở đúng chỗ đó.
                    # Kênh có trục xoay mà bộ hỏng thì đường dự phòng vẫn hợp lý (mỗi lượt một đề
                    # tài khác). Kênh KHÔNG có trục thì mọi lượt cho ra cùng một thứ — nhường slot
                    # cho kênh khác là đúng hơn hẳn việc đẻ thêm bản sao.
                    try:
                        import the_he_2 as _T2
                        _k2 = _T2.doc_kenh(channel or "")
                        # 27/8 — KÊNH GEN-2 KHÔNG BAO GIỜ ĐƯỢC RƠI XUỐNG ĐƯỜNG CŨ.
                        #
                        # Anh chỉ đúng chỗ: "kêu không làm kiểu footage free mà tự generate ảnh với
                        # tạo chart animation, sao ARCHIVEREEL vẫn dạng cũ". Truy ra bằng mã, không
                        # phải đoán: `dung_props_race`/`dung_props` của gen-2 KHÔNG hề trả `shots`
                        # hay `bg` ảnh — chúng chỉ có dữ liệu + màu thương hiệu. Nên MỌI clip có ảnh
                        # nền chụp sẵn đều KHÔNG do đường gen-2 làm; nó rơi xuống đây, và đường cũ
                        # (`datastory_ci`) đi lấy ảnh Pexels/Wikimedia rồi ghép làm nền.
                        #
                        # Bản vá trước chỉ chặn kênh KHÔNG có trục xoay (1/50 kênh). 49 kênh còn lại
                        # vẫn rơi xuống — nên cứ mỗi lần bộ gen-2 hỏng là ra một video sai hẳn phong
                        # cách, mà nhìn dashboard thì vẫn là "video của kênh đó", không ai biết.
                        #
                        # Đổi luật: gen-2 hỏng thì NHƯỜNG SLOT, không đẻ bản thay thế. Ít video hơn
                        # nhưng không có video sai nhận diện — và quan trọng hơn: lỗi gen-2 trở nên
                        # NHÌN THẤY ĐƯỢC (kênh ra 0 video) thay vì bị đường cũ che đi.
                        if _k2:
                            _ly = ("nguồn sống KHÔNG có trục xoay — mọi lượt sau cũng ra cùng một thứ"
                                   if not (_k2.get("tham_so") or {}).get("xoay")
                                   else "bộ gen-2 không đạt")
                            print(f"   🛰 {channel}: {_ly}. NHƯỜNG SLOT — kênh thế hệ 2 không dùng "
                                  f"đường cũ (đường đó ghép ảnh chụp sẵn, sai hẳn phong cách "
                                  f"'100% đồ hoạ tự sinh').")
                            return
                    except Exception:
                        pass
                    print(f"   ↩️ {channel}: bộ gen-2 không đạt — làm short rời phiên này.")
                elif fmt == "doc":
                    # Kênh doc: short DÙNG LẠI luôn props từng phần của long -> khớp 100%, 0 thêm Gemini.
                    if _doc_long_then_shorts(ch, keys, tier, niche, n, cool, okcb, R, _stopped):
                        return
                    print(f"   ↩️ {channel}: long doc không đạt — quay về làm short rời phiên này.")
                else:
                    # Kênh motif (swarm/pulse/ranked/...): component của chúng ép cứng khổ DỌC
                    # (SwarmShort đặt width/height ngay trong calculateMetadata, PulseShort có hằng
                    # W/H) — ép sang 16:9 sẽ ra long vỡ bố cục. Nên long dùng bản Cinematic 16:9
                    # (đã kiểm chứng), còn SHORT giữ nguyên motif riêng của kênh. Ràng buộc nội dung
                    # bằng cách cho short chạy ĐÚNG các subtopic mà long vừa kể.
                    _hop = []
                    _subs = _motif_long(ch, keys, tier, niche, n, cool, okcb, R, ra_id=_hop)
                    if _subs:
                        avoid = _avoid_for(channel)
                        _motif_shorts(ch, fmt, keys, tier, _subs[:n], cool, okcb, R, _stopped, avoid,
                                      ljob=(_hop[0] if _hop else ""))
                        return
        cat = niche   # ⚠️ KHÔNG dùng ch.get("category") — field đó giờ chứa mã YouTube category SỐ ("24"/"27"/"28",
                      # dashboard tự set cho brand kit), KHÔNG phải gợi ý chủ đề. Đụng nhầm = Gemini nhận "24" làm niche.
        avoid = _avoid_for(channel)
        made_here = []
        resumed = FB.find_resumable(OWNER, channel, "short")   # CHECKPOINT: job cũ lỗi/treo nhưng còn kịch bản -> dùng lại 1 lần
        for i in range(n):
            if _stopped():
                print(f"   ⛔ {channel}: dừng — bỏ {n - i} clip còn lại."); break
            # LÀM TƯƠI pool key giữa các video (đệm 180s -> ~0 chi phí): key vừa HỒI sau cooldown
            # quay lại vòng xoay ngay, key MỚI user dán (đã sync ở plan) vào trận không đợi hết luồng.
            keys = FB.read_keys(OWNER) or keys
            # 24/8: nhánh này là các format CHỈ-SHORT (guess/mapped/ranked/...) — không có LONG cha,
            # nên `cha` để rỗng. Bản vá đầu gán `cha=ljob` ở đây là SAI: `ljob` không tồn tại trong
            # hàm này -> NameError giết cả luồng ngay video đầu tiên. Bắt được nhờ bài kiểm tĩnh
            # "biến chưa gán trước khi dùng", không phải nhờ chạy thử.
            job = FB.new_job(OWNER, channel, "short", pver=_pv(fmt), thu_tu=i + 1)
            jst = lambda s, step, **x: FB.update_job(job, status=s, step=step, **x)
            out = os.path.join("out", DS.slug(channel) + f"_{fmt}{i}.mp4")
            story = ok = info = None; err = None
            resume_story = (resumed or {}).get("story")   # chỉ dùng cho clip ĐẦU (i=0) rồi tiêu luôn, clip sau viết mới bình thường
            for att in (1, 2):
                try:
                    if att > 1: jst("running", f"🔧 Tự thử lại {fmt}…"); resume_story = None   # thử lại lần 2 -> KHÔNG dùng lại kịch bản resume (lỗi có thể do chính nó)
                    dh_bat_dau("video ngắn")
                    _, story, ok, info = _dispatch_short(ch, fmt, cat, out, keys, tier, jst, cool, okcb,
                                                         resume_story=resume_story, avoid=(avoid + made_here))
                    err = None; break
                except (Exception, SystemExit) as e:
                    # BẮT CẢ SystemExit: key_manager/datastory_ci ném SystemExit khi hết Gemini key
                    # ("Chưa có Gemini key nào"). SystemExit kế thừa BaseException nên "except
                    # Exception" KHÔNG bắt -> nó xuyên lên giết cả kênh giữa chừng, để job ma kẹt ở
                    # "writing"/"qc" mà GitHub vẫn báo success (đúng lỗi đã gặp với enqueue 20/8).
                    err = e; print_exc_gon(); print(f"   🔧 {fmt.upper()} {channel}#{i} lỗi lần {att}: {str(e)[:100]}")
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
                eq = enqueue_drive(channel, out, story, "short", bo=f"S{i+1}")
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
            try: _hen_chu_de(channel, [str(x) for x in made_here if x])
            except Exception: pass
        print(f"   ✅ {channel}: xong {fmt} ({R['done']} clip)"); return

    do_long = ch.get("make_long", True)
    n_shorts = int(ch.get("n_shorts", n_shorts) or 0)
    # MỤC TIÊU: anh đặt (>0) = trần thật · không đặt = kho trôi, mỗi vòng thêm một mẻ (xem _muc_tieu).
    long_target = _muc_tieu(ch, channel, "long")
    short_target = _muc_tieu(ch, channel, "short")
    if do_long and FB.count_done(OWNER, channel, "long") >= long_target:
        do_long = False; print(f"🎯 {channel}: đủ {long_target} long (dự trữ) — bỏ qua long.")
    n_shorts = max(0, min(n_shorts, short_target - FB.count_done(OWNER, channel, "short")))
    # LUẬT 1 long : 3 short — chốt bằng số đếm thật, tự chữa kênh đang lệch.
    _need_long, n_shorts = _ratio_plan(channel, n_shorts, long_target)
    if _need_long and not do_long:
        do_long = True
        print(f"⚖️ {channel}: short đã kín theo tỉ lệ 1:3 — bắt buộc làm LONG trước.")
    if not do_long and n_shorts <= 0:      # ĐỦ CẢ long+short -> thoát NGAY (không gọi Gemini) -> made=0 SẠCH (phân biệt với lỗi quota)
        print(f"🎯 {channel}: đủ target (long+short) — không làm gì thêm."); return
    subtopics = []
    ljob = ""          # id của LONG trong mẻ này -> short ghi `cha=ljob` để khâu đăng biết chúng cùng một bài
    if do_long:
        # ---- LONG ---- SELF-HEAL: render lỗi -> tự thử lại NHẸ hơn (4 race -> 2).
        ljob = FB.new_job(OWNER, channel, "long", pver=CLASSIC_PVER)
        lst = lambda s, step, **x: (_bo_chu_de(channel, str(step)) if s == "failed" else None,
                                   FB.update_job(ljob, status=s, step=step, **x))[-1]
        lst = _lst_noi(channel, lst)   # 27/8: mọi lần 'failed' phải có tiếng trong log
        plan = ok = info = None; last_err = None
        resumed_long = FB.find_resumable(OWNER, channel, "long")   # CHECKPOINT: phiên trước lỗi/treo nhưng còn kịch bản
        for attempt, nr in enumerate([4, 2], start=1):
            try:
                avoid = _avoid_for(channel)      # chủ đề đã dùng CỦA KÊNH + CỤM -> tránh trùng chéo kênh
                lout = os.path.join("out", DS.slug(channel) + "_long.mp4")
                rck = None
                if attempt == 1 and resumed_long:
                    rck = resumed_long["story"]   # chỉ dùng lần 1; lần 2 (thử nhẹ hơn) viết mới bình thường
                elif attempt > 1:
                    lst("running", f"🔧 Tự thử lại nhẹ hơn ({nr} race)…")
                dh_bat_dau("video dài")
                _, plan, subtopics, ok, info, stories = DS.make_long(channel, niche, lout, keys=keys, tier=tier,
                                                            on_status=lst, on_limit=cool, avoid=avoid, n_races=nr, on_ok=okcb,
                                                            resume_checkpoint=rck,
                                                            accent=ch.get("accent", "#22D3EE"), accent2=ch.get("accent2", "#F5B301"))
                last_err = None; break
            except (Exception, SystemExit) as e:
                last_err = e; print_exc_gon()
                print(f"   🔧 LONG {channel} lỗi lần {attempt} ({nr} race): {str(e)[:120]}")
        if resumed_long:
            FB.clear_resumed(resumed_long["job_id"])
        try:
            if subtopics:
                _hen_chu_de(channel, subtopics)     # HÀNG CHỜ — chỉ vào sổ bền khi video ra lò thật
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
                                                   "_thumb": plan.get("_thumb") or (info or {}).get("thumb")}, "long", seri=ljob, bo="L")
                did = (eq or {}).get("id"); acc = (eq or {}).get("account", "")
                lst("done", "Long đã đẩy Drive" if did else "Long xong (chưa đẩy Drive)", title=plan.get("pillar_title"),
                    description=(plan.get("description") or plan.get("hook") or ""), hashtags=plan.get("hashtags") or [], tags=plan.get("tags") or [],
                    score=(info or {}).get("score"),
                    dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0), res=(info or {}).get("res", ""),
                    drive_id=did or "", drive_account=acc, thumb_id=(eq or {}).get("thumb_id", ""), preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""),
                    script=_script_json({"pillar_title": plan.get("pillar_title"), "hook": plan.get("hook"), "races": stories})); R["done"] += 1; R["done_long"] = R.get("done_long", 0) + 1
            else:
                lst("failed", f"QC long trượt: {info}"); R["fails"].append(f"{channel} LONG: QC trượt {info}")
        except Exception as e:
            print_exc_gon(); lst("failed", str(e)[:140]); R["fails"].append(f"{channel} LONG: {str(e)[:100]}")
    else:
        # TEMPLATE "chỉ short": lấy subtopics KHÔNG render long (rẻ, nhanh).
        try:
            import content_brain as CB, key_manager as KM
            # 26/8 — `key_order(...)[0]` KHÔNG có bảo vệ. Phiên 19:59: cả pool key viết cạn sạch,
            # hàm trả danh sách RỖNG và `[0]` nổ IndexError -> 3 lane ra 0 video, 12 Traceback,
            # log toàn stack thay vì một dòng nói "hết key". Cạn key là tình huống BÌNH THƯỜNG
            # của hệ chạy trên hạn mức free, không phải sự cố — phải báo gọn rồi bỏ lượt.
            _ds = KM.key_order(channel, keys)
            if not _ds:
                raise RuntimeError("hết key viết dùng được — bỏ lượt · "
                                   + KM.vi_sao_het_key(keys))
            k0 = _ds[0]
            plan = CB.plan_pillar(niche, max(n_shorts, 3), api_key=k0["key"], model_name=KM.model_for(tier),
                                  avoid=FB.recent_topics(OWNER, channel))
            subtopics = (plan.get("subtopics") or [])[:max(n_shorts, 3)]
            if subtopics:
                _hen_chu_de(channel, subtopics)
        except Exception as e:
            print_exc_gon(); R["fails"].append(f"{channel} PLAN: {str(e)[:100]}")
    # ---- SHORTS (viết LẠI cho 9:16 từ 2-3 chủ đề con) ----
    resumed_short = FB.find_resumable(OWNER, channel, "short")   # CHECKPOINT: phiên trước lỗi/treo nhưng còn kịch bản
    for i, sub in enumerate(subtopics[:n_shorts]):
        keys = FB.read_keys(OWNER) or keys      # làm tươi pool giữa các video (đệm 180s)
        if _stopped():   # ⛔ đã xong clip trước -> ngừng, KHÔNG bắt đầu clip mới (tiết kiệm, không dở dang).
            print(f"   ⛔ {channel}: dừng theo yêu cầu — xong clip hiện tại, bỏ {n_shorts - i} short còn lại."); break
        sjob = FB.new_job(OWNER, channel, "short", pver=CLASSIC_PVER, cha=ljob, thu_tu=i + 1)
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
                serr = e; print_exc_gon(); print(f"   🔧 SHORT {channel}#{i} lỗi lần {satt}: {str(e)[:100]}")
        if resumed_short:
            FB.clear_resumed(resumed_short["job_id"]); resumed_short = None
        if serr is not None and _is_ratelimit(serr):
            sst("ratelimited", "⏳ hết quota tạm — thử lại sau"); R["rl"] = R.get("rl", 0) + 1   # KHÔNG tính Lỗi
        elif serr is not None:
            sst("failed", f"Tự thử lại vẫn lỗi: {str(serr)[:110]}"); R["fails"].append(f"{channel} SHORT {i}: {str(serr)[:100]}")
        elif sok:
            eq = enqueue_drive(channel, sout, story, "short", seri=ljob, bo=f"S{i+1}")
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



def _gen2_bo(ch, keys, cool, okcb, R, stopped, n_shorts=3):
    """THẾ HỆ 2 — dựng MỘT BỘ: 1 long 16:9 + n short 9:16, mỗi short gộp 2-3 chương của long.

    26/8 — luật anh nêu nhiều lần: tỉ lệ 1 long : 3 short · 3 short CẮT TỪ LONG · đánh số để khâu
    đăng đăng từ nhỏ tới lớn · short luôn đi kèm long, không nhảy cóc.
    Hai trường quyết định điều đó là `cha` (id job của long) và `thu_tu` (short thứ mấy) — khâu
    đăng đã đọc sẵn hai trường này (`auto_enqueue._theo_cha`), nên chỉ cần ghi cho đúng.
    Trả True nếu ra được long."""
    channel = ch.get("name")
    import the_he_2 as TH2
    k2 = TH2.doc_kenh(channel or "")
    # 27/8 — NGUỒN SỐNG CHỈ LÀM MỘT BỘ MỖI PHIÊN.
    # Đo thật: lane SKYRIGHTNOW ra 18 video trùng đúng một tiêu đề. Kênh này lấy dữ liệu OpenSky
    # "ngay lúc này" và KHÔNG có trục xoay (`xoay: None`), nên mọi lượt trong cùng phiên hỏi lại
    # cùng một nguồn. Gọi thẳng nguồn hai lượt cách nhau 3 giây: **giống hệt nhau ở mọi trường**
    # (200 máy bay · cao nhất 22.738m · 190 chiếc Mỹ · 7 nước) — nguồn không làm mới nhanh như chữ
    # "right now" gợi ý.
    # Nên đổi tiêu đề kiểu gì cũng vẫn là video trùng NỘI DUNG. Thứ đúng là làm một bộ rồi nhường
    # slot cho kênh khác; phiên sau (cách hàng giờ) mới có dữ liệu thật sự mới.
    if k2 and not (k2.get("tham_so") or {}).get("xoay"):
        if _SESSION_TOPICS.get(str(channel)):
            print(f"   🛰 {channel}: nguồn sống, đã làm 1 bộ trong phiên này — nhường slot "
                  f"(dữ liệu chưa kịp đổi, làm thêm là ra video trùng).")
            return False
    if not k2:
        print(f"   ⚠️ {channel}: có cờ thế hệ 2 nhưng không có trong kenh_the_he_2.json")
        return False
    ljob = FB.new_job(OWNER, channel, "long", pver=_pv(ch.get("format") or "th2"))
    lst = lambda st, step, **x: (_bo_chu_de(channel, str(step)) if st == "failed" else None,
                                 FB.update_job(ljob, status=st, step=step, **x))[-1]
    lst = _lst_noi(channel, lst)   # 27/8: mọi lần 'failed' phải có tiếng trong log
    lst("writing", "Đọc dữ liệu mở — dựng bộ 1 long + %d short" % n_shorts)
    try:
        # 26/8 — `so_chuong` gấp đôi `so_short`: long ghép các chương, còn mỗi short GỘP 2 chương
        # thành một clip riêng. `keys` bắt buộc phải truyền — dạng `cinematic` (10 kênh) vẽ ảnh
        # bằng AI, thiếu key là bỏ lượt im lặng.
        #
        # 27/8 — SỐ CHƯƠNG TỰ CO THEO KHO ĐỀ TÀI CỦA TỪNG KÊNH.
        # Anh chốt: long nên 5-10 phút, 10 càng tốt.
        #
        # ĐO THẬT (không tính nhẩm): dựng một bộ RECALL PLATE 6 chương -> long **297 giây =
        # 4'57"**, tức **49,5 giây/chương**. Con số này lớn hơn ước tính đầu (46,5) vì câu neo
        # so sánh cộng thêm ~3 giây mỗi chương.
        # Và nó lộ ra một chuyện: 6 chương ra 4'57" — HỤT SÀN 5 PHÚT ĐÚNG BA GIÂY. Ước tính cũ
        # bảo 4'39" nên em tưởng còn xa sàn; thực tế chỉ thiếu 3 giây. Đây đúng là loại sai số
        # mà chỉ render thật mới thấy.
        # => SÀN LÀ 7 CHƯƠNG, không phải 6. Thêm đúng một đề tài mỗi bộ để mọi kênh đều vượt
        # sàn, thay vì để 33 kênh nằm hụt 3 giây.
        #
        # Vẫn phải co theo kho: MỖI CHƯƠNG ĂN MỘT ĐỀ TÀI, kho trung bình 9,8 đề tài/kênh. Đặt
        # cứng 12 chương là một video nuốt trọn kho, kênh câm ngay bộ sau.
        #   kho >= 22 -> 12 chương (~9'54")   ·   kho >= 18 -> 10 chương (~8'15")
        #   kho >= 14 ->  8 chương (~6'36")   ·   còn lại   ->  7 chương (~5'46")
        _GIAY_CHUONG = 49.5                   # đo thật 27/8: 297s / 6 chương
        _kho_n = 0
        try:
            _tr, _kho = TH2._kho_xoay_cua(k2)
            _kho_n = len(_kho or [])
        except Exception:
            pass
        _sc = 12 if _kho_n >= 22 else 10 if _kho_n >= 18 else 8 if _kho_n >= 14 else 7
        _sc = max(_sc, n_shorts * 2)          # vẫn phải đủ chương để chia cho từng short
        _ph = _sc * _GIAY_CHUONG
        print(f"   📏 {channel}: kho {_kho_n} đề tài -> long {_sc} chương "
              f"(~{int(_ph // 60)}'{int(_ph % 60):02d}\")")
        kq = TH2.chay_bo(k2, avoid=_avoid_for(channel), so_short=max(1, n_shorts),
                         so_chuong=_sc, keys=keys)
    except (Exception, SystemExit) as e:
        print_exc_gon()
        lst("failed", f"bộ gen-2 lỗi: {str(e)[:110]}")
        R["fails"].append(f"{channel} BỘ: {str(e)[:100]}")
        return False
    if not kq:
        lst("failed", "nguồn thiếu dữ liệu -> bỏ lượt")
        return False
    # 26/8 — nhận thêm story GỘP CẢ BỘ. Trước đây tiêu đề long lấy `chuong[0][1]` = story của short
    # đầu; từ lúc short gộp 2 chương thì short đầu chỉ phủ 1/3 long ⇒ tên long nói sai phạm vi.
    long_path, chuong, st_long = kq
    # Ghi NGAY tiêu đề long + mọi short vào sổ phiên, trước cả khi đẩy Drive: lượt sau của phiên
    # này phải tránh chúng, không đợi Firestore cập nhật.
    _nho_chu_de(channel, (st_long or {}).get("title"),
                *[(s_ or {}).get("title") for _p, s_ in (chuong or [])])
    ok, info = DS.qc(long_path)
    if not ok:
        lst("failed", f"QC long trượt: {info}"); R["fails"].append(f"{channel} LONG: QC trượt {info}")
        return False
    _t0 = st_long or (chuong[0][1] if chuong else {})
    # `seri=ljob` + `bo="L"` -> tên file trên Drive mang mã cụm và vai trò, nên nhìn tên là biết
    # short nào thuộc long nào (xem `doi_ten_kho.py`: bo = "L" | "S1" | "S2"…).
    eq = enqueue_drive(channel, long_path,
                       {"topic": _t0.get("title"), "title": _t0.get("title"),
                        "description": _t0.get("intro_vo", ""), "sources": [_t0.get("nguon", "")],
                        "_thumb": (info or {}).get("thumb")}, "long", seri=ljob, bo="L")
    did = (eq or {}).get("id")
    lst("done", "Long đã đẩy Drive" if did else "Long xong (chưa đẩy Drive)",
        title=(_t0.get("title") or channel), dur=(info or {}).get("dur", 0),
        size_mb=(info or {}).get("size_mb", 0), res=(info or {}).get("res", ""),
        drive_id=did or "", drive_account=(eq or {}).get("account", ""),
        thumb_id=(eq or {}).get("thumb_id", ""))
    R["done"] += 1; R["done_long"] = R.get("done_long", 0) + 1

    for i, (sp, st) in enumerate(chuong):
        if stopped():
            print(f"   ⛔ {channel}: dừng — bỏ {len(chuong) - i} short còn lại."); break
        # `cha=ljob` + `thu_tu=i+1`: khâu đăng xếp long trước, rồi short 1,2,3 của ĐÚNG long đó.
        sjob = FB.new_job(OWNER, channel, "short", pver=_pv(ch.get("format") or "th2"),
                          cha=ljob, thu_tu=i + 1)
        sst = lambda s_, step, **x: FB.update_job(sjob, status=s_, step=step, **x)
        sok, sinfo = DS.qc(sp)
        if not sok:
            sst("failed", f"QC short {i + 1} trượt: {sinfo}")
            R["fails"].append(f"{channel} S{i + 1}: QC trượt {sinfo}"); continue
        seq = enqueue_drive(channel, sp,
                            {"topic": st.get("title"), "title": st.get("title"),
                             "description": st.get("intro_vo", ""), "sources": [st.get("nguon", "")],
                             "_thumb": (sinfo or {}).get("thumb")}, "short",
                            seri=ljob, bo=f"S{i + 1}")
        sdid = (seq or {}).get("id")
        sst("done", "Short đã đẩy Drive" if sdid else "Short xong (chưa đẩy Drive)",
            title=(st.get("title") or channel), dur=(sinfo or {}).get("dur", 0),
            size_mb=(sinfo or {}).get("size_mb", 0), res=(sinfo or {}).get("res", ""),
            drive_id=sdid or "", drive_account=(seq or {}).get("account", ""),
            thumb_id=(seq or {}).get("thumb_id", ""))
        R["done"] += 1
    return True


def _doc_long_then_shorts(ch, keys, tier, niche, n_shorts, cool, okcb, R, stopped):
    """Kênh doc: dựng 1 LONG rồi ĐẺ RA n_shorts SHORT từ chính các phần của long đó.

    Rule user: short đi SAU long và bám nội dung long (1 long -> 3 short). Chi phí Gemini KHÔNG
    tăng: 1 lần lập pillar + 3 lần viết doc, dùng chung cho cả long lẫn 3 short (short dùng lại
    nguyên giọng + ảnh của phần tương ứng). Trả True nếu đã ra được long."""
    channel = ch.get("name")
    ljob = FB.new_job(OWNER, channel, "long", pver=_pv("doc"))
    lst = lambda st, step, **x: (_bo_chu_de(channel, str(step)) if st == "failed" else None,
                                 FB.update_job(ljob, status=st, step=step, **x))[-1]
    lst = _lst_noi(channel, lst)   # 27/8: mọi lần 'failed' phải có tiếng trong log
    # RESUME: checkpoint từng-phần của phiên trước chết giữa chừng -> khỏi trả Gemini lần 2
    _rck = FB.find_resumable(OWNER, channel, "long")
    _resume = _rck["story"] if (_rck and isinstance(_rck.get("story"), dict) and _rck["story"].get("parts")) else None
    try:
        avoid = _avoid_for(channel)
        lout = os.path.join("out", DS.slug(channel) + "_doclong.mp4")
        lo, plan, subs, ok, info, parts = DS.make_doc_long(
            channel, niche, lout, keys=keys, tier=tier, on_status=lst, on_limit=cool, on_ok=okcb,
            avoid=avoid, resume=_resume, n_parts=max(1, n_shorts), accent=ch.get("accent", "#22D3EE"),
            accent2=ch.get("accent2", "#F5B301"), ai_style=ch.get("ai_style"),
            ai_only=bool(ch.get("ai_only")), music=ch.get("music"), mode=ch.get("mode"),
            host_prompt=ch.get("host_prompt"))
    except (Exception, SystemExit) as e:
        print_exc_gon()
        if _is_ratelimit(e):
            lst("ratelimited", "⏳ hết quota tạm — thử lại sau"); R["rl"] = R.get("rl", 0) + 1
        else:
            lst("failed", f"LONG doc lỗi: {str(e)[:120]}"); R["fails"].append(f"{channel} LONG: {str(e)[:100]}")
        return False
    if _rck:
        FB.clear_resumed(_rck["job_id"])    # đã dùng checkpoint -> job cũ khỏi bị nhặt lại lần nữa
    # XẢ ĐỆM NGAY SAU KHÂU VIẾT (trước/ngay quanh render dài): checkpoint phải nằm trên Firestore
    # trước giai đoạn rủi ro nhất, không đợi cuối luồng (luồng bị giết là đệm chết theo tiến trình).
    try:
        FB.flush_soft()
    except Exception:
        pass
    if subs:
        _hen_chu_de(channel, subs)
    if not ok:
        lst("failed", f"QC long trượt: {info}"); R["fails"].append(f"{channel} LONG: QC trượt {info}")
        return False
    eq = enqueue_drive(channel, lo, {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"),
                                     "description": plan.get("hook", ""),
                                     "sources": plan.get("sources") or [],
                                     "_thumb": (info or {}).get("thumb")}, "long", seri=ljob, bo="L")
    did = (eq or {}).get("id")
    lst("done", "Long đã đẩy Drive" if did else "Long xong (chưa đẩy Drive)", title=plan.get("pillar_title"),
        description=(plan.get("description") or plan.get("hook") or ""), hashtags=plan.get("hashtags") or [], tags=plan.get("tags") or [],
        score=(info or {}).get("score"), dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0),
        res=(info or {}).get("res", ""), drive_id=did or "", drive_account=(eq or {}).get("account", ""),
        thumb_id=(eq or {}).get("thumb_id", ""),
        preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""),
        script=_script_json(_ks_long(plan, parts)))
    R["done"] += 1; R["done_long"] = R.get("done_long", 0) + 1

    # ---- SHORT: mỗi phần của long -> 1 short, bám nội dung 100% ----
    for pi, part in enumerate(parts):
        if stopped():
            print(f"   ⛔ {channel}: dừng — bỏ {len(parts) - pi} short còn lại."); break
        keys = FB.read_keys(OWNER) or keys      # key hồi cooldown/key mới -> vào trận ngay
        sjob = FB.new_job(OWNER, channel, "short", pver=_pv("doc"), cha=ljob, thu_tu=pi + 1)
        sst = lambda st, step, **x: FB.update_job(sjob, status=st, step=step, **x)
        try:
            sout = os.path.join("out", DS.slug(channel) + f"_docshort{pi}.mp4")
            sst("rendering", f"Short {pi + 1}/{len(parts)} (từ long)")
            sok, sinfo = DS.render_short_from_props(channel, part["props"], part["story"], sout,
                                                    keys=keys, prefix=f"p{pi}", lite=(pi > 0))
        except (Exception, SystemExit) as e:
            print_exc_gon()
            sst("failed", f"Short lỗi: {str(e)[:120]}"); R["fails"].append(f"{channel} SHORT {pi}: {str(e)[:100]}")
            continue
        if not sok:
            sst("failed", f"QC short trượt: {sinfo}"); R["fails"].append(f"{channel} SHORT {pi}: QC trượt")
            continue
        st_ = part["story"]
        seq = enqueue_drive(channel, sout, st_, "short", seri=ljob, bo=f"S{pi+1}")
        sdid = (seq or {}).get("id")
        sst("done", "Short đã đẩy Drive" if sdid else "Short xong (chưa đẩy Drive)",
            description=_desc_src(st_), hashtags=st_.get("hashtags") or [], tags=st_.get("tags") or [],
            title=st_.get("title_yt") or st_.get("title"), score=(sinfo or {}).get("score"),
            dur=(sinfo or {}).get("dur", 0), size_mb=(sinfo or {}).get("size_mb", 0),
            res=(sinfo or {}).get("res", ""), drive_id=sdid or "", drive_account=(seq or {}).get("account", ""),
            thumb_id=(seq or {}).get("thumb_id", ""),
            preview=(("https://drive.google.com/file/d/%s/preview" % sdid) if sdid else ""),
            script=_script_json(st_))
        R["done"] += 1
    return True


def _motif_long(ch, keys, tier, niche, n_parts, cool, okcb, R, ra_id=None):
    """`ra_id`: hộp 1 phần tử để trả id job của LONG ra ngoài — short cần nó làm `cha`/`seri`
    (24/8). Không dùng biến toàn cục để tránh 18 luồng ghi đè nhau."""
    """LONG 16:9 cho kênh MOTIF. Trả list subtopic để short chạy đúng nội dung đó, hoặc [] nếu hỏng.

    Component motif (SwarmShort/PulseShort/...) ép cứng khổ DỌC nên không render 16:9 được -> long
    dùng bản Cinematic (make_doc_long, đã kiểm chứng end-to-end). Short vẫn giữ motif riêng của kênh
    -> kênh không mất bản sắc, mà vẫn đúng rule 'short đi sau long và bám nội dung long'."""
    channel = ch.get("name")
    ljob = FB.new_job(OWNER, channel, "long", pver=_pv("", cinematic=True))
    if ra_id is not None:
        ra_id.append(ljob)
    lst = lambda st, step, **x: (_bo_chu_de(channel, str(step)) if st == "failed" else None,
                                 FB.update_job(ljob, status=st, step=step, **x))[-1]
    lst = _lst_noi(channel, lst)   # 27/8: mọi lần 'failed' phải có tiếng trong log
    try:
        lout = os.path.join("out", DS.slug(channel) + "_motiflong.mp4")
        lo, plan, subs, ok, info, _parts = DS.make_doc_long(
            channel, niche, lout, keys=keys, tier=tier, on_status=lst, on_limit=cool, on_ok=okcb,
            avoid=_avoid_for(channel), n_parts=max(1, n_parts),
            accent=ch.get("accent", "#22D3EE"), accent2=ch.get("accent2", "#F5B301"),
            ai_style=ch.get("ai_style"), ai_only=bool(ch.get("ai_only")),
            music=ch.get("music"), mode=ch.get("mode"), host_prompt=ch.get("host_prompt"))
    except (Exception, SystemExit) as e:
        print_exc_gon()
        if _is_ratelimit(e):
            lst("ratelimited", "⏳ hết quota tạm — thử lại sau"); R["rl"] = R.get("rl", 0) + 1
        else:
            lst("failed", f"LONG motif lỗi: {str(e)[:120]}"); R["fails"].append(f"{channel} LONG: {str(e)[:100]}")
        return []
    if subs:
        _hen_chu_de(channel, subs)
    if not ok:
        lst("failed", f"QC long trượt: {info}"); R["fails"].append(f"{channel} LONG: QC trượt {info}")
        return []
    eq = enqueue_drive(channel, lo, {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"),
                                     "description": plan.get("hook", ""),
                                     "sources": plan.get("sources") or [],
                                     "_thumb": (info or {}).get("thumb")}, "long", seri=ljob, bo="L")
    did = (eq or {}).get("id")
    lst("done", "Long đã đẩy Drive" if did else "Long xong (chưa đẩy Drive)", title=plan.get("pillar_title"),
        description=(plan.get("description") or plan.get("hook") or ""), hashtags=plan.get("hashtags") or [], tags=plan.get("tags") or [],
        score=(info or {}).get("score"), dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0),
        res=(info or {}).get("res", ""), drive_id=did or "", drive_account=(eq or {}).get("account", ""),
        thumb_id=(eq or {}).get("thumb_id", ""),
        preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""),
        script=_script_json(_ks_long(plan, _parts)))
    R["done"] += 1; R["done_long"] = R.get("done_long", 0) + 1
    return subs


def _motif_shorts(ch, fmt, keys, tier, subs, cool, okcb, R, stopped, avoid, ljob=""):
    """SHORT theo motif riêng của kênh, chạy ĐÚNG các subtopic mà long vừa kể -> bám nội dung long."""
    channel = ch.get("name")
    for i, sub in enumerate(subs):
        if stopped():
            print(f"   ⛔ {channel}: dừng — bỏ {len(subs) - i} short còn lại."); break
        keys = FB.read_keys(OWNER) or keys      # key hồi cooldown/key mới -> vào trận ngay
        job = FB.new_job(OWNER, channel, "short", pver=_pv(fmt))
        jst = lambda st, step, **x: FB.update_job(job, status=st, step=step, **x)
        out = os.path.join("out", DS.slug(channel) + f"_{fmt}{i}.mp4")
        story = ok = info = None; err = None
        for att in (1, 2):
            try:
                if att > 1:
                    jst("running", "🔧 Tự thử lại short…")
                _, story, ok, info = _dispatch_short(ch, fmt, sub, out, keys, tier, jst, cool, okcb,
                                                     resume_story=None, avoid=avoid)
                err = None; break
            except (Exception, SystemExit) as e:
                err = e; print_exc_gon()
                print(f"   🔧 SHORT {channel}#{i} lỗi lần {att}: {str(e)[:100]}")
        if err is not None and _is_ratelimit(err):
            jst("ratelimited", "⏳ hết quota tạm — thử lại sau"); R["rl"] = R.get("rl", 0) + 1; continue
        if err is not None:
            jst("failed", f"Tự thử lại vẫn lỗi: {str(err)[:110]}"); R["fails"].append(f"{channel} SHORT {i}: {str(err)[:100]}"); continue
        if not ok:
            jst("failed", f"QC trượt: {info}"); R["fails"].append(f"{channel} SHORT {i}: QC trượt"); continue
        eq = enqueue_drive(channel, out, story, "short", seri=ljob, bo=f"S{i+1}")
        did = (eq or {}).get("id")
        jst("done", "Short đã đẩy Drive" if did else "Short xong (chưa đẩy Drive)",
            title=story.get("title_yt") or story.get("title"), score=(info or {}).get("score"),
            description=_desc_src(story), hashtags=story.get("hashtags") or [], tags=story.get("tags") or [],
            dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0),
            res=(info or {}).get("res", ""), drive_id=did or "", drive_account=(eq or {}).get("account", ""),
            thumb_id=(eq or {}).get("thumb_id", ""),
            preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""),
            script=_script_json(story))
        R["done"] += 1


def _dispatch_short(ch, fmt, cat, out, keys, tier, jst, cool, okcb, resume_story=None, avoid=None):
    """ĐỊNH TUYẾN SHORT theo format của kênh — NGUỒN DUY NHẤT, dùng chung cho cả render thường
    (run_one) lẫn render lại (process_requests, nút 🔄).

    TRƯỚC ĐÂY process_requests LUÔN gọi DS.make_video (engine data-race) bất kể kênh format gì ->
    bấm 🔄 trên 30/40 kênh (doc + motif + wave4) render RA SAI ENGINE hoàn toàn, mất luôn
    accent/style/mode/host_prompt của kênh. Gộp về 1 hàm để 2 đường đi không bao giờ lệch nhau nữa.
    """
    avoid = avoid or []
    # ── KÊNH THẾ HỆ 2 (26/8) ────────────────────────────────────────────────────────────────
    # Nhận ra bằng cờ `the_he == 2` chứ không bằng `format`: dạng render của chúng trùng tên với
    # dạng cũ (ranked/mapped/scaled…) nhưng NGUỒN NỘI DUNG khác hẳn — dựng thẳng từ dữ liệu mở,
    # không gọi Gemini viết kịch bản, không dùng footage. Đi nhầm nhánh là ra sai hẳn loại video.
    if str(ch.get("the_he") or "") == "2":
        import the_he_2 as TH2
        k2 = TH2.doc_kenh(ch.get("name") or "")
        # BA nơi gọi hàm này đều mở gói ĐÚNG BỐN giá trị (`_, story, ok, info`). Trả `None` là
        # `TypeError: cannot unpack non-sequence NoneType` — và với thế hệ 2 thì "bỏ lượt" không
        # phải trường hợp hiếm, nó là HÀNH VI THIẾT KẾ mỗi khi nguồn thiếu dữ liệu. Luôn trả bốn.
        if not k2:
            print(f"   ⚠️ {ch.get('name')}: có cờ thế hệ 2 nhưng không có trong kenh_the_he_2.json")
            return out, {"title": ch.get("name")}, False, {"err": "không có trong danh sách thế hệ 2"}
        jst("writing", f"Đọc dữ liệu mở ({k2['nguon']})")
        # 26/8 — TRUYỀN `avoid`. Thiếu nó thì cơ chế xoay vòng đề tài không có gì để so, kênh làm
        # đúng MỘT câu chuyện rồi lặp lại mãi (xem khối XOAY VÒNG ĐỀ TÀI trong the_he_2.py).
        # `avoid` ở đây đã được tính sẵn ở đầu hàm cho mọi dạng — chỉ là nhánh thế hệ 2 chưa dùng.
        kq = TH2.chay_chung(k2, ra=out, avoid=avoid)
        if not kq:
            return out, {"title": k2["ten"]}, False, {"err": "nguồn thiếu dữ liệu -> bỏ lượt"}
        _duong, _info = kq
        return _duong, {"title": k2["ten"], "_that": True}, True, _info

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
    if fmt == "toon":    # TOON (22/8): skit 2 nhân vật cố định — style/giọng/màu lấy từ config kênh
        return DS.make_toon(ch.get("name"), cat, out, keys=keys, tier=tier,
                            accent=ch.get("accent", "#E4562B"), avoid=avoid, on_status=jst,
                            on_limit=cool, on_ok=okcb, resume_story=resume_story,
                            toon_style=ch.get("toon_style", ""),
                            voice_a=ch.get("voice_a", "en-US-ChristopherNeural"), rate_a=ch.get("rate_a", "+0%"),
                            voice_b=ch.get("voice_b", "en-US-GuyNeural"), rate_b=ch.get("rate_b", "+8%"),
                            color_a=ch.get("color_a", "#7DD3FC"), color_b=ch.get("color_b", "#FCA5A5"),
                            display=ch.get("display") or ch.get("name"), toon_mode=ch.get("toon_mode", "skit"))
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


def process_requests(keys, report, chi_kenh=None):
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
        if chi_kenh and str(ch or "").upper() != str(chi_kenh).upper():
            continue                     # lane chỉ xử yêu cầu của kênh mình (plan không render, 25/8)
        if not (ch and seed):
            FB.mark_request_done(req["id"], "thiếu thông tin"); continue
        FB.mark_request_status(req["id"], "processing")   # KHÓA hủy: đã bắt đầu render lại
        cfg = chans.get(str(ch).upper()) or {"name": ch}
        fmt = (cfg.get("format") or "").lower()
        job = FB.new_job(OWNER, ch, typ, pver=_pv(fmt))
        st = lambda s, step, **x: FB.update_job(job, status=s, step=step, **x)
        cool = lambda kid, mins=90: FB.cool_key(kid, mins)   # giới hạn PHÚT -> nghỉ ngắn; quota NGÀY -> 90'
        try:
            # GIỌNG RIÊNG của kênh (giống run_one) — thiếu bước này thì bản render lại đọc giọng
            # mặc định, khác hẳn các video còn lại của kênh.
            try:
                import tts_karaoke as _TK
                _TK.set_voice(cfg.get("voice"), cfg.get("voice_rate"), cfg.get("voice_pitch"))
            except Exception:
                pass
            try:
                old = FB.get_script_by_drive(OWNER, req.get("replace_id"))
            except FB.DocLoi as e:
                # Đọc hỏng ≠ "không có kịch bản". Viết mới ở đây là render một video KHÁC ĐỀ TÀI
                # rồi bỏ bản cũ vào thùng rác — người dùng bấm 🔄 mà mất luôn video đang có.
                st("ratelimited", f"⏳ {e} — hoãn, giữ nguyên bản cũ")
                print(f"   ⏳ {ch}: {e} — để lượt sau (KHÔNG viết mới, KHÔNG đụng bản cũ).")
                continue
            st("running", ("♻️ Render lại (dùng kịch bản cũ): " if old else "🔄 Render lại: ") + seed[:40])
            out = os.path.join("out", DS.slug(ch) + "_rr.mp4")
            if typ == "long":
                # 24/8 tối — LỖI NẶNG: nhánh này gọi CỨNG `DS.make_long` (long DATARACE, biểu đồ
                # đua cột) cho MỌI kênh. Bấm 🔄 trên một long doc/toon/motif là thay video đúng
                # định dạng bằng một video SAI HẲN ĐỊNH DẠNG — mà bản cũ thì đã bị bỏ thùng rác.
                # Lại còn không nhận ra kịch bản cũ (long doc lưu `parts`, không có `races`) nên
                # viết mới bằng Gemini, tốn quota đúng việc lẽ ra miễn phí.
                # Nay chia đường ĐÚNG như run_one: toon -> make_toon_long · doc và mọi motif ->
                # make_doc_long (motif dùng bản Cinematic 16:9) · còn lại -> make_long.
                _cu = old if isinstance(old, dict) else None
                if fmt == "toon":
                    _, plan, _subs, ok, info, _parts = DS.make_toon_long(
                        ch, seed, out, keys=keys, tier=cfg.get("tier", "normal"),
                        accent=cfg.get("accent", "#E4562B"), on_status=st, on_limit=cool,
                        n_parts=max(1, min(3, int(cfg.get("n_shorts", 3) or 3))),
                        resume=(_cu if (_cu or {}).get("parts") else None),
                        toon_style=cfg.get("toon_style", ""),
                        voice_a=cfg.get("voice_a", "en-US-ChristopherNeural"), rate_a=cfg.get("rate_a", "+0%"),
                        voice_b=cfg.get("voice_b", "en-US-GuyNeural"), rate_b=cfg.get("rate_b", "+8%"),
                        color_a=cfg.get("color_a", "#7DD3FC"), color_b=cfg.get("color_b", "#FCA5A5"),
                        display=cfg.get("display") or ch, toon_mode=cfg.get("toon_mode", "skit"))
                elif fmt in ("doc", "guess", "mapped", "ranked", "scaled", "thennow",
                             "swarm", "pulse", "clockwork", "longshot"):
                    _, plan, _subs, ok, info, _parts = DS.make_doc_long(
                        ch, seed, out, keys=keys, tier=cfg.get("tier", "normal"),
                        on_status=st, on_limit=cool,
                        n_parts=max(1, int(cfg.get("n_shorts", 3) or 3)),
                        resume=(_cu if (_cu or {}).get("parts") else None),
                        accent=cfg.get("accent", "#22D3EE"), accent2=cfg.get("accent2", "#F5B301"),
                        ai_style=cfg.get("ai_style"), ai_only=bool(cfg.get("ai_only")),
                        music=cfg.get("music"), mode=cfg.get("mode"), host_prompt=cfg.get("host_prompt"))
                else:
                    _, plan, _subs, ok, info, _parts = DS.make_long(
                        ch, seed, out, keys=keys, on_status=st, on_limit=cool, n_races=4,
                        resume_checkpoint=(_cu if (_cu or {}).get("races") else None),
                        accent=cfg.get("accent", "#22D3EE"), accent2=cfg.get("accent2", "#F5B301"))
                    _parts = [{"story": x, "topic": (x or {}).get("topic")} for x in (_parts or [])]
                story = {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"), "description": plan.get("hook", "")}
                script = _script_json({**_ks_long(plan, _parts),
                                       **({"races": [p["story"] for p in _parts]} if fmt not in (
                                           "toon", "doc", "guess", "mapped", "ranked", "scaled",
                                           "thennow", "swarm", "pulse", "clockwork", "longshot") else {})})
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
                    description=_desc_src(story), hashtags=story.get("hashtags") or [], tags=story.get("tags") or [],
                   dur=(info or {}).get("dur", 0), size_mb=(info or {}).get("size_mb", 0), res=(info or {}).get("res", ""),
                   drive_id=did or "", drive_account=acc, thumb_id=(eq or {}).get("thumb_id", ""), preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""),
                   script=script)
                report["done"] += 1; FB.mark_request_done(req["id"], "done")
            else:
                st("failed", f"Render lại QC trượt: {info}"); FB.mark_request_done(req["id"], "qc-trượt")
        except (Exception, SystemExit) as e:
            print_exc_gon(); st("failed", str(e)[:120]); FB.mark_request_done(req["id"], "lỗi")


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
    # 27/8 — `repository_dispatch` (nhịp do Cloudflare bắn) phải được coi NGANG `schedule`.
    # Van giãn cách phiên chỉ kiểm khi sự kiện là `schedule`; đổi nhịp sang Cloudflare mà quên
    # chỗ này thì mỗi lượt cron của Cloudflare đều mở phiên mới, van thành vô dụng và quota bị
    # đốt nhanh gấp nhiều lần. Chỉ `workflow_dispatch` (người bấm tay) mới được vượt van.
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    run_now = bool(cfg.get("run_now"))
    # 20/8: cron khai báo mỗi 10' nhưng GitHub Actions THỰC TẾ hay trễ 30-50' (nghẽn nền tảng, quan sát
    # nhiều lần đêm nay) -> cửa sổ cũ minute<25 bị TRƯỢT HẲN mẻ 04h UTC (lần chạy trước 03:55, lần sau
    # 04:28, đều ngoài [xx:00,xx:25)). Nới lên minute<55 (gần hết giờ) để chịu được độ trễ lịch thực tế,
    # vẫn an toàn không lấn giờ mẻ kế (batch_hours cách nhau ít nhất 4h).
    is_nightly = (datetime.now(timezone.utc).hour in (cfg.get("batch_hours") or [0, 4, 8, 12, 16, 20])
                  and datetime.now(timezone.utc).minute < 55)
    if event in ("schedule", "repository_dispatch") and not run_now and not is_nightly:
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
    # luồng render: ăn đệm (18 luồng cùng đáp án, khỏi 18 lần quét bảng kho ở project A)
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
            print_exc_gon(); report["fails"].append(f"{ch.get('name')}: {str(e)[:120]}")
        if max_run and report["done"] >= max_run:
            print(f"🎯 Đạt {max_run} video/lần chạy — dừng."); break

    # ── XONG VIỆC CỦA MÌNH THÌ LẤY VIỆC KẾ, KHÔNG NGỒI KHÔNG ────────────────────────────────
    # 24/8 (anh chỉ ra): mỗi luồng nhận CỨNG một kênh rồi thôi. Kênh nhẹ xong sau 20' là máy đó
    # đứng im, trong khi kênh nặng chạy gần 2 tiếng — mà khoá concurrency của GitHub bắt phiên sau
    # đợi luồng CHẬM NHẤT. Đo phiên 11:00Z: 18/19 job xong từ lâu, còn đúng WHYUSA chạy 1h53
    # -> 17 máy ngồi không gần một tiếng, phiên kế nằm chờ. Đó là chia việc TĨNH.
    # Nay: plan để phần kênh dư vào HÀNG CHỜ; luồng nào xong thì tự lấy kênh kế (work stealing).
    # Lấy bằng GIAO DỊCH nguyên tử nên 18 máy không bao giờ nhận trùng kênh.
    _t0 = time.time()
    _da_lam = {str(c.get("name")) for c in channels}     # kênh luồng này đã làm -> không làm lại
    _NGAN_SACH = float((os.environ.get('LANE_BUDGET_MIN') or '130')) * 60   # chừa biên trước cap 165'
    _by_name = {c.get("name"): c for c in FB.read_channels(OWNER) if c.get("name")}
    while time.time() - _t0 < _NGAN_SACH:
        if FB.read_config(OWNER).get("stop"):
            print("⛔ Dừng theo yêu cầu — không lấy thêm việc."); break
        if max_run and report["done"] >= max_run:
            break
        _ke = FB.lay_viec_ke(OWNER)
        if not _ke:
            break                                   # hàng chờ rỗng -> hết việc thật, nghỉ
        _ch2 = _by_name.get(_ke)
        if not _ch2:
            print(f"   ⚠️ hàng chờ có {_ke} nhưng không thấy cấu hình kênh — bỏ qua"); continue
        # CHỐNG CHỒNG CHÉO lớp 2: hàng chờ đã nguyên tử (mỗi kênh về đúng một máy), nhưng nếu một
        # luồng chết giữa chừng rồi phiên sau xếp lại, hoặc cấu hình đổi, thì kênh có thể đã đủ
        # chỉ tiêu trước khi tới lượt. Kiểm lại NGAY trước khi làm — 1 lượt đếm (có đệm 90s), rẻ hơn
        # nhiều so với render dư một mẻ.
        if _ke in _da_lam:
            print(f"   ⏭ {_ke} luồng này đã làm trong phiên — bỏ qua (không làm hai lần)."); continue
        _da_lam.add(_ke)
        _con = int((_NGAN_SACH - (time.time() - _t0)) // 60)
        print(f"\n♻️ Luồng rảnh -> nhận thêm kênh {_ke} từ hàng chờ (còn {_con}' ngân sách).")
        try:
            run_one(_ch2, keys, report=report)
        except BaseException as e:
            print_exc_gon(); report["fails"].append(f"{_ke}: {str(e)[:120]}")

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
            if not cfg:
                # 23/8 (20:11Z): B cạn quota ĐỌC -> read_config trả {} -> enabled=False -> GATE ĐÓNG
                # CẢ ĐÊM dù render + GHI vẫn sống (mẻ ra mắt 5 kênh toon bị giam oan). Hệ sản xuất
                # 24/7: mất liên lạc config thì MẶC ĐỊNH CHẠY (fail-open) — nút Dừng của user chỉ bị
                # hoãn tới khi quota đọc hồi, còn fail-closed thì cả dây chuyền đứng máy hàng giờ.
                print("   ⚠️ Config không đọc được (quota B chết) -> FAIL-OPEN: coi như enabled, cho mẻ chạy.")
                enabled = True
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
            # 24/8: cờ Dừng do NGƯỜI bấm phải chặn ngay tại cổng. Trước đây chỉ xét enabled/run_now
            # nên một `run_now` cũ còn sót vẫn mở phiên dù người đã bấm Dừng.
            _nguoi_dung = bool(cfg.get("stop"))
            if _nguoi_dung:
                print("⛔ Người đã bấm DỪNG — cổng đóng (bấm ▶️ Chạy tiếp / Render ngay để mở lại).")
            elif ((event != "schedule") or run_now or batch_ok) and (enabled or run_now):
                run = "true"
        except Exception:
            print_exc_gon()
    # 23/8 tối: khối kiểm kho Drive ĐÃ CHUYỂN sang plan_mode. Lý do: bước --gate chạy TRƯỚC khi
    # workflow tải mã AutoPublisher về, nên `import storage` luôn ném "No module named 'storage'"
    # -> cổng im lặng fail-open, không kiểm được gì. Ở plan thì mã đã có sẵn.
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


# Nhóm chủ đề NHẠY CẢM theo chính sách quảng cáo YouTube + rào chắn kỳ vọng trong niche prompt.
# Máy lint này chạy trong plan (niche đã tải sẵn -> 0 quota thêm), in cảnh báo kênh thiếu rào chắn
# — audit 40 kênh TỰ ĐỘNG mỗi phiên thay vì rà tay.
_POLICY_RISK = {
    "crime":     (("crime", "criminal", "heist", "murder"), "statistics/no graphic detail"),
    "thảm hoạ":  (("disaster", "tragedy", "accident"),      "no victim detail/glorification"),
    "quân sự":   (("defense", "military", "weapon"),        "capability/cost only, no violence"),
    "tài chính": (("debt", "money", "invest", "tax", "finance", "profit"), "never personal financial advice"),
    "sức khoẻ":  (("body", "health", "medical", "psycholog"), "educational only, not medical advice"),
}
_GUARD_WORDS = ("strict", "never", "no graphic", "not medical", "not financial", "statistics only",
                "illustrative", "educational", "no gore", "no victim")


def policy_lint(all_ch):
    """Soi niche THẬT (từ Firestore) của mọi kênh: chủ đề nhạy cảm mà niche không chứa từ rào chắn
    -> cảnh báo. Chỉ đọc dữ liệu đã có trong tay, không gọi API nào."""
    flags = []
    for c in all_ch:
        nm = c.get("name") or "?"
        niche = str(c.get("niche") or "").lower()
        if not niche:
            continue
        guarded = any(g in niche for g in _GUARD_WORDS)
        for label, (keys, want) in _POLICY_RISK.items():
            if any(k in niche for k in keys) and not guarded:
                flags.append(f"{nm} ({label}: cần '{want}')")
                break
    if flags:
        print(f"   🛡️ CHÍNH SÁCH: {len(flags)} kênh nhạy cảm CHƯA có rào chắn trong niche -> TỰ VÁ:")
        for f_ in flags:
            print(f"      ⚠️ {f_}")
    else:
        print("   🛡️ CHÍNH SÁCH: mọi kênh nhạy cảm đều có rào chắn trong niche.")
    return flags


# Câu STRICT chuẩn theo nhóm rủi ro — máy TỰ NỐI vào niche khi lint phát hiện thiếu (đêm 21/8
# lint chỉ ra 6 kênh: GRIDIRON/DATARACE/LEDGERUSA tài chính, MAPPEDUSA/BODYUSA sức khoẻ,
# STATEWARS crime). Để danh sách nằm chờ người sửa là kiểu lỗi "rule không có cổng chặn" —
# nên vá luôn bằng máy: ghi mềm, quota chết thì phiên sau tự làm lại.
_GUARD_SENTENCE = {
    "crime":     " STRICT: statistics and documented facts only; no graphic detail, no victim identification, no glorification.",
    "thảm hoạ":  " STRICT: factual causes and data only; no victim detail or sensationalized tragedy.",
    "quân sự":   " STRICT: capability, budgets and documented facts only; never glorify violence.",
    "tài chính": " STRICT: real figures from cited public sources; illustrative only, never personal financial advice.",
    "sức khoẻ":  " STRICT: educational information only, not medical advice; cite real studies/agencies.",
}


def policy_autofix(all_ch, flags):
    """Nối câu STRICT chuẩn vào niche của kênh bị lint gắn cờ. Ghi qua _soft -> không bao giờ
    làm gãy plan; ghi xong thì phiên sau lint tự im (niche đã có STRICT)."""
    if not flags:
        return 0
    by_name = {c.get("name"): c for c in all_ch}
    fixed = 0
    for f_ in flags:
        nm = f_.split(" (")[0]
        label = f_.split("(")[1].split(":")[0] if "(" in f_ else ""
        c = by_name.get(nm)
        guard = _GUARD_SENTENCE.get(label)
        if not (c and guard) or "strict" in str(c.get("niche", "")).lower():
            continue
        new_niche = (str(c.get("niche") or "").rstrip(". ") + "." + guard)
        FB._soft(lambda _n=nm, _v=new_niche: FB._db_meta().collection("render_channels")
                 .document(f"{OWNER}__{_n}").set({"niche": _v}, merge=True), "policy_autofix")
        fixed += 1
    if fixed:
        print(f"   🛡️ Đã gửi bản vá STRICT cho {fixed} kênh (ghi mềm — quota chết thì phiên sau tự ghi lại).")
    return fixed


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



def _gio_toi_reset() -> float:
    """Số giờ từ bây giờ tới mốc reset hạn mức Google (00:00 giờ Thái Bình Dương = 07:00Z).

    `datetime` trong file này được nhập TRONG TỪNG HÀM, không ở tầm mô-đun — nhập lại ở đây,
    nếu không hàm chết `NameError` ngay lượt đầu và van hạn mức rơi về giãn cách cứng."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    moc = now.replace(hour=7, minute=0, second=0, microsecond=0)
    if moc <= now:
        moc += timedelta(days=1)
    return max(0.1, (moc - now).total_seconds() / 3600.0)


class _BoPhanh(Exception):
    """Thoát khỏi khối phanh mà không bị nhánh `except Exception` bên dưới hiểu nhầm là lỗi đo."""


def plan_mode():
    """ĐIỀU PHỐI (matrix 18 luồng): gating + health-check + re-render — CHẠY 1 LẦN — rồi xuất danh sách kênh
    cho các job render song song. Các job render KHÔNG lặp health-check/re-render (đỡ tốn API)."""
    # 23/8 tối — ĐỒNG HỒ CHẶNG: phiên treo 3 lần liên tiếp mà vá timeout Firestore vẫn không hết,
    # nghĩa là chỗ treo KHÔNG nằm ở nơi mình đoán. In mốc giây trước mỗi việc nặng: lần treo sau chỉ
    # cần nhìn dòng cuối cùng in ra là biết chính xác đang đứng ở đâu, khỏi đoán tiếp.
    import time as _T0
    _t_plan = _T0.time()

    def _moc(ten):
        print(f"   ⏱ [{_T0.time() - _t_plan:6.1f}s] {ten}", flush=True)

    _moc("bắt đầu điều phối")
    import json
    _cong_dong = False          # cổng kho Drive: True = không kho nào đọc được -> dừng phiên
    from datetime import datetime, timezone, timedelta
    _du_hang = []          # phần kênh dư (hàng chờ) — gửi kèm xuống lane

    def out_channels(lst, cau_hinh=None):
        """Trả danh sách kênh cho matrix — VÀ kèm luôn CẤU HÌNH của chúng.

        24/8 tối — hai lane mất trắng cả phiên: HAULUSA và FAKEUSA thoát ngay với "kênh không còn
        (đã xoá)", trong khi chính plan này vừa liệt kê cả hai. Truy ra: lane đã lật sang **gương
        B2 cũ 156 phút** (B cạn hạn mức đọc từ trước lúc plan chạy nên gương không được làm tươi),
        mà gương thiếu hai kênh đó ⇒ `read_one_channel` trả None ⇒ lane hiểu là "bị xoá".
        Lệnh đọc KHÔNG hỏng, dữ liệu chỉ THIẾU — nên `DocLoi` không đỡ được ca này.

        Cách chắc nhất: plan đã đọc đủ 50 kênh khi nó còn đọc được, vậy thì **đưa thẳng cấu hình
        xuống cho lane**, khỏi bắt lane đi đọc lại từ một nguồn có thể đã cũ. Nén + base64 cho gọn
        (50 kênh ≈ 20KB, dư sức trong hạn mức output của GitHub Actions)."""
        # ── PHANH THEO HẠN MỨC CÒN LẠI (26/8) ──────────────────────────────────────────
        # Đo thật phiên 00:01 hôm nay: 18 lane ra 101 video (kỷ lục) — nhưng sổ quota đọc chạm
        # **50.153/50.000 = 100%** ngay trong 2 giờ đầu ngày. Tải thật vượt trần free, không
        # phải lỗi đo.
        #
        # Phanh KHÔNG phải cắt tính năng — anh nói đúng, cắt `top_titles`/`read_channels` là bỏ
        # feedback học gu khán giả và cấu hình kênh, tức đổi chất lượng lấy hạn mức. Ở đây chỉ
        # giảm SỐ LANE của phiên: mọi kênh vẫn tới lượt, chỉ chậm hơn, không kênh nào mất gì.
        # Hạn mức Firestore reset theo ngày, nên chạy chậm nửa ngày còn hơn đứng hẳn nửa ngày.
        try:
            _pd = FB.phan_tram_da_dung("doc")
            _pg = FB.phan_tram_da_dung("ghi")
            _muc = max(_pd, _pg)
            _tran_lane = None
            # 27/8 — PHANH PHẢI TẮT KHI QUOTA ĐÃ CHẾT HẲN.
            # Phanh sinh ra để KHÔNG CHẠM trần: chạy chậm lại thì hạn mức đủ dùng cả ngày. Nhưng
            # khi đã chạm trần rồi thì cắt lane không tiết kiệm được gì nữa — lượt đọc có tốn đâu
            # mà tiết kiệm, nó đang bị từ chối. Lúc đó phanh chỉ còn một tác dụng: giảm sản lượng
            # từ 18 lane xuống 3.
            # Đo được ở bài chạy `--plan` với Firestore chết: plan tìm đủ 50 kênh, xếp 18 lane, rồi
            # tự cắt còn 3 — đúng cái cảnh "hệ thống bị quota làm cho ì" mà anh bảo phải hết.
            # Giờ 18 lane đều có đường lui (repo cho kênh, D1/env cho key), nên cạn quota là lúc
            # phải chạy ĐỦ lane, không phải ít hơn.
            _chet_han = bool(FB._RQ_DEAD.get("until", 0) > _T0.time()) or _muc >= 98
            if _chet_han:
                print(f"   🔓 Quota đã cạn ({_muc}%) — KHÔNG phanh: cắt lane lúc này không tiết "
                      f"kiệm được gì, chỉ giảm sản lượng. 18 lane chạy bằng đường lui repo/D1.")
                raise _BoPhanh()
            if _muc >= 95:
                _tran_lane = 3
            elif _muc >= 85:
                _tran_lane = 6
            elif _muc >= 70:
                _tran_lane = 10
            if _tran_lane and len(lst) > _tran_lane:
                print(f"   🛑 PHANH: quota đã dùng {_muc}% (đọc {_pd}% · ghi {_pg}%) — "
                      f"phiên này chạy {_tran_lane}/{len(lst)} lane, phần còn lại để phiên sau.")
                lst = lst[:_tran_lane]
        except _BoPhanh:
            pass
        except Exception as _e:
            print(f"   ⚠️ không đọc được mức quota để phanh ({str(_e)[:50]}) — chạy đủ lane")

        payload = json.dumps(lst)
        goi = ""
        try:
            if cau_hinh:
                import base64 as _b64, gzip as _gz
                # 27/8 — GÓI CẤU HÌNH PHẢI GỒM CẢ HÀNG CHỜ, không chỉ 18 kênh vào mẻ.
                # Đo log phiên: "⚠️ hàng chờ có PENTAGONLEDGER nhưng không thấy cấu hình — bỏ qua"
                # (và RENTREALITY). Lane xong sớm lấy việc kế từ hàng chờ, nhưng gói cấu hình chỉ
                # đóng cho `lst` = 18 kênh của mẻ, nên 32 kênh trong hàng chờ KHÔNG có cấu hình.
                # Lane lấy được tên rồi bỏ ngay — hàng chờ sinh ra để lane khỏi ngồi không, mà lại
                # thành lane chạy không tải. Đóng gói cả hàng chờ: thêm ~20KB, đổi lấy việc lane
                # thật sự làm được.
                _can = set(lst) | set(_du_hang or [])
                _bo = {str(c.get("name") or ""): c for c in cau_hinh if c.get("name") in _can}
                goi = _b64.b64encode(_gz.compress(
                    json.dumps(_bo, ensure_ascii=False, default=str).encode())).decode()
        except Exception as e:
            print(f"   ⚠️ không đóng gói được cấu hình kênh ({str(e)[:50]}) — lane tự đọc như cũ")
        gh = os.environ.get("GITHUB_OUTPUT")
        if gh:
            with open(gh, "a") as f:
                f.write(f"channels={payload}\n")
                f.write(f"cfgs={goi}\n")
                # HÀNG CHỜ gửi thẳng xuống lane (24/8 tối). `lay_viec_ke` giành việc bằng GIAO DỊCH
                # trên Firestore — mà Firestore chính là thứ đang cạn: log GRIDIRON phiên 21:52Z
                # `⚠️ lấy việc kế hụt (429 Quota exceeded.)`. Hàng chờ nằm trong tài nguyên đã hết
                # thì đúng lúc cần nhất nó không dùng được.
                # Đường không cần Firestore: gửi danh sách dư + thứ tự mẻ xuống, lane tự cắt phần
                # của mình theo VỊ TRÍ (i, i+N, i+2N…). Không cần điều phối, không thể trùng.
                f.write(f"queue={json.dumps(_du_hang or [])}\n")
                # HỒ KEY A gửi kèm (26/8). Đo thật: `merge_keys_A` = 29% toàn bộ lượt đọc, mà
                # dòng "Hợp nhất N key CHỈ CÓ Ở A" in ra 0 lần — 18 lane đọc project A để rồi
                # không tìm thấy gì mới. Plan đọc một lần, phát xuống: 1.260 lượt còn 70.
                f.write(f"keys_a={FB.dong_goi_keys_a(OWNER)}\n")
        try:
            FB.flush_rw_ledger(OWNER)   # kể cả plan cũng cộng sổ ngày — mọi ngả thoát đều đi qua đây
        except Exception:
            pass
        print(f"PLAN channels={payload}")

    # CỔNG KHO DRIVE (chuyển từ --gate xuống đây): không lấy nổi kho nào thì mọi video render ra đều
    # bị từ chối đẩy -> thoát sớm, khỏi đốt 18 luồng. Lỗi mạng vẫn cho chạy (fail-open) vì storage.py
    # đã có đệm + B2 + thử lại.
    try:
        _src = os.environ.get("AUTOPUBLISHER_SRC")
        if _src and _src not in sys.path:
            sys.path.insert(0, _src)
        import storage as _ST
        _accs = _ST.pool_accounts()
        _moc(f"kho Drive sẵn sàng: {len(_accs)} kho")
        if not _accs:
            _cong_dong = True
    except Exception as e:
        # 24/8 tối — CỔNG KHO ĐÃ MỞ TOANG SUỐT MÀ KHÔNG AI BIẾT. `return out_channels([])` nằm ngay
        # trong `try` này, mà `out_channels` khi đó CHƯA được định nghĩa (nó ở dưới, dòng 1266) ->
        # NameError -> rơi thẳng vào `except` này -> in "vẫn chạy (fail-open)" rồi mở 18 luồng.
        # Tức cổng chặn "không đọc được kho Drive nào" **chưa từng chặn được gì**: nó luôn tự ném
        # lỗi rồi tự nuốt. Nay `out_channels` được định nghĩa TRƯỚC cổng, và quyết định dừng được
        # đưa RA NGOÀI khối try để không bao giờ bị nuốt nữa.
        _moc(f"không kiểm được kho Drive ({str(e)[:60]}) — vẫn chạy (fail-open)")
    if _cong_dong:
        print("🛑 GATE ĐÓNG — DỪNG PHIÊN: không đọc được kho Drive nào "
              "(render ra cũng bị từ chối đẩy, mở 18 luồng là đốt không).")
        return out_channels([])
    # IN TRƯỚC MỌI LỆNH GHI: dính 429 thì vẫn biết đang nối vào project nào (B thật hay đã lùi về A).
    try:
        print(FB.where_am_i())
    except Exception:
        pass
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
    # ── VAN THEO HẠN MỨC CÒN LẠI, KHÔNG THEO ĐỒNG HỒ (26/8, anh chỉ ra) ──────────────────────
    # Anh nói đúng: độ dài phiên phụ thuộc độ dài video. Phiên xong sớm mà bắt chờ đủ 180 phút là
    # máy nằm không; phiên chạy lâu thì 180 phút vẫn có thể tràn. Đồng hồ là biến điều khiển SAI.
    # Biến đúng là **hạn mức còn lại của ngày**: rải phần còn lại đều cho số giờ còn lại.
    #     phiên còn cho phép = (còn lại − dự trữ 25%) ÷ chi phí một phiên (đo thật: 4.219 lượt)
    #     khoảng cách cần    = số giờ tới lúc reset ÷ số phiên còn cho phép
    # Hệ quả: đầu ngày hạn mức đầy -> khoảng cách ngắn, phiên nối nhau liên tục; càng tiêu nhiều
    # thì khoảng cách TỰ giãn ra; gần cạn thì dừng hẳn. Không bao giờ chạm trần, cũng không nằm
    # không khi còn dư. Vẫn giữ sàn 20' để một phiên hỏng ngay lập tức không quay vòng đốt quota.
    _gap_thuc = gap_min
    try:
        _da = FB.phan_tram_da_dung("doc")                  # % trần ngày đã tiêu (đọc D1 trước)
        _con = max(0.0, (100 - _da - 25) / 100.0) * 50000  # để dành 25% cho đăng/thống kê/dashboard
        _gio_con = _gio_toi_reset()
        _phien = _con / CHI_PHI_PHIEN_DOC
        if _phien < 1:
            print(f"⏭ Hạn mức đọc đã dùng {_da}% — không đủ cho một phiên nữa hôm nay, nghỉ.")
            return out_channels([])
        _gap_thuc = max(20, min(240, int(_gio_con * 60 / _phien)))
        print(f"   ⏱️ Van phiên: đã dùng {_da}% · còn ~{_con:,.0f} lượt · {_gio_con:.1f}h tới reset "
              f"⇒ còn {_phien:.1f} phiên ⇒ giãn cách {_gap_thuc}' (không phải {gap_min}' cứng).")
        if last:
            recently = ((datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 60) < _gap_thuc
    except Exception as e:
        print(f"   ⚠️ không tính được van theo hạn mức ({str(e)[:50]}) — dùng giãn cách cứng {gap_min}'.")
    if event in ("schedule", "repository_dispatch") and not run_now and recently:
        print(f"⏭ Nhịp kiểm — phiên gần đây còn trong giãn cách {_gap_thuc}', bỏ qua (free)."); return out_channels([])
    FB.set_config(OWNER, {"last_session_at": datetime.now(timezone.utc).isoformat()})   # đánh dấu phiên bắt đầu -> chống trùng
    if run_now:
        FB.set_config(OWNER, {"run_now": None, "run_now_done_at": datetime.now(timezone.utc).isoformat()})
        print("⚡ Nhận lệnh 'Render ngay'.")
    if not cfg.get("enabled") and os.environ.get("FORCE") != "1" and not run_now:
        if not cfg:
            # 23/8: cùng lớp lỗi fail-closed như gate — quota đọc chết thì cfg rỗng KHÔNG có nghĩa là user tắt.
            print("   ⚠️ Config không đọc được (quota) -> FAIL-OPEN tầng plan: coi như enabled.")
        else:
            print("⏸ Pipeline TẮT — bật ở Render Studio hoặc bấm Render ngay."); return out_channels([])
    all_keys = FB.read_keys(OWNER, include_cooling=True)   # TẤT CẢ (kể cả chết/cooling) -> health-check test hết
    if not all_keys:
        import time as _tt3
        if FB._RQ_DEAD.get("until", 0) > _tt3.time():
            print("⚠️ Không đọc được key (quota đọc chết) — KHÔNG phải hết key. Bỏ mẻ, nhịp cron sau tự thử.")
        else:
            print("❌ Chưa có Gemini key.")
        return out_channels([])
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
    # CHẨN ĐOÁN QUOTA: in rõ pool còn bao nhiêu key. Sự cố 21/8: log báo "quota cạn thật" trong khi
    # thực tế chỉ 5/56 key khả dụng — số còn lại đang NGHỈ 90' do dính 429 trước đó trong CÙNG phiên.
    # Không có dòng này thì không phân biệt được "hết quota thật" với "pool teo vì cooldown".
    try:
        _all = FB.read_keys(OWNER, include_cooling=True)
        _dead = sum(1 for k in _all if k.get("alive") is False)
        _cool_n = len(_all) - _dead - len(keys)
        # 26/8 — DÒNG NÀY TỪNG GÂY HIỂU NHẦM SUỐT MỘT ĐÊM. Nó báo "43 dùng được" trong khi các
        # lane in 196 lượt "hết key viết", và đã mất nhiều lượt soi log mới ra: cả 43 key ấy đều
        # là key ẢNH (px:/pb:), số key VIẾT dùng được là 0. Một con số gộp hai loại tài nguyên
        # khác nhau thì không trả lời được câu hỏi thật — "còn viết được không". Tách ra.
        _viet = [k for k in keys if not str(k.get("key", "")).startswith(("px:", "pb:", "r2:"))]
        _anh = [k for k in keys if str(k.get("key", "")).startswith(("px:", "pb:"))]
        print(f"🔑 Pool key: {len(keys)} dùng được / {len(_all)} tổng "
              f"({_cool_n} đang nghỉ · {_dead} hỏng vĩnh viễn)")
        # 26/8 — anh hỏi đúng câu quan trọng: "199 key mà sao hết key được?".
        # Số KEY không phải thứ quyết định, HẠN MỨC MỖI KEY mới là. Gemini free cho 20 lượt/ngày
        # một key; Groq cho ~1.000 lượt nhưng chặn theo TOKEN/ngày (TPD) — đo tối nay: 15 lượt
        # chạm TPD, tức Groq cạn vì token chứ không vì số lượt. Nhìn con số gộp "199 key" thì
        # tưởng dư dả, trong khi trần thật có thể chỉ vài trăm lượt viết mỗi ngày.
        # In cấu trúc pool để biết nên thêm key LOẠI NÀO, thay vì thêm bừa.
        def _loai(ks):
            g = sum(1 for k in ks if str(k.get("key", "")).startswith("gsk_"))
            c = sum(1 for k in ks if str(k.get("key", "")).startswith("cf:"))
            return g, c, len(ks) - g - c

        _vt_all = [k for k in _all if not str(k.get("key", "")).startswith(("px:", "pb:", "r2:"))]
        _g0, _c0, _m0 = _loai(_vt_all)
        _g1, _c1, _m1 = _loai(_viet)
        print(f"   ├─ VIẾT kịch bản : {len(_viet)}/{len(_vt_all)} key dùng được"
              f"  (groq {_g1}/{_g0} · cf {_c1}/{_c0} · gemini {_m1}/{_m0})" +
              ("  ⛔ KHÔNG CÒN KEY VIẾT — phiên này sẽ gần như trắng" if not _viet else ""))
        print(f"   └─ vẽ ảnh        : {len(_anh)} key dùng được")
        # Trần lượt viết/ngày ước theo hạn mức free công bố của từng nhà: gemini 20, groq/cf lớn
        # hơn nhiều nhưng chặn theo token. Con số này để SO SÁNH với nhu cầu, không phải cam kết.
        print(f"   ℹ️ trần thô mỗi ngày ≈ gemini {_m0}×20 = {_m0 * 20} lượt viết"
              f" + groq/cf {_g0 + _c0} key (chặn theo token/ngày)")
        if len(keys) <= 5 and len(_all) > 10:
            print(f"   ⚠️ Chỉ {len(keys)}/{len(_all)} key khả dụng — phần lớn đang NGHỈ, không phải hết quota vĩnh viễn.")
    except Exception:
        pass
    if not keys:
        import time as _tt2
        if FB._RQ_DEAD.get("until", 0) > _tt2.time():
            # 23/8: quota ĐỌC chết thì "0 key" là ẢO (không đọc được, không phải hết key) — đừng
            # bắn email báo động giả mỗi 30'; phiên sau quota hé là key về.
            print("⚠️ Không đọc được key (quota đọc chết) — KHÔNG phải hết key. Bỏ mẻ này, phiên sau tự thử.")
            return out_channels([])
        note = "⚠️ KHÔNG còn Gemini key SỐNG nào — thêm/thay key ở Render Studio."
        print(note)
        try:
            import alert_email; alert_email.send_alert("⚠️ MM0 Render dừng: hết key Gemini sống", note)
        except Exception:
            pass
        return out_channels([])
    # 📟 CHUÔNG QUOTA NGÀY (23/8): đọc sổ tổng 1 lượt -> thấy lũy kế CẢ NGÀY ngay đầu phiên,
    # không còn cảnh đọc cháy ngầm từ trưa mà tối mới lộ (đêm 22/8 đứng máy 9 tiếng vì thế).
    FB.nap_nen_ngan_sach(OWNER)   # biết CẢ HỆ đã tiêu bao nhiêu hôm nay, không chỉ phần mình
    try:
        import hot_db as _H
        _H.don_job_ma(OWNER)      # job ma nói dối "đang chạy" -> dọn đầu mỗi phiên, khỏi phải nhớ

    except Exception:
        pass
    _moc("quota_pulse")
    FB.quota_pulse(OWNER)   # sổ quota ngày + chuông 60/85% + ≥90% lật B2 CHỦ ĐỘNG (gương còn tươi)
    # GƯƠNG kho Drive A->B (23/8) — publisher fallback khi A nghẽn; phải chạy TRƯỚC heal để
    # phiên đầu tiên A còn thở là gương sống, heal thấy "có đường đẩy" mà làm việc.
    try:
        _moc("gương kết nối A→B")
        FB.mirror_connections_to_b()
    except Exception:
        pass
    # GƯƠNG B->B2 (23/8): B2 dự phòng luôn có sẵn kênh/config/key — B cạn là failover_to_b2 lật ngay.
    try:
        _moc("gương B→B2")
        FB.mirror_b_to_b2(OWNER)
        FB.don_nhip_song()      # doc nhịp sống ghi merge nên không tự mất -> dọn 1 lần/phiên
    except Exception:
        pass
    # 23/8 (user: "mọi logic liên quan tới R2 tạm thời bỏ, tránh xung đột lỗi"): đã NGẮT hoàn toàn
    # bến phụ R2 khỏi luồng sản xuất. Lưới an toàn còn 2 lớp và cả hai đang chạy: heal_unpushed đẩy
    # lại video hụt kho ở phiên sau, và mọi bản render đều nằm trong artifact GitHub.
    # Muốn bật lại: khôi phục _r2_park() trong enqueue_drive + repush_r2() ở đây (xem git 23/8).
    # TỰ CHỮA video render-xong-nhưng-chưa-đẩy-kho -> lật failed để lane render lại TỪ SCRIPT.
    # 23/8: user chốt DỌN SẠCH kho cũ và BỎ 180 video kẹt (chúng làm bằng pipeline cũ: ảnh dễ trùng,
    # sub chưa khớp) -> tắt tự chữa cho tới khi có nhu cầu mới. Bật lại: HEAL_UNPUSHED=1.
    # 23/8 chiều: sổ đã dọn sạch (0 job) nên tự-chữa KHÔNG còn nguy cơ dựng dậy video cũ; ngược lại
    # rất cần bật, vì hôm nay quota chập chờn -> video render xong mà đẩy hụt phải được đẩy lại,
    # không thì mất trắng như 180 video sáng nay. Tắt lại: HEAL_UNPUSHED=0.
    if (os.environ.get('HEAL_UNPUSHED') or '1') != "0":
        try:
            _moc("tự chữa video chưa đẩy")
            FB.heal_unpushed(OWNER)
            _moc("heal_unpushed xong")
        except Exception:
            pass
    else:
        print("   🩹 heal_unpushed: TẮT theo env HEAL_UNPUSHED=0.")
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
        # 25/8 — CHÍNH BƯỚC NÀY LÀM PLAN 07:05Z TREO 14,5 PHÚT RỒI BỊ CHÉM Ở TIMEOUT 18'.
        # 73 kho × (làm tươi token + about.get) chạy TUẦN TỰ, mỗi kho 2-15s, không có ngân sách
        # thời gian — rơi đúng chu kỳ 20h sau mốc reset quota là plan chết, phiên mất trắng, và vì
        # `usage_synced_at` chưa kịp đóng dấu nên PLAN NÀO KẾ TIẾP CŨNG DÍNH Y HỆT (vòng lặp chết).
        # Chữa hai tầng: (1) 8 luồng song song — I/O mạng là chỗ thread giúp thật; (2) ngân sách
        # 150 giây, hết giờ thì lấy phần đã xong. LUÔN đóng dấu synced_at kể cả xong một phần:
        # kho lỡ nhịp sẽ được làm tươi ở chu kỳ 20h sau, còn hơn cả phiên chết.
        import concurrent.futures as _cf, time as _t9
        _hang = [a for a in ST.pool_accounts() if not (a.get("owner") and a["owner"] != OWNER)]
        _het = _t9.time() + 150
        synced = 0
        def _mot(acc):
            stt = ST.account_status(acc)
            return acc, stt.get("used", 0)
        # KHÔNG dùng `with`: __exit__ gọi shutdown(wait=True) sẽ ĐỢI đủ 73 kho — đúng cái treo
        # đang chữa. TimeoutError của as_completed cũng phải nuốt để vẫn đóng dấu synced_at.
        _ex = _cf.ThreadPoolExecutor(max_workers=8)
        _cho = {_ex.submit(_mot, a): a for a in _hang}
        try:
            for _f in _cf.as_completed(_cho, timeout=max(10, _het - _t9.time())):
                try:
                    acc, _used = _f.result()
                    FB.update_storage_used(OWNER, acc["name"], _used, acc.get("cap_gb"))
                    synced += 1
                except Exception:
                    pass
                if _t9.time() > _het:
                    break
        except _cf.TimeoutError:
            pass
        finally:
            _ex.shutdown(wait=False, cancel_futures=True)
        _moc(f"đồng bộ dung lượng {synced} kho xong")
        if synced < len(_hang):
            print(f"   ⏳ đồng bộ kho chạm ngân sách 150s — lấy {synced}/{len(_hang)} kho, "
                  f"phần còn lại chu kỳ 20h sau.")
        FB.set_config(OWNER, {"usage_synced_at": datetime.now(timezone.utc).isoformat()})
        print(f"   💾 Đã đồng bộ dung lượng thật {synced}/{len(_hang)} kho.")
      except Exception as e:
        print(f"   ⚠️ Sync dung lượng kho lỗi: {e}")
    _moc("trước guard kho gần đầy")
    # GUARD KHO GẦN ĐẦY (tính tổng cả 33 kho, dùng số VỪA sync).
    # moi_nhat=True: plan là chỗ DUY NHẤT quét thật bảng kho — nó vừa sync xong nên số mới nhất,
    # và nó dựng lại đệm cho 18 luồng phía sau dùng chung (khỏi 18 lần quét project A).
    safety_pct = float(cfg.get("drive_safety_pct", DRIVE_SAFETY_PCT) or DRIVE_SAFETY_PCT)
    used, cap = FB.drive_usage(OWNER, moi_nhat=True)
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
    # 24/8 — CHỈ xoá cờ do MÁY tự đặt. Trước đây xoá luôn `stop` (cờ do NGƯỜI bấm Dừng) nên đêm 23/8
    # bấm Dừng lúc 03:50Z mà phiên 04:24Z vẫn mở đủ 18 luồng — dừng không nổi, phải khoá workflow ở
    # tầng GitHub. Cờ người đặt chỉ người mới được gỡ (nút ▶️ Chạy tiếp / Render ngay).
    FB.set_config(OWNER, {"last_safety_stop": None})   # kho ổn -> gỡ cờ dừng AN TOÀN do máy đặt
    # 25/8 — HUNG THỦ CUỐI của chuỗi plan chết 18': `process_requests` RENDER video ngay trong
    # plan — mỗi yêu cầu là một lượt render + đẩy kho nhiều phút, mà hàng đang có ~25 yêu cầu
    # (lô render-lại 24/8) ⇒ plan nào cũng chết trước khi kịp mở matrix; kiểm-kho/sync/guard chỉ
    # là kẻ tình nghi đứng gần hiện trường. Plan là NGƯỜI ĐIỀU PHỐI, không phải thợ render:
    # chỉ đếm hàng rồi giao cho lane (timeout 165') — lane nhận kênh nào thì render lại video của
    # kênh đó trước khi làm video mới (process_requests(chi_kenh=...) ở channel_mode).
    try:
        _n_req = len(FB.read_render_requests(OWNER))
        if _n_req:
            print(f"   🔄 {_n_req} yêu cầu render lại đang chờ — giao cho lane xử (plan không render).")
    except Exception:
        print_exc_gon()
    _moc("đọc danh sách kênh")
    all_ch = [c for c in FB.read_channels(OWNER) if c.get("name")]
    try:
        # LINT ĐỒNG BỘ KÊNH: mọi kênh render PHẢI có trong channels.yaml của publisher — thiếu là
        # video QC đạt vẫn bị enqueue TỪ CHỐI (đêm 21/8: DEBTUSA/FILEUSA/VOXUSA sót từ đầu, 3 video
        # QC 97-98 của DEBTUSA bị vứt). Phép so TẬP HỢP tự động, không đếm tay nữa.
        import yaml as _yaml
        _src = os.environ.get("AUTOPUBLISHER_SRC", "")
        _yp = os.path.join(os.path.dirname(_src.rstrip("/")), "config", "channels.yaml") if _src else ""
        if _yp and os.path.exists(_yp):
            _have_yaml = set((_yaml.safe_load(open(_yp)) or {}).get("channels") or {})
            _missing = sorted({c.get("name") for c in all_ch if c.get("name")} - _have_yaml)
            if _missing:
                print(f"   🚨 {len(_missing)} kênh render THIẾU trong channels.yaml (video sẽ bị enqueue từ chối): {_missing}")
    except Exception:
        print_exc_gon()
    try:
        _pf = policy_lint(all_ch)       # audit chính sách tự động (0 quota)
        policy_autofix(all_ch, _pf)     # thiếu rào chắn -> máy tự nối câu STRICT chuẩn
    except Exception:
        print_exc_gon()
    try:
        import time as _tt; _tt.sleep(2.5)   # hạ nhiệt sau loạt đọc policy/requests -> sync khỏi dính burst
        FB.sync_keys_from_a(OWNER)      # key mới thêm trên dashboard (ghi vào A) -> render thấy được
    except Exception:
        print_exc_gon()
    try:
        # TỰ-SEED WAVE 8: workflow seed chạy tay 21/8 dính đúng lúc B cạn quota ghi. Thay vì hẹn
        # người chạy lại, plan tự so wave8_channels.json với danh sách kênh -> thiếu thì ghi (qua
        # _soft: quota chết thì lượt sau tự thử tiếp). Đủ 10 kênh rồi thì đoạn này thành no-op 0 ghi.
        import json as _j
        _w8p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wave8_channels.json")
        if os.path.exists(_w8p):
            _have = {c.get("name") for c in all_ch}
            # 27/8 — KHÔNG HỒI SINH KÊNH ĐÃ NGHỈ. Tự-seed sinh ra để cứu lượt seed hỏng vì cạn
            # quota, nhưng nó so với `wave8_channels.json` một cách mù quáng: 55 kênh thế hệ 1 vừa
            # được dọn xong thì phiên sau nó ghi lại 15 cái. Đo thật đêm nay: 5 lane chạy
            # BALDBANDIT / UNDERUSA / MADEUSA / FAKEUSA / FIRSTUSA — toàn kênh đã xoá — trong khi
            # 50 kênh mới nằm chờ. Dọn bao nhiêu lần cũng vô nghĩa nếu có thứ tự dựng lại.
            # Không xoá `wave8_channels.json` (quy tắc: dọn chỉ đụng video, không đụng cấu hình);
            # chỉ chặn hồi sinh những tên nằm trong bản chụp kênh THẾ HỆ 1.
            _nghi = set()
            try:
                _snap = _j.load(open(os.path.join(os.path.dirname(_w8p), "kenh_the_he_1.json")))
                _nghi = {str(t).upper() for t in (_snap.get("ten") or [])}
            except Exception:
                pass
            _miss = {k: v for k, v in _j.load(open(_w8p)).items()
                     if k not in _have and str(k).upper() not in _nghi}
            if _nghi:
                _bo = [k for k in _j.load(open(_w8p)) if str(k).upper() in _nghi]
                if _bo:
                    print(f"   🪦 Tự-seed BỎ QUA {len(_bo)} kênh đã nghỉ (thế hệ 1): {', '.join(sorted(_bo)[:6])}"
                          + ("…" if len(_bo) > 6 else ""))
            if _miss:
                _db = FB._db_meta()
                for _nm, _cfg in _miss.items():
                    # 23/8: PHẢI ghi "name" — wave8_channels.json để tên ở KHOÁ dict, seed cũ quên
                    # đẩy vào doc -> 5 doc KHÔNG TÊN nằm song song 5 doc thật (dashboard đếm 60/55,
                    # matrix có thể cấp slot cho kênh vô danh). Kèm khoá theo tên chuẩn hoá.
                    FB._soft(lambda _n=_nm, _c=_cfg: _db.collection("render_channels")
                             .document(f"{OWNER}__{_n}").set({**_c, "name": _n, "owner": OWNER}, merge=True),
                             "seed_wave8")
                print(f"   🌱 Tự-seed Wave 8: đã gửi {len(_miss)} kênh còn thiếu (quota chết thì phiên sau tự thử lại).")
            # ĐỒNG BỘ CONFIG THEO REV (23/8): kênh ĐÃ TỒN TẠI nhưng file có cfg_rev MỚI HƠN thì đẩy
            # xuống Firestore. Vì sao cần: đổi format 5 kênh (skit -> essay) mà seed cũ chỉ thêm-nếu-thiếu
            # -> Firestore giữ config cũ, phiên sau vẫn render sai format. Chỉ ghi khi rev khác nhau
            # (idempotent, không đè lặp lại chỉnh tay của user ở các trường khác).
            _all_w8 = _j.load(open(_w8p))
            _by = {c.get("name"): c for c in all_ch}
            _sync = 0
            for _nm, _cfg in _all_w8.items():
                _rev = _cfg.get("cfg_rev")
                _cur = _by.get(_nm)
                if not (_rev and _cur) or _cur.get("cfg_rev") == _rev:
                    continue
                _patch = {k: v for k, v in _cfg.items() if k not in ("name",)}
                _patch["cfg_rev"] = _rev
                _cid = _cur.get("id")
                if _cid:
                    FB._soft(lambda _i=_cid, _p=_patch: FB._db_meta().collection("render_channels")
                             .document(_i).set(_p, merge=True), "sync_cfg_rev")
                    _sync += 1
                    _cur.update(_patch)      # lane trong CÙNG phiên này dùng ngay config mới
            if _sync:
                print(f"   🔄 Đồng bộ config từ file cho {_sync} kênh (cfg_rev mới) — format/niche/giọng cập nhật ngay phiên này.")
    except Exception:
        print_exc_gon()
    try:
        sweep_ai_quality(all_ch, cfg)   # xếp render lại các video ra đời khi bước vẽ ảnh AI còn hỏng
    except Exception:
        print_exc_gon()
    # ƯU TIÊN KÊNH MỚI (22/8, user): kênh priority=1 LUÔN có suất trong matrix (đứng đầu),
    # kênh cũ xoay ngẫu nhiên phần suất còn lại -> dồn lực cho 5 kênh mới mà cũ không chết hẳn.
    _nameless = [c for c in all_ch if not str(c.get("name") or "").strip()]
    if _nameless:
        print(f"   🧹 Bỏ qua {len(_nameless)} doc kênh KHÔNG TÊN (rác seed cũ) — không cấp slot render.")
        all_ch = [c for c in all_ch if str(c.get("name") or "").strip()]
    # 27/8 — LOẠI KÊNH THẾ HỆ 1 NGAY Ở KHÂU CHỌN, KHÔNG ĐỢI DỌN ĐƯỢC BẢN GHI.
    # Đêm nay dọn bản ghi kênh cũ tới bốn lượt vẫn còn sót: lượt cuối chết vì
    # `❌ không đọc được danh sách kênh (kể cả gương B2): 429 Quota exceeded` — công cụ quản trị
    # cần Firestore, mà Firestore đang cạn, nên đúng lúc cần dọn nhất thì không dọn được.
    # Trong khi đó phiên render vẫn chạy (nó dùng gói plan + D1, 0 lượt đọc) và cấp 18 lane cho
    # kênh cũ, mỗi lane ra 0 video — phí trọn một phiên.
    # Chốt ở đây KHÔNG cần Firestore, không tốn lượt nào: tên nằm trong bản chụp thế hệ 1 mà không
    # có trong bảng thế hệ 2 thì không được cấp slot, bất kể bản ghi còn hay đã xoá.
    _nghi_t1 = set()
    try:
        import json as _j2
        _g = os.path.dirname(os.path.abspath(__file__))
        _nghi_t1 = {str(t).upper() for t in
                    (_j2.load(open(os.path.join(_g, "kenh_the_he_1.json"))).get("ten") or [])}
        _k2 = _j2.load(open(os.path.join(_g, "kenh_the_he_2.json")))
        _k2 = _k2 if isinstance(_k2, list) else list(_k2.values())
        _nghi_t1 -= {str(x.get("ten", "")).replace(" ", "").upper() for x in _k2}
    except Exception as _e:
        print(f"   ⚠️ không đọc được bản chụp kênh thế hệ 1 ({str(_e)[:50]}) — bỏ qua chốt loại")
    def _con_dung(c):
        return str(c.get("name", "")).upper() not in _nghi_t1
    _bo_t1 = [c["name"] for c in all_ch if not _con_dung(c)]
    if _bo_t1:
        print(f"   🪦 LOẠI {len(_bo_t1)} kênh thế hệ 1 khỏi phiên (bản ghi chưa dọn được vì quota): "
              f"{', '.join(sorted(_bo_t1)[:8])}" + ("…" if len(_bo_t1) > 8 else ""))
    all_ch = [c for c in all_ch if _con_dung(c)]
    _pri = [c["name"] for c in all_ch if not c.get("paused") and int(c.get("priority") or 0) >= 1]
    channels = [c["name"] for c in all_ch if not c.get("paused") and int(c.get("priority") or 0) < 1]
    # XÁO THỨ TỰ mỗi phiên: Firestore trả channels theo ID tài liệu (~alphabet cố định) -> KHÔNG xáo thì cùng nhóm
    # đầu bảng chữ cái LUÔN vào 18 slot đầu (ưu tiên), nhóm cuối LUÔN bị đẩy xuống chờ mỗi phiên -> thiên vị có hệ
    # thống. Xáo ngẫu nhiên -> mỗi phiên 1 nhóm khác được ưu tiên, công bằng thật sự về lâu dài.
    random.shuffle(channels)
    channels = _pri + channels          # priority đứng đầu -> chắc suất trong MAX_MATRIX
    n_paused = len(all_ch) - len(channels)
    # 20/8: comment ở trên ("18 slot đầu") LUÔN giả định matrix chỉ có tối đa MAX_MATRIX kênh/phiên — nhưng
    # code TRƯỚC ĐÂY gửi NGUYÊN list (không cắt) -> khi tổng kênh > max-parallel (18, YAML), GitHub KHÔNG bỏ
    # qua phần dư mà XẾP HÀNG chạy tiếp đợt 2/3 NỐI TIẾP trong CÙNG workflow run -> 1 "phiên" kéo dài
    # 7-10+ tiếng (40 kênh/18 = 3 đợt × ~3.5h) thay vì ~3.5h như thiết kế, giữ khoá concurrency quá lâu,
    # nuốt mất cơ hội của các mẻ 4h kế tiếp -> tổng video/ngày sụt hẳn dù không lỗi gì. Cắt về đúng
    # MAX_MATRIX (khớp max-parallel YAML) -> mỗi phiên LUÔN 1 đợt, xong đúng hạn, nhường lượt sòng phẳng
    # cho phiên sau (đã xáo ngẫu nhiên nên nhóm bị cắt lần này ưu tiên lần sau).
    MAX_MATRIX = 18   # PHẢI khớp strategy.max-parallel trong .github/workflows/render_cron.yml
                      # Mẻ 10 long/30 short do round_long/round_short lo (trần TỪNG KÊNH mỗi phiên),
                      # không phải do số luồng -> 18 luồng vẫn đúng mẻ, chỉ phục vụ được nhiều kênh hơn.

    # CHỈ XẾP KÊNH CÒN VIỆC — 20/8: trước đây lấy đại 18 kênh mà KHÔNG xét kênh nào đã đủ chỉ tiêu.
    # Kênh đủ target vẫn được cấp 1 slot, job khởi động rồi thoát ngay -> nhìn dashboard thấy "đang
    # chạy 3" trong khi đã cấp 18 slot: phí 15 luồng mỗi phiên. Đếm phần CÒN THIẾU trước (count_done
    # dùng aggregation, ~1 read/kênh nên rẻ), bỏ kênh đã đủ, rồi ưu tiên kênh thiếu NHIỀU nhất.
    _by_ch = {c.get("name"): c for c in all_ch}
    need = []
    for nm in channels:
        c = _by_ch.get(nm) or {}
        # trần THẬT chỉ tồn tại khi anh tự đặt; không đặt = kho trôi (xem _muc_tieu)
        lt_raw = int(c.get("long_target", 0) or 0)
        st_raw = int(c.get("short_target", 0) or 0)
        try:
            # RẢI NHỊP 0.35s/kênh (22/8): ~106 lệnh count bắn liền tay là dính 429 BURST THEO PHÚT
            # của Firestore (13:55Z cả loạt chết dù _retry) -> sync/seed trượt theo. Chậm ~40s/plan
            # đổi lấy cả loạt đọc sống — rẻ.
            time.sleep(0.35)
            dl = FB.count_done(OWNER, nm, "long") if c.get("make_long", True) else 0
            ds = FB.count_done(OWNER, nm, "short")
        except Exception as e:
            print(f"   ⚠️ đếm {nm} lỗi ({str(e)[:50]}) -> vẫn cho vào hàng"); dl = ds = 0
        # Kênh CHỈ nghỉ khi anh đã tự đặt CẢ HAI chỉ tiêu và đã đạt. Không đặt -> luôn còn việc,
        # mỗi vòng làm đúng một mẻ round_long/round_short rồi nhường slot cho kênh khác.
        if lt_raw and st_raw and dl >= lt_raw and ds >= st_raw:
            continue
        need.append((dl + ds, nm))
    n_full = len(channels) - len(need)
    if need:
        # 22/8 tối: sort thuần theo "thiếu nhiều" từng XÓA SẠCH ưu tiên _pri xếp ở trên (kênh cũ
        # thiếu 30 video luôn đè kênh mới priority=1) -> sort 2 khóa: priority trước, thiếu sau.
        _prs = set(_pri)
        # 24/8 — CHIA ĐỀU: sắp theo TỔNG VIDEO ĐÃ CÓ, ÍT NHẤT ĐỨNG TRƯỚC. Khoá cũ (-x[0] = thiếu
        # nhiều nhất) chỉ đúng khi mọi kênh cùng một trần trọn đời; với kho trôi thì "còn thiếu" gần
        # như bằng nhau ở mọi kênh nên khoá đó vô nghĩa, và kênh nhiều video vẫn được làm tiếp trong
        # khi kênh mới nằm chờ. Sắp theo số đã có = kênh non được kéo lên ngang bằng trước.
        need.sort(key=lambda x: (0 if x[1] in _prs else 1, x[0]))
        channels = [nm for _, nm in need]
    else:
        print("🎯 Mọi kênh đã đủ chỉ tiêu — không mở phiên (khỏi đốt runner).")
        return out_channels([])
    # ══ PHẢN ÁP LỰC: ĐỪNG LÀM THỨ KHÔNG ĐĂNG ĐƯỢC (24/8/2026) ═══════════════════════════════
    # Đo thật: sản xuất ~976 video/ngày, đăng được 6 (YouTube cho 10.000 đơn vị/ngày mỗi dự án
    # Google Cloud, một lần đăng tốn 1.600). Tỉ lệ 163:1. Tồn 644 video -> cái xếp cuối phải chờ
    # 107 NGÀY mới tới lượt, mà nội dung nói số liệu 2026 thì lúc đó đã hỏng: làm ra để mốc.
    # Kể cả có đủ 37 dự án (222/ngày) thì vẫn dư 754/ngày — thêm dự án chỉ NỚI CỔ CHAI, không sửa
    # được lệch dòng chảy.
    # Cách chữa đúng (và là điều đầu tiên các hệ hàng đợi nghiêm túc làm): CHẶN NGƯỢC nơi sản xuất.
    # Kênh nào đã tồn quá `TON_TRAN` video chưa đăng thì NGƯNG làm thêm cho kênh đó, nhường máy cho
    # kênh đang đói. Hàng đợi không chặn được nơi sản xuất là một LỖI, không phải một tính năng.
    # Đo bằng SỐ NGÀY CÒN BÀI, không phải số video thô (anh chốt 24/8):
    #   "kênh nào sắp hết video lên lịch thì tự động ưu tiên, và nên chia đều".
    # Một kênh chạy nhịp 4 video/ngày mà tồn 28 cái = còn 7 NGÀY bài. Kênh nhịp 1 video/ngày mà tồn
    # 28 cái = còn 28 ngày — cùng con số 28 nhưng mức độ đói khác hẳn. Nên phải quy về NGÀY.
    # 25/8 — ANH CHỐT LẠI ĐÍCH: "đủ 7 ngày đệm ĐÂU PHẢI LÀ DỪNG — target 100 long, 300 short
    # mỗi channel, cứ làm tối ưu". Vậy phản áp lực đổi thước đo: không đo "còn mấy ngày bài chưa
    # đăng" nữa mà đo ĐỘ ĐẦY KHO so với ĐÍCH KHO của từng kênh. Ưu tiên vẫn là kênh VƠI NHẤT
    # trước (chính là "làm đều videos các channel" anh dặn) — chỉ kênh đã đầy CẢ long lẫn short
    # mới nhường máy. Đích đọc từ cấu hình kênh (target_long/target_short) nếu có, mặc định 100/300.
    TARGET_LONG = int(os.environ.get('TARGET_LONG') or '100')
    TARGET_SHORT = int(os.environ.get('TARGET_SHORT') or '300')
    try:
        import hot_db as _H
        _dem = _H.nap_dem(OWNER)     # {"CHANNEL|vtype": n} — 1 lời gọi cho mọi kênh
        if _dem is None:
            print(f"   📦 Độ đầy kho: KHÔNG có số đếm từ D1 (chế độ {_H.che_do()}) -> "
                  f"PHẢN ÁP LỰC KHÔNG CHẠY phiên này, thứ tự kênh giữ như cũ.")
        else:
            try:
                _cfg_kenh = {str(c.get('name') or '').upper(): c for c in all_ch}
            except Exception:
                _cfg_kenh = {}
            def _muc(c, loai):
                cf = _cfg_kenh.get(str(c).upper()) or {}
                if loai == 'long':
                    return int(cf.get('target_long') or TARGET_LONG)
                return int(cf.get('target_short') or TARGET_SHORT)
            def _co(c, loai):
                return _dem.get(f"{str(c).upper()}|{loai}", 0)
            def _do_day(c):
                """0.0 = kho trống, 1.0 = đã đạt đích cả hai loại."""
                return min(_co(c, 'long') / max(1, _muc(c, 'long')),
                           _co(c, 'short') / max(1, _muc(c, 'short')))
            # 1) LÀM ĐỀU + LUÂN PHIÊN (anh dặn 25/8: "không channel nào nhiều quá, không được
            # chạy 1 phát lên target — luân phiên 55 channel để đều nhau"). Hai tầng bảo đảm:
            #   • sắp theo độ đầy: kênh vơi nhất lên đầu, nên không kênh nào bị bỏ lại;
            #   • mỗi kênh mỗi phiên chỉ làm đúng khẩu phần round_long/round_short (đã có sẵn),
            #     nên cũng không kênh nào ăn một phát lên đích.
            # Hoà độ đầy thì xoay theo NGÀY (băm tên+ngày) — không thiên vị bảng chữ cái, hôm nay
            # nhóm này trước thì mai nhóm khác trước.
            import hashlib as _hh
            _ngay_xoay = __import__('datetime').date.today().isoformat()
            def _xoay(c):
                return _hh.md5(f"{c}|{_ngay_xoay}".encode()).hexdigest()
            channels = sorted(channels, key=lambda c: (round(_do_day(c), 2), _xoay(c)))
            _day = [c for c in channels if _co(c, 'long') >= _muc(c, 'long')
                    and _co(c, 'short') >= _muc(c, 'short')]
            _voi = [c for c in channels if c not in _day]
            _suc = _H.suc_dang_ngay()
            print(f"   📦 Độ đầy kho: đích {TARGET_LONG} long + {TARGET_SHORT} short/kênh · "
                  f"{len(_day)} kênh đã đầy · {len(_voi)} kênh còn vơi · "
                  + (f"đăng được hôm nay: {_suc}" if _suc >= 0
                     else "sức đăng hôm nay: CHƯA BIẾT (bảng dự án YouTube trên D1 còn trống)"))
            if _voi:
                print("      vơi nhất: " + ", ".join(
                    f"{c}={_co(c,'long')}L/{_co(c,'short')}S" for c in _voi[:6]))
            if _day:
                print(f"   🛑 PHẢN ÁP LỰC: {len(_day)} kênh đã ĐẠT ĐÍCH KHO (không phải mốc 7 ngày) "
                      f"-> nhường máy cho {len(_voi)} kênh còn vơi.")
                channels = _voi or channels[:1]
    except Exception as _e:
        print(f"   ⚠️ không đọc được độ đầy kho ({str(_e)[:50]}) — chạy như cũ")

    # PILOT (23/8 — user: "chưa kiểm tra đẩy lên xong render rồi kịch bản lộn xộn thì sao"): chạy
    # ĐÚNG 1 KÊNH, 1 short để soi trọn chuỗi viết → soi kịch bản → render → thumbnail → đẩy kho,
    # trước khi mở 18 luồng. Bật bằng env PILOT_CHANNEL=<TÊN KÊNH>.
    _pilot = (os.environ.get("PILOT_CHANNEL") or "").strip().upper()
    if _pilot:
        channels = [c for c in channels if str(c).upper() == _pilot] or [_pilot]
        print(f"🧪 PILOT: chỉ chạy {channels[0]} (1 video) để kiểm trọn chuỗi trước khi mở 18 luồng.")
        return out_channels(channels[:1])
    if len(channels) > MAX_MATRIX:
        # Phần dư KHÔNG còn phải "đợi phiên sau" nữa: đưa vào HÀNG CHỜ để luồng nào xong trước thì
        # lấy tiếp (xem lay_viec_ke). 18 slot vẫn là số máy, nhưng số kênh làm được trong một phiên
        # giờ phụ thuộc THỜI GIAN CÒN LẠI chứ không phải số slot.
        _du = channels[MAX_MATRIX:]
        _du_hang = list(_du)          # gửi kèm xuống lane (xem out_channels)
        FB.dat_hang_cho(OWNER, _du)
        print(f"   ✂️ {len(channels)} kênh còn việc > {MAX_MATRIX} slot -> {MAX_MATRIX} kênh vào mẻ, "
              f"{len(_du)} kênh vào HÀNG CHỜ (luồng nào xong trước tự lấy, không ngồi không).")
        channels = channels[:MAX_MATRIX]
    else:
        FB.dat_hang_cho(OWNER, [])          # không dư -> dọn hàng chờ cũ, tránh luồng lấy việc rác
    _cfg_goi = all_ch          # cấu hình plan ĐÃ đọc được -> gửi kèm cho lane (xem out_channels)
    _kiem_kho_ngay(cfg)        # đối chiếu sổ đếm với SỐ THẬT trên Drive, 1 lần/ngày (xem hàm)
    print(f"▶ {len(channels)} kênh -> render SONG SONG."
          + (f" (⏸ {n_paused} pause)" if n_paused else "")
          + (f" (🎯 {n_full} kênh đã đủ chỉ tiêu, bỏ qua)" if n_full else ""))
    out_channels(channels, cau_hinh=_cfg_goi)


def _kiem_kho_ngay(cfg: dict) -> None:
    """ĐỐI CHIẾU SỔ ĐẾM VỚI SỐ THẬT TRÊN DRIVE — 1 lần/ngày, chạy NGAY TRONG PLAN (25/8/2026).

    Vì sao ở đây chứ không phải workflow riêng: `wipe_queue` chạy `kiem_kho.py` đếm được số thật
    (1.996 video) nhưng **ghi sổ luôn trả `400 Invalid database id`**, trong khi plan của render_cron
    ghi Firestore bình thường suốt đêm. Đặt việc đối chiếu vào nơi lệnh ghi CHẮC CHẮN chạy được thì
    con số tự đúng mỗi ngày, không cần ai bấm nút.
    Bộ đếm `__pushed__` chỉ cộng (render lại +1, dọn rác vẫn +1) nên KHÔNG BAO GIỜ tự đúng lại được;
    chỉ có đếm lại từ Drive mới kéo nó về sự thật.
    Rẻ: đi 72 kho mất ~35 giây, mỗi ngày một lần. Đọc kho qua `pool_accounts` (có gương + lớp cứu KV)
    nên không tốn hạn mức Firestore."""
    try:
        from datetime import datetime as _d3, timezone as _tz3
        ngay = _d3.now(_tz3.utc).strftime("%Y%m%d")
        if str(cfg.get("kiem_kho_ngay") or "") == ngay:
            return                                   # hôm nay đối chiếu rồi
        # CHỐT PHẢI NẰM Ở CHỖ GHI ĐƯỢC. Chốt trên chỉ đọc `render_config` ở Firestore — mà lượt GHI
        # vào Firestore đang trả 400 (xem 7.dm). Ghi hụt ⇒ chốt không bao giờ đóng ⇒ plan đi 72 kho
        # MỖI LƯỢT (~48 lượt/ngày × 72 kho ≈ 3.500 lượt quét) thay vì 1 lần. Đúng thứ anh dặn phải
        # tránh: tối ưu mà đẻ ra lãng phí lớn hơn.
        # D1 luôn ghi được và không nằm trong tài nguyên đang cạn -> đặt chốt ở đó, hạn 20 giờ.
        try:
            import hot_db as _H
            _gio = _d3.now(_tz3.utc).isoformat()
            if any(str(r.get("kid") or "") == "kiem_kho"
                   for r in (_H.key_nghi_doc(_gio) or [])):
                return                               # chốt D1 còn hiệu lực -> khỏi đi lại
        except Exception:
            pass
        src = os.environ.get("AUTOPUBLISHER_SRC")
        if src and src not in sys.path:
            sys.path.insert(0, src)
        import storage as _ST
        accs = _ST.pool_accounts() or []
        if len(accs) < 5:
            print(f"   ⏭ Kiểm kho: chỉ đọc được {len(accs)} kho — BỎ QUA (đếm thiếu còn tệ hơn không đếm).")
            return
        import kiem_kho as _KK
        # 25/8 — CHÍNH BƯỚC NÀY (chứ không riêng sync dung lượng) giết plan 07:05Z và 07:28Z:
        # 72 kho đi bộ TUẦN TỰ, mỗi kho liệt kê toàn bộ file theo trang, tổng 12-15 phút — mà nó
        # đứng ngay TRƯỚC lệnh xuất matrix nên 18 luồng không bao giờ được mở, phiên chết ở
        # timeout 18'. Rơi đúng lượt plan đầu tiên sau mốc reset ngày (chu kỳ 20h) nên "mỗi ngày
        # chết một buổi". Cùng công thức với sync dung lượng: 8 luồng song song + ngân sách 240s.
        # DỞ DANG THÌ BỎ NGUYÊN LƯỢT (giữ nguyên tắc của kiem_kho.py: số thiếu độc hơn không có
        # số — dashboard từng "tụt kho ảo" vì ghi số đếm hụt), phiên sau đi tiếp.
        import concurrent.futures as _cf2, time as _t10
        _han = _t10.time() + 240
        song = 0
        hong = 0
        # 25/8 — NHẶT LUÔN MAP FILE->KHO trong cùng lượt đi bộ (0 lượt Drive thêm): bản ghi thời
        # Firestore-nghẽn thiếu drive_account nên thư viện hiện "kho chưa rõ" hàng loạt. Lượt này
        # vốn đi qua từng file — thấy file nào nằm trong danh sách đang thiếu thì ghi lại kho.
        try:
            import hot_db as _HD
            _thieu = _HD.kho_can_acc(OWNER)          # {drive_id: job_id} — thiếu KHO CHỨA
            _tcan = _HD.thumb_can(OWNER)             # {drive_id: job_id} — thiếu THUMBNAIL
        except Exception:
            _thieu, _tcan = {}, {}
        _thay = []                                    # [{'did':..., 'acc':...}]
        _tthay = []                                   # [{'did':..., 'tid':...}]
        def _dem_kho(acc):
            drv = _ST.account_drive(acc)
            n = 0
            mp4_can = {}                              # {tên gốc: drive_id} video thiếu thumb ở kho này
            jpg_co = {}                               # {tên gốc: id .jpg} ảnh thấy trong kho này
            for f in _KK._quet(drv, acc.get("root")):
                ten = str(f.get("name", ""))
                t = ten.lower()
                if t.endswith(".mp4"):
                    n += 1
                    if f.get("id") in _thieu:
                        _thay.append({"did": f["id"], "acc": acc.get("name") or ""})
                    if f.get("id") in _tcan:
                        mp4_can[ten[:-4]] = f["id"]
                elif t.endswith((".jpg", ".jpeg", ".png")):
                    jpg_co[ten.rsplit(".", 1)[0]] = f.get("id")
            # .jpg thumbnail nằm CẠNH video, CÙNG TÊN GỐC (sidecar["thumbnail"] = vbase + ext)
            for goc, vid in mp4_can.items():
                tid = jpg_co.get(goc)
                if tid:
                    _tthay.append({"did": vid, "tid": tid})
            return n
        _ex2 = _cf2.ThreadPoolExecutor(max_workers=8)
        _viec = {_ex2.submit(_dem_kho, a2): a2 for a2 in accs}
        try:
            for _f2 in _cf2.as_completed(_viec, timeout=max(15, _han - _t10.time())):
                try:
                    song += _f2.result()
                except Exception:
                    hong += 1
        except _cf2.TimeoutError:
            hong += sum(1 for f2 in _viec if not f2.done())
            print(f"   ⏳ Kiểm kho chạm ngân sách 240s — dở dang, BỎ lượt này (phiên sau đi tiếp).")
        finally:
            _ex2.shutdown(wait=False, cancel_futures=True)
        if _thay or _tthay:
            try:
                import hot_db as _HD2
                _n_acc = _HD2.kho_acc_ghi(OWNER, _thay) if _thay else 0
                _n_th = _HD2.thumb_ghi(OWNER, _tthay) if _tthay else 0
                print(f"   🧭 Lấp bản ghi từ lượt đi bộ (0 lượt Drive thêm): "
                      f"kho chứa {_n_acc}/{len(_thieu)} · thumbnail {_n_th}/{len(_tcan)}.")
            except Exception:
                pass
        if hong:
            print(f"   ⏭ Kiểm kho: {hong}/{len(accs)} kho đọc hụt — BỎ QUA lượt ghi (sẽ đếm thiếu).")
            return
        FB.dat_so_kho_that(OWNER, song)
        try:                                          # đóng chốt ở D1 TRƯỚC (chắc chắn ghi được)
            import hot_db as _H2
            _den = (_d3.now(_tz3.utc) + __import__("datetime").timedelta(hours=20)).isoformat()
            _H2.key_nghi_ghi("kiem_kho", "ngay", _den)
        except Exception:
            pass
        FB.set_config(OWNER, {"kiem_kho_ngay": ngay})
        try:                                          # cùng nhịp 1 lần/ngày: giữ D1 khỏi phình
            _r = _H2.don_job_cu(OWNER, 14)
            if _r.get("xoa"):
                print(f"   🧹 D1: dọn {_r['xoa']:,} bản ghi job cũ hơn {_r.get('giu_ngay')} ngày "
                      f"(còn {_r.get('con_lai'):,}) — giữ mức đọc D1 phẳng, không phình theo thời gian.")
        except Exception:
            pass
        print(f"   🧮 Kiểm kho: {song:,} video THẬT trên {len(accs)} kho -> đã ghi đè sổ đếm "
              f"(bộ đếm cộng dồn không tự đúng lại được).")
    except Exception as e:
        print(f"   ⚠️ Kiểm kho hụt ({str(e)[:70]}) — bỏ qua, không ảnh hưởng phiên.")


def _viec_chia_san(ten_lane: str, da_lam: set) -> str:
    """Lấy việc kế mà KHÔNG cần Firestore (24/8 tối).

    `FB.lay_viec_ke` giành việc bằng giao dịch trên Firestore — đúng thứ đang cạn hạn mức: log
    GRIDIRON phiên 21:52Z `⚠️ lấy việc kế hụt (429 Quota exceeded.)`. Hàng chờ nằm trong tài nguyên
    đã hết thì đúng lúc cần nhất nó không dùng được.
    Đường thay thế: plan gửi kèm danh sách dư (`QUEUE_LIST`) và thứ tự mẻ (`PLAN_CHANNELS`) qua env.
    Lane tự cắt phần của mình theo VỊ TRÍ trong mẻ: lane thứ i lấy các mục i, i+N, i+2N… Chia tĩnh
    nên **không cần điều phối và không thể trùng** — đổi lại nếu một lane chết thì phần của nó chờ
    phiên sau (chấp nhận được: hiện tại phần dư CHẲNG AI làm cả)."""
    try:
        ds = json.loads(os.environ.get("QUEUE_LIST") or "[]")
        me = json.loads(os.environ.get("PLAN_CHANNELS") or "[]")
        if not ds or not me:
            return ""
        i = [str(x).upper() for x in me].index(str(ten_lane).upper())
        n = max(1, len(me))
        for k in range(i, len(ds), n):
            if str(ds[k]).upper() not in {str(x).upper() for x in da_lam}:
                return str(ds[k])
    except Exception:
        pass
    return ""


def channel_mode(name):
    """RENDER 1 KÊNH (1 luồng của matrix). Đọc reserve + tôn trọng cờ Dừng (per-clip trong run_one)."""
    if not OWNER:
        raise SystemExit("❌ Thiếu OWNER_UID.")
    FB.quota_pulse(OWNER)   # lane = tiến trình riêng: ≥90% trần thì tự lật B2 chủ động ngay từ đầu lane
    cfg = FB.read_config(OWNER)
    global RESERVE_LONG, RESERVE_SHORT
    RESERVE_LONG = int(cfg.get("reserve_long", RESERVE_LONG) or RESERVE_LONG)
    RESERVE_SHORT = int(cfg.get("reserve_short", RESERVE_SHORT) or RESERVE_SHORT)
    if cfg.get("stop"):
        print(f"⛔ Đang dừng — bỏ {name}."); return
    keys = FB.read_keys(OWNER)
    if not keys:
        raise SystemExit("❌ Chưa có Gemini key.")
    # 1 read (không đọc cả 15 kênh). Đọc HỎNG ≠ kênh bị xoá — xem FB.read_one_channel: trước đây
    # gộp hai chuyện làm một nên một lệnh đọc trục trặc là mất trắng một lane (~2 tiếng máy).
    import time as _tg
    one = None
    for _l in range(3):
        try:
            one = FB.read_one_channel(OWNER, name); break
        except FB.DocLoi as e:
            if _l == 2:
                raise SystemExit(f"❌ {name}: {e} — DỪNG lane (KHÔNG phải kênh bị xoá; "
                                 f"phiên sau tự làm lại).")
            print(f"   ⚠️ {name}: {e} — thử lại lần {_l + 2}/3…"); _tg.sleep(5 * (_l + 1))
    if not one:
        print(f"⚠️ Kênh {name} không còn (đã xóa) — bỏ."); return
    if one.get("paused"):
        print(f"⏸ {name}: đang PAUSE — bỏ qua (bấm ▶ Chạy để tiếp)."); return
    # 25/8 — LANE xử yêu cầu render-lại CỦA KÊNH MÌNH trước khi làm video mới (plan không render
    # nữa, xem chú thích ở plan_mode: 25 yêu cầu tồn đọng từng giết 3 plan liên tiếp ở timeout 18').
    try:
        _rep_rq = {"done": 0, "fails": []}
        process_requests(keys, _rep_rq, chi_kenh=name)
        if _rep_rq["done"]:
            print(f"   🔄 {name}: đã render lại {_rep_rq['done']} video theo yêu cầu.")
    except Exception:
        print_exc_gon()
    chs = [one]
    # STAGGER theo kênh (0-18s): 10 luồng KHÔNG gọi Gemini/Drive cùng 1 khoảnh khắc -> đỡ bị coi là burst/lạm dụng.
    import time
    delay = sum(ord(c) for c in name) % 18
    if delay:
        print(f"   ⏳ {name}: giãn {delay}s (chống burst song song)…"); time.sleep(delay)
    report = {"done": 0, "fails": [], "rl": 0}
    # VÒNG LẶP A-Z: làm LIÊN TỤC nhiều mẻ trong 1 phiên tới khi — ĐỦ TARGET / HẾT GIỜ (trừ hao) / HẾT QUOTA / KHO ĐẦY / bấm Dừng.
    # 22/8: ĐỒNG BỘ với timeout matrix THẬT (165') — bộ số cũ (210'/330') viết thời timeout 350',
    # hậu quả phiên 07:40Z: 16/18 lane bị trần 150' chém giữa chừng vì lane tưởng còn cả tiếng.
    # Ngân sách mềm 110' + cứng 150' (chừa 15' buffer setup/flush/render đang dở) -> lane TỰ thoát
    # sạch sẽ (flush đủ, không job ma, không phí render dở) trước khi workflow kịp chém.
    # 25/8 — PHIÊN NGẮN LẠI ĐỂ THÔNG XE. Đo thật: phiên 08:55 giữ khoá `concurrency` suốt 150',
    # số lane rơi 18 → 3 → 1 (kênh nào xong thì lane THOÁT, runner được trả lại — nhưng khoá vẫn
    # do lane cuối giữ). Hậu quả đo được: **hai phiên 10:03 và 10:44 bị HUỶ TRẮNG**, không một lane
    # nào chạy. Tức 2,5 giờ chỉ có một mẻ 18 lane rồi thoi thóp, còn 16 chỗ runner bỏ không.
    # Rút ngân sách xuống 60'/75' thì cứ ~80 phút có một mẻ ĐỦ 18 LANE mới, đuôi thưa ngắn hơn
    # hẳn và không phiên nào bị huỷ. Long nặng nhất ~50' vẫn lọt (vòng lặp đã tự kiểm
    # "còn giờ < ước tính mẻ → dừng" nên không có video nào bị cắt ngang).
    # 27/8 — DÙNG HẾT QUỸ THỜI GIAN GITHUB CHO, THAY VÌ 1/5.
    #
    # Giới hạn job của GitHub là 6 TIẾNG. Lane đang tự dừng ở 75' (timeout matrix 90'), nên mỗi
    # lượt cron chỉ khai thác ~1/5 quỹ được cấp. Đo thật: hai phiên gần nhất chạy 62' và 70'.
    # Mà nhịp cron thì GitHub bóp còn 4-6 lượt/ngày (đo: 04:59 · 23:38 · 20:17 · 18:20). Hai
    # chuyện đó cộng lại thành ~5 giờ chạy/ngày trên một hạ tầng cho phép ~24.
    # KHÔNG kéo thẳng lên 5,5 tiếng, dù GitHub cho phép. Ngày 25/8 đã có bài học: một phiên giữ
    # khoá `concurrency` 150 phút trong khi SỐ LANE RƠI 18 -> 3 -> 1, hai phiên sau bị huỷ trắng
    # — 2,5 giờ chỉ ra một mẻ, 16 chỗ runner bỏ không. Phiên dài chỉ tốt khi lane KHÔNG rơi.
    # Nay điều đó đã khác: có hàng chờ, lane xong sớm tự lấy kênh tiếp (đo phiên 04:59Z: 38 lượt
    # "lấy việc kế"). Nhưng đó là bằng chứng cho 150', chưa phải cho 330' — nên đi từng bước và
    # đo lại, thay vì tin vào lý thuyết.
    # 150' ≈ gấp đôi mức cũ (đo thật hai phiên gần nhất: 62' và 70').
    #
    # Vòng lặp vốn đã tự kiểm "còn giờ < ước tính một mẻ -> dừng" nên kéo trần KHÔNG làm video
    # nào bị cắt ngang: nó chỉ cho phép chạy thêm mẻ khi còn đủ giờ cho trọn mẻ đó.
    budget_s = int(cfg.get("batch_budget_min", 150) or 150) * 60
    HARD_S = 150 * 60                                               # lane tự thoát 150'; workflow chém 180
    max_run = int(cfg.get("max_per_run", 0) or 0)                   # 0 = ∞ (vòng lặp tự giới hạn theo target/quota/giờ); >0 = trần cứng/kênh/phiên
    # ROUND CAP (xoay vòng công bằng): mỗi kênh làm TỐI ĐA round_long/round_short video RỒI NHƯỜNG SLOT (không cắt ngang —
    # check SAU khi run_one() hoàn tất trọn video). Mặc định 10 long/30 short -> phiên xong sớm hơn, kênh khác kịp có lượt.
    # 0 = không giới hạn round (giữ hành vi cũ, chạy tới hết target/giờ/quota).
    _rl, _rs = cfg.get("round_long"), cfg.get("round_short")        # None (chưa set) = mặc định 10/30; 0 = anh chọn "không giới hạn"
    round_long = int(_rl) if _rl is not None else 10
    round_short = int(_rs) if _rs is not None else 30
    # 23/8 (user chốt: "nâng chất, giảm lượng"): kênh TOON siết mẻ còn 2 long / 6 short mỗi phiên.
    # Lý do: toon nay vẽ tới 16 khung/skit (mật độ ảnh ×2-3) + hiệu ứng rối giấy -> mỗi video nặng
    # gấp bội; chạy ít mà kỹ thì FLUX/Vision có chỗ thở, video nào ra cũng đủ đô, thay vì 30 cái
    # hao hao nhau. Kênh cũ (doc/race) giữ nguyên nhịp — chúng rẻ và đã ổn định.
    if str(one.get("format", "")).lower() == "toon":
        # 23/8 — PHIÊN RA MẮT: kênh essay siết còn 1 long + 3 short/phiên. Lý do: mỗi video giờ nặng
        # (16 khung FLUX + QC lưới 2 đầu + loudnorm) và đây là mẻ ĐẦU của format mới -> làm ít mà
        # chắc, soi kỹ rồi mới nới. Đổi round_long/round_short trên dashboard là ghi đè được.
        _ess = str(one.get("toon_mode", "")).lower() == "essay"
        round_long = int(_rl) if _rl is not None else (1 if _ess else 2)
        if (os.environ.get("PILOT_CHANNEL") or "").strip():
            round_long, round_short = 0, 1          # pilot: đúng 1 short, đủ để soi chất lượng
        round_short = int(_rs) if _rs is not None else (3 if _ess else 6)
        print(f"   🎨 TOON chế độ CHẤT: mẻ tối đa {round_long} long / {round_short} short (ảnh dày + rối giấy).")
    MAX_EMPTY = int(cfg.get("empty_retry", 4) or 4)                 # số vòng LIỀN ra 0 video (do rate-limit) rồi mới chịu ngừng -> quota cạn thật
    start = time.monotonic(); rounds = 0; last_dur = 0; empty_streak = 0
    _het_key_lien = 0        # số kênh liên tiếp hỏng vì hết key (xem thoát sớm bên dưới)
    while True:
        rounds += 1
        remain = min(budget_s, HARD_S) - (time.monotonic() - start)
        need = max(last_dur * 1.3, 20 * 60)    # TRỪ HAO: ước tính mẻ tới = mẻ vừa rồi ×1.3 (tối thiểu 20')
        if rounds > 1 and remain < need:       # còn ít giờ hơn 1 mẻ -> DỪNG, để phiên SAU làm (tránh bị timeout giết giữa chừng = phí)
            print(f"   ⏱ {name}: còn {remain/60:.0f}' < ước tính {need/60:.0f}'/mẻ → DỪNG, phiên sau tự làm tiếp (tránh treo/phí)."); break
        if FB.read_config(OWNER).get("stop"):
            print(f"   ⛔ {name}: có lệnh Dừng → ngừng."); break
        # 1 READ/vòng (thay vì 15): bắt PAUSE + đổi target kịp, tiết kiệm Firestore.
        # Đọc hỏng giữa chừng thì GIỮ cấu hình vòng trước và làm tiếp — lane đang ra video, không
        # được để một lệnh đọc trục trặc kết liễu phần giờ còn lại của nó.
        try:
            one = FB.read_one_channel(OWNER, name)
        except FB.DocLoi as e:
            print(f"   ⚠️ {name}: {e} — giữ cấu hình vòng trước, làm tiếp."); one = chs[0]
        if not one:
            print(f"   ⚠️ {name}: kênh đã bị xóa → ngừng."); break
        if one.get("paused"):   # ⏸ PAUSE: clip hiện tại đã XONG (check ở đầu vòng sau) -> dừng, giữ nguyên tiến độ, KHÔNG cắt ngang
            print(f"   ⏸ {name}: đã PAUSE (đã làm xong clip đang dở + upload) → ngừng."); break
        chs = [one]
        before = report["done"]; before_rl = report.get("rl", 0); t0 = time.monotonic()
        try:
            run_one(chs[0], keys, report=report)
        except BaseException as e:
            print_exc_gon()
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
    # ── XONG KÊNH CỦA MÌNH THÌ LẤY VIỆC KẾ, KHÔNG NGỒI KHÔNG ────────────────────────────────
    # 24/8 tối — LỖI ĐẶT NHẦM CHỖ, đo được: mọi lane đều kết thúc bằng
    #   `⏱ DEBTUSA: còn 58' < ước tính 68'/mẻ → DỪNG`
    # rồi thoát, trong khi plan vừa xếp **32 kênh vào HÀNG CHỜ**. Dòng `♻️ Luồng rảnh -> nhận thêm
    # kênh` CHƯA TỪNG xuất hiện trong bất kỳ log lane nào — vì vòng lấy-việc-kế được viết trong
    # `main()`, mà matrix chạy `run_render.py --channel X` tức vào `channel_mode()`. Hai đường vào
    # khác nhau, tính năng nằm ở đường KHÔNG được dùng.
    # Giá phải trả: 18 lane × ~58 phút bỏ không mỗi phiên (~17 giờ máy), còn hàng chờ thì chỉ để đó.
    try:
        _da_lam = {name}
        _by_name = {}
        while True:
            # ĐO THEO TRẦN THẬT (HARD_S), KHÔNG theo ngân sách mềm — 24/8 tối, đo được:
            # lane dừng với `còn 57' < ước tính 69'/mẻ` rồi thoát, dòng `♻️ … rảnh` KHÔNG hề xuất
            # hiện. Vì vòng này dùng LẠI ĐÚNG cái ngưỡng vừa chặn vòng trên (`min(budget_s, HARD_S)`
            # = 110'), nên nó luôn break ngay lượt đầu — bản vá 7.ci đúng chỗ nhưng vô hiệu.
            # Số thật: lane tiêu 53' trong khi trần cứng là 150' (timeout matrix 165' − 15' đệm).
            # Còn 97' — thừa cho một mẻ 69'. Ngân sách mềm 110' sinh ra để một KÊNH đừng ôm máy quá
            # lâu; phần giờ thừa thì phải chảy về HÀNG CHỜ, không phải bỏ không.
            _con_s = HARD_S - (time.monotonic() - start)
            _need = max(last_dur * 1.3, 20 * 60)
            if _con_s < _need:
                break                     # không đủ giờ cho một mẻ nữa -> nghỉ thật
            # 24/8 tối — SUÝT LẶP LẠI "bản vá không chạy". Ba lệnh Firestore trong vòng này
            # (`read_config`, `lay_viec_ke`, `read_channels`) đều có thể ném 429 — mà chỉ
            # `lay_viec_ke` được bọc. Lệnh đầu ném là rơi thẳng xuống `except` ngoài cùng, in
            # "lấy việc kế hụt" rồi thoát: đường chia-sẵn (không cần Firestore) KHÔNG BAO GIỜ được
            # dùng tới. Bọc từng lệnh một, và mặc định phải là "chạy tiếp", không phải "chết".
            try:
                if FB.read_config(OWNER).get("stop"):
                    print("   ⛔ Có lệnh Dừng — không lấy thêm việc."); break
            except Exception:
                pass          # không đọc nổi cờ Dừng -> coi như không có lệnh dừng, làm tiếp
            _ke = ""
            try:
                _ke = FB.lay_viec_ke(OWNER)   # giao dịch nguyên tử -> 18 máy không nhận trùng kênh
            except Exception as _e:
                print(f"   ⚠️ hàng chờ trên Firestore không dùng được ({str(_e)[:50]}) — "
                      f"chuyển sang phần chia sẵn của lane.")
            if not _ke:
                _ke = _viec_chia_san(name, _da_lam)   # đường không cần Firestore, xem hàm
            if not _ke:
                break                     # hết việc thật
            if _ke in _da_lam:
                continue
            _da_lam.add(_ke)
            # 26/8 — ĐẢO THỨ TỰ: hỏi GÓI CỦA PLAN trước, Firestore chỉ là đường lùi.
            # Trước đây lane đọc `read_channels` rồi mới fallback về gói plan — nhưng gói plan
            # CHÍNH LÀ dữ liệu plan vừa đọc ở đầu phiên, mới hơn hoặc bằng thứ lane sắp đọc.
            # Đọc lại chỉ để nhận cùng câu trả lời: 5.460 lượt Firestore mỗi ngày, đổi lấy 0.
            # Đây là GỘP (bỏ lượt hỏi trùng), không phải CẮT (bỏ tính năng) — cấu hình vẫn đủ.
            _ch2 = FB._cfg_tu_plan().get(str(_ke).upper())
            if not _ch2:
                if not _by_name:          # gói plan thiếu kênh này -> mới đụng Firestore
                    try:
                        _by_name = {c.get("name"): c for c in FB.read_channels(OWNER) if c.get("name")}
                    except Exception as _e:
                        _by_name = {"_": None}
                        print(f"   ⚠️ không đọc được danh sách kênh ({str(_e)[:45]}) — "
                              f"dùng gói cấu hình plan gửi kèm.")
                _ch2 = _by_name.get(_ke)
            if not _ch2:
                print(f"   ⚠️ hàng chờ có {_ke} nhưng không thấy cấu hình — bỏ qua."); continue
            print(f"\n♻️ {name} rảnh -> nhận thêm kênh {_ke} từ hàng chờ "
                  f"(còn {_con_s / 60:.0f}' ngân sách).")
            _t2 = time.monotonic()
            # 26/8 — THOÁT SỚM KHI CẢ POOL KEY ĐÃ CẠN. Phiên 21:32: 7 lane chạy hết ngân sách để
            # ra ĐÚNG 1 video, với 54 lượt "hết key viết". Hết key thì kênh nào cũng hỏng y như
            # nhau — bốc thêm kênh chỉ tốn phút máy GitHub (free có hạn theo tháng).
            #
            # ⚠️ BẢN VÁ ĐẦU ĐẶT SAI CHỖ, ĐO MỚI BIẾT. Nó bắt ở `except BaseException` quanh
            # `run_one` — nhưng `run_one` có 11 khối except và TỰ ghi lỗi vào `report["fails"]`,
            # gần như không bao giờ ném lên. Phiên 22:52 có 80 lượt "hết key" mà dòng thoát sớm
            # in ra ĐÚNG 0 LẦN. Nay đếm trên `report["fails"]` — nơi lỗi thật sự đọng lại.
            _truoc = len(report.get("fails") or [])
            _xong = int(report.get("done") or 0)
            try:
                run_one(_ch2, keys, report=report)
            except BaseException as e:
                print_exc_gon(); report["fails"].append(f"{_ke}: {str(e)[:120]}")
            _moi = (report.get("fails") or [])[_truoc:]
            if int(report.get("done") or 0) > _xong:
                _het_key_lien = 0                       # có video ra -> pool còn sống
            elif _moi and all(any(t in str(x) for t in
                                  ("hết key viết", "KHÔNG CÒN KEY NÀO", "pool vẽ ảnh CẠN SẠCH"))
                              for x in _moi):
                _het_key_lien += 1
                if _het_key_lien >= 3:
                    print(f"   🛑 {name}: 3 kênh liên tiếp hết key — dừng lane, trả phút máy lại "
                          f"cho phiên sau (key hồi thì chạy tiếp)")
                    break
            else:
                _het_key_lien = 0
            last_dur = time.monotonic() - _t2
    except Exception as e:
        print(f"   ⚠️ lấy việc kế hụt ({str(e)[:60]}) — bỏ qua, không ảnh hưởng phần đã làm.")

    print(f"✅ {name}: TỔNG {report['done']} video · {len(report['fails'])} lỗi (qua {rounds} vòng).")
    _dh = dh_bao(name)
    if _dh:
        print("   " + _dh)      # 26/8 — mỗi lane tự nói thời gian đi đâu, khỏi phải đoán
    bao_da_luong()
    try:
        FB.flush_soft()                    # xả ghi done/topics bị hoãn -> count_done không đếm thiếu
        FB.update_channel_stats(OWNER, name)   # sổ thống kê 1-doc cho dashboard (số thật mọi kênh, 1 ghi)
        print("   " + FB.write_report())   # SỐ ĐO THẬT lượt ghi Firestore — khỏi ước lượng lần sau
        print("   " + FB.bao_ngan_sach())
        FB.xa_ngan_sach_d1()          # cộng vào sổ ngân sách chung trên D1 (không tốn quota Firestore)
        try:
            _luu_kich_ban_du_phong(name)   # kịch bản sang 2 kho KHÁC — mất 1 kho vẫn dựng lại được
            import hot_db as _H
            _n = _H.xa_het()          # BẮT BUỘC: thiếu bước này là mất các lượt ghi còn trong đệm
            if _n:
                print(f"   💾 xả nốt {_n} bản ghi còn trong đệm sang D1")
            print("   " + _H.bao_cao())
        except Exception:
            pass
        try:
            _bc = DS.bao_cao_khau()        # máy dò "chết câm": khâu nào thử nhiều mà 0 lần được
            if _bc:
                print(_bc)
        except Exception:
            pass
        FB.flush_rw_ledger(OWNER)          # cộng vào sổ tổng NGÀY (1 ghi) -> plan rung chuông 60%/85% sớm
    except Exception:
        pass
    # ── TỔNG KẾT LANE (27/8) ────────────────────────────────────────────────────────────────
    # Trước đây lane kết thúc IM LẶNG. GitHub chấm `success` cho mọi lane thoát mã 0, kể cả lane
    # ra 0 video — nên nhìn bảng Actions thì 18 lane xanh hết, mà thực tế có kênh không đẻ được
    # gì và không ai biết kênh nào. Trạng thái xanh mà không đúng sự thật còn tệ hơn trạng thái
    # đỏ: nó làm người ta thôi đi tìm.
    # KHÔNG cho lane thoát mã khác 0: ra 0 video là chuyện HỢP LỆ (kênh đã đủ chỉ tiêu, hoặc
    # nguồn hôm nay không có dữ liệu). Thứ cần là NHÌN THẤY ĐƯỢC, không phải báo động giả.
    try:
        _sl = int(report.get("done", 0))
        _sf = len(report.get("fails") or [])
        _dg = "✅" if _sl else ("⚠️" if _sf else "➖")
        print(f"{_dg} LANE {name}: video={_sl} · lỗi={_sf}"
              + (f" · {report['fails'][0][:70]}" if _sf else ""))
        # Ghi lên trang tổng kết của GitHub: mở một lượt chạy là thấy ngay kênh nào câm, khỏi
        # phải mở từng lane rồi lần trong log.
        _gs = os.environ.get("GITHUB_STEP_SUMMARY")
        if _gs:
            with open(_gs, "a", encoding="utf-8") as _f:
                _f.write(f"| {name} | {_sl} | {_sf} | "
                         f"{(report.get('fails') or ['—'])[0][:80].replace('|', '/')} |\n")
    except Exception:
        pass

    # GHI số request/key hôm nay -> theo dõi quota còn free + chia đều lần sau.
    try:
        import key_manager as KM
        from datetime import datetime as _dt, timezone as _tz
        # NGÀY-GOOGLE: quota Gemini reset 07:00Z (nửa đêm Thái Bình Dương), KHÔNG phải 00:00Z.
        # Đếm theo 00:00Z làm bảng quota "tươi lại" sớm 7 tiếng trong khi sổ Google vẫn tính cú đốt
        # hôm trước -> dashboard báo "còn nhiều" mà key vẫn 429 (sáng 22/8 user vạch ra đúng ca này).
        reqs = KM.flush_requests(); today = (_dt.now(_tz.utc) - __import__("datetime").timedelta(hours=7)).isoformat()[:10]
        # GỘP 1 GHI cho cả mẻ (22/8): trước là 1 ghi/key -> 3-8 ghi/luồng; giờ 1 doc __req__ Increment nguyên tử.
        FB.incr_key_requests_bulk(OWNER, reqs, today)
        if reqs:
            print(f"   📊 {name}: +{sum(reqs.values())} request lên {len(reqs)} key (1 lượt ghi gộp).")
    except Exception:
        print_exc_gon()




def _toon_long_then_shorts(ch, keys, tier, niche, n_shorts, cool, okcb, R, stopped):
    """Kênh TOON: 1 LONG (tuyển tập 3 skit, 16:9) -> 3 SHORT = chính 3 skit đó (9:16, dùng lại
    nguyên audio + ảnh — 0 gọi thêm AI). Đúng luật 1:3, chi phí = đúng 3 skit."""
    channel = ch.get("name")
    ljob = FB.new_job(OWNER, channel, "long", pver=_pv("toon"))
    lst = lambda st, step, **x: (_bo_chu_de(channel, str(step)) if st == "failed" else None,
                                 FB.update_job(ljob, status=st, step=step, **x))[-1]
    lst = _lst_noi(channel, lst)   # 27/8: mọi lần 'failed' phải có tiếng trong log
    _rck = FB.find_resumable(OWNER, channel, "long")
    _resume = _rck["story"] if (_rck and isinstance(_rck.get("story"), dict) and _rck["story"].get("parts")) else None
    _kw = dict(toon_style=ch.get("toon_style", ""),
               voice_a=ch.get("voice_a", "en-US-ChristopherNeural"), rate_a=ch.get("rate_a", "+0%"),
               voice_b=ch.get("voice_b", "en-US-GuyNeural"), rate_b=ch.get("rate_b", "+8%"),
               color_a=ch.get("color_a", "#7DD3FC"), color_b=ch.get("color_b", "#FCA5A5"),
               display=ch.get("display") or channel, toon_mode=ch.get("toon_mode", "skit"))
    try:
        lout = os.path.join("out", DS.slug(channel) + "_toonlong.mp4")
        lo, plan, subs, ok, info, parts = DS.make_toon_long(
            channel, niche, lout, keys=keys, tier=tier, accent=ch.get("accent", "#E4562B"),
            avoid=_avoid_for(channel), on_status=lst, on_limit=cool, on_ok=okcb,
            n_parts=max(1, min(3, n_shorts or 3)), resume=_resume, **_kw)
    except (Exception, SystemExit) as e:
        print_exc_gon()
        if _is_ratelimit(e):
            lst("ratelimited", "⏳ hết quota tạm — thử lại sau"); R["rl"] = R.get("rl", 0) + 1
        else:
            lst("failed", f"LONG toon lỗi: {str(e)[:120]}"); R["fails"].append(f"{channel} LONG toon: {str(e)[:100]}")
        return False
    if _rck:
        FB.clear_resumed(_rck["job_id"])
    try:
        FB.flush_soft()
    except Exception:
        pass
    if subs:
        _hen_chu_de(channel, subs)
    if not ok:
        lst("failed", f"QC long toon trượt: {info}"); R["fails"].append(f"{channel} LONG toon: QC trượt")
        return False
    # 23/8: gom SOURCES + tóm tắt từ mọi phần -> mô tả có dẫn nguồn (essay bắt buộc có nguồn; trước
    # đây enqueue chỉ đẩy hook nên nguồn AI viết ra bị vứt = mất điểm tin cậy khi YouTube xét kênh).
    _src, _bul = [], []
    for _pt in (plan.get("parts") or parts or []):
        _st2 = (_pt.get("story") or {}) if isinstance(_pt, dict) else {}
        for _s in (_st2.get("sources") or []):
            if _s and _s not in _src:
                _src.append(_s)
        if _st2.get("title"):
            _bul.append("• " + str(_st2["title"]))
    _desc = (plan.get("hook", "") or "") + (("\n\n" + "\n".join(_bul[:6])) if _bul else "")
    eq = enqueue_drive(channel, lo, {"topic": plan.get("pillar_title"), "title": plan.get("pillar_title"),
                                     "description": _desc, "sources": _src[:6],
                                     "_thumb": (info or {}).get("thumb")}, "long", seri=ljob, bo="L")
    did = (eq or {}).get("id")
    lst("done", "Long toon đã đẩy Drive" if did else "Long toon xong (chưa đẩy Drive)",
        description=(plan.get("description") or plan.get("hook") or ""), hashtags=plan.get("hashtags") or [], tags=plan.get("tags") or [],
        title=plan.get("pillar_title"), score=(info or {}).get("score"), dur=(info or {}).get("dur", 0),
        size_mb=(info or {}).get("size_mb", 0), res=(info or {}).get("res", ""), drive_id=did or "",
        drive_account=(eq or {}).get("account", ""), thumb_id=(eq or {}).get("thumb_id", ""),
        preview=(("https://drive.google.com/file/d/%s/preview" % did) if did else ""),
        script=_script_json(_ks_long(plan, parts)))
    R["done"] += 1; R["done_long"] = R.get("done_long", 0) + 1

    for pi, part in enumerate(parts):
        if stopped():
            print(f"   ⛔ {channel}: dừng — bỏ {len(parts) - pi} short còn lại."); break
        sjob = FB.new_job(OWNER, channel, "short", pver=_pv("toon"))
        sst = lambda st, step, **x: FB.update_job(sjob, status=st, step=step, **x)
        st_ = part["story"]
        try:
            sout = os.path.join("out", DS.slug(channel) + f"_toonshort{pi}.mp4")
            sst("rendering", f"Short toon {pi + 1}/{len(parts)} (từ long)")
            sok, sinfo = DS.render_toon_short_props(channel, part["props"], st_, sout, keys=keys, prefix=f"p{pi}")
        except (Exception, SystemExit) as e:
            print_exc_gon()
            sst("failed", f"Short toon lỗi: {str(e)[:120]}"); R["fails"].append(f"{channel} TOON SHORT {pi}: {str(e)[:100]}")
            continue
        if not sok:
            sst("failed", f"QC short toon trượt: {sinfo}"); R["fails"].append(f"{channel} TOON SHORT {pi}: QC trượt")
            continue
        # mô tả short = 2 câu đầu (hook + claim) thay vì 1 câu cụt + kèm nguồn của chính bài đó
        _ls = [str((d or {}).get("line", "")).strip() for d in (st_.get("dialog") or [])][:2]
        meta = {"topic": st_.get("title"), "title": st_.get("title"),
                "description": " ".join([x for x in _ls if x]),
                "sources": (st_.get("sources") or [])[:4],
                "_thumb": (sinfo or {}).get("thumb")}
        seq = enqueue_drive(channel, sout, meta, "short")
        sdid = (seq or {}).get("id")
        sst("done", "Short toon đã đẩy Drive" if sdid else "Short toon xong (chưa đẩy Drive)",
            description=_desc_src(st_), hashtags=st_.get("hashtags") or [], tags=st_.get("tags") or [],
            title=st_.get("title"), score=(sinfo or {}).get("score"), dur=(sinfo or {}).get("dur", 0),
            size_mb=(sinfo or {}).get("size_mb", 0), res=(sinfo or {}).get("res", ""), drive_id=sdid or "",
            drive_account=(seq or {}).get("account", ""), thumb_id=(seq or {}).get("thumb_id", ""),
            preview=(("https://drive.google.com/file/d/%s/preview" % sdid) if sdid else ""))
        R["done"] += 1
    return True


# 25/8/2026 — KHỐI CHẠY PHẢI LÀ THỨ CUỐI CÙNG CỦA FILE. Trước đây nó nằm TRƯỚC hàm
# `_toon_long_then_shorts` (hàm toon được nối vào cuối file ở phiên 23/8): với đường
# `--channel` của matrix, Python chạy khối này khi hàm kia CHƯA ĐƯỢC ĐỊNH NGHĨA ⇒ NameError,
# bị vòng thử-lại nuốt êm ⇒ 5 lane toon phiên 08:55 đứng câm 40+ phút không một bản ghi.
# Toon chạy đường render_datastory/main() thì không sao — nên bug nấp được 2 ngày, tới lần
# ĐẦU TIÊN toon vào matrix mới lộ. Chốt: t_khoi_main_cuoi_file.
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
