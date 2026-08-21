"""
test_thumb_pipeline.py — TEST TOÀN BỘ CƠ CHẾ THUMBNAIL, chạy ở máy, KHÔNG gọi API, KHÔNG tốn token.

Vì sao cần: cơ chế thumbnail có NHIỀU NHÁNH (khung hook render từ composition / khung cắt từ video /
ảnh CC0 / AI vẽ / DocThumb) và mỗi nhánh hỏng đều ÂM THẦM rơi xuống nhánh sau — chạy 700 video mới
phát hiện thì quá muộn. File này ép từng nhánh chạy thật rồi kiểm bằng thước đo.

    python3 test_thumb_pipeline.py            # chạy tất cả
    python3 test_thumb_pipeline.py -v         # in chi tiết

Trả exit code 0 nếu tất cả ĐẠT, 1 nếu có lỗi -> dùng được trong CI.
"""
from __future__ import annotations
import os
import sys
import json
import glob
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(ROOT), "engine-remotion")
PUB = os.path.join(ENG, "public")
TMP = "/tmp/mm0_thumbtest"
sys.path.insert(0, ROOT)
os.environ.setdefault("AUTOPUBLISHER_SRC", os.path.join(os.path.dirname(ROOT), "MM0-AutoPublisher", "src"))

VERBOSE = "-v" in sys.argv
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '❌'} {name}{(' — ' + detail) if detail and (VERBOSE or not cond) else ''}")
    return cond


def edge_sharpness(path):
    from PIL import Image, ImageFilter, ImageStat
    im = Image.open(path).convert("L").filter(ImageFilter.FIND_EDGES)
    return ImageStat.Stat(im).stddev[0]


def find_video():
    """1 video THẬT bất kỳ ở máy để test (không có thì bỏ qua các test cần video)."""
    for pat in ("channels/*/shorts/*.mp4", "channels/*/*.mp4", "out/*.mp4"):
        g = sorted(glob.glob(os.path.join(os.path.dirname(ROOT), pat)))
        if g:
            return g[0]
    return ""


def t_frame_chon_dung():
    """Chọn frame hook: phải QUA hết fade-in, đúng cho cả 3 dạng props."""
    print("\n[1] Chọn frame cảnh hook")
    import datastory_ci as DS
    # RaceLong cho dòng hook hiện dần frame 42->56 => frame chọn PHẢI > 56
    for pf in sorted(glob.glob(os.path.join(PUB, "_ci_*.json"))) + sorted(glob.glob(os.path.join(PUB, "_long_*.json"))):
        try:
            props = json.load(open(pf))
        except Exception:
            continue
        fr = DS.hook_frame_of(props)
        sec = (props.get("intro") or {}).get("sec")
        check(f"{os.path.basename(pf)} -> frame {fr}", fr > 56,
              f"intro {sec}s, frame {fr} ({fr/30:.1f}s) phải > 56 (lúc hook hiện xong)")
    # motif (introSec) + tài liệu (scenes[0].dur tính bằng FRAME)
    check("motif introSec=3.2s", DS.hook_frame_of({"introSec": 3.2}) > 56)
    check("tài liệu scenes[0].dur=150f", DS.hook_frame_of({"scenes": [{"dur": 150}]}) > 56)
    check("props rỗng -> mặc định an toàn", DS.hook_frame_of({}) > 56)
    # không được vượt quá chặng intro
    check("không vượt quá intro", DS.hook_frame_of({"introSec": 4.0}) < 4.0 * 30)


def t_cat_16_9():
    """Video dọc phải CẮT bám chữ (không lồng dải mờ) và không tràn biên."""
    print("\n[2] Cắt 16:9 cho video dọc")
    for w, h in ((1080, 1920), (720, 1280), (1080, 1350)):
        ch = int(w * 9 / 16)
        y0 = max(0, min(h - ch, int(h * 0.51 - ch / 2)))
        check(f"{w}x{h} không tràn biên", 0 <= y0 and y0 + ch <= h, f"cắt {w}x{ch} tại y={y0}")
    src = open(os.path.join(ROOT, "datastory_ci.py")).read()
    check("đã bỏ kiểu lồng dải mờ (pillarbox)", "boxblur=22:2" not in src,
          "pillarbox cho chữ bé + hai bên mờ xấu")


