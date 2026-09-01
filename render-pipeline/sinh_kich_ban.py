#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINH KỊCH BẢN COMIC — nguồn cho hàng nghìn tập (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

Anh: *"nâng cấp sao cho sau mỗi channel có làm hàng nghìn videos đảm bảo được tính đa dạng
sáng tạo, ko nhàm chán, lặp lại hay cùng 1 motip — sáng tạo linh động trong khuôn khổ."*

Kho viết tay có 40 mẩu, tức 4 tập cho mỗi kênh. Tập thứ năm đã phải quay lại mẩu thứ nhất, và
từ đó trở đi mọi tập đều là bản lặp. Không có cách nào viết tay tới hàng nghìn.

Tệp này sinh kịch bản bằng CHÍNH bộ khoá AI đang có trên hệ (Gemini, xoay khoá như mọi chỗ
khác) — không dùng Claude Code, nên chạy được trong GitHub Actions y như ở máy.

── BA TẦNG CHỐNG LẶP ─────────────────────────────────────────────────────────────────────
Sinh bằng mô hình KHÔNG tự nhiên cho ra sự đa dạng: hỏi cùng một câu thì nó trả về cùng một
vùng ý tưởng, và sau vài chục lần thì mọi mẩu đều là một biến thể của nhau. Đa dạng phải được
ép từ bên ngoài, ở ba tầng:

  1. KHUNG TRUYỆN xoay vòng — sáu kiểu dựng chuyện khác nhau (hiểu lầm · leo thang · đảo vai ·
     luật ngớ ngẩn · thú nhận · đếm ngược). Kiểu khác nhau thì trò đùa nằm ở chỗ khác nhau,
     không chỉ chữ khác nhau.
  2. CẤM TÁI DÙNG — mỗi lần hỏi đều kèm danh sách tình huống kênh ĐÃ dùng, và cấm chạm lại.
  3. CỔNG KHUÔN CÂU — mẩu sinh ra bị chuẩn hoá (số, tên riêng, ngày tháng thành ký hiệu) rồi
     đối chiếu với khuôn của cả kho. Trùng khuôn quá ngưỡng thì LOẠI, không lưu.

