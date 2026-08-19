"""
health_guardian.py — TỰ ĐỘNG canh hệ thống 24/7 (thay việc phải tự check tay mỗi giờ).
Chạy HOURLY qua .github/workflows/health_guardian.yml. 100% FREE (chỉ Firestore + GitHub có sẵn).

Làm 2 việc:
  1. TỰ CHỮA: job render "treo" (status queued/running/writing/rendering/qc) quá STALE_HOURS -> tự
     đánh dấu "failed". TRƯỚC ĐÂY việc này CHỈ chạy phía dashboard (JavaScript trong trình duyệt,
     xem dashboard/index.html) -> nếu KHÔNG ai mở dashboard, job treo ở lại mãi -> has_active_render()
     coi là còn "đang chạy" vô thời hạn -> CỔNG RENDER CÓ THỂ BỊ KẸT VĨNH VIỄN. Chạy server-side ở đây
     -> luôn tự chữa dù không ai mở máy/dashboard, đúng tinh thần "machine-off, vẫn chạy" của cả hệ thống.
  2. CẢNH BÁO THẬT: nếu SILENT_HOURS gần nhất KHÔNG có video "done" nào (mọi kênh cộng lại) dù
     render đang BẬT -> khác với lỗi quota tạm (tự hồi) -> exit(1) để GitHub TỰ GỬI EMAIL báo lỗi
     (tính năng free có sẵn của GitHub Actions khi 1 scheduled workflow fail) — không cần thêm dịch vụ
     thông báo ngoài nào, không tốn gì thêm.
"""
from __future__ import annotations
import os, sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firestore_bridge as FB

OWNER = os.environ.get("OWNER_UID")
STALE_HOURS = float(os.environ.get("STALE_HOURS_OVERRIDE") or 6)   # job render 1 kênh hiếm khi quá 6h thật (matrix timeout 350')
# -> quá STALE_HOURS là coi như treo. Chỉnh STALE_HOURS_OVERRIDE khi chạy tay (workflow_dispatch) để can thiệp NGAY,
# không đợi đủ 6h — vd 1 job kẹt cổng render biết chắc đã treo lúc chưa tới 6h.
SILENT_HOURS = 12     # 12h không có video nào xong dù render đang bật -> báo động thật, không phải quota tạm


def _now():
    return datetime.now(timezone.utc)


def heal_stale_jobs() -> int:
    """Đánh dấu 'failed' job treo quá STALE_HOURS — chạy được dù không ai mở dashboard."""
    active = ("queued", "running", "writing", "rendering", "qc")
    n = 0
    try:
        db = FB._db_jobs()
        cutoff = (_now() - timedelta(hours=STALE_HOURS)).isoformat()
        q = db.collection("render_jobs").where("owner", "==", OWNER).where("status", "in", list(active))
        for d in q.stream():
            job = d.to_dict() or {}
            if (job.get("created_at") or "9999") < cutoff:
                try:
                    d.reference.set({"status": "failed",
                                     "step": f"⏱ Quá {STALE_HOURS}h — job treo, health_guardian tự dọn"},
                                    merge=True)
                    n += 1
                except Exception as e:
                    print(f"   ⚠️ heal job {d.id} lỗi: {e}")
    except Exception as e:
        print(f"   ⚠️ heal_stale_jobs lỗi: {e}")
    return n


def check_alive() -> bool:
    """True nếu hệ thống đang thực sự sản xuất được (có job done gần đây), hoặc render đang TẮT (bình thường)."""
    try:
        cfg = FB.read_config(OWNER)
        if not cfg.get("enabled", True):
            print("   ℹ️ render đang TẠM DỪNG (chủ động, nút ⏸ trên dashboard) -> không báo động.")
            return True
        db = FB._db_jobs()
        cutoff = (_now() - timedelta(hours=SILENT_HOURS)).isoformat()
        q = db.collection("render_jobs").where("owner", "==", OWNER).where("status", "==", "done")
        recent = [d for d in q.stream() if (d.to_dict() or {}).get("created_at", "") >= cutoff]
        if recent:
            print(f"   ✅ {len(recent)} video 'done' trong {SILENT_HOURS}h qua -> hệ thống sống khoẻ.")
            return True
        print(f"   ❌ KHÔNG có video nào xong trong {SILENT_HOURS}h qua dù render đang BẬT — có thể có lỗi hệ thống thật.")
        return False
    except Exception as e:
        print(f"   ⚠️ check_alive lỗi ({e}) -> fail-open (không báo động nhầm vì chính health_guardian lỗi đọc).")
        return True


def main():
    if not OWNER:
        print("⚠️ Thiếu OWNER_UID -> bỏ qua."); return
    print(f"🩺 Health Guardian — {_now().isoformat()}")
    n = heal_stale_jobs()
    if n:
        print(f"   🔧 Đã tự dọn {n} job treo (>{STALE_HOURS}h) — không phụ thuộc dashboard có mở hay không.")
    if not check_alive():
        print("🚨 BÁO ĐỘNG: hệ thống có vẻ ngừng sản xuất bất thường -> để GitHub tự gửi email báo lỗi.")
        sys.exit(1)
    print("✔ Hệ thống bình thường.")


if __name__ == "__main__":
    main()