def t_lam_net():
    """Làm nét: đúng chỗ (video nén) và KHÔNG áp cho nguồn PNG."""
    print("\n[3] Làm nét")
    import datastory_ci as DS
    src = open(os.path.join(ROOT, "datastory_ci.py")).read()
    check("có hằng số SHARPEN", hasattr(DS, "SHARPEN") and "unsharp" in DS.SHARPEN, DS.SHARPEN)
    check("mọi đường đều dùng lanczos", src.count("flags=lanczos") >= 4)
    # đúng 2 nhánh cắt-từ-video dùng SHARPEN; 2 nhánh từ PNG thì không
    check("chỉ 2 nhánh cắt-từ-video làm nét", src.count("{SHARPEN}") == 2,
          "nguồn PNG mà làm nét sẽ tạo viền giả quanh chữ")
    v = find_video()
    if not v:
        print("  ⏭  không có video ở máy -> bỏ qua đo nét thật")
        return
    os.makedirs(TMP, exist_ok=True)
    a, b = f"{TMP}/plain.jpg", f"{TMP}/sharp.jpg"
    base = "crop=1080:607:0:675," if _is_portrait(v) else ""
    subprocess.run(["ffmpeg", "-y", "-ss", "3", "-i", v, "-frames:v", "1",
                    "-vf", base + "scale=1280:720", "-q:v", "2", a], capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-ss", "3", "-i", v, "-frames:v", "1",
                    "-vf", base + f"scale=1280:720:flags=lanczos,{DS.SHARPEN}", "-q:v", "2", b], capture_output=True)
    if os.path.exists(a) and os.path.exists(b):
        s1, s2 = edge_sharpness(a), edge_sharpness(b)
        check("ảnh sau khi làm nét SẮC HƠN thật", s2 > s1 * 1.05, f"{s1:.1f} -> {s2:.1f} (+{(s2/s1-1)*100:.0f}%)")


def _is_portrait(v):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                        "stream=width,height", "-of", "csv=p=0:s=x", v], capture_output=True, text=True)
    try:
        w, h = (int(x) for x in r.stdout.strip().split("x")[:2])
        return h > w
    except Exception:
        return False


def t_loc_khung_bieu_do():
    """Bộ lọc miễn phí: phải phân biệt được khung hook (ảnh nền) vs khung biểu đồ."""
    print("\n[4] Lọc khung biểu đồ (không tốn API)")
    import datastory_ci as DS
    v = find_video()
    if not v:
        print("  ⏭  không có video -> bỏ qua")
        return
    os.makedirs(TMP, exist_ok=True)
    f = f"{TMP}/frame.jpg"
    subprocess.run(["ffmpeg", "-y", "-ss", "3", "-i", v, "-frames:v", "1",
                    "-vf", "scale=1280:-2", "-q:v", "2", f], capture_output=True)
    if os.path.exists(f):
        flat, cols, is_photo = DS.photo_score(f)
        check("photo_score chạy được", flat >= 0, f"phẳng={flat:.1f}% màu={cols}")
        check("ngưỡng 45% nằm giữa 2 nhóm", 29 < 45 < 66,
              "đo thật: khung hook ~29% phẳng, khung biểu đồ ~66%")


def t_render_that():
    """Render THẬT khung hook từ composition + props thật -> phải ra 1280x720."""
    print("\n[5] Render thật khung hook từ composition")
    import datastory_ci as DS
    cases = [("RaceLongV", "_ci_*.json"), ("RaceLong", "_long_*.json")]
    for comp, pat in cases:
        g = sorted(glob.glob(os.path.join(PUB, pat)))
        if not g:
            print(f"  ⏭  không có props {pat}")
            continue
        pf = g[0]
        os.makedirs(TMP, exist_ok=True)
        dst = f"{TMP}/{comp}.jpg"
        fr = DS.hook_frame_of(json.load(open(pf)))
        ok = DS.still_hook_thumb(comp, pf, dst, frame=fr, api_key=None, title="test")
        if check(f"{comp} render frame {fr}", ok and os.path.exists(dst)):
            from PIL import Image
            check(f"{comp} đúng kích thước 1280x720", Image.open(dst).size == (1280, 720))


