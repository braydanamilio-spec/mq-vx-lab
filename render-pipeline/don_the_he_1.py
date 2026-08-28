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
    # 27/8 — CHẾ ĐỘ `--gen2`: dọn VIDEO của 50 kênh THẾ HỆ 2 để làm lại từ đầu.
    #
    # Anh yêu cầu "dọn sạch toàn bộ nội dung các channel và cải tổ cho đẹp". Viết công cụ mới thì
    # phải viết lại từ đầu mọi lớp an toàn mà tệp này đã có và đã trả giá để có:
    #   • CHỈ đưa vào THÙNG RÁC (`dr.trash`), không xoá hẳn -> còn khôi phục được
    #   • chừa `_KICHBAN`/`_BACKUP`/`brand`/`config` -> không mất kịch bản, không mất nhận diện
    #   • lọc theo TIỀN TỐ TÊN KÊNH, không quét mù cả kho
    #   • xoá tuần tự có in tiến độ, tránh bị giết giữa chừng mà không biết đã dọn tới đâu
    # Nên chỉ đổi ĐÍCH NHẮM, giữ nguyên toàn bộ phần còn lại.
    #
    # Sổ chủ đề (`render_topics`) KHÔNG bị đụng — đúng luật CHANNEL_METHODS, và còn có lợi: làm
    # lại mà vẫn nhớ đề tài cũ thì loạt mới ra đề tài KHÁC, không lặp lại đúng những video vừa xoá.
    gen2 = "--gen2" in sys.argv
    tha = "--tha-de-tai" in sys.argv
    that = "--that" in sys.argv
    if gen2 and "--ban-ghi" in sys.argv:
        # KHOÁ CỨNG. `--ban-ghi` xoá BẢN GHI KÊNH khỏi Firestore. Với thế hệ 1 thì đúng (những
        # kênh đó đã nghỉ hẳn). Với thế hệ 2 thì đó là xoá cấu hình của 50 kênh đang sống —
        # mất chỉ tiêu, mất trạng thái bật/tắt, mất mọi thứ trừ thứ repo giữ hộ.
        # Anh dặn "đừng xoá nhầm những gì quan trọng". Hai cờ này không bao giờ được đi cùng nhau,
        # nên chặn ở đây thay vì trông vào việc gõ lệnh đúng.
        print("🛑 TỪ CHỐI: `--gen2` không được đi cùng `--ban-ghi`.")
        print("   `--ban-ghi` xoá BẢN GHI KÊNH — với gen-2 nghĩa là xoá cấu hình 50 kênh đang chạy.")
        print("   Dọn video thì dùng: --gen2 --kho --job --that")
        return 2
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
    # 27/8 — LỌC THEO KÊNH: dọn ĐÚNG cái hỏng, không nuke cả mẻ.
    #
    # Hôm nay dính đúng tình huống cần nó: bản vá "số hiện ra mất độ lớn" chỉ ảnh hưởng 3/50 kênh
    # (AMERICA LOOKED UP mất chữ `K`; PENTAGON LEDGER và SPACE INVOICE in `2,540 $M` thay vì
    # `$2,540M`). Không có bộ lọc thì lựa chọn duy nhất là `--gen2` = dọn video của CẢ 50 kênh —
    # ném đi hàng chục video hoàn toàn tốt để sửa ba cái. Dọn thừa cũng là mất mát, chỉ là loại
    # mất mát không ai ghi sổ.
    _chi = {t.strip().upper().replace(" ", "") for t in
            (os.environ.get("CHI_KENH") or "").replace(";", ",").split(",") if t.strip()}
    if _chi and not gen2:
        # 27/8 — CHẶN CỨNG. Ở nhánh KHÔNG gen2, `moi` là danh sách kênh được MIỄN dọn (dòng
        # `... not in moi` ngay dưới). Lọc nó xuống 3 tên thì 47 kênh thế hệ 2 còn lại rơi vào diện
        # "kênh cũ" và bị dọn sạch — đúng thảm hoạ mà bộ lọc này sinh ra để tránh. Cùng một biến,
        # hai nhánh, hai nghĩa ngược nhau: ở gen2 nó là ĐÍCH NHẮM, ở đây nó là DANH SÁCH MIỄN.
        print("🛑 TỪ CHỐI: `CHI_KENH` chỉ dùng được cùng `--gen2`.")
        print("   Không có `--gen2` thì danh sách này mang nghĩa NGƯỢC LẠI (kênh được miễn dọn),")
        print("   và lọc nó sẽ khiến 47 kênh thế hệ 2 còn lại bị dọn nhầm.")
        return 2
    if _chi:
        _la = {str(t).upper().replace(" ", "") for t in moi}
        _sai = _chi - _la
        if _sai:
            # Gõ sai tên mà im lặng bỏ qua thì lệnh chạy "thành công" và không dọn gì — người dùng
            # tưởng đã dọn. Chặn thẳng, và in ra danh sách đúng để sửa được ngay.
            print(f"🛑 TỪ CHỐI: không có kênh {sorted(_sai)} trong 50 kênh thế hệ 2.")
            print(f"   Tên hợp lệ: {', '.join(sorted(_la))}")
            return 2
        moi = [t for t in moi if str(t).upper().replace(" ", "") in _chi]
        print(f"🎯 CHỈ DỌN {len(moi)} kênh được chỉ định: {', '.join(sorted(moi))}")
    if gen2:
        # Đích nhắm = 50 kênh gen-2, lấy TỪ REPO chứ không từ Firestore: repo là nơi định nghĩa
        # kênh nào tồn tại, và nó đọc được cả khi Firestore cạn hạn mức.
        cu = [{"name": t, "the_he": 2} for t in sorted(moi)]
        m2 = []
        print(f"🧹 CHẾ ĐỘ GEN-2: dọn video của {len(cu)} kênh thế hệ 2 (làm lại từ đầu).")
        print("   Giữ nguyên: kịch bản (_KICHBAN), brand kit, cấu hình kênh, sổ chủ đề.")
    else:
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
    if gen2 and tha:
        # Dọn video ĐỂ LÀM LẠI thì sổ đề tài phải được thả, nếu không hệ sẽ né đúng những đề tài
        # vừa xoá và đi làm cái khác — "dọn để làm lại" thành "dọn rồi làm cái khác".
        n = 0
        for c in cu:
            if that and FB.tha_de_tai(owner, c["name"]):
                n += 1
        print(f"  🔓 {'đã thả' if that else '(sẽ thả)'} sổ đề tài của {n if that else len(cu)} kênh "
              f"— những đề tài đó được LÀM LẠI. Kịch bản trên Drive (_KICHBAN) giữ nguyên.")
    if not (lam_tat or lam_kho or lam_bg or lam_job or tha):
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
        # 27/8 — HAI BƯỚC DƯỚI ĐÂY CHỈ ĐÚNG CHO CHẾ ĐỘ GEN-1, VÀ LÀM HỎNG HẲN CHẾ ĐỘ GEN-2.
        # Bản chạy khô lôi ra: ở `--gen2`, đích nhắm CHÍNH LÀ 50 kênh mới. Nhưng bước này (a) nhập
        # thêm 55 tên thế hệ 1 từ bản chụp, rồi (b) chốt cứng "tên nào có ở CẢ hai danh sách thì
        # bỏ qua" — mà cả 50 tên gen-2 đều nằm ở cả hai ⇒ bị loại sạch, và lệnh đi xoá nhầm job
        # của 55 kênh cũ. Kết quả: video gen-2 vẫn nằm nguyên trong thư viện, mà log vẫn báo
        # "đã xoá 365 job".
        # Chốt (b) sinh ra để chống xoá nhầm KHI dọn kênh cũ; ở chế độ gen-2 nó chống nhầm mục tiêu.
        if not gen2:
            try:
                _snap = json.load(io.open(os.path.join(GOC, "kenh_the_he_1.json"), encoding="utf-8"))
                ten_cu |= {str(t).upper() for t in (_snap.get("ten") or [])}
            except Exception as e:
                print(f"  ⚠️ không đọc được bản chụp tên kênh cũ: {str(e)[:60]}")
        ten_cu.discard("")
        ten_moi = set() if gen2 else {str(t).upper() for t in _kenh_moi()}
        # CHẶN CỨNG: tên nào vừa ở danh sách cũ vừa ở danh sách 50 kênh mới thì BỎ QUA. Trùng tên
        # là chuyện có thật (bản chụp lấy từ lịch sử), và xoá nhầm job của kênh mới là mất video
        # thật chứ không phải rác.
        chong = ten_cu & ten_moi
        if chong:
            print(f"  🛡  {len(chong)} tên có ở CẢ hai danh sách — bỏ qua để khỏi xoá nhầm: "
                  f"{', '.join(sorted(chong))}")
            ten_cu -= ten_moi
        # 26/8 — QUÉT CẢ HAI PROJECT, KHÔNG CHỈ B.
        # Anh chỉ ra dashboard vẫn hiện job kênh cũ sau khi em báo "đã dọn sạch". Đo ra: Firestore B
        # trả về 0 job kênh cũ (sạch thật), nhưng dashboard hiện 40 — vì `__rsJobsData` của nó là
        # HỢP NHẤT ba nguồn: `__jA` (render_jobs project A), `__jB` (project B), `__jX` (đệm trong
        # trang). Bản dọn dùng `_db_meta()` = CHỈ project B, nên A chưa bao giờ bị đụng tới.
        # Đây là lần thứ ba trong ngày em đếm thiếu nơi lưu: tưởng một (B) -> thêm D1 -> thêm
        # render_stats -> nay thêm A. Nên từ đây in số RIÊNG TỪNG PROJECT, không gộp thành một con
        # số duy nhất — một con số gộp là chỗ để lỗi này trốn.
        import firestore_bridge as _FB2
        _ds, _thay = [], set()
        for _ten, _lay in (("B (meta)", _FB2._db_meta), ("A (gốc)", _FB2._db)):
            try:
                _c = _lay()
                _pid = str(getattr(_c, "project", _ten))
                if _pid in _thay:
                    continue
                _thay.add(_pid)
                _ds.append((_ten, _c))
            except Exception as _e:
                print(f"  ⚠️ không mở được project {_ten}: {str(_e)[:70]}")
        _lo_theo_proj: dict = {}      # project -> [(client, ref)] — xem khối xoá bên dưới
        print(f"\n  🔎 quét render_jobs của {len(ten_cu)} kênh cũ trên {len(_ds)} project…")
        xoa, giu, theo_kenh = 0, 0, {}
        lo = []
        for _ten, _c in _ds:
            # 26/8 — BỌC LỖI THEO TỪNG PROJECT. Bản đầu chỉ bọc lúc MỞ client, không bọc lúc QUÉT.
            # Chạy thật: project A trả `RESOURCE_EXHAUSTED` (cạn hạn mức đọc ngày) ngay giữa vòng
            # lặp ⇒ ném lên trên ⇒ giết cả lượt dọn, kéo theo bước `render_stats` phía sau không
            # bao giờ chạy. Một project cạn quota KHÔNG được phép làm hỏng việc dọn ở project khác —
            # đó đúng là lý do hệ chia ba project ngay từ đầu.
            _x = _g = 0
            try:
                for d in _c.collection("render_jobs").where("owner", "==", owner).stream():
                    j = d.to_dict() or {}
                    ch = str(j.get("channel") or "").upper()
                    if ch in ten_cu:
                        _x += 1
                        theo_kenh[ch] = theo_kenh.get(ch, 0) + 1
                        lo.append(d.reference)
                        _lo_theo_proj.setdefault(_ten, []).append((_c, d.reference))
                    else:
                        _g += 1
                print(f"      project {_ten}: khớp {_x} · giữ {_g}")
            except Exception as _e:
                _msg = str(_e)[:90]
                _can = "RESOURCE_EXHAUSTED" in str(_e) or "Quota exceeded" in str(_e)
                print(f"      project {_ten}: {'CẠN HẠN MỨC' if _can else 'lỗi'} — bỏ qua project này "
                      f"({_msg})")
                print(f"         ⚠️ job kênh cũ ở {_ten} CHƯA được dọn. Chạy lại sau khi hạn mức hồi "
                      f"(00:00 giờ Thái Bình Dương = 07:00Z).")
            xoa += _x; giu += _g
        print(f"  📊 TỔNG khớp {xoa} job của kênh cũ · giữ nguyên {giu} job (kênh mới/khác)")
        for k, n in sorted(theo_kenh.items(), key=lambda x: -x[1])[:8]:
            print(f"      {k}: {n}")
        if that and lo:
            # Xoá theo lô 400 (trần Firestore là 500 thao tác/lô) — 2.486 job thành ~7 lượt ghi lô
            # thay vì 2.486 lượt gọi lẻ.
            #
            # 27/8 — LÔ PHẢI DỰNG TỪ ĐÚNG CLIENT ĐÃ ĐỌC RA REF ĐÓ.
            # Bản cũ gom ref của MỌI project vào một danh sách `lo` rồi xoá bằng đúng một client
            # `db`. Firestore từ chối thẳng:
            #     "The request was for database 'projects/A/...' but was attempting to access
            #      database 'projects/B/...'"
            # Nên lệnh dọn ĐẾM ĐƯỢC (365 job) nhưng XOÁ HỎNG — chạy khô thì xanh, chạy thật thì
            # ném, và rác vẫn nằm nguyên. Đúng loại lỗi chỉ lộ ra ở đường ghi.
            # Nay gom ref theo TỪNG project và commit bằng chính client của project đó.
            _tong = sum(len(v) for v in _lo_theo_proj.values())
            _da = 0
            for _ten2, _cap in _lo_theo_proj.items():
                if not _cap:
                    continue
                _cli = _cap[0][0]
                b = _cli.batch(); n = 0
                try:
                    for i, (_c2, ref) in enumerate(_cap, 1):
                        b.delete(ref); n += 1
                        if n >= 400 or i == len(_cap):
                            b.commit(); b = _cli.batch(); n = 0
                            _da += min(400, i)
                            print(f"      … {_ten2}: đã xoá {i}/{len(_cap)}", flush=True)
                except Exception as _e2:
                    print(f"      ⚠️ {_ten2}: xoá hụt ({str(_e2)[:70]}) — project khác vẫn dọn tiếp")
            print(f"      ✅ tổng đã xoá ~{_da}/{_tong} bản ghi")
        print(f"  🧹 {'đã xoá' if that else '(sẽ xoá)'} {xoa} job Firestore của "
              f"{len(ten_cu)} kênh {'THẾ HỆ 2' if gen2 else 'thế hệ 1'}")
        # ── ĐỐI CHIẾU SAU KHI XOÁ (27/8) ─────────────────────────────────────────────────────
        # Vừa dính đúng bài học này: lệnh dọn ĐẾM ĐƯỢC 365 job rồi in "đã xoá 365", trong khi
        # lệnh xoá ném vì dùng client sai project — rác vẫn nằm nguyên mà log vẫn đẹp.
        # In con số mình ĐỊNH làm thì rẻ; đọc lại xem thực tế còn bao nhiêu mới là bằng chứng.
        # Đọc lại tốn thêm ít lượt, nhưng rẻ hơn nhiều so với tin vào một con số không đúng rồi
        # phát hiện sau vài ngày.
        if that and lo:
            _con = 0
            for _ten2, _cap in _lo_theo_proj.items():
                if not _cap:
                    continue
                _cli = _cap[0][0]
                try:
                    for _c2, _ref in _cap[:60]:          # lấy mẫu 60 bản/project, đủ để biết thật giả
                        if _ref.get().exists:
                            _con += 1
                except Exception as _e3:
                    print(f"      ⚠️ không đối chiếu được {_ten2}: {str(_e3)[:60]}")
            if _con:
                print(f"  🚨 ĐỐI CHIẾU: còn {_con} bản ghi TRONG MẪU vẫn tồn tại — lệnh xoá KHÔNG "
                      f"ăn. Đừng tin con số phía trên.")
            else:
                print("  ✅ đối chiếu: mẫu kiểm tra đã sạch — lệnh xoá ăn thật.")
        # D1 LÀ KHO THỨ HAI, KHÔNG PHẢI BẢN SAO CHO VUI. Dashboard đọc D1 khi có lọc ngày, nên bỏ
        # bước này thì video cũ biến mất ở "Mọi lúc" rồi hiện lại y nguyên khi bấm "Hôm nay" —
        # nhìn như đã dọn xong mà chưa xong, tệ hơn là không dọn.
        try:
            import hot_db as H
            if that:
                # 28/8 — DỌN NỐT `videos`. Thiếu bước này là dọn nửa vời: D1 báo "còn 81" mà
                # dashboard vẫn hiện 1218, vì thư viện đọc `videos` chứ không đọc `render_jobs`.
                # Bản ghi của kênh KHÔNG CÒN TỒN TẠI — không tra được bằng tên, phải hỏi ngược
                # "kênh này còn sống không". Đây là chỗ ~1218 bản ghi ma nằm.
                # Bản ghi `videos` không còn job mang `drive_id` đó = file đã vào thùng rác.
                # Suy từ TRẠNG THÁI THẬT, không đoán theo tên kênh hay theo ngày.
                _kj, _tv, _ts = FB.don_videos_khong_con_job(owner, that)
                print(f"  👻 videos không còn job: {'đã xoá' if that else '(sẽ xoá)'} {_kj}/{_tv} "
                      f"bản ghi · {_ts} drive_id còn sống trong render_jobs")
                _mc, _bang = FB.don_videos_mo_coi(owner, list(_kenh_moi()), that)
                if _mc:
                    print(f"  👻 videos mồ côi (kênh không còn tồn tại): "
                          f"{'đã xoá' if that else '(sẽ xoá)'} {_mc} bản ghi")
                    for k, n in sorted(_bang.items(), key=lambda x: -x[1])[:8]:
                        print(f"        {k}: {n}")
                _nv = FB.don_videos_theo_kenh(owner, sorted(ten_cu), that)
                print(f"  🧹 videos: {'đã xoá' if that else '(sẽ xoá)'} {_nv} bản ghi thư viện "
                      f"của {len(ten_cu)} kênh — đây là thứ dashboard đếm")
                r = H.don_job_kenh(owner, sorted(ten_cu))
                print(f"  🧹 D1: đã xoá {r.get('xoa', 0)} job · còn lại {r.get('con_lai', '?')} "
                      f"bản ghi done-có-file")
            else:
                print(f"  🧹 D1: (sẽ xoá job của {len(ten_cu)} kênh cũ)")
        except Exception as e:
            print(f"  ⚠️ không dọn được D1: {str(e)[:80]} — Kho tổng video sẽ còn video cũ khi lọc ngày")

        # KHO THỨ BA. Anh gửi ảnh: "Tất cả kênh (0)" — kho video đã sạch — mà ô xổ VẪN liệt kê 49
        # kênh cũ kèm số đếm riêng (THENNOWUSA 15, UNDERUSA 36…). Vì `rsGalInto` dựng danh sách kênh
        # bằng cách GỘP BA nguồn:
        #     all.map(j => j.channel)      -> render_jobs (đã dọn)
        #     rsD1Chans(dv)                -> D1 render_job (đã dọn)
        #     window.__chStats             -> render_stats/{owner}  <- CÒN NGUYÊN
        # `render_stats/{owner}` là MỘT doc, khoá là tên kênh, mỗi khoá giữ {l, s}. Gộp ba nguồn thì
        # chỉ cần một nguồn còn sót là kênh cũ vẫn hiện — và đây là lần thứ hai trong ngày em báo
        # "đã dọn xong" khi chưa xong, vì đếm thiếu nơi lưu.
        try:
            ref = db.collection("render_stats").document(owner)
            d = (ref.get().to_dict() or {}) if that or True else {}
            bo = [k for k, v in d.items()
                  if isinstance(v, dict) and ("l" in v or "s" in v) and k.upper() in ten_cu]
            print(f"  🔎 render_stats: {len(bo)} khoá kênh cũ / {len(d)} khoá")
            if that and bo:
                from google.cloud import firestore as _fs
                ref.update({k: _fs.DELETE_FIELD for k in bo})
            print(f"  🧹 render_stats: {'đã xoá' if that else '(sẽ xoá)'} {len(bo)} khoá kênh cũ")
        except Exception as e:
            print(f"  ⚠️ không dọn được render_stats: {str(e)[:80]} — ô xổ sẽ còn tên kênh cũ")

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
