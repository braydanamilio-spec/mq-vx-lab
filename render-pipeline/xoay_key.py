#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XOAY KHOÁ — MỘT ĐƯỜNG DUY NHẤT, CHẶN LỖI "TƯỞNG HẾT QUOTA" (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

Anh: *"qua cũng bị lỗi thế sao nay vẫn bị, cần fix đúng rule ko lặp lại nha"* và *"fix cả auto
trên pipeline sau này tự động trên github"*.

Anh nói đúng chỗ đau: luật đã ghi trong PIPELINE_RULES từ hôm qua, mà hôm nay tôi lặp lại y
nguyên — vì luật chỉ nằm trong tài liệu, không có gì trong CODE chặn nó.

── LỖI GỐC ───────────────────────────────────────────────────────────────────────────────
Cloudflare trả HTTP 429 cho HAI chuyện khác hẳn nhau:
    · hết neuron trong ngày (mã 4006)  — thật sự phải chờ;
    · gọi quá nhanh, giới hạn theo phút — chỉ cần nghỉ một nhịp.
Thông điệp lỗi cũ ghi cứng "hết neuron CF trong ngày" cho cả hai. Tôi đọc log, thấy dòng ấy,
rồi báo với anh rằng phải chờ hôm sau — trong khi 94 tài khoản CF mới dùng 52 ảnh trên trần
khoảng 16.000 ảnh/ngày, và ảnh NGAY SAU đó vẫn sinh thành công.

── BA THỨ TỆP NÀY BẢO ĐẢM ────────────────────────────────────────────────────────────────
  1. XOAY TỪ VỊ TRÍ KHÁC NHAU. Luôn bắt đầu từ khoá đầu danh sách nghĩa là mỗi lần gọi đều
     đâm vào đúng khoá vừa cạn, và mỗi lần đâm vẫn TRỪ hạn mức của nhà cung cấp.
  2. NGHỈ KHI GẶP RATE-LIMIT. 429 không kèm mã 4006 thì nghỉ một nhịp rồi đi tiếp; không coi
     là hỏng.
  3. CHỈ ĐƯỢC KẾT LUẬN "CẠN" KHI ĐÃ THỬ HẾT. Và khi ấy vẫn phải nói rõ đã thử bao nhiêu khoá,
     bao nhiêu cái báo 4006 — con số ấy là thứ phân biệt "cạn thật" với "gọi quá nhanh".

