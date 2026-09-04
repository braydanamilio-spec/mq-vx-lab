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
# Job còn sống có LUỒNG NỀN đóng dấu updated_at mỗi 2' (firestore_bridge._beat_loop).
# Im lặng 45' = lỡ ~22 nhịp -> chết chắc. KHÔNG hạ thấp hơn: cổng render nay KHÔNG còn phụ
# thuộc vào việc dọn job ma (đã gỡ has_active_render khỏi gate) nên không có lý do gì phải
# giết gấp; giết sớm chỉ rước rủi ro chém nhầm job đang render (đã xảy ra 20/8: 15 job).
# Đặt rộng rãi so với 90s để KHÔNG giết oan job đang render 1 clip nặng (render lâu vẫn có nhịp).
STALE_BEAT_MIN = float(os.environ.get("STALE_BEAT_MIN") or 45)
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
        # NHỊP TIM: update_job() nay đóng dấu updated_at mỗi lần ghi (~90s/lần khi job còn sống).
        # Im lặng quá STALE_BEAT_MIN phút = lỡ ~20 nhịp = tiến trình đã chết -> dọn NGAY, khỏi chờ đủ
        # STALE_HOURS(6h). Nhờ vậy dashboard không còn hiện "Đang làm (39)" hàng giờ trong khi thực tế
        # chẳng có gì chạy (đúng thứ gây hiểu lầm 20/8). Job CŨ chưa có updated_at -> vẫn theo mốc 6h.
        beat_cut = (_now() - timedelta(minutes=STALE_BEAT_MIN)).isoformat()
        # TRẦN: vòng này quét job ĐANG hoạt động nên bình thường chỉ vài chục dòng — nhưng
        # "bình thường" không phải bảo vệ (§13.7). Một đợt job kẹt trạng thái là một đợt
        # đọc không trần, và nó xảy ra đúng lúc hệ đang hỏng, tức lúc hạn mức quý nhất.
        q = (db.collection("render_jobs").where("owner", "==", OWNER)
               .where("status", "in", list(active)).limit(400))
        for d in q.stream():
            job = d.to_dict() or {}
            beat = job.get("updated_at")
            dead = (beat < beat_cut) if beat else ((job.get("created_at") or "9999") < cutoff)
            if dead:
                try:
                    why = (f"⏱ Im lặng quá {STALE_BEAT_MIN}' (mất nhịp tim)" if beat
                           else f"⏱ Quá {STALE_HOURS}h")
                    d.reference.set({"status": "failed",
                                     "step": f"{why} — job treo, health_guardian tự dọn"},
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
        # TRƯỚC ĐÂY: q.stream() không giới hạn -> đọc TOÀN BỘ lịch sử job 'done' (hàng nghìn doc, chỉ tăng
        # dần) MỖI GIỜ chỉ để biết có job nào done trong SILENT_HOURS gần đây -> tốn quota đọc free tier vô
        # ích (đã cạn quota 2 lần trong tháng). Sắp theo created_at GIẢM DẦN + limit -> chỉ đọc vài chục doc
        # GẦN NHẤT là đủ kết luận đúng. Thiếu composite index (owner+status+order by created_at) -> fallback
        # limit thô (giống top_titles() đã làm) — vẫn giới hạn được số đọc, không đọc cả collection nữa.
        # ── ĐƯỜNG DỰ PHÒNG KHÔNG ĐƯỢC PHÉP BÁO ĐỘNG  (3/9/2026) ────────────────────────────
        # Lượt 09:40 hôm nay báo *"KHÔNG có video nào xong trong 12h qua"* và cho cả workflow
        # HỎNG. Nhưng ngay phía trên trong cùng log: *"Firestore HẾT HẠN MỨC ĐỌC -> dùng config
        # đệm"*. Guardian không đọc được dữ liệu, và nó kết luận như thể đã đọc được.
        #
        # Cụ thể hơn: nhánh `order_by` cần composite index (owner + status + created_at). Thiếu
        # index thì nó rơi xuống `q.limit(200)` **KHÔNG SẮP XẾP** — tức đọc 200 tài liệu BẤT KỲ
        # trong hàng nghìn, rồi hỏi "có cái nào mới không". Không có cái nào mới trong 200 tài
        # liệu ngẫu nhiên KHÔNG chứng minh được điều gì.
        #
        # Đây đúng họ lỗi §12.8: một phép đo không phân biệt được *"không có gì"* với *"tôi
        # không nhìn thấy"*, và nghiêng về phía kết luận sai. Ở đó nó báo XANH nhầm; ở đây nó
        # báo ĐỎ nhầm — cùng một gốc, và báo đỏ nhầm cũng đắt: nó dạy người ta bỏ qua báo động.
        sap_duoc = True
        try:
            from google.cloud.firestore_v1 import Query
            docs = list(q.order_by("created_at", direction=Query.DESCENDING).limit(20).stream())
        except Exception as _e:
            sap_duoc = False
            # ── KHÔNG ĐỌC 200 TÀI LIỆU RỒI VỨT ĐI  (4/9/2026) ────────────────────────────
            # Bản trước rơi xuống `q.limit(200).stream()`. Bản vá §15.12 đúng ở chỗ NGỪNG KẾT
            # LUẬN từ 200 tài liệu không sắp xếp — nhưng nó vẫn ĐỌC chúng. Tức mỗi giờ tiêu
            # 200 lượt đọc để lấy về một kết quả mà chính đoạn dưới tuyên bố là không dùng
            # được: **4.800 lượt/ngày, gần 10% hạn mức free, đổi lấy không gì cả.**
            #
            # Đo bằng log guardian thật (lượt 33858866081): Firestore trả `400 The query
            # requires an index`. Index `owner+status+created_at DESCENDING` CÓ trong
            # `dashboard/firestore.indexes.json` nhưng CHƯA ĐƯỢC TRIỂN KHAI — khai một index
            # không phải là có nó, và đây là chỗ dễ tin nhầm nhất vì tệp đọc lên rất thuyết phục.
            #
            # Chữa đúng chỗ: thiếu index thì phép đo này KHÔNG TỒN TẠI, nên đừng trả tiền cho
            # nó. Vẫn fail-open như cũ, chỉ khác là không tốn gì.
            print(f"   ⚠️ không sắp được theo created_at ({str(_e)[:70]}) — thiếu composite index")
            docs = []
        recent = [d for d in docs if (d.to_dict() or {}).get("created_at", "") >= cutoff]
        if recent:
            print(f"   ✅ {len(recent)} video 'done' trong {SILENT_HOURS}h qua -> hệ thống sống khoẻ.")
            return True
        if not sap_duoc:
            # KHÔNG kết luận. Nói rõ vì sao không kết luận được — im lặng ở đây lại thành một
            # dạng nói dối khác.
            print("   ⚠️ KHÔNG KẾT LUẬN ĐƯỢC: thiếu composite index nên không sắp được theo "
                  "thời gian. Đọc bừa 200 tài liệu cũng không trả lời được câu hỏi, nên KHÔNG "
                  "đọc — tiết kiệm 200 lượt/giờ = 4.800 lượt/ngày. Triển khai index "
                  "(owner + status + created_at DESC) đã khai sẵn trong "
                  "dashboard/firestore.indexes.json thì phép đo này mới dùng được. "
                  "-> fail-open, không báo động.")
            return True
        print(f"   ❌ KHÔNG có video nào xong trong {SILENT_HOURS}h qua dù render đang BẬT — có thể có lỗi hệ thống thật.")
        return False
    except Exception as e:
        print(f"   ⚠️ check_alive lỗi ({e}) -> fail-open (không báo động nhầm vì chính health_guardian lỗi đọc).")
        return True


def _bao_cao_doc() -> None:
    """In số lượt ĐỌC Firestore mà dashboard đã tự đếm — để biết ai ăn hết hạn mức.

    1/9 — anh: *"làm gì đâu mà hết firebase"*. Đo ra: GitHub Actions chỉ chạy 34 lượt ngày
    31/8, không thể sinh 50.000 lượt đọc. Dashboard thì viết chắc — bộ đếm 5 giây của nó chỉ
    bầu tab chủ bằng localStorage, và chỉ MỘT tab được lắng nghe.
    Nhưng chính dashboard đã tự đếm số đọc và ghi vào `render_stats/__rw__<owner>` mỗi 5 phút.
    Con số ấy nằm sẵn trong Firestore mà chưa ai nhìn. In nó ra mỗi giờ thì hết phải đoán.
    Tốn đúng MỘT lượt đọc mỗi giờ — 24 lượt/ngày trên hạn mức 50.000.
    """
    try:
        import firestore_bridge as FB
        db = FB._db()
        d = db.collection("render_stats").document("__rw__" + OWNER).get()
        if not d.exists:
            print("   📖 chưa có sổ đếm đọc (dashboard chưa chạy lần nào hôm nay)")
            return
        x = d.to_dict() or {}
        ngay = sorted(x.keys())[-3:]
        print("   📖 lượt ĐỌC Firestore dashboard tự đếm (hạn mức free 50.000/ngày):")
        for k in ngay:
            v = x.get(k) or {}
            r = v.get("r", 0) if isinstance(v, dict) else v
            canh = " ⚠️ SÁT HẠN MỨC" if isinstance(r, int) and r > 40000 else ""
            print(f"      {k}: {r:,} lượt{canh}")
    except Exception as e:
        print(f"   📖 không đọc được sổ đếm: {str(e)[:80]}")


def main():
    if not OWNER:
        print("⚠️ Thiếu OWNER_UID -> bỏ qua."); return
    print(f"🩺 Health Guardian — {_now().isoformat()}")
    _bao_cao_doc()
    n = heal_stale_jobs()
    if n:
        print(f"   🔧 Đã tự dọn {n} job treo (>{STALE_HOURS}h) — không phụ thuộc dashboard có mở hay không.")
    if not check_alive():
        print("🚨 BÁO ĐỘNG: hệ thống có vẻ ngừng sản xuất bất thường -> để GitHub tự gửi email báo lỗi.")
        sys.exit(1)
    print("✔ Hệ thống bình thường.")


if __name__ == "__main__":
    main()
