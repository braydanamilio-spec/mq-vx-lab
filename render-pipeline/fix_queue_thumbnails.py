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

# Màu THẬT từng kênh (khớp RS_BRANDS trên dashboard, đã patch vào Firestore render_channels ở
# phiên này). accent2 chỉ cần khác accent khi accent trùng #F5B301 (mặc định) -> tránh vàng-trên-vàng.
ACCENTS = {
    "DATARACE":    ("#F5B301", "#22D3EE"),
    "STATEWARS":   ("#E4562B", "#F5B301"),
    "MONEYMOVES":  ("#2FA84F", "#F5B301"),
    "POWERPLAY":   ("#22D3EE", "#F5B301"),
    "GRIDIRON":    ("#FB923C", "#F5B301"),
    "SCREENKINGS": ("#EC4899", "#F5B301"),
    "PAYCHECK":    ("#2DD4BF", "#F5B301"),
    "BODYUSA":     ("#7C5CFF", "#F5B301"),
    "RIDEUSA":     ("#38BDF8", "#F5B301"),
    "EATSUSA":     ("#A3E635", "#F5B301"),
}


def build_thumb(channel: str, title: str, topic: str, dest_local: str) -> bool:
    """Dựng 1 ảnh thumbnail DocThumb tại dest_local. Trả True/False."""
    accent, accent2 = ACCENTS.get(channel, ("#22D3EE", "#F5B301"))
    tag = f"_fixq_{slug(channel)}_{abs(hash(dest_local)) % 999999}"
    bg_dir = os.path.join(PUB, tag)
    os.makedirs(bg_dir, exist_ok=True)
    bg_local = os.path.join(bg_dir, "bg.jpg")
    bg_rel = ""
    try:
        if fetch_image(topic or title, bg_local, orient="wide"):
            bg_rel = f"{tag}/bg.jpg"
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
    """Upload ảnh MỚI trước (tên tạm) -> chỉ xoá ảnh CŨ sau khi upload mới thành công -> đổi tên
    ảnh mới về đúng tên cũ. Không bao giờ để video ở trạng thái KHÔNG có thumbnail nào."""
    tmp_name = thumb_name + ".new.jpg"
    up = drv.upload_file(parent_id, local_path, name=tmp_name)
    new_id = (up or {}).get("id")
    if not new_id:
        return False
    old_id = drv.find_file(parent_id, thumb_name)
    if old_id and old_id != new_id:
        try:
            drv.delete(old_id)
        except Exception as e:
            print("     ⚠️ xoá thumbnail cũ lỗi (bỏ qua, vẫn còn 2 file):", str(e)[:80])
    drv.svc.files().update(fileId=new_id, body={"name": thumb_name}, fields="id").execute()
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