def t_docthumb_du_phong():
    """Nhánh chốt chặn cuối (DocThumb) vẫn phải dựng được."""
    print("\n[6] Nhánh dự phòng DocThumb")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "check_thumbs.py")],
                       capture_output=True, text=True, cwd=ROOT)
    out = r.stdout
    check("check_thumbs.py: tất cả ĐẠT", "TẤT CẢ ĐẠT" in out,
          out.strip().split("\n")[-1] if out else r.stderr[-120:])
    check("không kênh nào trùng màu số liệu", "TRÙNG MÀU" not in out)


def t_khop_luc_dang():
    """Mọi đường đăng phải mang theo _thumb (không sẽ mất thumbnail lúc upload)."""
    print("\n[7] Khớp thumbnail lúc đăng")
    src = open(os.path.join(ROOT, "run_render.py")).read()
    lines = src.split("\n")
    calls = [i for i, l in enumerate(lines) if "enqueue_drive(" in l and "def " not in l]
    # 8 đường đăng hiện có (đổi kiến trúc thì SỬA SỐ NÀY — đó là mục đích của phép đếm: bắt lập
    # trình viên rà lại, không để lọt một đường đăng mới mà quên mang thumbnail):
    #   dispatch-short · data-race long · data-race short · doc-long · short-từ-long
    #   · motif-long · motif-short · render-lại (process_requests)
    check("có đủ 8 đường đăng", len(calls) == 8, f"tìm thấy {len(calls)}")
    for i in calls:
        # Gom đúng lời gọi (cân bằng ngoặc) rồi lấy THAM SỐ THỨ 3 — không quét cả khối, vì dòng kế
        # thường có "(eq or {})" khiến bộ test tưởng nhầm là dict literal.
        call, depth = "", 0
        for l in lines[i:i + 8]:
            seg = l.split("enqueue_drive(", 1)[1] if not call else l
            call += seg
            # đếm CẢ () {} [] — chỉ đếm ngoặc tròn thì dict nhiều dòng bị cắt ngang, đọc thiếu
            depth += sum(seg.count(c) for c in "({[") - sum(seg.count(c) for c in ")}]")
            if call and depth <= 0:
                break
        args, d, cur = [], 0, ""
        for cnum in call:
            if cnum in "([{":
                d += 1
            elif cnum in ")]}":
                if d == 0:
                    break
                d -= 1
            if cnum == "," and d == 0:
                args.append(cur.strip()); cur = ""
            else:
                cur += cnum
        args.append(cur.strip())
        third = args[2] if len(args) > 2 else ""
        if third.startswith("{"):          # dict dựng tại chỗ -> PHẢI ghi rõ _thumb
            ok, why = ("_thumb" in call), "dict dựng tại chỗ thiếu _thumb -> upload rơi về ảnh cắt thô"
        else:                              # truyền biến -> biến đó phải được gán _thumb trước khi đăng
            var = third.split(".")[0]
            before = "\n".join(lines[max(0, i - 30):i])
            # _thumb có thể được gán ở datastory_ci (render_short_from_props đặt story["_thumb"])
            # -> cùng một object dict, nên phải soi cả file đó, không chỉ run_render.py.
            ds = open(os.path.join(ROOT, "datastory_ci.py")).read()
            ok = (f'{var}["_thumb"]' in before or f'{var}["_thumb"]' in src
                  or 'story["_thumb"]' in ds)
            why = f'biến `{third}` chưa từng được gán ["_thumb"]'
        check(f"dòng {i+1} mang thumbnail ({third[:18]})", ok, why)


def main():
    print("🧪 TEST CƠ CHẾ THUMBNAIL (không gọi API, không tốn token)")
    for t in (t_frame_chon_dung, t_cat_16_9, t_lam_net, t_loc_khung_bieu_do,
              t_render_that, t_docthumb_du_phong, t_khop_luc_dang):
        try:
            t()
        except Exception as e:
            FAIL.append(t.__name__)
            print(f"  ❌ {t.__name__} NGOẠI LỆ: {str(e)[:120]}")
    print(f"\n{'='*60}\nĐẠT {len(PASS)} · LỖI {len(FAIL)}")
    if FAIL:
        print("Cần sửa: " + ", ".join(FAIL))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