Mọi chỗ gọi ảnh CF đều phải đi qua đây, kể cả trong GitHub Actions.
"""
import os
import time
import random


class CanThat(Exception):
    """Cạn hạn mức THẬT: mọi khoá đều trả mã 4006 (hết neuron ngày)."""


# ── SỔ TRẠNG THÁI KHOÁ, GHI LÚC DÙNG THẬT  (2/9/2026) ───────────────────────────────────────
# Anh: *"sao a thấy ko thấy tình trạng, sao ko spam mà cập nhật và tiết kiệm quota, có thể lúc
# dùng mình lưu tình trạng lại."* — đúng, và đây là cách rẻ nhất có thể:
#
# Dây chuyền GỌI các khoá này hàng nghìn lượt mỗi ngày. **Mỗi lượt gọi thật đã là một phép đo
# sức khoẻ miễn phí.** Đi dò riêng là trả tiền lần thứ hai cho thông tin mình vừa có — và đó
# đúng là thứ nút "kiểm tất cả khoá" trên dashboard đang làm: gọi lại 295 khoá, tốn hạn mức của
# cả nhà cung cấp lẫn Firestore, để biết điều dây chuyền đã biết.
#
# `goi_xoay` vốn ĐÃ phân loại từng khoá (4006 = cạn ngày · 429 = gọi nhanh · khác) — rồi vứt đi,
# chỉ giữ mấy con số tổng. Nay giữ lại theo `id`, và ghi một lượt ở cuối tập.
#
# KHÔNG BAO GIỜ lưu chuỗi khoá. Chỉ lưu `id` (doc id sẵn có) và bốn ký tự cuối để người đọc
# nhận ra — đúng luật đã đặt: khoá không được in ra, không được ghi xuống.
_QUAN_SAT: dict = {}


def _moc_hoi_cf() -> str:
    """Mốc hồi neuron của Cloudflare: 00:00 UTC ngày hôm sau.

    Viết ra thành hàm chứ không rải hằng số: mốc hồi là thuộc tính của NHÀ CUNG CẤP, và một hằng
    số chép rải rác là cách chắc chắn để hôm nào họ đổi thì ta sửa được ba chỗ, quên chỗ thứ tư.
    """
    import datetime
    n = datetime.datetime.now(datetime.timezone.utc)
    return (n.replace(hour=0, minute=0, second=0, microsecond=0)
            + datetime.timedelta(days=1)).isoformat()


def _ghi_nhan(kid: str, s: str, song: bool, ly_do: str = "", nghi_den: str = "") -> None:
    if not kid:
        return
    import datetime
    _QUAN_SAT[kid] = {"alive": bool(song), "last4": str(s)[-4:],
                      "ly_do": ly_do[:80], "nghi_den": nghi_den,
                      "at": datetime.datetime.now(datetime.timezone.utc).isoformat()}


def loc_cf(keys) -> list:
    """Trả danh sách (chuỗi_khoá, id). Bản trước chỉ trả chuỗi, nên `goi_xoay` biết khoá nào
    hỏng mà KHÔNG biết nó là bản ghi nào — thông tin sức khoẻ vì thế không ghi lại được."""
    ra = []
    for k in keys or []:
        if isinstance(k, str):
            s, kid = k, ""
        elif isinstance(k, dict):
            s, kid = k.get("key", ""), str(k.get("id", "") or "")
        else:
            continue
        if s.startswith("cf:"):
            ra.append((s, kid))
    return ra


def goi_xoay(keys, ham, hat: int = 0, nghi_ratelimit: float = 1.2, giua_lan: float = 0.25):
    """Gọi `ham(khoa)` lần lượt qua các khoá cho tới khi một khoá trả về giá trị "thật".

    `ham` trả về giá trị falsy (hoặc ném lỗi) thì thử khoá tiếp theo.
    Ném `CanThat` chỉ khi MỌI khoá đều báo mã 4006 — tức cạn thật, không phải gọi nhanh.
    """
    cf = loc_cf(keys)
    if not cf:
        return None, {"da_thu": 0, "cf": 0, "ly_do": "không có khoá CF nào"}

    # Điểm bắt đầu đổi theo `hat` — mỗi ảnh/mỗi lần gọi vào một chỗ khác trong vòng khoá.
    dau = (hat * 7919 + random.randint(0, 97)) % len(cf)
    so_4006 = so_429 = so_khac = 0

    for i in range(len(cf)):
        k, kid = cf[(dau + i) % len(cf)]
        try:
            r = ham(k)
            if r:
                _ghi_nhan(kid, k, True)
                return r, {"da_thu": i + 1, "cf": len(cf), "4006": so_4006, "429": so_429}
            so_khac += 1
            _ghi_nhan(kid, k, False, "gọi được nhưng không ra kết quả")
        except Exception as e:
            t = str(e)
            if "4006" in t or "neuron" in t.lower():
                so_4006 += 1
                # CẠN NGÀY ≠ CHẾT. Khoá này mai lại dùng được, nên đánh dấu là còn sống nhưng
                # đang nghỉ — ghi `alive=False` ở đây là đẩy 97 khoá tốt vào cột "chết", rồi
                # sáng mai người đọc đi thay 97 khoá không hỏng.
                # Ghi `nghi_den` = mốc hồi neuron. Dashboard ĐÃ có sẵn trạng thái 😴 "Đang nghỉ"
                # đọc từ `cooling_until`, nên chỉ cần điền đúng trường ấy là anh nhìn ra ngay
                # "hôm nay cạn" — không phải sửa một dòng nào bên web.
                # Nếu chỉ ghi `alive=True` thì khoá hiện 🟢 Sống, đúng về mặt "mai còn dùng được"
                # nhưng SAI về mặt thứ anh cần biết lúc này: hôm nay nó không vẽ được nữa.
                _ghi_nhan(kid, k, True, "cạn neuron ngày (4006) — hồi lúc 00:00 UTC",
                          _moc_hoi_cf())
            elif "429" in t:
                so_429 += 1
                _ghi_nhan(kid, k, True, "gọi quá nhanh (429) — nghỉ rồi đi tiếp")
                time.sleep(nghi_ratelimit)     # rate-limit theo phút: nghỉ rồi đi tiếp
            else:
                so_khac += 1
                _ghi_nhan(kid, k, False, f"{type(e).__name__}: {t[:60]}")
        time.sleep(giua_lan)

    tk = {"da_thu": len(cf), "cf": len(cf), "4006": so_4006, "429": so_429, "khac": so_khac}
    if so_4006 >= len(cf):
        raise CanThat(f"cả {len(cf)} khoá CF đều hết neuron ngày (4006)")
    return None, tk


def bao_cao(tk: dict) -> str:
    """Câu báo cáo TRUNG THỰC — không được nói 'hết quota' khi chưa thử hết."""
    if not tk or not tk.get("cf"):
        return "không có khoá CF"
    if tk.get("da_thu", 0) < tk["cf"]:
        return f"xong sau {tk['da_thu']}/{tk['cf']} khoá"
    return (f"thử hết {tk['cf']} khoá · {tk.get('4006', 0)} cạn ngày · "
            f"{tk.get('429', 0)} rate-limit · {tk.get('khac', 0)} lỗi khác")


def ghi_trang_thai(owner: str = "") -> int:
    """Ghi trạng thái QUAN SÁT ĐƯỢC của các khoá vào đúng doc mà dashboard đang đọc.

    ── VÌ SAO GHI Ở ĐÂY, KHÔNG ĐI DÒ  (2/9/2026) ───────────────────────────────────────────
    Anh: *"sao ko spam mà cập nhật và tiết kiệm quota, có thể lúc dùng mình lưu tình trạng lại."*

    Ảnh chụp dashboard: **295 khoá · 241 "Chưa kiểm"**. Nút "kiểm tất cả" hiện có gọi lại đủ 295
    khoá — tốn hạn mức của cả nhà cung cấp lẫn Firestore — để biết đúng thứ dây chuyền vừa biết
    xong. Mỗi lượt gọi thật ĐÃ LÀ một phép đo sức khoẻ miễn phí; đi dò là trả tiền lần thứ hai.

    ── HAI QUYẾT ĐỊNH QUAN TRỌNG ──────────────────────────────────────────────────────────
    1. **Cạn neuron ngày KHÔNG phải chết.** Khoá 4006 mai lại dùng được, nên nó ghi `alive=True`
       kèm lý do. Ghi `alive=False` ở đây là đẩy 97 khoá tốt vào cột "chết", và sáng mai người
       đọc đi thay 97 khoá không hỏng — cổng bắt oan còn tệ hơn cổng không bắt.
    2. **Không bao giờ lưu chuỗi khoá.** Chỉ `id` (doc id sẵn có) và 4 ký tự cuối.

    Chi phí: ~100 lượt GHI mỗi lượt render, trên trần 20.000/ngày (hôm nay mới dùng 373). Ghi
    theo LÔ nên chỉ vài vòng mạng. Đây là việc phụ nên đi qua bức tường ngân sách.
    """
    if not _QUAN_SAT:
        return 0
    try:
        import firestore_bridge as FB
    except Exception:
        return 0
    try:
        FB.nap_nen_ngan_sach(owner)
    except Exception:
        pass
    if not FB.con_ngan_sach("ghi"):
        print(f"   ⏹ hoãn ghi sổ trạng thái khoá ({len(_QUAN_SAT)} khoá) — ngân sách GHI đã qua 70%")
        return 0
    try:
        db = FB._db_meta()
        if db is None:
            return 0
        # ── KHỚP THEO 4 KÝ TỰ CUỐI, KHÔNG THEO `id`  (3/9/2026) ──────────────────────────
        # Dashboard hiện `⚪ 97 chưa kiểm` cho CF trong khi tôi vừa đo cả 97 đều cạn — và
        # `nguon_kiem="dùng thật"` đếm được **0**. Tức bộ ghi này chưa ghi nổi một dòng nào.
        #
        # Gốc: khoá của dây chuyền có trường `id`, nhưng giá trị là **`local3`** — id tự sinh
        # khi đọc tệp khoá cục bộ / biến môi trường, KHÔNG phải doc id của Firestore. Nên nó
        # ghi vào `gemini_keys/local3`, một tài liệu chẳng ứng với khoá nào, còn dashboard đọc
        # doc thật nên không bao giờ thấy.
        #
        # Có `id` nên nhìn qua thì tưởng đúng — đây là kiểu lỗi tệ nhất: **trường tồn tại,
        # kiểu dữ liệu đúng, chỉ sai HỆ QUY CHIẾU.** Cùng họ với "chép hằng số sang hệ quy
        # chiếu khác" (§6): không có gì báo lỗi, chỉ có dữ liệu đi lạc chỗ.
        #
        # Khớp theo `last4` — chính thứ dashboard hiển thị và chắc chắn có ở cả hai phía. Tốn
        # MỘT truy vấn cho cả lượt chạy (đệm theo tiến trình), đổi lấy việc cơ chế thật sự chạy.
        if not hasattr(ghi_trang_thai, "_ban_do"):
            bd = {}
            try:
                for d in db.collection("gemini_keys").where("owner", "==", owner).stream():
                    x = d.to_dict() or {}
                    l4 = str(x.get("last4") or "")[-4:]
                    if l4:
                        bd[l4] = d.id
            except Exception as e:
                print(f"   ⚠ không dựng được bản đồ khoá ({str(e)[:60]}) — bỏ ghi sổ lượt này")
            ghi_trang_thai._ban_do = bd
            print(f"   🗺 bản đồ khoá: {len(bd)} doc khớp theo 4 ký tự cuối")
        _bd = ghi_trang_thai._ban_do
        if not _bd:
            return 0
        lo, n, _lac = db.batch(), 0, 0
        for kid, v in list(_QUAN_SAT.items()):
            _doc = _bd.get(str(v.get("last4") or "")[-4:])
            if not _doc:
                _lac += 1
                continue
            kid = _doc
            # `cooling_until` rỗng khi khoá gọi được -> XOÁ trạng thái nghỉ cũ. Không ghi đè
            # bằng chuỗi rỗng thì một khoá từng cạn hôm qua sẽ nằm mãi ở cột 😴, kể cả khi hôm
            # nay nó vẽ ngon — đúng họ lỗi "cờ bật thì có người bật, tắt thì không ai tắt".
            lo.set(db.collection("gemini_keys").document(kid),
                   {"alive": v["alive"], "last_checked": v["at"],
                    "cooling_until": v.get("nghi_den") or "",
                    "dead_reason": "" if v["alive"] else v["ly_do"],
                    "ghi_chu": v["ly_do"], "nguon_kiem": "dùng thật"}, merge=True)
            n += 1
            if n % 400 == 0:
                lo.commit(); lo = db.batch()
        lo.commit()
        if _lac:
            print(f"   ⚠ {_lac} khoá không tìm được doc khớp 4 ký tự cuối — bỏ qua")
        nghi = sum(1 for v in _QUAN_SAT.values() if v.get("nghi_den"))
        song = sum(1 for v in _QUAN_SAT.values() if v["alive"]) - nghi
        print(f"   🗝 ghi sổ trạng thái {n} khoá từ LƯỢT DÙNG THẬT — "
              f"🟢 {song} sống · 😴 {nghi} cạn hôm nay · 🔴 {n - song - nghi} hỏng "
              f"(không tốn lượt gọi dò nào)")
        _QUAN_SAT.clear()
        return n
    except Exception as e:
        print(f"   ⚠ ghi sổ trạng thái khoá hụt: {str(e)[:80]}")
        return 0
