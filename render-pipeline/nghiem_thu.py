#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NGHIỆM THU — chấm THỨ ĐI RA, không chấm hình dạng mã (28/8/2026).

VÌ SAO CẦN, SAU 60+ CHỐT KIỂM ĐÃ CÓ
------------------------------------
Đêm 27-28/8 vá 8 lỗi, và gần như MỌI lỗi đều cùng một họ — hai nơi hiểu khác nhau về cùng
một thứ:
    • chống trùng kiểm chuỗi A, video mang chuỗi B     -> 334/600 video trùng
    • dữ liệu là ĐẾM, nhãn thang ghi XÁC SUẤT           -> "1 in 10,000" cạnh "63.4K"
    • `DongNguon` được nhập mà không được vẽ            -> 4 kênh mất dòng nguồn
    • nhạc có ở máy, không có trong git                 -> 29 kênh hỏng lệnh render
    • hồ key đầy, không ai truyền vào `chay_phim`       -> 10 kênh ra 0 video
    • ghi Firestore B, dashboard đọc A                  -> đếm sai

Không cái nào là "mã dở". Tất cả nằm ở ĐƯỜNG NỐI giữa các tầng (bộ dựng -> story -> props ->
composition -> đẩy kho). Và 60+ chốt đã có đều soi HÌNH DẠNG MÃ — hàm này có gọi hàm kia không,
chuỗi này có trong tệp kia không. Không chốt nào bắt được một lỗi nào trong danh sách trên, vì
lỗi không nằm trong mã: nó nằm trong THỨ ĐI RA.

Nên bài này chấm sản phẩm:
    1. dựng story THẬT cho từng dạng (đúng đường mà 50 kênh đi)
    2. soi tiêu đề + props sẽ đi ra
    3. RENDER THẬT một dạng mỗi phiên (xoay vòng) rồi đo tệp: ra được không, đủ dài không,
       có tiếng không, đúng khổ không
Bước 3 là thứ bắt được lớp "chạy được ở máy tôi" — thiếu nhạc, thiếu phông, thiếu khoá.

CHẠY Ở ĐÂU
----------
Trong job `plan`, TRƯỚC khi sinh 18 luồng. Đỏ thì chặn cả phiên — vì sinh 18 luồng vào một bản
hỏng là đốt hàng giờ để ra rác, đúng thứ vừa xảy ra.
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import time

GOC = os.path.dirname(os.path.abspath(__file__))
DANG = ["ranked", "scaled", "mapped", "thennow", "race", "longshot", "cinematic"]


