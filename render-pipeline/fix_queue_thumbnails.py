"""
fix_queue_thumbnails.py — MỘT LẦN (không cron): nâng cấp thumbnail cho video 10 KÊNH GỐC đã
render nhưng CÒN NẰM TRONG Drive _QUEUE (chưa đăng, chưa lên lịch) — KHÔNG đụng file video.

Vì sao cần: bản vá 9091e66 (DocThumb cho 10 kênh gốc) chỉ áp dụng cho video MỚI render từ lúc
đó. Video đã render TRƯỚC bản vá nhưng vẫn còn trong _QUEUE (chưa publish) giữ nguyên thumbnail
kiểu cũ (cắt khung video, chữ đè chữ, xấu). Script này quét lại các video CŨ đó và thay ảnh.

Giới hạn thật (đã báo user trước khi làm): ảnh gốc từng cảnh dùng lúc render đã bị máy CI dọn
sau mỗi job -> KHÔNG phục dựng đúng 100% khung hình gốc. Sidecar trên Drive cũng không có
hook_stat/hook_caption (chỉ title/description/tags). Vì vậy mức "khớp" tối đa làm được:
  - title THẬT (từ sidecar)
  - màu (accent) THẬT của đúng kênh đó
  - 1 ảnh THẬT tìm lại theo topic/title qua Openverse (fetch_image — free, CC0, không cần Gemini)
-> vẫn ảnh thật + đúng thương hiệu kênh, chỉ không phải pixel-exact như trong video gốc.

AN TOÀN:
  - CHỈ đụng file ẢNH THUMBNAIL (cùng tên) trong đúng folder chứa video đó — KHÔNG đụng
    video.mp4 / sidecar .json / phụ đề.
  - Thay bằng UPLOAD-TRƯỚC-XOÁ-SAU: upload ảnh mới với tên tạm -> chỉ xoá ảnh cũ SAU KHI upload
    mới thành công -> đổi tên ảnh mới về đúng tên cũ. Nếu upload lỗi giữa chừng, ảnh cũ vẫn còn
    nguyên (không bao giờ để video ở trạng thái KHÔNG có thumbnail nào).
  - Idempotent: đọc thẳng trạng thái Drive _QUEUE mỗi lần chạy. Video đã publish tự biến khỏi
    _QUEUE (chuyển sang _POSTED) -> tự động bỏ qua, không xử lý nhầm video đã đăng.

CHẠY: workflow_dispatch TAY 1 LẦN qua .github/workflows/fix_queue_thumbnails.yml — KHÔNG cron,
KHÔNG tự `gh workflow run` (theo PIPELINE_RULES.md — luôn cần user yêu cầu trực tiếp trong chat).

    python3 fix_queue_thumbnails.py --dry-run          # xem trước, không đổi gì
    python3 fix_queue_thumbnails.py --limit 20         # chạy thật, giới hạn 20 video (test nhỏ trước)
    python3 fix_queue_thumbnails.py                    # chạy thật, toàn bộ
"""
from __future__ import annotations
import os
import sys
import json
import argparse
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(ROOT), "engine-remotion")
PUB = os.path.join(ENG, "public")

sys.path.insert(0, ROOT)
from datastory_ci import fetch_image, slug, photo_score  # noqa: E402  — tái dùng: ảnh thật CC0 + slug helper

AP_SRC = os.environ.get("AUTOPUBLISHER_SRC")
if AP_SRC and AP_SRC not in sys.path:
    sys.path.insert(0, AP_SRC)
import storage as ST  # noqa: E402

