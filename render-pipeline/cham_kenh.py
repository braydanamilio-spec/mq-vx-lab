#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHẤM CẢ 50 KÊNH TRƯỚC KHI RENDER — chọn kênh nào được vào mẻ (28/8/2026).

VÌ SAO
------
Đo phiên ngày 28/8: 600 video ra lò, 266 đạt / 334 hỏng theo phép đo trùng tiêu đề. Tức là hơn một
nửa công suất máy đi vào thứ phải xoá. Và cách phát hiện là SAU khi render xong — mỗi lượt hỏng đã
tiêu một suất TTS, một suất vẽ ảnh, vài phút CPU và một chỗ trên kho.

Điều đáng nói: gần như mọi lỗi ấy ĐỀU THẤY ĐƯỢC Ở TẦNG STORY, trước khi render một khung hình nào —
tiêu đề lộ mã nội bộ, tiêu đề hai con số chỏi nhau, bảng sáu mục mà chỉ một giá trị, story thiếu
`nguon`, tiêu đề nói một đằng dữ liệu một nẻo. Dựng story chỉ tốn vài lượt gọi dữ liệu công khai,
KHÔNG tốn hạn mức Firestore, KHÔNG tốn khoá AI, KHÔNG tốn phút render.

Nên: chấm trước, rồi mới cho vào mẻ. Kênh đạt đi trước, kênh hỏng nằm lại kèm lý do CỤ THỂ để sửa.

    python cham_kenh.py                 # chấm cả 50, in bảng, ghi chat_luong_kenh.json
    python cham_kenh.py --kenh SKYRIGHTNOW
    python cham_kenh.py --nguong 90     # đổi mức đạt

FAIL-OPEN LÀ BẮT BUỘC
---------------------
`run_render` đọc tệp kết quả này để xếp thứ tự. Tệp thiếu, cũ, hay hỏng thì nó phải chạy y như
trước. Một cổng chất lượng tự nó làm đứng cả phiên thì tệ hơn hẳn thứ nó định ngăn — đã vấp đúng
vậy hôm 28/8 khi một chốt kiểm của tôi chặn một phiên thật chỉ vì repo kia không có mặt trên CI.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)

RA = os.path.join(GOC, "chat_luong_kenh.json")
NGUONG = 90


def _kenhs() -> list:
    ks = json.load(io.open(os.path.join(GOC, "kenh_the_he_2.json"), encoding="utf-8"))
    return ks if isinstance(ks, list) else list(ks.values())


def _gia_tri(st: dict) -> list:
    """Mọi con số hiển thị của story, bất kể dạng nào cất chúng ở khoá gì."""
    ra = []
    for khoa in ("items", "data", "pairs"):
        for m in (st.get(khoa) or []):
            if isinstance(m, dict) and isinstance(m.get("value"), (int, float)):
                ra.append(float(m["value"]))
    for fr in (st.get("frames") or [])[-1:]:
        for m in (fr.get("data") or []):
            if isinstance(m, dict) and isinstance(m.get("value"), (int, float)):
                ra.append(float(m["value"]))
    return ra