def _kenh_mau(dang: str) -> dict | None:
    """Một kênh thật của dạng này — nghiệm thu phải đi đúng đường mà 50 kênh đi."""
    ks = json.load(io.open(os.path.join(GOC, "kenh_the_he_2.json"), encoding="utf-8"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    for k in ks:
        if k.get("dinh_dang") == dang:
            return k
    return None


def cham_tieu_de(t: str) -> list:
    """Soi một tiêu đề như người xem Mỹ nhìn nó. Trả danh sách lỗi."""
    e = []
    t = str(t or "")
    if not t.strip():
        return ["tiêu đề rỗng"]
    if "_" in t:
        e.append(f"lộ mã nội bộ (có gạch dưới): {t[:60]}")
    if re.search(r"\[['\"]", t):
        e.append(f"lộ repr Python (dấu ngoặc vuông + nháy): {t[:60]}")
    if any(ord(c) > 127 and c not in "—–’‘“”" for c in t):
        e.append(f"có ký tự không phải tiếng Anh: {t[:60]}")
    if len(t) > 100:
        e.append(f"dài {len(t)} ký tự — YouTube cắt quanh 70, phần đầu phải đủ ý")
    # HAI CHỦ THỂ MÂU THUẪN trong một tiêu đề — lỗi thật ngày 28/8:
    #     "Dodgers: 98 W — MLB wins by season (2025) — Brewers, 97 W (2025)"
    # Người xem đọc ra hai kẻ dẫn đầu khác nhau và không biết tin ai.
    # Bắt bằng khuôn "TÊN RIÊNG + dấu ngăn + SỐ" xuất hiện nhiều hơn một lần. Biểu thức đầu của
    # tôi quá lỏng (`[\w' .-]{2,28}` nuốt cả câu) nên trượt đúng ví dụ nó sinh ra để bắt.
    ten_so = re.findall(r"\b([A-Z][A-Za-z.'’-]*(?:\s[A-Z][A-Za-z.'’-]*){0,2})\s*[:,]\s*[\d$]", t)
    rieng = {x.strip().lower() for x in ten_so if len(x.strip()) > 2}
    if len(rieng) > 1:
        e.append(f"hai chủ thể mang số khác nhau trong một tiêu đề ({', '.join(sorted(rieng))}): {t[:60]}")
    return e


def cham_story(dang: str, st: dict) -> list:
    """Soi STORY — chỗ props lấy dữ liệu ra. Chạy được mà KHÔNG cần render.

    28/8 — lỗ trong chính bài này: chế độ `--khong-render` (đúng chế độ gắn vào workflow) chỉ soi
    TIÊU ĐỀ, không soi props. Mà props là chỗ chứa dòng nguồn, phụ đề, kiểu thang — tức ba trong
    sáu lỗi lớn đêm qua. Cổng chặn phiên mà bỏ qua đúng ba lỗi đó thì gần như vô dụng.
    Dựng props thật thì phải tổng hợp giọng đọc (tốn tiền, tốn phút). Nhưng props chỉ ĐỌC LẠI từ
    story — nên soi story là soi đúng nguồn của chúng, mà không tốn gì."""
    e = []
    if not str(st.get("nguon") or "").strip():
        e.append(f"{dang}: story thiếu `nguon` -> props không có gì để ghi, video mất dòng nguồn")
    if dang == "ranked" and not str(st.get("subtitle") or "").strip():
        e.append("ranked: story thiếu `subtitle` -> người xem không biết đang xếp theo gì")
    if dang == "longshot":
        muc = st.get("items") or []
        co_dem = any(re.search(r"\d[\d,.]*\s*[KMB]?\s*(read|view|play|user)",
                               str(m.get("oddsDisp") or ""), re.I)
                     for m in muc if isinstance(m, dict))
        if co_dem and str(st.get("rung_kieu") or "") != "dem":
            e.append("longshot: dữ liệu là ĐẾM nhưng story không khai `rung_kieu` "
                     "-> thang vẫn ghi '1 in N', vô nghĩa với con số")
    # TIÊU ĐỀ PHẢI KHỚP NỘI DUNG — lỗi thật 28/8: tiêu đề "Breakfast cereal" mà các mục là KEM.
    # Nguyên nhân: nhãn tĩnh trong cấu hình kênh không xoay theo trục. Đây là loại sai tệ nhất:
    # không phải xấu, không phải thiếu, mà là NÓI SAI — người xem bấm vào vì tưởng một đằng rồi
    # thấy một nẻo. Bắt bằng cách so danh từ chính của tiêu đề với tên các mục.
    # 28/8 — CHỈ SO KHI GIÁ TRỊ TRỤC LÀ NHÃN NỘI DUNG.
    # Nhiều kênh xoay theo NGÀY hoặc NĂM (`tu_ngay`, `nam`, `lui`, `den_ngay`). So tiêu đề
    # "Where America shakes — Alaska, M7.9" với giá trị trục "2015-01-01" rồi kết luận "NÓI SAI
    # nội dung" là vô nghĩa: một cái là chủ đề, một cái là mốc thời gian, chúng vốn không phải
    # cùng loại chữ. Phép kiểm này sinh ra để bắt ca "tiêu đề ghi Breakfast cereal mà mục là KEM",
    # tức là khi trục mang MỘT NHÃN CHỦ ĐỀ. Trục thời gian thì không có gì để đối chiếu.
    # Trục kiểu DANH SÁCH (`bangs` = ['California','Texas',...]) không có "một chủ đề" để đối
    # chiếu: nó là phạm vi truy vấn, không phải nhan đề. So tiêu đề với chuỗi repr của cả danh
    # sách thì lượt nào cũng đỏ, mà đỏ vô nghĩa còn nguy hơn không kiểm — nó dạy người đọc bỏ qua.
    _gtr = st.get("_truc_gia_tri")
    _gt0 = "" if isinstance(_gtr, (list, tuple, dict)) else str(_gtr or "")
    _la_thoi_gian = bool(re.fullmatch(r"[\d\s./-]+", _gt0.strip())) if _gt0 else False
    if _gt0 and not _la_thoi_gian:
        gt = _gt0.replace("-", " ").lower()
        t0 = str(st.get("title") or "").lower()
        # Lấy chữ đầu tiêu đề (trước dấu hai chấm) — đó là thứ tiêu đề tự nhận là đang nói về.
        # 28/8 — HỎI "GIÁ TRỊ TRỤC CÓ MẶT TRONG TIÊU ĐỀ KHÔNG", đừng cắt tiêu đề ra rồi so.
        # Phép kiểm này sinh ra để bắt đúng một ca: khung ghi "Breakfast cereal: what is really in
        # it" trong khi các mục là KEM. Hai bản trước đều cắt tiêu đề để tìm "phần khung" — cắt
        # trước dấu hai chấm, rồi cắt sau dấu gạch dài — và cả hai đều báo đỏ oan, vì tiêu đề có
        # HAI khuôn ngược nhau ("CHỦ THỂ: số — khung" và "khung — CHỦ THỂ, số", bốc theo băm tên
        # kênh) nên không có một vị trí cố định nào là "phần khung".
        # Điều thật sự cần biết đơn giản hơn nhiều: chủ đề đang nói tới có được nhắc ở đâu đó
        # trong tiêu đề không. Có thì tiêu đề khớp nội dung; không thì nó đang nói về chuyện khác.
        # Bỏ qua giá trị trục có gạch dưới (`chet_yeu`, `dong_nhat`) — đó là mã lọc nội bộ, vốn
        # KHÔNG được phép lên tiêu đề, nên vắng mặt là đúng chứ không phải sai.
        if "_" not in _gt0 and gt and gt.split()[0][:5] not in t0:
            e.append(f"{dang}: tiêu đề {t0[:52]!r} không nhắc gì tới chủ đề {gt!r} "
                     f"-> người xem bấm vào vì tưởng một đằng, thấy một nẻo")
    if dang in ("ranked", "scaled", "longshot"):
        muc = [m for m in (st.get("items") or []) if isinstance(m, dict)]
        gt = {str(m.get("stat") or m.get("disp") or m.get("oddsDisp") or "") for m in muc}
        if len(muc) >= 3 and len(gt) < 3:
            e.append(f"{dang}: {len(muc)} mục mà chỉ {len(gt)} giá trị khác nhau "
                     f"-> bảng không thật sự xếp hạng")
    return e


def cham_props(dang: str, props: dict) -> list:
    """Soi props sẽ truyền xuống composition — chỗ các tầng hay bất đồng nhất."""
    e = []
    if not props.get("source"):
        e.append(f"{dang}: props KHÔNG có `source` -> video ra không ghi nguồn")
    if dang == "longshot":
        # Thang xác suất mà dữ liệu là ĐẾM -> mọi nhãn thang vô nghĩa (lỗi FAME CURVE 28/8)
        kieu = str(props.get("rungKieu") or "odds")
        don = str(props.get("rungDonVi") or "")
        muc = props.get("items") or []
        co_dem = any(re.search(r"\d[\d,.]*\s*[KMB]?\s*(read|view|play|user)", str(m.get("oddsDisp") or ""), re.I)
                     for m in muc if isinstance(m, dict))
        if co_dem and kieu != "dem":
            e.append("longshot: dữ liệu là ĐẾM nhưng thang vẫn ghi kiểu xác suất '1 in N'")
        if kieu == "dem" and not don:
            e.append("longshot: khai thang kiểu đếm mà thiếu đơn vị -> nhãn trống nghĩa")
    if dang == "ranked" and not str(props.get("subtitle") or "").strip():
        e.append("ranked: thiếu phụ đề -> người xem không biết đang xếp theo gì")
    return e


def do_tep(duong: str, doc: bool) -> list:
    """Đo TỆP THẬT. Đây là thứ bắt được lớp 'chạy được ở máy tôi'."""
    e = []
    if not (duong and os.path.exists(duong)):
        return ["KHÔNG ra được tệp video"]
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size:stream=width,height,codec_type",
                        "-of", "json", duong], capture_output=True, text=True, timeout=90)
    try:
        j = json.loads(r.stdout or "{}")
    except Exception:
        return ["ffprobe không đọc được tệp"]
    d = float((j.get("format") or {}).get("duration") or 0)
    st = j.get("streams") or []
    v = next((x for x in st if x.get("codec_type") == "video"), {})
    co_tieng = any(x.get("codec_type") == "audio" for x in st)
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    if d < (45 if doc else 15):
        e.append(f"quá ngắn: {d:.1f}s")
    if not co_tieng:
        e.append("KHÔNG có tiếng — TTS hỏng")
    if doc and (w, h) != (1920, 1080):
        e.append(f"long phải 1920x1080, đang {w}x{h}")
    if not doc and (w, h) != (1080, 1920):
        e.append(f"short phải 1080x1920, đang {w}x{h}")
    return e


