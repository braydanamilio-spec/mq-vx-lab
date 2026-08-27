#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BỘ ĐỀ TÀI — AI ĐỀ XUẤT, DỮ LIỆU THẬT XÁC MINH (27/8/2026).

VẤN ĐỀ
------
Kho đề tài của 50 kênh là danh sách em GÕ TAY vào `kenh_the_he_2.json` (`kho_<trục>`). Nó hữu
hạn: kênh làm hết kho là hết chuyện, dù nguồn dữ liệu vẫn còn vô số góc chưa khai thác. Và nó
tĩnh: gõ hồi tháng trước thì không biết tháng này người ta đang quan tâm gì.

NGUYÊN TẮC — AI ĐỀ XUẤT, DỮ LIỆU PHÁN
-------------------------------------
Không để AI bịa nội dung. Lợi thế của cả hệ này là MỌI CON SỐ ĐỀU TRA ĐƯỢC — đánh đổi nó lấy
vài đề tài kêu là mất thứ không mua lại được. Nên chia vai dứt khoát:

    AI          -> ĐỀ XUẤT giá trị trục mới (tên hãng xe, món ăn, từ khoá vụ kiện…)
    NGUỒN THẬT  -> PHÁN. Dựng thử story với giá trị đó; dựng được mới nhận, không thì vứt.
    RADAR       -> XẾP HẠNG những cái đã nhận, theo nhu cầu tìm kiếm thật.

Ba cửa nối tiếp. Đề tài AI bịa ra mà nguồn không có số thì chết ngay ở cửa hai, không bao giờ
tới được màn hình.

CHỐNG TRÙNG — BA LỚP
--------------------
  1. đã làm THẬT của chính kênh   (sổ bền — chỉ ghi khi video đã ra lò, xem `_chot_chu_de`)
  2. đang có sẵn trong kho         (khỏi đề xuất lại thứ đã nằm đó)
  3. của các kênh ANH EM cùng cụm  (tránh hai kênh cùng chủ làm trùng đề tài — đây là thứ
                                    người xem nhận ra ngay và là rủi ro "nội dung hàng loạt")

    python y_tuong.py --kenh "CAR RECALL"          # xem thử, không ghi
    python y_tuong.py --kenh "CAR RECALL" --ghi    # ghi kho mở rộng vào JSON
    python y_tuong.py --tat-ca --ghi
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
DS_JSON = os.path.join(GOC, "kenh_the_he_2.json")


# ── TẦNG GỌI AI: CLOUDFLARE TRƯỚC, GEMINI SAU ──────────────────────────────────────────────
def _cf_chu(nhac: str, key: str, so_chu: int = 700) -> str:
    """Sinh chữ bằng Cloudflare Workers AI (Llama 3.1 8B) — cùng hồ neuron với FLUX.

    Dùng CF trước vì hồ Gemini còn phải gánh khâu VIẾT KỊCH BẢN của đường cũ; mỗi lượt tiêu ở
    đây là một lượt viết bị mất. CF thì chỉ dùng cho những việc phụ như thế này."""
    import urllib.request
    import json as _j
    _, acc, tok = str(key).split(":", 2)
    than = _j.dumps({"messages": [
        {"role": "system", "content": "You output ONLY a JSON array of strings. No prose."},
        {"role": "user", "content": nhac}], "max_tokens": so_chu}).encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/@cf/meta/llama-3.1-8b-instruct",
        data=than, headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = _j.loads(r.read().decode())
    return str(((d or {}).get("result") or {}).get("response") or "")


def _gemini_chu(nhac: str, key: str) -> str:
    import content_brain as CB
    m = CB._genai(key)
    if not m:
        return ""
    return str(getattr(m.generate_content(nhac), "text", "") or "")


