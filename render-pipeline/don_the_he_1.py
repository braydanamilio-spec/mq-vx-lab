#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DỌN 55 KÊNH THẾ HỆ 1 — kiểm kê trước, dọn sau, và KHÔNG xoá vĩnh viễn (26/8/2026).

MẶC ĐỊNH CHỈ ĐẾM. Không truyền cờ thì script này không thay đổi một byte nào.

Ba lớp dọn, tách riêng để làm từng bước và dừng được giữa chừng:
    --tat        tắt 55 kênh cũ (paused=True). ĐẢO NGƯỢC ĐƯỢC, làm trước tiên.
    --kho        chuyển video + thumbnail + sidecar của kênh cũ vào THÙNG RÁC Drive (giữ 30 ngày)
    --ban-ghi    xoá bản ghi Firestore của kênh cũ (render_channels + hàng chờ)
    --job        xoá job của kênh cũ trong render_jobs (thứ dashboard hiện ở "Kho tổng video")

Vì sao thùng rác chứ không xoá thẳng: dọn nhầm một điều kiện lọc là mất hàng nghìn video không
có đường lùi. Thùng rác cho 30 ngày để phát hiện. Việc đổ thùng rác để người chủ tự bấm.

    python don_the_he_1.py                    # chỉ đếm
    python don_the_he_1.py --tat --that       # tắt kênh cũ
    python don_the_he_1.py --kho --that       # đưa kho vào thùng rác