Tầng 3 là tầng duy nhất đo được, và nó cũng là tầng mà chính sách YouTube nói tới khi dùng chữ
"templated storylines". Hai tầng trên làm cho tầng ba ít phải loại.
"""
import os
import io
import re
import sys
import json
import time
import random
import hashlib
import argparse

GOC = os.path.dirname(os.path.abspath(__file__))
KHO_TEP = os.path.join(GOC, "kho_comic.json")

# ══ SÁU KHUNG TRUYỆN ═══════════════════════════════════════════════════════════════════
# Sáu cách dựng một mẩu hài hai người, lấy từ chính cách sitcom Mỹ dựng một phân đoạn ngắn.
# Chúng khác nhau ở CHỖ ĐẶT TRÒ ĐÙA, không ở chủ đề — nên cùng một kênh, cùng một nơi chốn,
# sáu khung vẫn cho ra sáu mẩu không ai bảo là giống nhau.
KHUNG = {
    "hieu_lam": (
        "MISUNDERSTANDING: B answers a completely different question than the one A asked, "
        "and never realises it. A keeps trying to steer back. The last line proves B was "
        "answering something else the whole time."),
    "leo_thang": (
        "ESCALATION: A reports a small problem. Each of B's replies makes the situation "
        "slightly worse while sounding helpful. By the last line the problem is enormous and "
        "B is proud of the outcome."),
    "dao_vai": (
        # 31/8 — bản đầu của khung này cho ra hai mẩu mà hai người nói lộn xộn: mô hình hiểu
        # "swap" là ĐỔI DANH TÍNH, nên giữa chừng người gọi hỗ trợ bỗng nói bằng giọng nhân
        # viên. Cái đảo phải nằm ở LẬP LUẬN, còn ai là ai thì giữ nguyên suốt.
        "ARGUMENT REVERSAL: A complains about a rule; B defends it. Both keep their own jobs "
        "and identities the whole time — never swap who is who. What swaps is the ARGUMENT: by "
        "the end A is using B's original reasoning to argue for the rule, and B has been talked "
        "into A's original objection. Neither notices they traded sides."),
    "luat_ngo": (
        "ABSURD RULE: B enforces a rule that is internally consistent but insane. A tries to "
        "find the edge of the rule. Every attempt reveals the rule is even wider than feared."),
    "thu_nhan": (
        "CONFESSION: A is hiding something small and keeps almost admitting it. B misreads "
        "every hint as something worse. The last line is A finally confessing the tiny thing "
        "after B has already forgiven the enormous thing."),
    "dem_nguoc": (
        "COUNTDOWN: something is about to happen in a few seconds and A needs one answer from "
        "B before it does. B insists on giving context first. The last line lands after it is "
        "too late, and the answer turns out to be trivial."),
}

# Mỗi tập cũng đổi cả ĐỘ DÀI. Sáu lượt là nhịp chuẩn, nhưng bốn lượt cho ra một cú đấm nhanh và
# tám lượt cho phép leo thang hai nấc. Ba độ dài × sáu khung = mười tám dạng dựng.
DO_DAI = [4, 6, 6, 6, 8]


def _chuan_hoa(cau: str) -> str:
    """Bỏ phần thay-được của một câu, giữ lại KHUÔN của nó.

    Đây là phép đo trung tâm của cổng chống lặp. Hai câu "They raised my rent four hundred
    dollars" và "They raised my fee two hundred dollars" khác nhau về chữ nhưng CÙNG một khuôn —
    và người xem tập thứ hai sẽ thấy đúng cái cảm giác "xem rồi". Chuẩn hoá đưa cả hai về một
    chuỗi, nên bộ đếm nhìn ra chúng là một.
    """
    t = " " + cau.lower().strip() + " "
    t = re.sub(r"[\d]+([.,]\d+)?", " «số» ", t)
    t = re.sub(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|forty|fifty|"
               r"hundred|thousand|million)\b", " «số» ", t)
    t = re.sub(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|"
               r"march|april|may|june|july|august|september|october|november|december)\b",
               " «ngày» ", t)
    # danh từ riêng còn sót (viết hoa giữa câu ở bản gốc) đã mất khi lower -> bù bằng cách bỏ
    # mọi danh từ đứng sau mạo từ, thứ thay được mà không đổi khuôn
    t = re.sub(r"\b(the|a|an|my|your|his|her|their|our)\s+\w+", " «tên» ", t)
    t = re.sub(r"[^a-z«»\s]", " ", t)
    return " ".join(t.split())


def _nap_kho() -> dict:
    if os.path.exists(KHO_TEP):
        try:
            return json.load(io.open(KHO_TEP, encoding="utf-8"))
        except Exception as e:
            # KHÔNG nuốt lỗi: kho hỏng mà lặng lẽ trả rỗng thì lần ghi sau đè mất toàn bộ mẩu cũ.
            print(f"❌ kho hỏng, DỪNG để không ghi đè: {e}")
            raise SystemExit(3)
    return {"mau": {}, "khuon": {}, "tinh_huong": {}}


def _luu_kho(kho: dict) -> None:
    tam = KHO_TEP + ".tam"
    io.open(tam, "w", encoding="utf-8").write(json.dumps(kho, ensure_ascii=False, indent=1))
    os.replace(tam, KHO_TEP)          # ghi nguyên tử: đứt giữa chừng không mất kho cũ


def _hoi_ai(hoi: str, keys) -> str:
    """Hỏi mô hình, xoay khoá theo đúng lối của cả hệ. Trả chuỗi rỗng nếu mọi khoá đều hỏng."""
    import content_brain as CB
    from kich_hai import xoay_key
    for kk in xoay_key(keys):
        for ten_mo_hinh in ("gemini-2.5-flash", "gemini-2.5-flash-lite"):
            try:
                g = CB._genai(kk if isinstance(kk, str) else kk.get("key"))
                m = g.GenerativeModel(ten_mo_hinh)
                t = str(getattr(m.generate_content(hoi), "text", "") or "").strip()
                if t:
                    return t
            except Exception:
                continue
    return ""


def _rule_model(k: dict, khung: str, n_luot: int, cam: list) -> str:
    """Bản mô tả công việc gửi cho mô hình. Đây là 'rule model' anh dặn phải có."""
    from kich_hai import NHAN_VAT
    nv = NHAN_VAT.get(k["de"])
    ai = (f"A is {nv[0][0]}, {nv[0][2]}. B is {nv[1][0]}, {nv[1][2]}.\n" if nv else "")
    # ── VÍ DỤ MẪU LẤY TỪ KHO VIẾT TAY ────────────────────────────────────────────────
    # Mẻ đầu sinh ra một mẩu "đảo vai" mà hai người nói lộn xộn, và một câu chốt không lật được
    # gì. Nguyên nhân không nằm ở luật — luật đã viết đủ — mà ở chỗ luật MÔ TẢ giọng thay vì
    # CHO XEM giọng. Bốn mươi mẩu viết tay là thứ đắt nhất đang có; đưa hai mẩu của đúng kênh
    # ấy vào làm mẫu thì mô hình bắt được nhịp ngay, thay vì phải suy ra từ tính từ.
    from kich_hai import KHO as _KHO_TAY
    _mau = _KHO_TAY.get(k["de"], [])[:2]
    if not _mau:
        # KÊNH MỚI KHÔNG CÓ MẨU VIẾT TAY -> `vidu` rỗng -> lời nhắc chỉ MÔ TẢ giọng bằng tính
        # từ, và mô hình rơi về bản năng sitcom chung: "tôi có điều muốn thú nhận" → đoán sai →
        # lộ chuyện vặt → xì hơi. Đó đúng thứ anh xem xong bảo "chưa thấy funny".
        # Chú thích ngay bên trên đã ghi bài học ấy: *luật MÔ TẢ giọng thay vì CHO XEM giọng*.
        # Kênh mới thì mượn mẫu của kênh CŨ — giọng chuyển được, chuyện thì cấm chép.
        for _d in ("rent", "gym", "tech", "airport"):
            _mau = _KHO_TAY.get(_d, [])[:2]
            if _mau:
                break
    vidu = ""
    if _mau:
        vidu = "\n\nExamples of the exact voice and rhythm wanted on this channel:\n"
        for j, mm in enumerate(_mau):
            vidu += f"\nExample {j+1}:\n" + "\n".join(
                f"{'AB'[c[1]]}: {c[0]}" for c in mm["loi"]) + "\n"
        vidu += ("\nMatch that rhythm and that dryness. Do NOT reuse their situations, and do "
                 "NOT reuse their industry — rewrite the same dryness inside THIS channel's "
                 "world.\n"
                 "Notice what those examples do NOT do: nobody confesses, nobody guesses wrong, "
                 "nobody says 'well, at least'. They open on ONE absurd concrete fact, and the "
                 "other character defends it with a straight face until it gets worse.\n")

    tranh = ""
    if cam:
        tranh = ("\nSituations already used on this channel — do NOT reuse any of them, not even "
                 "a variation:\n" + "\n".join(f"- {x}" for x in cam[-40:]) + "\n")
    # ── NƠI CHỐN PHẢI DO KỊCH BẢN CHỌN, TRONG DANH SÁCH CÓ SẴN ────────────────────────
    # Anh: *"bối cảnh đã đa dạng và liên quan tới nội dung videos được nói tới chưa?"*
    # Đa dạng thì có, nhưng nơi chốn đang chọn theo SỐ TẬP — tức hình và lời chỉ tình cờ khớp
    # nhau. Nếu mô hình viết một chuyện xảy ra ở nhà khách mà engine vẫn vẽ bàn hỗ trợ văn
    # phòng thì lại đúng cái lỗi "giỏ giặt chắn ngang bụng" của bản cũ, chỉ khác nguồn.
    #
    # Cho mô hình chọn nơi TRONG DANH SÁCH engine vẽ được, và bắt nó trả về nhãn đã chọn. Nó
    # không mô tả nơi chốn tự do (mô tả tự do thì engine không vẽ nổi), nó chỉ CHỌN — nên hình
    # và lời khớp nhau từ gốc, không phải khớp nhờ may.
    import json as _js, os as _os
    _dsn = {}
    try:
        _dsn = _js.load(io.open(_os.path.join(GOC, "noi_chon.json"), encoding="utf-8"))
    except Exception:
        pass
    _noi = _dsn.get(k["de"], [])
    _kn = ""
    if _noi:
        _kn = ("\nThe scene must take place in ONE of these locations (pick the one that fits "
               "your story best, and use its exact label):\n"
               + "\n".join(f"- {x}" for x in _noi) + "\n")

    return f"""You write short two-person comedy scenes for an American animated series.{vidu}{_kn}

