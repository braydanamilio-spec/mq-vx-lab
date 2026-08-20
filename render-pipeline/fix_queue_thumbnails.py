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
from datastory_ci import fetch_image, slug  # noqa: E402  — tái dùng: ảnh thật CC0 + slug helper

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


def _vision_key():
    """1 key Gemini để Vision kiểm ảnh. Ưu tiên biến môi trường; không có -> đọc từ Firestore
    (gemini_keys, cùng nguồn với dây chuyền render). Không có key -> trả None: script vẫn chạy,
    chỉ là không kiểm được ảnh (fail-open, không chặn cả mẻ)."""
    global _VKEY
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


def build_thumb(channel: str, title: str, topic: str, dest_local: str) -> bool:
    """Dựng 1 ảnh thumbnail DocThumb tại dest_local. Trả True/False."""
    accent, accent2 = ACCENTS.get(channel, ("#22D3EE", "#F5B301"))
    tag = f"_fixq_{slug(channel)}_{abs(hash(dest_local)) % 999999}"
    bg_dir = os.path.join(PUB, tag)
    os.makedirs(bg_dir, exist_ok=True)
    bg_local = os.path.join(bg_dir, "bg.jpg")
    bg_rel = ""
    q = image_query(title, topic)
    # ẢNH PHẢI KHỚP NỘI DUNG 100%: Openverse CC0 nghiêng nhiều về ảnh tư liệu cũ nên tìm theo từ khoá
    # thôi VẪN ra ảnh lạc đề (thử thật: "nợ y tế" -> ảnh toà nhà năm 1909). Bắt Gemini Vision nhìn từng
    # ảnh ứng viên và CHỈ nhận ảnh nó xác nhận đúng chủ đề; duyệt tới 5 ảnh, không ảnh nào khớp -> BỎ
    # ẢNH HẲN, dùng nền gradient thiết kế sẵn. Thà không ảnh còn hơn ảnh sai — nền gradient vẫn đẹp,
    # còn ảnh sai chủ đề là lừa người xem (và kéo tụt CTR/độ tin cậy của kênh).
    vkey = _vision_key()
    verify = None
    if vkey:
        import qc_vision as QV
        verify = lambda p: QV.verify_image(p, q, api_key=vkey)   # True/False/None(Vision lỗi -> fail-open)
    try:
        if q and fetch_image(q, bg_local, orient="wide", verify=verify, max_check=5):
            bg_rel = f"{tag}/bg.jpg"
        elif q:
            print(f"     ℹ️ không có ảnh CC0 nào KHỚP '{q}' -> dùng nền thiết kế")
    except Exception as e:
        print("     ⚠️ fetch_image lỗi:", str(e)[:80])
    tprops = {"bg": bg_rel, "big": title, "kicker": channel, "accent": accent, "accent2": accent2}
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
    a = ap.parse_args()

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
                title = sidecar.get("title") or sidecar.get("topic") or f["name"]
                topic = sidecar.get("topic") or title
                print(f"  🎯 [{channel}] {f['name']} -> {thumb_name}")
                if a.dry_run:
                    done += 1
                    continue
                local = os.path.join(tempfile.gettempdir(), thumb_name)
                if not build_thumb(channel, title, topic, local):
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