def mot_dang(dang: str, render: bool) -> tuple:
    """Nghiệm thu một dạng. Trả (danh sách lỗi, tiêu đề)."""
    import the_he_2 as T
    k = _kenh_mau(dang)
    if not k:
        return [f"{dang}: không có kênh nào dùng dạng này"], ""
    try:
        st = T.DUNG_STORY[dang](k, dict(k.get("tham_so") or {}))
    except Exception as ex:
        return [f"{dang}: dựng story ném {type(ex).__name__}: {str(ex)[:80]}"], ""
    if not st:
        # Nguồn không trả dữ liệu là chuyện BÌNH THƯỜNG (mạng, hạn mức) — không phải lỗi chất
        # lượng. Báo nhưng không đánh trượt: đánh trượt thì một nguồn chập là chặn cả phiên.
        return [], f"({dang}: nguồn không trả dữ liệu — bỏ qua lượt nghiệm thu)"
    tieu = str(st.get("title") or "")
    loi = [f"{dang}: {x}" for x in cham_tieu_de(tieu)] + cham_story(dang, st)
    if not render:
        return loi, tieu
    try:
        ra = T.chay_chung(k, ky=dict(k.get("tham_so") or {}))
    except Exception as ex:
        return loi + [f"{dang}: render ném {type(ex).__name__}: {str(ex)[:90]}"], tieu
    if not ra:
        return loi + [f"{dang}: RENDER KHÔNG RA TỆP"], tieu
    duong = ra[0] if isinstance(ra, (tuple, list)) else ra
    return loi + [f"{dang}: {x}" for x in do_tep(duong, False)], tieu


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Nghiệm thu chất lượng trên SẢN PHẨM")
    ap.add_argument("--render", default="", help="dạng cần render thật (bỏ trống = tự xoay theo giờ)")
    ap.add_argument("--khong-render", action="store_true", help="chỉ soi story/props, không render")
    a = ap.parse_args()
    sys.path.insert(0, GOC)

    # XOAY VÒNG: mỗi phiên render thật MỘT dạng. Render cả 7 thì job `plan` (trần 18') không đủ
    # giờ, mà bỏ hẳn thì mất đúng thứ bắt được lỗi "thiếu tài sản". Xoay theo giờ trong ngày:
    # 7 dạng phủ hết trong ~4 tiếng, đủ nhanh để bắt hồi quy trong ngày.
    quay = a.render or ("" if a.khong_render else DANG[int(time.time() // 3600) % len(DANG)])
    print(f"🧾 NGHIỆM THU — soi {len(DANG)} dạng"
          + (f", RENDER THẬT dạng `{quay}`" if quay else ", không render"))

    loi, tieu = [], {}
    for d in DANG:
        e, t = mot_dang(d, render=(d == quay))
        loi += e
        tieu[d] = t
        print(f"  {'❌' if e else '✅'} {d:10} {t[:72]}")
        for x in e:
            print(f"       · {x}")

    # TRÙNG TIÊU ĐỀ GIỮA CÁC DẠNG — thứ mà soi từng dạng riêng không bao giờ thấy.
    tt = [t for t in tieu.values() if t and not t.startswith("(")]
    if len(tt) != len({x.strip().lower() for x in tt}):
        loi.append("có hai dạng ra CÙNG một tiêu đề")

    print(f"\n{'═' * 70}")
    if loi:
        print(f"🚨 NGHIỆM THU TRƯỢT ({len(loi)} lỗi) — CHẶN PHIÊN, không sinh 18 luồng vào bản hỏng:")
        for x in loi[:12]:
            print(f"   - {x}")
        return 1
    print("✅ NGHIỆM THU ĐẠT — sản phẩm ra đúng chuẩn, cho phép chạy phiên.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