def cham_mot(k: dict) -> dict:
    """Chấm một kênh. Trả {ten, diem, loi[], bo_qua, tieu_de, ...}."""
    import nghiem_thu as NT
    import the_he_2 as T
    ten = str(k.get("ten") or "?")
    dang = str(k.get("dinh_dang") or "")
    ra = {"ten": ten, "khoa": ten.replace(" ", "").upper(), "dang": dang,
          "ham": k.get("ham"), "motif": (k.get("brand") or {}).get("motif"),
          "diem": 0, "loi": [], "bo_qua": False, "tieu_de": "", "so_muc": 0}
    t0 = time.time()
    truc0, _kho0 = T._kho_xoay_cua(k)
    try:
        _ts0 = dict(k.get("tham_so") or {})
        st = T.DUNG_STORY[dang](k, _ts0)
        if st:
            # ĐI ĐÚNG ĐƯỜNG MÁY ĐI. `DUNG_STORY` mới là nửa đầu; tiêu đề còn qua `hoan_tieu_de`
            # (gắn giá trị trục + ưu tiên tiêu đề dựng từ dữ liệu) trong `_dung_story_xoay`.
            # Bản đầu của bộ chấm bỏ qua nửa sau và kết luận 23 kênh "tiêu đề cố định" — sai hết.
            st = T.hoan_tieu_de(st, k, truc0, _ts0, [])
    except Exception as ex:
        ra["loi"] = [f"dựng story ném {type(ex).__name__}: {str(ex)[:90]}"]
        return ra
    ra["giay"] = round(time.time() - t0, 1)
    if not st:
        # Nguồn không trả dữ liệu là chuyện mạng/hạn mức, KHÔNG phải lỗi chất lượng của kênh.
        # Đánh trượt ở đây thì một API chập nửa phút là loại oan một kênh khỏi cả ngày.
        ra["bo_qua"] = True
        ra["loi"] = ["nguồn không trả dữ liệu lượt này (không tính là hỏng)"]
        return ra

    tieu = str(st.get("title") or "")
    ra["tieu_de"] = tieu
    diem = 100
    loi = []
    for x in NT.cham_tieu_de(tieu):
        loi.append(f"tiêu đề: {x}")
        diem -= 25
    for x in NT.cham_story(dang, st):
        loi.append(x)
        diem -= 20

    # ── TIÊU ĐỀ CÓ ĐỔI GIỮA HAI LƯỢT KHÔNG ─────────────────────────────────────────────────
    # Phép kiểm này ứng đúng với con số đã đo: 334/600 video ngày 28/8 trùng tiêu đề.
    # Không phải "tiêu đề xấu" — "Where America shakes" đọc rất được. Vấn đề là nó CỐ ĐỊNH: kênh
    # đó chạy bao nhiêu lượt cũng ra đúng chuỗi ấy, nên video thứ hai trở đi trùng chắc chắn, kể
    # cả khi dữ liệu bên trong đã khác hẳn. Với người xem, trang kênh thành một cột chữ lặp; với
    # YouTube, đó đúng khuôn "nội dung lặp lại, sản xuất hàng loạt" bị hạn chế phân phối.
    #
    # KHÔNG ĐOÁN QUA HÌNH DẠNG CHUỖI. Bản đầu của tôi soi xem tiêu đề có mang số hay tên mục đầu
    # bảng không. Nó đánh trượt oan cả 6 kênh cinematic — tiêu đề của chúng CHÍNH LÀ dữ liệu
    # ("Disappearance of Marvin Clark"), mỗi lượt một vụ án khác — và trượt cả FAME CURVE, nơi chủ
    # thể là bài Wikipedia đứng đầu, không nằm trong `items`. Cùng họ với mọi lỗi tuần này: suy ra
    # kết luận từ hình dạng thay vì đo thứ đi ra.
    # Nên dựng story LẦN THỨ HAI với một giá trị trục KHÁC rồi so hai tiêu đề. Đó đúng là điều cần
    # biết, và nó đắt hơn đúng một lượt gọi dữ liệu công khai.
    truc, kho = truc0, _kho0
    if truc and len(kho) > 1:
        # Thử BA giá trị trục (đầu / giữa / cuối kho) và đòi ra ít nhất HAI tiêu đề khác nhau.
        #
        # Bản đầu chỉ thử hai giá trị rồi đánh trượt nếu trùng. Nhưng đường chạy thật không dừng
        # ở một bước: `_dung_story_xoay` gặp tiêu đề đã dùng thì XOAY TIẾP sang giá trị sau, và
        # chỉ bỏ lượt khi cả kho không còn tiêu đề mới. Nên "hai giá trị liền nhau cho cùng một
        # tiêu đề" chưa phải hỏng — hỏng là khi CẢ KHO chỉ đẻ ra đúng một tiêu đề.
        # Ba điểm rải đều là mẫu đủ để phân biệt hai chuyện đó, mà vẫn chỉ tốn hai lượt gọi thêm.
        goc = (k.get("tham_so") or {}).get(truc)
        thu = [kho[0], kho[len(kho) // 2], kho[-1]]
        thay = {tieu.strip().lower()}
        for v in thu:
            if str(v) == str(goc):
                continue
            ts2 = {**(k.get("tham_so") or {}), truc: v}
            ts2.pop("nhan", None)      # cùng luật với `_dung_story_xoay`: xoay trục thì bỏ nhãn tĩnh
            try:
                st2 = T.DUNG_STORY[dang](k, ts2)
                if st2:
                    thay.add(str(T.hoan_tieu_de(st2, k, truc, ts2, [])
                                 .get("title") or "").strip().lower())
            except Exception:
                pass
        ra["tieu_de_thu"] = sorted(x for x in thay if x)
        if len(ra["tieu_de_thu"]) < 2:
            loi.append(f"CẢ KHO trục `{truc}` ({len(kho)} giá trị) chỉ đẻ ra đúng một tiêu đề "
                       f"— kênh này ra video thứ 2 là trùng, không có đường xoay nào cứu được")
            diem -= 30
    elif not truc:
        loi.append("kênh KHÔNG có trục xoay — mọi lượt dựng lại cùng một câu hỏi, "
                   "chỉ khác nhau nếu chính nguồn đổi số")
        diem -= 10

    muc = [m for m in (st.get("items") or st.get("data") or []) if isinstance(m, dict)]
    ra["so_muc"] = len(muc)
    if dang in ("ranked", "scaled", "longshot") and len(muc) < 4:
        loi.append(f"chỉ {len(muc)} mục — bảng quá thưa để thành một video xếp hạng")
        diem -= 15

    # DẢI GIÁ TRỊ. Sáu cột cao bằng nhau thì người xem không rút ra được gì — đúng thứ đã thấy ở
    # CALORIE SHOCK (599/534/529/526/525/517). Không phải sai số, mà là không có chuyện để kể.
    gt = _gia_tri(st)
    # Dạng `race` KHÔNG bị phạt dải hẹp: kịch tính của biểu đồ đua nằm ở THỨ HẠNG ĐỔI CHỖ qua
    # từng năm, không nằm ở cột nào dài hơn cột nào. NBA 26-33 điểm hay MLB 90-97 trận thắng vốn
    # là những dải hẹp thật, và xem một cuộc đua bám đuôi nhau còn hồi hộp hơn xem một cuộc đua
    # đã phân định. Phạt chúng là đòi dữ liệu phải khác đi cho vừa một phép đo.
    if len(gt) >= 4 and dang in ("ranked", "scaled"):
        hi, lo = max(gt), min(gt)
        if hi > 0 and (hi - lo) / hi < 0.25:
            loi.append(f"dải giá trị chỉ {100 * (hi - lo) / hi:.0f}% (từ {lo:g} tới {hi:g}) "
                       f"— các cột cao gần bằng nhau, không có gì để so")
            diem -= 15

    # LỜI DẪN. Không có lời thì TTS không có gì để đọc; ít quá thì video ngắn ngủn.
    dan = st.get("narration") or st.get("dan") or st.get("lines") or []
    if isinstance(dan, list) and 0 < len(dan) < 4:
        loi.append(f"chỉ {len(dan)} câu dẫn — video sẽ hụt hơi")
        diem -= 10

    ra["diem"] = max(0, diem)
    ra["loi"] = loi
    return ra


def trung_motip(kq: list) -> list:
    """Cảnh báo TRÙNG MOTIP: hai kênh cùng dạng + cùng biến thể bố cục, hoặc cùng dạng + cùng motif.

    `bien_cua` đã phát biến thể bố cục khác nhau trong mỗi nhóm `dinh_dang` (27 tổ hợp cho nhóm
    lớn nhất là 18 kênh), nên trùng bố cục lẽ ra không xảy ra — kiểm ở đây là để biết NGAY nếu
    ai đó thêm kênh mới mà quên, chứ không phải để phạt kênh."""
    import the_he_2 as T
    canh = []
    theo_bien, theo_motif = {}, {}
    for r in kq:
        k = next((x for x in _kenhs() if str(x.get("ten")) == r["ten"]), None)
        if not k:
            continue
        b = (r["dang"], T.bien_cua(k))
        theo_bien.setdefault(b, []).append(r["ten"])
        m = (r["dang"], r.get("motif"))
        theo_motif.setdefault(m, []).append(r["ten"])
    for b, ts in theo_bien.items():
        if len(ts) > 1:
            canh.append(f"TRÙNG BỐ CỤC {b[0]}#{b[1]}: {', '.join(ts)}")
    for m, ts in theo_motif.items():
        if len(ts) > 1 and m[1]:
            canh.append(f"trùng motif '{m[1]}' trong dạng {m[0]}: {', '.join(ts)}")
    return canh


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--nguong", type=int, default=NGUONG)
    ap.add_argument("--luong", type=int, default=8)
    a = ap.parse_args()

    ks = _kenhs()
    if a.kenh:
        ks = [k for k in ks if str(k.get("ten", "")).replace(" ", "").upper()
              == a.kenh.replace(" ", "").upper()]
        if not ks:
            print(f"❌ không thấy kênh {a.kenh}")
            return 2

    t0 = time.time()
    kq = []
    with ThreadPoolExecutor(max_workers=a.luong) as ex:
        fs = {ex.submit(cham_mot, k): k for k in ks}
        for i, f in enumerate(as_completed(fs), 1):
            try:
                kq.append(f.result())
            except Exception as e:
                kq.append({"ten": str(fs[f].get("ten")), "diem": 0, "bo_qua": False,
                           "loi": [f"chấm ném {type(e).__name__}: {str(e)[:70]}"]})
            if i % 10 == 0:
                print(f"   … {i}/{len(ks)}", flush=True)

    kq.sort(key=lambda r: (-r["diem"], r["ten"]))
    dat = [r for r in kq if not r["bo_qua"] and r["diem"] >= a.nguong]
    hong = [r for r in kq if not r["bo_qua"] and r["diem"] < a.nguong]
    bo = [r for r in kq if r["bo_qua"]]

    print(f"\n{'═' * 92}")
    print(f"  CHẤM {len(kq)} KÊNH · ngưỡng {a.nguong}/100 · {time.time() - t0:.0f}s")
    print("═" * 92)
    for r in kq:
        cd = "⏭" if r["bo_qua"] else ("✅" if r["diem"] >= a.nguong else "❌")
        print(f"  {cd} {r['diem']:>3}  {r['ten'][:22]:22} {str(r.get('dang'))[:9]:9} "
              f"{r.get('tieu_de', '')[:44]}")
        for x in r["loi"][:3]:
            print(f"         └ {x[:96]}")

    canh = trung_motip([r for r in kq if r.get("dang")])
    if canh:
        print("\n  ⚠️ MOTIP:")
        for c in canh:
            print(f"     {c}")

    print(f"\n  ✅ đạt {len(dat)}  ·  ❌ hỏng {len(hong)}  ·  ⏭ nguồn chập {len(bo)}")
    if dat:
        print("  → vào mẻ trước: " + ", ".join(r["khoa"] for r in dat[:18]))

    json.dump({"luc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "nguong": a.nguong, "canh_bao_motip": canh,
               "kenh": {r["khoa"]: {"diem": r["diem"], "bo_qua": r["bo_qua"],
                                    "dang": r.get("dang"), "loi": r["loi"][:4],
                                    "tieu_de": r.get("tieu_de", "")} for r in kq if r.get("khoa")}},
              io.open(RA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  📝 {RA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