def hoi_ai(nhac: str, keys: list) -> str:
    """Hỏi AI, xoay key theo đúng luật của hệ: CF cạn hết rồi mới chạm Gemini."""
    cf = [k for k in keys if str(k).startswith("cf:")]
    gm = [k for k in keys if not str(k).startswith("cf:")]
    for i, k in enumerate(cf + gm):
        try:
            ra = _cf_chu(nhac, k) if str(k).startswith("cf:") else _gemini_chu(nhac, k)
            if ra.strip():
                if i:
                    print(f"   🔑 ý tưởng: xoay sang key thứ {i + 1}")
                return ra
        except Exception:
            continue
    return ""


def _boc_json(t: str) -> list:
    """Moi mảng JSON ra khỏi câu trả lời — model hay bọc thêm lời dẫn dù đã dặn đừng."""
    t = str(t or "")
    m = re.search(r"\[[\s\S]*?\]", t)
    if not m:
        return []
    try:
        ra = json.loads(m.group(0))
    except Exception:
        return []
    return [str(x).strip() for x in ra if isinstance(x, (str, int, float)) and str(x).strip()]


# ── ĐÃ LÀM THẬT + KÊNH ANH EM ──────────────────────────────────────────────────────────────
def da_lam_that(owner: str, kenh_ten: str, n: int = 120) -> list:
    """Đề tài ĐÃ THÀNH VIDEO của kênh. Đọc sổ bền — sổ này giờ chỉ ghi khi đẩy Drive xong."""
    try:
        import firestore_bridge as FB
        return list(FB.recent_topics(owner, kenh_ten.replace(" ", "").upper(), n) or [])
    except Exception as e:
        print(f"   ⚠️ không đọc được sổ đã làm ({str(e)[:50]}) — đề xuất có thể trùng bản cũ")
        return []


def kenh_anh_em(kenh: dict, tat_ca: list) -> list:
    """Kênh cùng NICHE — nơi dễ đẻ ra trùng lặp nhất giữa 50 kênh cùng một chủ."""
    nc = str(kenh.get("niche") or "")
    return [k for k in tat_ca if k is not kenh and str(k.get("niche") or "") == nc]


# ── ĐỀ XUẤT ────────────────────────────────────────────────────────────────────────────────
def nhac_de_xuat(kenh: dict, truc: str, kho: list, da_lam: list, tranh: list, n: int) -> str:
    return (
        f"Channel: {kenh.get('ten')} — {kenh.get('goc_nhin') or kenh.get('niche')}\n"
        f"It builds videos from a public dataset. The rotating parameter is `{truc}`.\n"
        f"Existing values already in the pool: {json.dumps(kho[:30], ensure_ascii=False)}\n"
        f"Topics this channel ALREADY published: {json.dumps(da_lam[:25], ensure_ascii=False)}\n"
        f"Topics sibling channels cover (do NOT overlap): {json.dumps(tranh[:20], ensure_ascii=False)}\n\n"
        f"Propose {n} NEW values for `{truc}` that:\n"
        f"  - are real, specific, and likely present in a US public dataset\n"
        f"  - are things people actually search for in {kenh.get('niche')}\n"
        f"  - do not repeat anything listed above\n"
        f"  - match the FORMAT of the existing values exactly (same style, same casing)\n"
        f"Return ONLY a JSON array of {n} strings."
    )


def xac_minh(kenh: dict, truc: str, gt) -> bool:
    """CỬA THẬT: dựng thử story với giá trị này. Dựng được = nguồn có số = nhận.

    Đây là chỗ chặn mọi thứ AI bịa. Model rất sẵn lòng nghĩ ra một hãng xe không tồn tại hay một
    món ăn mà USDA không có mã — dựng thử là biết ngay, khỏi tranh luận."""
    try:
        import the_he_2 as T
        f = {"ranked": T.dung_story_ranked, "scaled": T.dung_story_scaled,
             "mapped": T.dung_story_mapped, "longshot": T.dung_story_longshot,
             "race": T.dung_story_race, "thennow": T.dung_story_thennow,
             "cinematic": T.dung_story_cinematic}.get(kenh.get("dinh_dang"))
        if not f:
            return False
        return bool(f(kenh, {truc: gt}))
    except BaseException:
        return False