# Màu THẬT từng kênh (accent = màu thương hiệu, khớp RS_BRANDS dashboard + Firestore render_channels).
#
# accent2 QUAN TRỌNG HƠN accent ở thumbnail: DocThumb tô SỐ LIỆU TO NHẤT (thứ đập vào mắt đầu tiên)
# bằng accent2, còn accent chỉ hiện ở thanh kicker nhỏ + nền gradient của pill câu hỏi. Nếu để accent2
# trống -> DocThumb lấy mặc định #F5B301 -> 9/10 kênh gốc có số liệu VÀNG Y HỆT NHAU = nhìn như cùng
# một lò sản xuất hàng loạt (đúng thứ YouTube/Facebook đánh dấu rủi ro). Vì vậy MỖI kênh được gán 1
# accent2 riêng, trải đều dải màu (cyan/vàng/mint/gold/lục/sky/hồng/aqua/hổ phách/cam) và tương phản
# tốt với accent của chính kênh đó.
ACCENTS = {
    "DATARACE":    ("#F5B301", "#22D3EE"),   # vàng  -> số cyan
    "STATEWARS":   ("#E4562B", "#FFD93D"),   # đỏ    -> số vàng
    "MONEYMOVES":  ("#2FA84F", "#7CF6C0"),   # lục   -> số mint
    "POWERPLAY":   ("#22D3EE", "#F5B301"),   # cyan  -> số vàng gold
    "GRIDIRON":    ("#FB923C", "#4ADE80"),   # cam   -> số lục
    "SCREENKINGS": ("#EC4899", "#38BDF8"),   # hồng  -> số sky
    "PAYCHECK":    ("#2DD4BF", "#FB7185"),   # teal  -> số hồng đào
    "BODYUSA":     ("#7C5CFF", "#5EEAD4"),   # tím   -> số aqua
    "RIDEUSA":     ("#38BDF8", "#FACC15"),   # sky   -> số hổ phách
    "EATSUSA":     ("#A3E635", "#F97316"),   # chanh -> số cam
}


# Từ bỏ khi tìm ảnh: hư từ + từ "câu view" (không mô tả VẬT THỂ nào để chụp) + số/đơn vị.
_STOP = set("""a an the of in on for at to from by with and or but as is are was were be been being this that these those
it its his her their our your my we you they he she i us them me
how why what when where which who whom whose than then so if not no nor do does did done
real really truth true hidden secret shocking brutal terrifying wild wildest silent silently quietly
actually nobody everyone america american americas us usa state states new old big biggest most least
you're isn't aren't don't doesn't didn't can't won't it's thats that's here there now ever never
cost costs price prices money dollar dollars year years day days time times thing things
about into over under after before between across against during through
one two three four five six seven eight nine ten first last next best worst top
got get gets getting make makes made making take takes took taking keep keeps keeping
kill kills killed killing save saves saved saving hide hides hiding hidden beat beats
outsold outsell conquer conquers conquered flee flees fleeing fled leave leaves left
break breaks broke broken build builds built change changes changed turn turns turned
behind quietly update updates
""".split())


_VKEY = "__chua_doc__"
_VDEAD = False   # đã dính 429 (hết quota) -> ngừng gọi Vision cho phần còn lại của mẻ


def _vision_off(err) -> bool:
    """Hết quota thì TẮT Vision cho cả mẻ. Lượt chạy 20/8 gọi verify_image 313 lần rồi ăn 429 liên
    tục — mỗi lần vẫn tốn round-trip mà chắc chắn thất bại, làm chậm cả mẻ mà không được gì."""
    global _VDEAD
    if any(x in str(err) for x in ("429", "quota", "exceeded", "RESOURCE_EXHAUSTED")):
        if not _VDEAD:
            print("   ⛔ Gemini hết quota -> TẮT kiểm ảnh cho phần còn lại của mẻ (vẫn chạy bình thường)")
        _VDEAD = True
    return _VDEAD


def _vision_key():
    """1 key Gemini để Vision kiểm ảnh. Ưu tiên biến môi trường; không có -> đọc từ Firestore
    (gemini_keys, cùng nguồn với dây chuyền render). Không có key -> trả None: script vẫn chạy,
    chỉ là không kiểm được ảnh (fail-open, không chặn cả mẻ)."""
    global _VKEY
    if _VDEAD:
        return None
    if _VKEY != "__chua_doc__":
        return _VKEY
    _VKEY = os.environ.get("GEMINI_API_KEY") or None
    if not _VKEY:
        try:
            import firestore_bridge as FB
            ks = FB.read_keys(os.environ.get("OWNER_UID"))
            _VKEY = (ks[0].get("key") if ks else None) or None
        except Exception as e:
            print("   ⚠️ không đọc được key Gemini (bỏ kiểm ảnh):", str(e)[:70])
            _VKEY = None
    print("   🔎 Kiểm ảnh bằng Vision:", "BẬT" if _VKEY else "TẮT (không có key)")
    return _VKEY