"""
from __future__ import annotations

import io
import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))


def _db():
    """Client Firestore CÓ ĐƯỜNG LẬT B2 — dùng chung với dây chuyền chính.

    26/8 — bản đầu tự dựng client trỏ thẳng project B và chết ngay lần chạy đầu:
    `RESOURCE_EXHAUSTED: Quota exceeded.` vì B đang cạn hạn mức ngày (cờ nghỉ tới 06:59Z).
    Nghịch lý: đúng lúc hệ cạn quota là lúc cần thao tác quản trị nhất (tắt kênh, dọn kho), mà
    công cụ quản trị lại là thứ chết đầu tiên. `firestore_bridge._db_meta()` đã có sẵn failover
    sang gương B2 — dùng lại, đừng dựng client riêng."""
    import firestore_bridge as _FB
    return _FB._db_meta()


def _kenh_moi() -> set:
    p = os.path.join(GOC, "kenh_the_he_2.json")
    if not os.path.exists(p):
        return set()
    return {k["ten"].replace(" ", "") for k in json.load(io.open(p, encoding="utf-8"))}



def _duoi(ten: str) -> str:
    t = str(ten or "").rsplit(".", 1)
    return ("." + t[-1].lower()) if len(t) == 2 and len(t[-1]) <= 5 else "(không đuôi)"


# THƯ MỤC KHÔNG BAO GIỜ ĐƯỢC ĐỤNG TỚI (26/8).
# `CHANNEL_METHODS` có luật bất di bất dịch: "Dọn/xóa CHỈ đụng VIDEO. KHÔNG bao giờ xóa: method,
# repo, brand kit, config kênh, KỊCH BẢN/TOPIC ĐÃ LƯU." Kịch bản nằm trên Drive trong `_KICHBAN`,
# và tên tệp kịch bản cũng bắt đầu bằng tên kênh — tức bộ lọc theo tên sẽ quét trúng chúng.
# Mất kịch bản là mất thứ KHÔNG dựng lại được bằng tiền: phải gọi AI viết lại từ đầu.
# Chạy khô lần này đếm 3011 .mp4 · 3013 .jpg · 3013 .json — cân bằng 1:1:1 nên nhiều khả năng
# .json là sidecar chứ không phải kịch bản; nhưng "nhiều khả năng" không đủ để xoá 9.037 tệp.
CAM_DUNG = ("_KICHBAN", "_BACKUP", "_SCRIPT", "brand", "config")


def _di_het_kho(dr, goc: str, sau: int = 0, tran: int = 6, ten_kho: str = "?") -> list:
    """Đi HẾT cây thư mục, trả về MỌI tệp (không lọc theo loại).

    26/8 — BẢN ĐẦU DÙNG `dr._list_videos(goc)` VÀ SẼ DỌN ĐÚNG SỐ KHÔNG. Hai lý do, đo trên kho
    thật PAIZLYNOLUWADARA:
      • `_list_videos` chỉ hỏi `'<goc>' in parents` — tức CHỈ ngay tại thư mục gốc, không đi vào
        thư mục con. Mà tại gốc có **0 mp4, 0 jpg**; toàn bộ nằm trong `_QUEUE/` và `MM0-STORE/`:
        **85 mp4 · 85 jpg · 90 tệp khác**.
      • `_list_videos` còn lọc `mimeType in VIDEO_MIME`, nên thumbnail (.jpg) và sidecar (.json)
        không bao giờ bị đụng tới — dù chú thích của chính hàm `main` ghi là "video + thumbnail
        + sidecar".
    Kết quả sẽ là dòng "đã đưa vào thùng rác 0 tệp" — trông y hệt thành công.
    """
    ra = []
    try:
        muc = dr.svc.files().list(
            q=f"'{goc}' in parents and trashed = false",
            fields="nextPageToken, files(id,name,mimeType)",
            pageSize=200).execute()
    except Exception as e:
        # 26/8 — nêu TÊN KHO, không chỉ id. Log cũ in `thư mục undefined…: invalid_grant` mà
        # không nói kho nào ⇒ không biết đi sửa cái gì. Một cảnh báo không chỉ ra được thủ phạm
        # thì cũng gần như không có cảnh báo.
        print(f"      ⚠️ kho '{ten_kho}': không đọc được thư mục {str(goc)[:12]}… — {str(e)[:60]}")
        return ra
    tiep = muc.get("nextPageToken")
    ds = list(muc.get("files", []))
    while tiep:
        try:
            muc = dr.svc.files().list(
                q=f"'{goc}' in parents and trashed = false",
                fields="nextPageToken, files(id,name,mimeType)",
                pageSize=200, pageToken=tiep).execute()
        except Exception:
            break
        ds += list(muc.get("files", []))
        tiep = muc.get("nextPageToken")
    for f in ds:
        if "folder" in str(f.get("mimeType") or ""):
            ten_tm = str(f.get("name") or "")
            if any(c.lower() in ten_tm.lower() for c in CAM_DUNG):
                print(f"      🛡️ bỏ qua thư mục cấm đụng: {ten_tm}")
                continue
            if sau < tran:
                ra += _di_het_kho(dr, f["id"], sau + 1, tran, ten_kho)
        else:
            ra.append(f)
    return ra


def main() -> int:
    that = "--that" in sys.argv
    lam_tat = "--tat" in sys.argv
    lam_kho = "--kho" in sys.argv
    lam_bg = "--ban-ghi" in sys.argv
    lam_job = "--job" in sys.argv
    import firestore_bridge as FB
    db = _db()
    owner = os.environ.get("OWNER_UID") or ""
    # ĐỌC qua đường có failover B2. Stream thẳng thì B cạn hạn mức là chết ngay (đo thật 26/8:
    # `429 Quota exceeded` ngay lần chạy đầu). B2 là gương CHỈ ĐỌC — đủ cho bước kiểm kê; bước
    # ghi bên dưới vẫn phải vào B vì hạn mức đọc và ghi của Firestore tách riêng.
    try:
        tat_ca = [{**c, "_id": c.get("id") or f"{owner}__{c.get('name')}"}
                  for c in FB.read_channels(owner)]
    except Exception as e:
        print(f"❌ không đọc được danh sách kênh (kể cả gương B2): {str(e)[:90]}")
        return 2
    moi = _kenh_moi()
    cu = [c for c in tat_ca if str(c.get("the_he") or "") != "2" and (c.get("name") or "") not in moi]
    m2 = [c for c in tat_ca if str(c.get("the_he") or "") == "2"]

    print(f"\n{'='*70}\nKIỂM KÊ\n{'='*70}")
    print(f"  tổng kênh trong render_channels : {len(tat_ca)}")
    print(f"  kênh THẾ HỆ 1 (sẽ dọn)          : {len(cu)}")
    print(f"  kênh THẾ HỆ 2 (giữ)             : {len(m2)}")
    print(f"  đang bật trong nhóm cũ          : {sum(1 for c in cu if not c.get('paused'))}")
    # 26/8 — CỔNG NÀY PHẢI BIẾT MỌI CỜ. Thêm `--job` mà quên cập nhật cổng: workflow chạy đúng
    # `--job`, log không có lỗi nào, mà khối dọn job không bao giờ chạy tới — hàm thoát ở đây rồi.
    # Đúng dạng "thêm nhánh mới nhưng cổng cũ không biết đến nó", cùng họ với `tham_so.xoay` khai
    # ra mà không ai đọc. Chốt: t_cong_biet_moi_co.
    if not (lam_tat or lam_kho or lam_bg or lam_job):
        print("\n  (chỉ đếm. Thêm --tat / --kho / --ban-ghi / --job và --that để làm thật)")
        return 0

    if lam_tat:
        n = 0
        for c in cu:
            if c.get("paused"):
                continue
            n += 1
            if that:
                db.collection("render_channels").document(c["_id"]).set({"paused": True}, merge=True)
        print(f"\n  ⏸  {'đã tắt' if that else '(sẽ tắt)'} {n} kênh thế hệ 1")

    if lam_kho:
        src = os.environ.get("AUTOPUBLISHER_SRC")
        if src and src not in sys.path:
            sys.path.insert(0, src)
        try:
            import storage as ST
        except Exception as e:
            print(f"  ❌ không nạp được storage: {str(e)[:60]}")
            return 2
        ten_cu = {(c.get("name") or "").upper() for c in cu}
        # 26/8 — ĐƯỜNG LÙI KHI BẢN GHI ĐÃ BỊ XOÁ. Danh sách kênh cũ vốn suy ra từ chính
        # `render_channels`; xoá bản ghi trước rồi mới dọn kho thì `cu` rỗng ⇒ không tìm được tệp
        # nào ⇒ video/thumbnail cũ nằm lại vĩnh viễn, chiếm chỗ của 50 kênh mới. Nay tên đã được
        # chụp sẵn ra `kenh_the_he_1.json`, nên hai bước không còn phụ thuộc thứ tự.
        try:
            _snap = json.load(io.open(os.path.join(GOC, "kenh_the_he_1.json"), encoding="utf-8"))
            _them = {str(t).upper() for t in (_snap.get("ten") or [])} - ten_cu
            if _them:
                print(f"  📄 thêm {len(_them)} tên kênh cũ từ bản chụp (bản ghi đã xoá)")
                ten_cu |= _them
        except Exception as e:
            print(f"  ⚠️ không đọc được bản chụp tên kênh cũ: {str(e)[:60]}")
        tong = 0
        _loai: dict = {}
        for acc in ST.pool_accounts():
            try:
                dr = ST.account_drive(acc)
            except Exception as e:
                print(f"  ⚠️ kho {acc.get('name', '?')}: {str(e)[:50]}")
                continue
            goc = acc.get("root_id") or acc.get("root")
            if not goc:
                continue
            can_xoa = []
            for f in _di_het_kho(dr, goc, ten_kho=str(acc.get('name') or '?')):
                ten = str(f.get("name") or "")
                # CHỈ đụng tệp có tên kênh cũ ở đầu — không quét mù cả kho
                if not any(ten.upper().startswith(t) for t in ten_cu):
                    continue
                tong += 1
                _loai[_duoi(ten)] = _loai.get(_duoi(ten), 0) + 1
                can_xoa.append(f["id"])
            if that and can_xoa:
                # 26/8 — XOÁ SONG SONG + IN TIẾN ĐỘ. Bản đầu gọi `dr.trash()` tuần tự: 9.037 tệp
                # × ~0,3s/lượt ≈ 45 phút, đúng bằng `timeout-minutes` ⇒ job bị giết giữa chừng
                # (chạy 45'21" rồi `The operation was canceled`), dọn dở dang mà log KHÔNG cho biết
                # đã tới đâu. Một việc dài mà không in tiến độ thì lúc nó chết chẳng ai biết mất gì.
                # Thùng rác nên chạy lại là tiếp tục phần còn lại, không hỏng gì.
                # 26/8 — TUẦN TỰ, CÓ CHỦ Ý. Bản trước em cho 8 luồng cùng gọi `dr.trash()` để chạy
                # cho nhanh, và nó **làm hỏng bộ nhớ**: `free(): corrupted unsorted chunks` →
                # `Aborted (core dumped)`, exit 134. Client google-api-python-client dùng chung một
                # `httplib2.Http` KHÔNG an toàn đa luồng — chia sẻ giữa các luồng là hỏng ở tầng C,
                # không phải ngoại lệ Python nên `try/except` cũng không đỡ được.
                # Muốn nhanh thì phải mỗi luồng một `svc` riêng, hoặc dùng batch request. Nhưng
                # trần thời gian nay đã 330 phút trong khi việc chỉ tốn ~45 phút — không có lý do
                # gì đánh đổi rủi ro lấy tốc độ mình không cần.
                xong = 0
                for fid in can_xoa:
                    try:
                        dr.trash(fid)
                    except Exception as e:
                        print(f"      ⚠️ bỏ sót 1 tệp: {str(e)[:50]}")
                    xong += 1
                    if xong % 200 == 0:
                        print(f"      … {xong}/{len(can_xoa)} tệp của kho "
                              f"'{acc.get('name', '?')}'", flush=True)
                print(f"      ✅ kho '{acc.get('name', '?')}': {len(can_xoa)} tệp vào thùng rác",
                      flush=True)
        print(f"\n  🗑  {'đã đưa vào thùng rác' if that else '(sẽ đưa vào thùng rác)'} {tong} tệp "
              f"— Drive giữ 30 ngày, khôi phục được")
        if _loai:
            print("      " + " · ".join(f"{k}: {v}" for k, v in sorted(_loai.items(), key=lambda x: -x[1])))
        elif not that:
            print("      ⚠️ ĐẾM RA 0 TỆP. Kiểm lại trước khi chạy thật — 0 gần như luôn là lỗi lọc, "
                  "không phải kho trống.")

    if lam_job:
        # 26/8 — anh chỉ ra: dashboard vẫn liệt kê 2.486 video của 55 kênh cũ trong "Kho tổng video".
        # Đúng, vì gallery đọc `render_jobs` (Project B) chứ không đọc `render_channels`. Bản dọn
        # trước xoá bản ghi KÊNH và tệp trên Drive, nên các job này giờ trỏ vào tệp đã nằm trong
        # thùng rác — vừa rác mắt, vừa làm mọi con số tồn kho sai.
        #
        # Lấy tên kênh cũ từ BẢN CHỤP, không từ `render_channels`: bản ghi đã xoá rồi nên suy từ
        # đó ra sẽ được đúng số không (cùng cái bẫy thứ tự đã vấp ở bước dọn kho).
        ten_cu = {str(c.get("name") or "").upper() for c in cu if c.get("name")}
        try:
            _snap = json.load(io.open(os.path.join(GOC, "kenh_the_he_1.json"), encoding="utf-8"))
            ten_cu |= {str(t).upper() for t in (_snap.get("ten") or [])}
        except Exception as e:
            print(f"  ⚠️ không đọc được bản chụp tên kênh cũ: {str(e)[:60]}")
        ten_cu.discard("")
        ten_moi = {str(t).upper() for t in _kenh_moi()}
        # CHẶN CỨNG: tên nào vừa ở danh sách cũ vừa ở danh sách 50 kênh mới thì BỎ QUA. Trùng tên
        # là chuyện có thật (bản chụp lấy từ lịch sử), và xoá nhầm job của kênh mới là mất video
        # thật chứ không phải rác.
        chong = ten_cu & ten_moi
        if chong:
            print(f"  🛡  {len(chong)} tên có ở CẢ hai danh sách — bỏ qua để khỏi xoá nhầm: "
                  f"{', '.join(sorted(chong))}")
            ten_cu -= ten_moi
        print(f"\n  🔎 quét render_jobs của {len(ten_cu)} kênh cũ…")
        xoa, giu, theo_kenh = 0, 0, {}
        lo = []
        for d in db.collection("render_jobs").where("owner", "==", owner).stream():
            j = d.to_dict() or {}
            ch = str(j.get("channel") or "").upper()
            if ch in ten_cu:
                xoa += 1
                theo_kenh[ch] = theo_kenh.get(ch, 0) + 1
                lo.append(d.reference)
            else:
                giu += 1
        print(f"  📊 khớp {xoa} job của kênh cũ · giữ nguyên {giu} job (kênh mới/khác)")
        for k, n in sorted(theo_kenh.items(), key=lambda x: -x[1])[:8]:
            print(f"      {k}: {n}")
        if that and lo:
            # Xoá theo lô 400 (trần Firestore là 500 thao tác/lô) — 2.486 job thành ~7 lượt ghi lô
            # thay vì 2.486 lượt gọi lẻ.
            b = db.batch(); n = 0
            for i, ref in enumerate(lo, 1):
                b.delete(ref); n += 1
                if n >= 400 or i == len(lo):
                    b.commit(); b = db.batch(); n = 0
                    print(f"      … đã xoá {i}/{len(lo)}", flush=True)
        print(f"  🧹 {'đã xoá' if that else '(sẽ xoá)'} {xoa} job của 55 kênh cũ khỏi Kho tổng video")

    if lam_bg:
        n = 0
        for c in cu:
            n += 1
            if that:
                db.collection("render_channels").document(c["_id"]).delete()
        print(f"\n  🧹 {'đã xoá' if that else '(sẽ xoá)'} {n} bản ghi kênh trong render_channels")
    if not that:
        print("\n  ⚠️ CHƯA LÀM GÌ CẢ — thiếu cờ --that")
    return 0


if __name__ == "__main__":
    sys.exit(main())
