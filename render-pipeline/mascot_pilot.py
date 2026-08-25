#!/usr/bin/env python3
"""PILOT 5 KÊNH HOẠT HÌNH: seed kênh → dựng rig → render 1 long + 1 short để duyệt (25/8/2026).

Vì sao cần một trình riêng thay vì thả thẳng vào matrix: rig là tài sản DỰNG MỘT LẦN và tốn
~11 lượt vẽ/kênh (6 tư thế × số nhân vật + 4 lớp nền). Làm việc đó trong lane render thì lane
đầu tiên gánh hết, các lane sau đợi — và nếu tạo hình chưa ưng thì đã lỡ tiêu quota. Tách ra:
dựng rig → xem ảnh → render pilot → anh duyệt → mới bật `enabled` cho kênh vào matrix.

    python mascot_pilot.py --seed                    # ghi 5 kênh (enabled=false)
    python mascot_pilot.py --rig EAGLEBANDIT         # dựng nhân vật + sân khấu
    python mascot_pilot.py --pilot EAGLEBANDIT       # render 1 short + 1 long, đẩy kho
"""
from __future__ import annotations

import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))


def _cfg(kenh: str) -> dict:
    d = json.load(open(os.path.join(GOC, "mascot_channels.json"), encoding="utf-8"))
    return d.get(kenh.upper()) or {}


def seed(dry: bool = False) -> int:
    import firestore_bridge as FB
    owner = os.environ.get("OWNER_UID", "")
    if not owner:
        print("❌ thiếu OWNER_UID"); return 1
    data = json.load(open(os.path.join(GOC, "mascot_channels.json"), encoding="utf-8"))
    db = FB._db_meta()
    for name, cfg in data.items():
        print(f"  {name:<12} {cfg['display']:<18} voice={cfg['voice_a']} · enabled={cfg['enabled']}")
        if dry:
            continue
        db.collection("render_channels").document(f"{owner}__{name}").set(
            {**cfg, "owner": owner}, merge=True)
    print("(dry-run)" if dry else f"✅ đã ghi {len(data)} kênh mascot (enabled=false — chờ duyệt pilot)")
    return 0


def rig(kenh: str, lam_lai: bool = False) -> int:
    import firestore_bridge as FB
    import mascot_cast as MC
    import mascot_rig as MR
    cast = MC.cast_cua(kenh)
    if not cast:
        print(f"❌ {kenh}: chưa khai dàn nhân vật"); return 1
    keys = FB.read_keys(os.environ.get("OWNER_UID", ""))
    # hồ vẽ: chỉ lấy key vẽ được ảnh (CF trước, Gemini sau) — dùng chung bộ lọc của datastory
    import datastory_ci as DS
    DS.set_ai_pool(keys, kenh)
    print(f"🎨 dựng rig {kenh}: {len(cast)} nhân vật × {len(MR.TU_THE)} tư thế")
    MR.rig_kenh(kenh, cast, keys, lam_lai)
    for ten in MC.ten_san_khau(kenh):
        print(f"🏞  sân khấu {ten}")
        MR.dung_san_khau(kenh, ten, MC.san_khau_cua(kenh, ten), keys, lam_lai)
    ok_nv = MR.da_co_rig(kenh, cast)
    ok_sk = all(MR.da_co_san_khau(kenh, t) for t in MC.ten_san_khau(kenh))
    print(f"{'✅' if (ok_nv and ok_sk) else '⚠️'} rig nhân vật={ok_nv} · sân khấu={ok_sk}")
    return 0 if (ok_nv and ok_sk) else 2


def _viet_skit(niche: str, keys: list, kenh: str, tranh: list, nhan: str):
    """Viết MỘT skit, XOAY VÒNG QUA CÁC KEY khi gặp cạn hạn mức.

    25/8 — pilot 12:51Z: 3/3 skit hỏng với "You exceeded your current quota". Không phải lỗi
    kịch bản: pilot truyền thẳng `keys[0]` nên key đầu cạn là chết cả lượt, trong khi dây chuyền
    chính vẫn chạy ngon vì nó xoay key theo `key_manager.key_order` (ưu tiên key ÍT DÙNG NHẤT).
    Một đường phụ mà không dùng lại cơ chế của đường chính thì sớm muộn cũng lệch như vậy."""
    import content_brain as CB
    import key_manager as KM
    ho = KM.key_order(kenh, keys) or keys or []
    for i, k in enumerate(ho[:8]):
        try:
            return CB.generate_toon(niche, api_key=k.get("key", ""), avoid=tranh)
        except Exception as e:
            _m = str(e)[:70]
            _can = any(x in _m.lower() for x in ("quota", "429", "rate limit", "exhaust"))
            if not _can:
                print(f"   ⚠️ skit {nhan} viết hỏng ({_m}) — bỏ, đi tiếp")
                return None
            if i + 1 < len(ho[:8]):
                print(f"   🔑 skit {nhan}: key thứ {i + 1} cạn hạn mức — xoay sang key kế")
    print(f"   ⚠️ skit {nhan}: thử {min(8, len(ho))} key đều cạn hạn mức — bỏ, đi tiếp")
    return None