CHANNEL: {k['ten']} — every scene happens in the world of {k['ten'].lower()}.
{ai}
STORY FRAME for this episode — follow it exactly:
{KHUNG[khung]}
{tranh}
Write exactly {n_luot} lines of dialogue, alternating A and B, starting with A.

Craft rules — these are what separate a real sitcom beat from a joke listicle:
- Every line under 12 words. Spoken English, contractions allowed, no stage directions.
- The humour comes from the SITUATION and from characters being consistent, never from puns.
- Nobody is stupid. Both characters are smart people with incompatible premises.
- The last line must reframe everything before it. If you can delete the last line and the
  scene still makes sense, it is not a punchline.
- No brand names, no real people, no politics, no profanity, no violence.
- American idiom and American specifics (dollars, DMV, HOA, drive-thru, insurance).

Also give the scene a two-to-five word situation label, so it is never repeated later.

Also write a HOOK CARD: 4 to 7 words, shouted in capitals, shown on screen for the first two
seconds while the first line is spoken. Rules for it:
- It states the SITUATION, never the punchline. If it gives away the joke, nobody watches on.
- It must create one specific question in the viewer's head. "HE WAITED FORTY MINUTES. FOR THIS."
  works because you want to know what "this" is. "A FUNNY PHONE CALL" works on nobody.