def image_query(title: str, topic: str) -> str:
    """Rút 2-3 TỪ KHÓA VẬT THỂ từ tiêu đề để tìm ảnh.

    TRƯỚC ĐÂY ném nguyên cả câu tiêu đề vào Openverse -> câu dài toàn hư từ ("The State Where 1 in 4
    Adults Are in Medical Debt") khiến Openverse trả ảnh lạc đề hoàn toàn (thử thật: ra ảnh toà nhà
    cổ năm 1909). Tiêu đề tiếng Anh thường đặt CHỦ THỂ Ở CUỐI câu, nên lấy các từ mang nghĩa gần
    cuối cho ra chủ thể sát nhất ("medical debt", "original movies", "fast food milkshakes").
    Không rút được từ nào -> trả "" -> DocThumb dùng nền gradient thiết kế sẵn (vẫn đẹp, và CHẮC CHẮN
    tốt hơn một tấm ảnh sai chủ đề)."""
    import re as _re
    words = _re.findall(r"[A-Za-z']+", f"{title} {topic}")
    keep = [w for w in words if len(w) > 2 and w.lower() not in _STOP]
    if not keep:
        return ""
    return " ".join(keep[-3:]).lower()


# Phụ đề/HUD cháy vào khung nằm ở ĐÁY video (Cinematic: bottom 120px ngang / 520px dọc; RaceLong:
# bottom 96-104px). Cắt lấy phần TRÊN 58% chiều cao -> chắc chắn KHÔNG dính chữ, mà vẫn là footage
# thật của chính video đó. Đây là lý do bản thumbnail cũ xấu: nó cắt NGUYÊN khung nên dính chữ đè chữ.
SAFE_TOP = 0.58
# Khung video của kênh dữ liệu đầy nhãn/số sẵn. Thử thật: để nguyên -> chữ cũ đâm xuyên số liệu,
# rối mắt; mờ 5 vẫn đọc được "$1.4"/"Titanic"; mờ 9 thì chữ cũ tan hẳn thành kết cấu mà màu sắc +
# bố cục footage THẬT vẫn còn -> chọn 9.
BG_BLUR = 9


def _probe_dur(video: str) -> float:
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", video],
                           capture_output=True, text=True, timeout=60)
        return float((r.stdout or "0").strip() or 0)
    except Exception:
        return 0.0


def _score_frame(path: str) -> float:
    """Chấm điểm 1 khung: ưu tiên khung GIÀU CHI TIẾT + RỰC MÀU (footage thật, cảnh chính) và loại
    khung tối thui / đơn sắc (fade đen, nền trơn giữa 2 cảnh) — chính là những khung làm thumbnail chán."""
    try:
        from PIL import Image, ImageStat
        im = Image.open(path).convert("RGB")
        im.thumbnail((320, 320))
        st = ImageStat.Stat(im)
        detail = sum(st.stddev) / 3.0                 # chênh lệch sáng-tối = có chi tiết, không phẳng
        bright = sum(st.mean) / 3.0
        r, g, b = st.mean
        colorful = (max(r, g, b) - min(r, g, b))      # lệch kênh màu = ảnh có màu, không xám xịt
        if bright < 26:                               # gần như đen (fade chuyển cảnh) -> loại
            return 0.0
        return detail * 1.6 + colorful * 1.2 + min(bright, 150) * 0.25
    except Exception:
        return 1.0                                    # không chấm được -> vẫn chấp nhận


def frame_from_video(video: str, dest: str) -> bool:
    """LẤY ẢNH NỀN TỪ CHÍNH VIDEO (yêu cầu bắt buộc: footage thật, khớp nội dung 100%).

    Ảnh gốc từng cảnh lúc render đã bị máy CI xoá sau mỗi job, NHƯNG file video vẫn nằm trên Drive —
    trong đó chứa đúng footage đó. Rút 6 khung rải đều thân bài (bỏ 12% đầu/cuối vì là intro/outro
    chữ chạy), CẮT PHẦN TRÊN {SAFE_TOP:.0%} để không dính phụ đề, rồi chọn khung ĐIỂM CAO NHẤT
    (nhiều chi tiết + rực màu) làm nền. Thất bại -> trả False để lùi sang Openverse/gradient."""
    dur = _probe_dur(video)
    if dur <= 0:
        return False
    # 12 mốc: ảnh thật chỉ chèn vài giây -> lấy thưa là trượt hết vào đoạn biểu đồ
    marks = [dur * p for p in (0.10, 0.18, 0.26, 0.34, 0.42, 0.50, 0.58,
                               0.66, 0.74, 0.82, 0.88, 0.93)]
    best, best_s = None, -1.0
    tmpdir = os.path.dirname(dest)
    for i, t in enumerate(marks):
        cand = os.path.join(tmpdir, f"_f{i}.jpg")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                 # crop=toàn bộ chiều rộng, chiều cao = 58% tính từ đỉnh -> cắt bỏ hẳn dải phụ đề
                 "-vf", f"crop=iw:ih*{SAFE_TOP}:0:0,scale=1280:-2",
                 "-q:v", "3", cand],
                capture_output=True, timeout=90, check=True)
        except Exception:
            continue
        if not os.path.exists(cand):
            continue
        if not photo_score(cand)[2]:
            continue          # khung biểu đồ/đồ hoạ -> bỏ, nền phải là ẢNH THẬT mới hook
        s = _score_frame(cand)
        if s > best_s:
            best_s, best = s, cand
    if not best:
        return False
    try:
        if os.path.exists(dest):
            os.remove(dest)
        os.rename(best, dest)
    except Exception:
        return False
    for i in range(len(marks)):                       # dọn khung thừa
        try:
            os.remove(os.path.join(tmpdir, f"_f{i}.jpg"))
        except Exception:
            pass
    return best_s > 0