def de_xuat(kenh: dict, tat_ca: list, keys: list, owner: str, n: int = 8) -> list:
    import the_he_2 as T
    truc, kho = T._kho_xoay_cua(kenh)
    if not truc:
        print(f"   – {kenh.get('ten')}: không có trục xoay — bỏ qua")
        return []
    dl = da_lam_that(owner, kenh.get("ten", ""))
    ae = []
    for k in kenh_anh_em(kenh, tat_ca):
        ae += da_lam_that(owner, k.get("ten", ""), 12)
    tho = _boc_json(hoi_ai(nhac_de_xuat(kenh, truc, kho, dl, ae, n * 2), keys))
    if not tho:
        print(f"   ⚠️ {kenh.get('ten')}: AI không trả về đề xuất nào")
        return []
    co = {str(x).strip().lower() for x in kho}
    ung = [x for x in tho if x.lower() not in co][:n * 2]
    ok = []
    for x in ung:
        if xac_minh(kenh, truc, x):
            ok.append(x)
            print(f"      ✅ `{x}` — nguồn có dữ liệu")
        else:
            print(f"      ✗ `{x}` — nguồn không có, bỏ")
        if len(ok) >= n:
            break
    return ok


def ghi_kho(kenh_ten: str, truc: str, moi: list) -> int:
    """Nối giá trị đã xác minh vào `kho_<trục>` trong JSON. Không xoá gì, chỉ thêm."""
    ks = json.load(io.open(DS_JSON, encoding="utf-8"))
    for k in ks:
        if k["ten"] != kenh_ten:
            continue
        ts = k.setdefault("tham_so", {})
        kh = f"kho_{truc}"
        cu = ts.get(kh) or []
        if isinstance(cu, str):
            try:
                cu = json.loads(cu.replace("'", '"'))
            except Exception:
                cu = []
        co = {str(x).lower() for x in cu}
        them = [x for x in moi if str(x).lower() not in co]
        ts[kh] = list(cu) + them
        io.open(DS_JSON, "w", encoding="utf-8").write(json.dumps(ks, ensure_ascii=False, indent=1))
        return len(them)
    return 0


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--ghi", action="store_true")
    ap.add_argument("--so", type=int, default=8)
    a = ap.parse_args()
    owner = os.environ.get("OWNER_UID") or "THU"
    ks = json.load(io.open(DS_JSON, encoding="utf-8"))
    chon = ks if a.tat_ca else [k for k in ks if k["ten"].upper() == a.kenh.upper()]
    if not chon:
        print('❌ dùng --kenh "TÊN" hoặc --tat-ca')
        return 2
    try:
        import firestore_bridge as FB
        keys = [r.get("key") for r in (FB.read_keys(owner) or []) if r.get("key")]
    except Exception:
        keys = []
    keys = keys or [x for x in (os.environ.get("GEMINI_API_KEYS", "").split(",")) if len(x) > 20]
    if not keys:
        print("❌ không có key nào để hỏi AI")
        return 2
    print(f"🔑 {sum(1 for k in keys if str(k).startswith('cf:'))} key CF · "
          f"{sum(1 for k in keys if not str(k).startswith('cf:'))} key Gemini")
    tong = 0
    import the_he_2 as T
    for k in chon:
        print(f"\n── {k['ten']} ──")
        moi = de_xuat(k, ks, keys, owner, a.so)
        if moi and a.ghi:
            truc, _ = T._kho_xoay_cua(k)
            n = ghi_kho(k["ten"], truc, moi)
            print(f"   💾 thêm {n} đề tài vào kho_{truc}")
            tong += n
        elif moi:
            print(f"   (xem thử) {len(moi)} đề tài đạt: {moi}")
    print(f"\n{'✅' if tong or not a.ghi else '⚠️'} tổng thêm: {tong} đề tài")
    return 0


if __name__ == "__main__":
    sys.exit(main())