def pilot(kenh: str) -> int:
    import content_brain as CB
    import datastory_ci as DS
    import firestore_bridge as FB
    import mascot_build as MB
    owner = os.environ.get("OWNER_UID", "")
    cfg = _cfg(kenh)
    if not cfg:
        print(f"❌ {kenh}: không có trong mascot_channels.json"); return 1
    keys = FB.read_keys(owner)
    DS.set_ai_pool(keys, kenh)
    if not DS.render_canary():
        print("❌ engine render hỏng (canary) — dừng, không đốt quota"); return 1

    ra = []
    for dai in (False, True):
        loai = "long" if dai else "short"
        print(f"\n🎬 {kenh} · {loai}")
        job = FB.new_job(owner, kenh, loai, pver="mascot-v1")
        st = lambda s, step, **x: FB.update_job(job, status=s, step=step, **x)
        try:
            # LONG = TUYỂN TẬP 3 SKIT (short = 1). `generate_toon` viết skit 18-30s theo thiết kế;
            # dùng thẳng cho long thì ra 22s và QC chặn "quá ngắn <45s". Mỗi skit vào một sân khấu
            # khác nên long vừa đủ dài vừa đổi cảnh — không tốn thêm lượt vẽ nào.
            n_skit = 3 if dai else 1
            st("writing", f"Viết {n_skit} skit 2 vai")
            _tranh = list(FB.recent_topics(owner, kenh, 40) or [])
            stories = []
            for _i in range(n_skit):
                # MỘT SKIT HỎNG KHÔNG ĐƯỢC GIẾT CẢ BẢN DÀI (25/8): pilot 12:39Z skit 1 đạt, skit 2
                # bị loại rồi cả lượt long chết IM LẶNG — không một dòng nói vì sao. Nay: báo rõ,
                # bỏ skit hỏng, đi tiếp; cuối cùng có bao nhiêu skit thì dựng bấy nhiêu.
                _sk = _viet_skit(cfg["niche"], keys, kenh, _tranh, f"{_i + 1}/{n_skit}")
                if not _sk:
                    continue
                stories.append(_sk)
                _tranh.append(_sk.get("title", ""))     # skit sau không lặp ý skit trước
            if not stories:
                st("failed", "không viết được skit nào")
                print(f"   ❌ {loai}: không viết được skit nào"); continue
            if dai and len(stories) < n_skit:
                print(f"   ℹ️ long dựng bằng {len(stories)}/{n_skit} skit (skit hỏng đã bỏ)")
            story = stories if dai else stories[0]
            out = os.path.join("out", f"{DS.slug(kenh)}_{loai}.mp4")
            os.makedirs("out", exist_ok=True)
            ok, info = MB.dung_video(kenh, cfg, story, out, dai=dai, on_status=st)
            if not ok:
                st("failed", f"QC trượt: {info}")
                print(f"   ❌ {loai}: {info}"); continue
            st("rendering", "Đẩy kho Drive")
            # enqueue_drive nằm ở run_render (dùng chung đường đặt tên chuẩn + sidecar + thumbnail)
            import run_render as RR
            eq = RR.enqueue_drive(kenh, out, stories[0], loai, bo=("L" if dai else "S1"),
                                  script=json.dumps(story)[:400_000])
            _eq = eq if isinstance(eq, dict) else {}
            st("done", "Đã đẩy Drive" if _eq.get("id") else "Xong (chưa đẩy Drive)",
               title=stories[0].get("title", ""), drive_id=_eq.get("id", ""),
               drive_account=_eq.get("account", ""), size_mb=info.get("size_mb", 0),
               score=(story.get("self_score") or {}).get("total"),
               script=json.dumps(story)[:400_000])
            print(f"   ✅ {loai}: {stories[0].get('title')} · {info.get('dur')}s · "
                  f"{info.get('size_mb')}MB · {info.get('shots')} cảnh · {info.get('skit')} skit")
            ra.append(loai)
        except Exception as e:
            import traceback; traceback.print_exc()
            st("failed", f"pilot lỗi: {str(e)[:120]}")
    print(f"\n{'✅' if len(ra) == 2 else '⚠️'} pilot {kenh}: xong {ra}")
    return 0 if ra else 3


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rig", default="")
    ap.add_argument("--lam-lai", action="store_true")
    ap.add_argument("--pilot", default="")
    a = ap.parse_args()
    if a.seed:
        return seed(a.dry_run)
    if a.rig:
        return rig(a.rig.upper(), a.lam_lai)
    if a.pilot:
        return pilot(a.pilot.upper())
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