def build_thumb(channel: str, title: str, topic: str, dest_local: str, video_local: str = "") -> bool:
    """Dựng 1 ảnh thumbnail DocThumb tại dest_local. Trả True/False."""
    accent, accent2 = ACCENTS.get(channel, ("#22D3EE", "#F5B301"))
    tag = f"_fixq_{slug(channel)}_{abs(hash(dest_local)) % 999999}"
    bg_dir = os.path.join(PUB, tag)
    os.makedirs(bg_dir, exist_ok=True)
    bg_local = os.path.join(bg_dir, "bg.jpg")
    bg_rel = ""
    # ƯU TIÊN 0 — KHUNG HOOK MỞ ĐẦU dùng thẳng làm thumbnail. Video hệ thống đặt hook ngay đầu bài
    # (tiêu đề lớn + số sốc + ảnh nền thật) nên khung đó VỐN ĐÃ là thumbnail hoàn chỉnh, khớp nội
    # dung tuyệt đối và không cần vẽ chồng chữ. Chỉ nhận khi Vision chấm đạt.
    if video_local and os.path.exists(video_local):
        try:
            from datastory_ci import opening_thumb
            if opening_thumb(video_local, dest_local, api_key=_vision_key(), title=title):
                print("     ✅ dùng KHUNG HOOK MỞ ĐẦU của video")
                return True
        except Exception as e:
            print("     ⚠️ khung mở đầu bỏ qua:", str(e)[:70])
    # ƯU TIÊN 1 — FOOTAGE THẬT TRONG CHÍNH VIDEO (bắt buộc): khớp nội dung 100%, mỗi video một ảnh
    # khác nhau, không bao giờ "nền đơn điệu".
    if video_local and os.path.exists(video_local) and frame_from_video(video_local, bg_local):
        if _render_thumb(channel, title, f"{tag}/bg.jpg", tag, dest_local, bg_dir, bg_local, bg_blur=BG_BLUR):
            if _thumb_ok(dest_local, title):
                return True
            # QC visual chấm trượt (chữ tràn/chồng/khó đọc) -> KHÔNG đẩy ảnh hỏng lên Drive, thử tiếp
            # nhánh ảnh CC0 bên dưới thay vì chấp nhận đại.
            print("     ↩️ thử nền khác vì QC thumbnail trượt")
        os.makedirs(bg_dir, exist_ok=True)
    # ƯU TIÊN 2 — ảnh CC0 khớp chủ đề (chỉ khi không rút được khung nào từ video)
    q = image_query(title, topic)
    # ẢNH PHẢI KHỚP NỘI DUNG 100%: Openverse CC0 nghiêng nhiều về ảnh tư liệu cũ nên tìm theo từ khoá
    # thôi VẪN ra ảnh lạc đề (thử thật: "nợ y tế" -> ảnh toà nhà năm 1909). Bắt Gemini Vision nhìn từng
    # ảnh ứng viên và CHỈ nhận ảnh nó xác nhận đúng chủ đề; duyệt tới 5 ảnh, không ảnh nào khớp -> BỎ
    # ẢNH HẲN, dùng nền gradient thiết kế sẵn. Thà không ảnh còn hơn ảnh sai — nền gradient vẫn đẹp,
    # còn ảnh sai chủ đề là lừa người xem (và kéo tụt CTR/độ tin cậy của kênh).
    vkey = _vision_key()
    if vkey:
        import qc_vision as QV

        def verify(pth):
            try:
                return QV.verify_image(pth, q, api_key=vkey)
            except Exception as e:
                _vision_off(e)      # 429 -> tắt Vision cả mẻ, khỏi gọi vô ích
                return None
    else:
        verify = None
    try:
        if q and fetch_image(q, bg_local, orient="wide", verify=verify, max_check=5,
                             ai_key=vkey,
                             ai_prompt=f"dramatic cinematic editorial photo illustrating: {q}. "
                                       f"No text, no words, no charts, no watermark."):
            bg_rel = f"{tag}/bg.jpg"     # ảnh CC0 khớp, hoặc Nano Banana vẽ đúng chủ đề
        elif q:
            print(f"     ℹ️ không ra được ảnh nào cho '{q}' -> dùng nền thiết kế")
    except Exception as e:
        print("     ⚠️ fetch_image lỗi:", str(e)[:80])
    if not _render_thumb(channel, title, bg_rel, tag, dest_local, bg_dir, bg_local):
        return False
    _thumb_ok(dest_local, title)     # chấm + ghi log (đây đã là phương án cuối, không lùi thêm được)
    return True