- No question marks, no emoji, no channel name.

Before the dialogue, state in one sentence what the final line reframes. If you cannot state
it, the scene is not finished — rewrite it until you can.

Use only plain ASCII: straight quotes, normal hyphens, no typographic dashes.

Return STRICT JSON, nothing else:
{{"tinh_huong": "short label",
  "noi": "exact label of the chosen location, copied from the list",
  "hook": "4-7 WORD HOOK CARD IN CAPITALS",
  "cu_lat": "one sentence: what the last line reframes",
  "loi": [["line text", 0, "emotion"], ["line text", 1, "emotion"], ...]}}
where the second item is 0 for A and 1 for B, and emotion is exactly one of:
trung_tinh, vui, buon, so, tuc, bat_ngo, nghi_ngo, tu_tin."""


def _doc_json(t: str):
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def cham_chot(loi: list, keys, nguong: int = 6) -> tuple:
    """Chấm cú chốt bằng một lượt gọi RIÊNG, đóng vai người phản biện. Trả (đạt, điểm, lý do).

    ── VÌ SAO PHẢI CÓ LƯỢT THỨ HAI ───────────────────────────────────────────────────────
    Cổng hiện có chỉ bắt mô hình TỰ KHAI "cú chốt này lật cái gì" — và mô hình nào cũng khai
    được, kể cả khi câu chốt chẳng lật gì. Nó đang chấm bài của chính nó, ngay sau khi viết,
    trong cùng một mạch suy nghĩ đã sinh ra bài ấy.
    
    Lượt thứ hai KHÔNG thấy quá trình viết, chỉ thấy kết quả, và được giao đúng một việc: tìm
    lý do để loại. Đây là chỗ khác biệt giữa "tự chấm" và "bị chấm" — cùng một mô hình, nhưng
    một bên đang bảo vệ thứ vừa viết, một bên không có gì để bảo vệ.
    """
    ds = "\n".join(f"{'AB'[c[1]]}: {c[0]}" for c in loi)
    hoi = (
        "You are a tough comedy editor. Judge ONLY the last line of this scene.\n\n"
        + ds + "\n\n"
        "A good last line REFRAMES everything before it — after hearing it, the earlier lines "
        "mean something different. A weak last line merely continues the conversation, or is "
        "just one more complaint, or restates a joke already made.\n\n"
        "Test: if you delete the last line, does the scene lose its point? If it survives fine "
        "without it, the line is weak.\n\n"
        "Be strict. Most lines are weak. Score 7+ only if you can name exactly what got "
        "reframed.\n"
        'Return STRICT JSON: {"diem": 1-10, "vi_sao": "one short sentence"}'
    )
    t = _hoi_ai(hoi, keys)
    d = _doc_json(t) or {}
    try:
        diem = int(d.get("diem", 0))
    except (TypeError, ValueError):
        diem = 0
    return diem >= nguong, diem, str(d.get("vi_sao", ""))[:80]


def sinh_mot(k: dict, kho: dict, keys, khung: str, n_luot: int, nguong: float = 0.34):
    """Sinh MỘT mẩu cho kênh. Trả mẩu, hoặc None nếu bị cổng khuôn loại."""
    de = k["de"]
    cam = kho["tinh_huong"].get(de, [])
    t = _hoi_ai(_rule_model(k, khung, n_luot, cam), keys)
    if not t:
        return None
    d = _doc_json(t)
    if not d or not isinstance(d.get("loi"), list) or len(d["loi"]) < 4:
        return None

    # Ký tự sắp chữ giết bộ đọc: gạch nối không ngắt và nháy cong đi qua edge-tts thành âm lạ
    # hoặc thành khoảng lặng. Mẻ đầu có cả hai. Làm sạch tại đây, không để lọt vào kho.
    SACH = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
            "\u2011": "-", "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}
    loi = []
    for x in d["loi"]:
        if not (isinstance(x, list) and len(x) >= 3):
            return None
        chu = str(x[0])
        for a_, b_ in SACH.items():
            chu = chu.replace(a_, b_)
        chu = " ".join(chu.split()).strip()
        if not (4 <= len(chu) <= 96) or not chu.isascii():
            return None
        loi.append([chu, 1 if int(x[1]) else 0, str(x[2])])

    # ── CỔNG CẤU TRÚC ────────────────────────────────────────────────────────────────
    # Ba thứ đo được, và cả ba đều hỏng ở mẻ đầu nếu không chặn:
    #   · hai lượt liền cùng một người  -> mất nhịp đối đáp, đọc ra là độc thoại cắt khúc
    #   · câu chốt cụt                  -> không đủ chữ để lật được thứ gì
    #   · mô hình không nêu được cú lật -> chính nó cũng không biết trò đùa nằm ở đâu
    for j in range(1, len(loi)):
        if loi[j][1] == loi[j - 1][1]:
            return None
    if len(loi[-1][0].split()) < 5:
        return None
    if len(str(d.get("cu_lat", "")).split()) < 5:
        return None
    # Thẻ hook: 3–8 từ, và KHÔNG được trùng câu chốt. Hook lộ cú chốt là hook tự huỷ — người
    # xem biết kết quả rồi thì không có lý do gì xem tiếp.
    _hk = " ".join(str(d.get("hook", "")).split())
    if not (3 <= len(_hk.split()) <= 8):
        return None
    _chot_tu = set(loi[-1][0].lower().replace(".", "").split())
    _hook_tu = set(_hk.lower().replace(".", "").split())
    if len(_chot_tu & _hook_tu) >= max(3, len(_hook_tu) // 2):
        return None
    HOP_LE = {"trung_tinh", "vui", "buon", "so", "tuc", "bat_ngo", "nghi_ngo", "tu_tin"}
    for c in loi:
        if c[2] not in HOP_LE:
            c[2] = "trung_tinh"

    # ── CỔNG KHUÔN CÂU ────────────────────────────────────────────────────────────────
    # Đếm bao nhiêu câu của mẩu mới trùng khuôn với những mẩu ĐÃ có trong kho. Quá ngưỡng thì
    # loại — thà tốn một lượt gọi còn hơn thả vào kho một mẩu mà người xem thấy "quen quen".
    khuon_kho = kho["khuon"]
    trung = 0
    khuon_moi = []
    for c in loi:
        kh = _chuan_hoa(c[0])
        khuon_moi.append(kh)
        if kh in khuon_kho:
            trung += 1
    if trung / max(1, len(loi)) > nguong:
        return {"_loai": True, "ty_le": trung / max(1, len(loi))}

    # ── CỔNG CÂU MỞ — 1/9/2026 ────────────────────────────────────────────────────────
    # Cổng khuôn ở trên chuẩn hoá CẢ CÂU rồi so, nên "Well, at least you're not stealing
    # licenses" và "Well, at least the calculator's fine" là hai khuôn khác nhau — cả hai đều
    # lọt. Kết quả trên 10 kênh mới: 6 câu mở bằng "I forgive you / I absolve you", 4 câu chốt
    # mở bằng "Well, at least…". Người xem không đọc khuôn ngữ pháp; họ nghe BA TỪ ĐẦU, và ba
    # từ đầu giống nhau thì mọi tập nghe như một.
    # Nên đếm riêng CỤM MỞ ba từ. Ngưỡng chặt hơn cổng khuôn (0.25 so với 0.34) vì cụm mở nằm
    # ở vị trí mắt và tai bắt trước nhất.
    mo_kho = kho.setdefault("mo_dau", {})
    mo_moi = [" ".join(_chuan_hoa(c[0]).split()[:3]) for c in loi]
    trung_mo = sum(1 for m in mo_moi if m and mo_kho.get(m, 0) >= 2)
    if trung_mo / max(1, len(loi)) > 0.25:
        return {"_loai": True, "ty_le": trung_mo / max(1, len(loi)), "_mo": True}

    return {
        "loi": loi, "khung": khung, "noi": str(d.get("noi", ""))[:70],
        "hook": " ".join(str(d.get("hook", "")).split())[:60].upper(),
        "tinh_huong": str(d.get("tinh_huong", ""))[:70],
        "khuon": khuon_moi, "mo_dau": mo_moi,
        "ma": hashlib.md5(("|".join(c[0] for c in loi)).encode()).hexdigest()[:12],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="", help="lọc kênh, cách nhau bằng dấu phẩy")
    ap.add_argument("--so", type=int, default=4, help="số mẩu MỚI cần sinh cho mỗi kênh")
    ap.add_argument("--cham", action="store_true",
                    help="bật cổng chấm cú chốt bằng một lượt gọi riêng (chậm hơn, chất hơn)")
    ap.add_argument("--thu", type=int, default=3, help="số lần thử lại khi bị cổng loại")
    a = ap.parse_args()

    sys.path.insert(0, GOC)
    from kich_hai import KENH
    import the_he_2 as T2
    keys = T2.keys_cuc_bo() or None
    if not keys:
        print("❌ không có khoá AI nào — không sinh được")
        return 2

    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH if x["ten"].replace(" ", "").upper() in vt]

    kho = _nap_kho()
    tong_moi = tong_loai = tong_yeu = 0
    for k in chon:
        de = k["de"]
        kho["mau"].setdefault(de, [])
        kho["tinh_huong"].setdefault(de, [])
        print(f"\n▶ {k['ten']}  (kho đang có {len(kho['mau'][de])} mẩu)", flush=True)
        for i in range(a.so):
            # Khung truyện và độ dài xoay vòng theo TỔNG số mẩu đã có, nên tập thứ 1000 vẫn
            # không rơi vào cùng một khung với tập thứ 994.
            # 1/9 — `len(kho) + i` ĐẾM HAI LẦN: mỗi mẩu thêm vào thì `len` tăng 1 VÀ `i`
            # cũng tăng 1, nên `vt` nhảy 2 đơn vị và bỏ qua một khung mỗi lượt. Hậu quả: kênh
            # mới chỉ nhận khung chỉ số CHẴN — đúng ba khung yếu (hiểu lầm · đảo vai · thú
            # nhận), không bao giờ chạm ba khung mạnh (leo thang · luật ngớ ngẩn · đếm ngược)
            # vốn chiếm 87/99 mẩu của 10 kênh anh đã duyệt.
            # Đó là lý do 10 video demo đầu tiên "không thấy funny": chúng không phải kịch bản
            # dở ngẫu nhiên, chúng bị khoá vào đúng ba khung yếu nhất.
            # `len` tự tăng khi mẩu được lưu, nên nó ĐỦ làm con đếm; mẩu bị loại thì thử lại
            # cùng khung — đúng ý muốn.
            vt = len(kho["mau"][de])
            khung = list(KHUNG)[vt % len(KHUNG)]
            n_luot = DO_DAI[vt % len(DO_DAI)]
            got = None
            for _ in range(a.thu):
                r = sinh_mot(k, kho, keys, khung, n_luot)
                if r and not r.get("_loai"):
                    if a.cham:
                        dat, diem, vs = cham_chot(r["loi"], keys)
                        if not dat:
                            tong_yeu += 1
                            print(f"   ↺ cú chốt yếu ({diem}/10): {vs}", flush=True)
                            time.sleep(0.3)
                            continue
                        r["diem_chot"] = diem
                    got = r
                    break
                if r and r.get("_loai"):
                    tong_loai += 1
                    print(f"   ↺ loại: trùng khuôn {r['ty_le']*100:.0f}%", flush=True)
                time.sleep(0.4)
            if not got:
                print("   ⚠️ bỏ qua một mẩu (mọi lần thử đều hỏng hoặc bị loại)")
                continue
            kho["mau"][de].append({"loi": got["loi"], "khung": got["khung"], "noi": got["noi"],
                                   "hook": got["hook"], "diem_chot": got.get("diem_chot", 0),
                                   "tinh_huong": got["tinh_huong"], "ma": got["ma"]})
            kho["tinh_huong"][de].append(got["tinh_huong"])
            for kh in got["khuon"]:
                kho["khuon"][kh] = kho["khuon"].get(kh, 0) + 1
            # Ghi sổ CỤM MỞ song song với sổ khuôn — không ghi thì cổng câu mở luôn thấy kho
            # rỗng và không bao giờ chặn ai.
            for mo in (got.get("mo_dau") or []):
                if mo:
                    kho.setdefault("mo_dau", {})[mo] = kho.setdefault("mo_dau", {}).get(mo, 0) + 1
            tong_moi += 1
            print(f"   ✅ {got['khung']:9s} · {len(got['loi'])} lượt · {got['tinh_huong']}", flush=True)
            _luu_kho(kho)          # lưu sau MỖI mẩu: đứt giữa chừng vẫn giữ được phần đã sinh

    print(f"\n✅ thêm {tong_moi} mẩu · loại {tong_loai} trùng khuôn · {tong_yeu} chốt yếu · "
          f"kho tổng {sum(len(v) for v in kho['mau'].values())} mẩu")
    return 0 if tong_moi else 1


if __name__ == "__main__":
    raise SystemExit(main())