def _thumb_ok(jpg: str, title: str) -> bool:
    """QC VISUAL ẢNH THÀNH PHẨM (yêu cầu: kiểm chất lượng cả thumbnail, không chỉ video).
    Không có key Vision -> coi như đạt (fail-open, không chặn cả mẻ)."""
    vkey = _vision_key()
    if not vkey:
        return True
    try:
        import qc_vision as QV
        ok, info = QV.check_thumb(jpg, title=title, api_key=vkey)
    except Exception as e:
        print("     ⚠️ QC thumbnail lỗi (bỏ qua):", str(e)[:70])
        return True
    if ok:
        print(f"     ✅ QC thumbnail {info.get('score')}/100")
    else:
        print(f"     ❌ QC thumbnail {info.get('score')}/100 — {'; '.join(info.get('issues') or [])[:110]}")
    return ok


def _render_thumb(channel, title, bg_rel, tag, dest_local, bg_dir, bg_local, bg_blur=0) -> bool:
    """Gọi Remotion dựng DocThumb + dọn file tạm (dùng chung cho cả nhánh footage lẫn nhánh CC0)."""
    accent, accent2 = ACCENTS.get(channel, ("#22D3EE", "#F5B301"))
    tprops = {"bg": bg_rel, "big": title, "kicker": channel, "accent": accent, "accent2": accent2,
              "bgBlur": bg_blur}
    tf = os.path.join(PUB, f"{tag}.json")
    json.dump(tprops, open(tf, "w"))
    ok = False
    try:
        subprocess.run(
            ["npx", "remotion", "still", "src/index.ts", "DocThumb", dest_local,
             f"--props=./{os.path.relpath(tf, ENG)}", "--log=error"],
            cwd=ENG, check=True, timeout=120,
        )
        ok = os.path.exists(dest_local)
    except Exception as e:
        print("     ⚠️ remotion still lỗi:", str(e)[:100])
    finally:
        for p in (tf, bg_local):
            try:
                os.remove(p)
            except Exception:
                pass
        try:
            os.rmdir(bg_dir)
        except Exception:
            pass
    return ok


def replace_thumb_on_drive(drv, parent_id: str, thumb_name: str, local_path: str) -> bool:
    """Thay ảnh thumbnail TẠI CHỖ, đảm bảo lúc đăng LUÔN tìm thấy đúng ảnh của đúng video.

    Lúc đăng, main.py gọi find_file(parent_id, sidecar["thumbnail"]) — tìm ĐÚNG TÊN FILE trong ĐÚNG
    THƯ MỤC chứa video đó. Nên chỉ cần giữ nguyên tên + thư mục là khớp 100%.

    THỨ TỰ QUAN TRỌNG (bản đầu làm SAI): trước đây upload tên tạm -> xoá ảnh cũ -> đổi tên. Nếu hỏng
    ở giữa (mạng/quota/CI bị huỷ) thì ảnh cũ ĐÃ MẤT mà ảnh mới CHƯA có tên đúng -> find_file trả None
    -> video lên YouTube KHÔNG có thumbnail. Giờ: upload ảnh mới NGAY VỚI TÊN THẬT (Drive cho phép
    trùng tên) rồi mới xoá ảnh cũ theo id đã ghi trước. Mọi thời điểm đều tồn tại ít nhất một file
    đúng tên -> không bao giờ có khoảng trống."""
    old_id = drv.find_file(parent_id, thumb_name)          # ghi nhớ id ảnh cũ TRƯỚC
    up = drv.upload_file(parent_id, local_path, name=thumb_name)
    new_id = (up or {}).get("id")
    if not new_id:
        return False                                        # upload hỏng -> ảnh cũ còn nguyên, không mất gì
    if old_id and old_id != new_id:
        try:
            drv.delete(old_id)
        except Exception as e:
            # Không xoá được -> còn 2 file trùng tên, find_file lấy 1 trong 2: cả hai đều là thumbnail
            # hợp lệ của CHÍNH video này -> không sai video, chỉ tốn chỗ. Ghi log để dọn sau.
            print(f"     ⚠️ không xoá được ảnh cũ {old_id} ({str(e)[:60]}) — còn 2 bản trùng tên")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="chỉ liệt kê, không đổi gì")
    ap.add_argument("--limit", type=int, default=0, help="dừng sau N video (0 = không giới hạn)")
    ap.add_argument("--channel", default="", help="chỉ xử lý 1 kênh (để chạy SONG SONG mỗi kênh 1 luồng)")
    a = ap.parse_args()
    only = a.channel.strip().upper()

    accounts = ST.pool_accounts()
    print(f"📦 {len(accounts)} tài khoản Drive pool.")
    done = skip = err = 0

    for acc in accounts:
        drv = ST.account_drive(acc)
        try:
            items = drv.list_queue(acc["root"])
        except Exception as e:
            print(f"  ⚠️ {acc.get('name')}: list_queue lỗi: {e}")
            continue
        for f in items:
            if a.limit and done >= a.limit:
                print(f"⏸ đủ --limit {a.limit}, dừng.")
                _report(done, skip, err)
                return
            try:
                sidecar = drv.read_sidecar(f["parents"][0], f["name"])
                channel = (sidecar.get("channel") or "").upper()
                thumb_name = sidecar.get("thumbnail")
                if channel not in ACCENTS or not thumb_name:
                    skip += 1
                    continue
                if only and channel != only:
                    skip += 1
                    continue
                title = sidecar.get("title") or sidecar.get("topic") or f["name"]
                topic = sidecar.get("topic") or title
                print(f"  🎯 [{channel}] {f['name']} -> {thumb_name}")
                if a.dry_run:
                    done += 1
                    continue
                local = os.path.join(tempfile.gettempdir(), thumb_name)
                # TẢI VIDEO để rút footage thật làm nền (yêu cầu: ảnh phải khớp nội dung video).
                # Xoá ngay sau khi rút xong -> không phình đĩa CI dù chạy hàng trăm video.
                vid = os.path.join(tempfile.gettempdir(), "v_" + f["name"])
                try:
                    drv.download(f["id"], vid)
                except Exception as e:
                    print("     ⚠️ tải video lỗi (sẽ tìm ảnh CC0 thay):", str(e)[:70])
                    vid = ""
                try:
                    built = build_thumb(channel, title, topic, local, video_local=vid)
                finally:
                    if vid and os.path.exists(vid):
                        try:
                            os.remove(vid)
                        except Exception:
                            pass
                if not built:
                    print("     ⚠️ dựng thumbnail thất bại -> bỏ qua video này (giữ nguyên ảnh cũ).")
                    err += 1
                    continue
                if replace_thumb_on_drive(drv, f["parents"][0], thumb_name, local):
                    done += 1
                else:
                    print("     ⚠️ upload thumbnail mới thất bại -> bỏ qua (giữ nguyên ảnh cũ).")
                    err += 1
                try:
                    os.remove(local)
                except Exception:
                    pass
            except Exception as e:
                print(f"     ⚠️ lỗi item {f.get('name')}: {str(e)[:120]}")
                err += 1

    _report(done, skip, err)


def _report(done, skip, err):
    print(f"\n✅ Xong: {done} đã thay thumbnail, {skip} bỏ qua (không thuộc 10 kênh gốc / thiếu "
          f"thumbnail sidecar), {err} lỗi.")


if __name__ == "__main__":
    main()
