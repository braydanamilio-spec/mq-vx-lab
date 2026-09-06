#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐẠO DIỄN CẢNH — biến lời kể thành BẢNG PHÂN CẢNH.  (6/9/2026)

Anh: *"phải khớp với nội dung được nói tới trong kịch bản nha, khớp với nội dung được nói
từng phân đoạn footage"*.

── VÌ SAO PHẢI CÓ TẦNG NÀY, VÀ VÌ SAO NÓ KHÔNG ĐƯỢC ĐỘNG VÀO CON SỐ ────────────────────────
Bộ cũ để chính hàm sinh kịch bản viết luôn câu tả cảnh, và kết quả đọc được ngay trên dữ liệu
thật: 6/16 nhịp CÓ câu tả, 10 nhịp còn lại rỗng (vẽ bằng code). Sáu câu có thì lặp gần nguyên
văn — *"the same lone adult figure … still walking"* bốn nhịp liền. Người xem đọc ra đúng một
chữ: nhàm.

Nguyên nhân là cấu trúc: một hàm Python tất định phải viết cảnh cho MỌI chủ đề mà kênh có thể
bốc trúng, nên nó chỉ viết được câu chung nhất. Đây đúng chỗ mô hình ngôn ngữ làm tốt hơn hẳn.

VÀ ĐÂY CŨNG LÀ CHỖ DUY NHẤT trong bộ này mà AI được phép viết. Con số vẫn do Python tính —
`giai_thich` không đổi một dòng nào. AI chỉ trả lời một câu hỏi: *"câu này thì QUAY CÁI GÌ"*.
Bịa một cái cảnh sai thì chỉ là cảnh chưa hay; bịa một con số là kênh chết (§ mở đầu
`giai_thich.py`). Ranh giới ấy phải nằm ở đây, viết ra, không ngầm hiểu.

── GROQ, KHÔNG PHẢI GEMINI ────────────────────────────────────────────────────────────────
83 khoá `gsk_`, model `openai/gpt-oss-120b`, và — đo từ máy anh — Groq trả lời được trong khi
mọi khoá Gemini trả 429 vì vùng châu Á không có bậc free. Một tập tốn ĐÚNG MỘT lượt gọi: cả
bảng phân cảnh viết trong một lần, vì viết từng nhịp một thì mô hình không thấy nhịp bên cạnh
và sẽ lặp lại chính nó.
"""
import io
import json
import os
import re
import subprocess

GOC = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("PHIM_LLM") or "openai/gpt-oss-120b"


def _khoa_groq() -> list:
    tho = []
    # Đọc Groq từ MỌI khối secret, không chỉ `GROQ_KEYS`: repo này KHÔNG có secret tên đó
    # (danh sách secret thật: CF_KEYS · GEMINI_KEYS · GEMINI_API_KEY…), nên khoá `gsk_` nếu
    # có thì nằm lẫn trong một khối khác. Lọc theo TIỀN TỐ chứ không theo tên biến.
    for bien in ("GROQ_KEYS", "MM0_KEYS", "CF_KEYS", "GEMINI_KEYS", "GEMINI_API_KEYS"):
        for d in (os.environ.get(bien, "") or "").replace(",", "\n").splitlines():
            if d.strip().startswith("gsk_"):
                tho.append(d.strip())
    if not tho:
        p = os.path.join(GOC, ".keys.local")
        if os.path.exists(p):
            tho = [l.strip() for l in io.open(p, encoding="utf-8").read().splitlines()
                   if l.strip().startswith("gsk_")]
    return tho


# ══ ĐƯỜNG DỰ PHÒNG: CLOUDFLARE VIẾT BẢNG PHÂN CẢNH  (6/9/2026) ═══════════════════════════════
# Bảng phân cảnh là TIM của bộ v10 — không có nó thì mọi nhịp dùng câu dự phòng và cả tập ra
# một cảnh lặp (đã xảy ra thật, xem §10.2 của PHIM_METHOD). Mà nó lại đang phụ thuộc vào một
# thứ repo KHÔNG CÓ: secret `GROQ_KEYS`.
#
# `@cf/openai/gpt-oss-120b` chạy bằng CHÍNH `CF_KEYS` — thứ chắc chắn có, vì cả đường vẽ ảnh
# đang sống bằng nó. Đo thử: trả về đúng JSON, đúng định dạng, ngay lượt đầu.
# Đây là §7 (bốn tầng nền) áp cho tầng CHỮ: thứ gì gọi mạng phải có tầng dưới nó, và tầng dưới
# không được dùng chung điểm hỏng với tầng trên.
def _khoa_cf() -> list:
    tho = []
    for bien in ("CF_KEYS", "MM0_KEYS", "GEMINI_KEYS"):
        for d in (os.environ.get(bien, "") or "").replace(",", "\n").splitlines():
            if d.strip().startswith("cf:") and d.count(":") >= 2:
                tho.append(d.strip())
    if not tho:
        p = os.path.join(GOC, ".keys.local")
        if os.path.exists(p):
            tho = [l.strip() for l in io.open(p, encoding="utf-8").read().splitlines()
                   if l.strip().startswith("cf:") and l.count(":") >= 2]
    return tho


def _goi_cf(sys_p: str, user_p: str) -> str:
    import hashlib
    ks = _khoa_cf()
    if not ks:
        return ""
    b = int(hashlib.sha1(user_p.encode()).hexdigest()[:8], 16)
    body = {"messages": [{"role": "system", "content": sys_p},
                         {"role": "user", "content": user_p}],
            "max_tokens": 8000}
    for j in range(min(10, len(ks))):
        acc, tok = ks[(b + j) % len(ks)][3:].split(":", 1)
        u = f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/@cf/openai/gpt-oss-120b"
        p = subprocess.run(["curl", "-s", "--max-time", "150",
                            "-H", "Authorization: Bearer " + tok,
                            "-H", "Content-Type: application/json",
                            "-d", json.dumps(body), u], capture_output=True, text=True)
        try:
            d = json.loads(p.stdout)
            t = d["result"]["choices"][0]["message"]["content"]
            if t and t.strip():
                return t
        except Exception:
            continue
    return ""


def _goi(sys_p: str, user_p: str, keys: list) -> str:
    """Gọi Groq, xoay khoá tới khi có NỘI DUNG thật. Hỏng thì NÓI RA vì sao.

    ── VÌ SAO `max_tokens` LÀ 12.000, KHÔNG PHẢI 4.000  (6/9/2026) ─────────────────────────
    Một lượt dựng bản dài ra 36 khung y hệt nhau, và sổ cảnh cho thấy CẢ BẢNG rơi về cảnh dự
    phòng. Gọi lại bằng tay thì Groq trả lời bình thường — tức lỗi không tất định.
    `openai/gpt-oss-120b` là model có bước SUY LUẬN, và token suy luận tính vào `max_tokens`.
    Bảng 41 dòng cần ~1.900 token nội dung; cộng phần suy luận là chạm trần 4.000, và khi chạm
    trần thì API trả về `content` RỖNG chứ không báo lỗi. Mười hai khoá lần lượt "hỏng" theo
    cùng một cách, nên nhìn từ ngoài y hệt hết khoá.
    Đây là §15.2 đúng dạng: *bằng chứng luôn tồn tại, ta ném nó đi trước khi ai kịp đọc* — hàm
    này `except Exception: continue` nuốt sạch, và cả tập hỏng mà không một dòng nào báo."""
    import hashlib
    b = int(hashlib.sha1(user_p.encode()).hexdigest()[:8], 16)
    body = {"model": MODEL, "temperature": 0.85, "max_tokens": 12000,
            "reasoning_effort": "low",
            "messages": [{"role": "system", "content": sys_p},
                         {"role": "user", "content": user_p}]}
    vi = []
    for j in range(min(20, len(keys))):
        k = keys[(b + j) % len(keys)]
        p = subprocess.run(["curl", "-s", "--max-time", "180",
                            "-H", "Authorization: Bearer " + k,
                            "-H", "Content-Type: application/json",
                            "-d", json.dumps(body),
                            "https://api.groq.com/openai/v1/chat/completions"],
                           capture_output=True, text=True)
        if not p.stdout:
            vi.append("curl rỗng/quá giờ"); continue
        try:
            d = json.loads(p.stdout)
        except Exception:
            vi.append("phản hồi không phải JSON"); continue
        if d.get("error"):
            vi.append(str(d["error"].get("message"))[:60]); continue
        try:
            c = d["choices"][0]
        except Exception:
            vi.append("thiếu choices"); continue
        t = (c.get("message") or {}).get("content") or ""
        if t.strip():
            return t
        # `content` rỗng KÈM `finish_reason` — chính là dấu vết của việc chạm trần token.
        vi.append("content rỗng (finish_reason=%s)" % c.get("finish_reason"))
    print(f"   ⚠ Groq: {min(20, len(keys))} khoá đều không trả nội dung — "
          f"{', '.join(dict.fromkeys(vi))[:180]}")
    t = _goi_cf(sys_p, user_p)
    if t:
        print("   ↩ bảng phân cảnh viết bằng Cloudflare gpt-oss-120b thay cho Groq")
    return t


# ══ LỆNH HỆ THỐNG ════════════════════════════════════════════════════════════════════════════
# Bốn luật, và mỗi luật sinh ra từ một lỗi ĐÃ ĐO ĐƯỢC ở bộ cũ, không phải từ mong muốn:
#
#   1 "one specific moment"  <- 4 nhịp liền cùng câu "the same figure still walking"
#   2 "name the place"       <- 222/264 nhịp không có nơi chốn -> rơi về một căn phòng chung
#   3 "change something"     <- người xem nhận ra BỐ CỤC chứ không nhận ra sắc độ (§15.1)
#   4 "no text"              <- chữ trong ảnh là chỗ mô hình hỏng nặng nhất (§12.7)
#
# Luật 3 nói rõ ĐỔI CÁI GÌ (nơi · cỡ cảnh · giờ · số người), vì "hãy đa dạng" là một Ý và mô
# hình thoả một Ý bằng cách rẻ nhất câu chữ cho phép (§14.16).
LENH = """You are the storyboard artist for a high-end American explainer animation series.

You will be given the show's visual world and the narration of one episode, line by line.
For EVERY line you return one shot description for an image generator.

RULES
1. One specific moment, not a general idea. Somebody is doing one thing, right now.
   Name who they are, what their WHOLE BODY is doing, and their expression.
1b. NEVER describe hands or fingers doing something. No gripping, holding, carrying, tapping,
   pointing, reaching, leaning on, cradling, typing, stirring, opening. Describe the body
   instead: walking, standing, turning away, sitting down, crouching, stepping back, looking
   up. Objects sit on surfaces near the person, they are not held.
2. START the sentence with the person or the main subject and what they are doing. Only
   after that describe the place, one foreground object, and something visible far behind.
   Never open with the foreground object: whatever comes first becomes the picture.
3. Consecutive shots must CHANGE at least two of these four: the place, the shot size
   (wide / medium / close), the time of day, the number of people on screen.
3b. LOCATIONS: use at least five different locations across the episode, and never use the
   same location for more than three shots in total. Rotate through the places named in the
   show world, and invent new ones that belong to the same world when you run out.
4. Nothing in the frame may carry text: no signs, no screens with words, no labels, no
   numbers, no logos. If the line is about a number, show the THING the number counts.
5. The shot must depict what the line actually says. If the line is abstract, show the
   concrete consequence of it in this world.
6. 25 to 45 words. Plain descriptive English. No camera jargon beyond wide / medium / close.
   Never mention art style, colours, lighting or the word "illustration" - that is handled
   elsewhere.
7. SHOT SIZE should rotate: wide (the person small inside a big place), then medium, then a
   close shot of an OBJECT with no person in it, then wide again.
7c. CAMERA LANGUAGE - at most two shots in the whole episode may be "a person standing in the
   middle of a room facing the viewer". Every other shot uses one of these, and you rotate
   through them:
     - over the shoulder: we see past a person's shoulder at what they are looking at
     - foreground occlusion: something close to the camera partly blocks the view - a doorway
       edge, a shelf, a curtain, the back of a chair
     - from behind: the person is walking or looking away from us
     - low angle: camera near the floor looking up
     - high angle: camera above looking down on the person and the floor
     - through a frame: seen through a window, a door gap, a gap between two objects
     - close on hands-free detail: a face turned in profile, or an object mid-action
   Name the device in plain words at the start of the shot.
7b. RULE 5 BEATS RULE 7. Only put an object-only shot on a line that is ABOUT a thing, a
   place, a number or a passage of time. If the line is about a person doing, feeling,
   continuing or deciding something, the person MUST be in the frame - break the rotation and
   keep them. A shot that follows the rotation but contradicts its line is a wrong shot.
8. At most a quarter of the shots may have the person facing the viewer. In the rest they are
   seen from behind, from the side, or looking away at something inside the scene.
9. SHOT 0 IS THE HOOK and it obeys a different rule from every other shot. It shows the
   WORK ITSELF at its most extreme - the busiest, fullest, most piled-up, most crowded, most
   relentless version of what this episode is about, already at that peak. Never an
   establishing shot, never someone about to start, never a calm arrival.
9b. The hook is never a disaster happening TO the character. Nobody collapses, faints, lies
   on the floor, is injured, bleeding, unconscious or in danger. The character is upright and
   working; it is the SITUATION that is extreme, not their body.

10. THE LAST SHOT RETURNS TO THE PLACE OF SHOT 0, at a different moment - later, calmer,
   emptied out, or after the thing in shot 0 has been dealt with. Same room, same angle
   family, different state. It must still say what its own line says.
11. You are given a CAST. Refer to every person by their exact role word from that cast, and
   never invent a person who is not in it. A character keeps the same clothes and hair from
   the first shot to the last. The lead appears in most shots; the others appear only where
   the line actually calls for them.

Return ONLY a JSON array, one object per line, in order:
[{"i": 0, "shot": "..."}, {"i": 1, "shot": "..."}]
"""


def _tach_json(t: str):
    m = re.search(r"\[.*\]", t, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


_TU_TAM = set("""a an the and or of to in on at for with is are was were be been it its this
that these those you your they their he she his her we our as by from not no than then so
into over about all any each more most some such only own same very can will just don now""".split())


def _tu_chinh(s: str) -> set:
    return {w for w in re.findall(r"[a-z]+", (s or "").lower())
            if len(w) > 3 and w not in _TU_TAM}


# ── NƠI CHỐN LẶP: ĐO ĐƯỢC, VÀ ĐÃ XẢY RA THẬT ────────────────────────────────────────────────
# Bản dài `realcost` lượt đầu ra SÁU KHUNG LIỀN cùng một căn bếp đỏ-xanh, dù thế giới của kênh
# liệt kê bốn loại nơi chốn. Lệnh dặn chỉ nói "đổi nơi chốn giữa hai cảnh liền nhau" — mô hình
# thoả nó bằng cách rẻ nhất là quay lại nơi cũ ở cảnh thứ ba (§14.16).
#
# Phép đo: lấy danh từ nơi chốn của mỗi cảnh (cụm sau `in/at/inside/on`), đếm cụm phổ biến
# nhất. Quá 40% số cảnh dùng một nơi thì cả tập đọc ra là một phòng.
NOI = re.compile(r"\b(?:in|at|inside|on|outside|beside|near)\s+(?:the|a|an|her|his|their)\s+"
                 r"([a-z]+(?:\s+[a-z]+)?)", re.I)


def _noi_lap(ds: list) -> float:
    """Trả tỉ lệ cảnh dùng nơi chốn phổ biến nhất. 0 nếu không đọc được nơi nào."""
    dem = {}
    for s in ds:
        for t in set(x.group(1).lower() for x in NOI.finditer(s or "")):
            dem[t] = dem.get(t, 0) + 1
    if not dem or len(ds) < 6:
        return 0.0
    return max(dem.values()) / len(ds)


# Câu NÓI VỀ NGƯỜI: có đại từ nhân xưng, hoặc một động từ chỉ hành động/trạng thái của người.
# Cố ý HẸP — chỉ bắt đúng cái đã hỏng thật, không bắt "cảnh có khớp lời không" nói chung.
# §13.22: đo trên 42 nhịp thật thì phép "đếm từ chung giữa lời và cảnh" bắt 2 ca và CẢ HAI đều
# là kịch bản tốt. Nên phép đo ấy bị bác, và chỗ này chỉ đo một thứ dứt khoát: **lời nói về
# một người đang làm gì, mà cảnh lại tuyên bố không có người nào trong khung**.
NGUOI_NOI = re.compile(
    r"\b(you|your|i|we|he|she|they|him|her|them|his|their|my|me)\b|"
    r"\b(work(s|ing|ed)?|walk(s|ing|ed)?|sleep(s|ing)?|quit(s|ting)?|wait(s|ing|ed)?|"
    r"keep(s|ing)?|going|stay(s|ing|ed)?|start(s|ing|ed)?|stop(s|ping|ped)?|"
    r"feel(s|ing)?|think(s|ing)?|decide(s|d)?|try(ing)?|tried)\b", re.I)
KHONG_NGUOI = re.compile(r"\bno (?:person|people|one)\b|\bnobody\b|\bempty of people\b", re.I)


# Danh từ chỉ người, để nhận ra một cảnh CÓ người dù không gọi tên vai.
CO_NGUOI = re.compile(
    r"\b(he|she|they|him|her|man|woman|boy|girl|child|person|people|worker|nurse|doctor|"
    r"patient|driver|customer|visitor|crowd|figure|someone|his|hers|their)\b", re.I)


def _lech_nguoi(canh: str, loi: str, vai=None) -> bool:
    """Lời nói về một người đang làm gì, mà cảnh KHÔNG có người nào.

    Bản đầu chỉ bắt khi cảnh TỰ KHAI `"no person"`. Anh soi ra một khung lọt: lời *"On your
    feet in the dark. No break at noon."* mà cảnh là *"a pair of sneakers and a lanyard rest
    on the tile"* — không hề khai "no person", nó chỉ **không nhắc tới ai**. Cổng đo lời khai
    thay vì đo nội dung, nên nó bỏ qua đúng ca cần bắt.
    Nay: cảnh không khai có người VÀ không gọi tên vai nào VÀ không có danh từ chỉ người ->
    coi như cảnh không người."""
    if not NGUOI_NOI.search(loi or ""):
        return False
    if KHONG_NGUOI.search(canh or ""):
        return True
    ten = any(re.search(r"\b" + re.escape(v["vai"].split()[-1]) + r"\b", canh or "", re.I)
              for v in (vai or []))
    return not (ten or CO_NGUOI.search(canh or ""))


_VAI: list = []          # dàn vai của tập đang dựng — `_kiem` cần để nhận ra cảnh có người


def _kiem(ds: list, loi: list) -> list:
    """Trả danh sách chỉ số HỎNG. Ba phép, và cả ba đã thử ngược (xem `kiem_phim`).

    Cố ý KHÔNG kiểm "shot có khớp nghĩa với lời không" bằng cách đếm từ chung: đo thử trên 42
    nhịp thật thì phép ấy đánh trượt cả những cặp đúng nhất — lời *"Nobody has made this trip"*
    và cảnh *"an empty highway stretching to the horizon"* không chia một từ nào mà khớp hoàn
    hảo. §13.22: một cổng chỉ đáng ship khi đọc tay các ca nó bắt và thấy chúng thật sự hỏng."""
    hong = []
    for j, s in enumerate(ds):
        w = len((s or "").split())
        if w < 14 or w > 70:
            hong.append(j); continue
        if re.search(r"\b(sign|signage|label|text|letters?|words?|banner|billboard)\b",
                     s, re.I):
            hong.append(j); continue
        # ĐỘNG TỪ BÀN TAY — chỗ mô hình hỏng nặng nhất, và là nguyên nhân của 8/8 ảnh lỗi ở
        # bản short đầu tiên. Liệt kê ĐÚNG những từ mà lệnh dặn ở trên đã liệt kê (§13.2:
        # cổng đo một TỪ thì lệnh dặn phải nêu chính từ ấy) — không thêm từ nào ngoài bảng.
        if re.search(r"\b(grip(s|ping|ped)?|hold(s|ing)?|carr(y|ies|ying)|tap(s|ping|ped)?|"
                     r"point(s|ing|ed)?|reach(es|ing|ed)?|lean(s|ing|ed)?|cradl(e|es|ing)|"
                     r"typ(e|es|ing)|stir(s|ring|red)?|open(s|ing|ed)?|hand|hands|finger|"
                     r"fingers|palm)\b", s, re.I):
            hong.append(j); continue
        if j and " ".join(s.split()[:5]).lower() == " ".join(ds[j - 1].split()[:5]).lower():
            hong.append(j); continue
        # Anh soi ra một khung: lời *"And still going when the light goes."* mà cảnh là một
        # màn hình nhịp tim, không người. Thang cỡ cảnh (luật 7) đã đè lên luật 5 — cảnh phải
        # vẽ đúng mệnh đề đang nói. Nay luật 7b nói rõ luật 5 thắng, và cổng này canh nó.
        if j < len(loi) and _lech_nguoi(s, loi[j], _VAI):
            hong.append(j)
    return hong


def _du_phong(ma_the: str, loi: str, j: int) -> str:
    """Không có Groq (mạng hỏng · hết khoá) thì vẫn phải có cảnh — nhưng cảnh dự phòng nói
    THẲNG rằng nó là dự phòng bằng cách bám sát thế giới kênh, thay vì vẽ một phòng trống."""
    co = ("wide", "medium", "close")[j % 3]
    return (f"A {co} shot inside this world: {ma_the}. One person is in the middle of an "
            f"ordinary action connected to \"{loi.strip().rstrip('.')}\", with props around "
            f"them and more of the place visible behind.")


def _doc_bang(t: str, n: int) -> list:
    ra = [""] * n
    for o in (_tach_json(t) or []):
        try:
            i = int(o.get("i"))
        except Exception:
            continue
        if 0 <= i < n:
            ra[i] = str(o.get("shot") or "").strip()
    return ra


def dao_dien(ma: str, tieu_de: str, loi: list, the: str, nhan_vat: str = "") -> list:
    """Trả danh sách câu tả cảnh, ĐÚNG một câu cho mỗi dòng lời. Không bao giờ trả thiếu.

    HAI lượt gọi là trần: một lượt viết cả bảng, một lượt VÁ đúng những ô hỏng. Bản trước bắt
    viết lại TOÀN BỘ khi có một ô hỏng — vừa đắt vừa làm hỏng những ô vốn đã tốt, đúng họ lỗi
    §15.7 (*đặt bản sửa ở nơi biết đủ để nó chỉ chạm vào đúng thứ cần chạm*)."""
    keys = _khoa_groq()
    if not keys and not _khoa_cf():
        print("   ⚠ không có khoá Groq lẫn Cloudflare — dùng cảnh dự phòng cho cả tập")
        return [_du_phong(the, loi[j], j) for j in range(len(loi))]

    dau = (f"SHOW WORLD: {the}\nEPISODE TITLE: {tieu_de}\n"
           + (f"CAST (call every person by these exact role words, and never invent "
              f"another person):\n{nhan_vat}\n" if nhan_vat else ""))
    ra = _doc_bang(_goi(LENH, dau + f"\nNARRATION ({len(loi)} lines):\n"
                        + "\n".join(f"{i}. {t}" for i, t in enumerate(loi)), keys), len(loi))
    xau = sorted(set([j for j, s in enumerate(ra) if not s]) | set(_kiem(ra, loi)))
    if xau:
        # Vá: chỉ gửi lại những dòng hỏng, kèm cảnh LIỀN TRƯỚC của mỗi dòng để mô hình biết
        # phải đổi đi cái gì. Không gửi kèm thì nó viết lại gần y hệt câu vừa bị loại.
        u = dau + "\nRewrite ONLY these lines. Each must be 25-45 words, must open with a "
        u += "different phrase from the shot before it, and must contain no signs or text.\n"
        for j in xau:
            truoc = ra[j - 1] if j and ra[j - 1] else "(start of the episode)"
            u += f"\n{j}. LINE: {loi[j]}\n   SHOT BEFORE: {truoc}\n"
        va = _doc_bang(_goi(LENH, u, keys), len(loi))
        for j in xau:
            if va[j] and j not in set(_kiem([va[j] if i == j else ra[i]
                                             for i in range(len(ra))], loi)):
                ra[j] = va[j]
    # CỔNG NƠI CHỐN chạy SAU cùng, trên cả bảng: nó là tính chất của TẬP, không của một dòng,
    # nên không bắt được ở `_kiem` (thứ chỉ nhìn từng dòng và dòng liền trước).
    lap = _noi_lap(ra)
    if lap > 0.40:
        print(f"   ↻ nơi chốn lặp {lap:.0%} — viết lại bảng phân cảnh")
        u2 = (dau + f"\nNARRATION ({len(loi)} lines):\n"
              + "\n".join(f"{i}. {t}" for i, t in enumerate(loi))
              + "\n\nYour previous storyboard put most of the episode in one single location. "
                "Rewrite it so the episode moves through at least five clearly different "
                "places, and no place is used more than three times.")
        va = _doc_bang(_goi(LENH, u2, keys), len(loi))
        if all(va) and _noi_lap(va) < lap and not _kiem(va, loi):
            ra = va
    # SỐ CẢNH DỰ PHÒNG PHẢI ĐI KÈM MẪU SỐ, và phải kêu khi nó lớn. Bản trước điền dự phòng
    # trong im lặng, nên một tập có 36/36 cảnh dự phòng đọc từ log y hệt một tập hoàn hảo —
    # chỉ lộ ra khi soi khung, tức sau khi đã tốn 36 lượt vẽ và một lượt render (§15.2).
    du = [j for j, s in enumerate(ra) if not s]
    for j in du:
        ra[j] = _du_phong(the, loi[j], j)
    if du:
        muc = "⚠" if len(du) * 4 <= len(ra) else "❌"
        print(f"   {muc} bảng phân cảnh: {len(du)}/{len(ra)} cảnh phải dùng bản dự phòng")
    return ra


def _diem(ds: list, loi: list) -> int:
    return sum(1 for s in ds if not s) + len(_kiem(ds, loi))


def dan_vai(ma: str, tieu_de: str, the: str, doo: bool = False) -> list:
    """DÀN VAI của một tập: 2–4 người, mỗi người một bộ nhận diện RIÊNG.

    Anh: *"nếu có nhiều nhân vật trong 1 video thì phải xây nhiều nhân vật — bác sĩ khác, bệnh
    nhân khác, gái khác trai khác, chứ không dùng một dạng."*

    Bản trước trả về ĐÚNG MỘT bộ đồ rồi nướng thẳng vào câu hình que (*"one flat garment,
    always blue hospital scrubs"*). Câu ấy áp cho MỌI người trong khung — nên y tá, bệnh nhân
    và bác sĩ buộc phải mặc cùng một thứ. Nó chữa được lỗi "nhân vật đổi áo giữa các khung",
    nhưng chữa bằng cách xoá luôn sự khác nhau giữa các VAI. Sai một chiều, sang sai chiều kia.

    Nay mỗi vai có: TÊN VAI (đạo diễn gọi bằng tên này) + màu áo + mảng tóc + một dấu nhận
    diện đơn giản. Ba trục ấy đủ để phân biệt ở cỡ hình que, và không trục nào đòi vẽ chi tiết
    mặt — thứ đã phá kiểu vẽ một lần rồi.
    """
    # DÀN VAI KHAI SẴN ĐỨNG TRƯỚC. Casting bằng AI mỗi tập cho ra một người khác nhau ở mỗi
    # tập — đúng về "nhiều vai", sai về LOẠT. Xem `phim_gu.VAI`.
    import phim_gu as _G
    khai = _G.dan_vai_khai(ma)
    if khai:
        _VAI[:] = khai
        return khai
    keys = _khoa_groq()
    if not keys and not _khoa_cf():
        return []
    manh = ("Cast 2 to 4 characters for one episode of a stick-figure explainer cartoon.\n"
            "Return ONLY a JSON array: [{\"vai\":\"nurse\",\"ta\":\"...\"}]\n"
            "RULES\n"
            "1. \"vai\" is one lowercase word or two, the role the storyboard will call them "
            "by: nurse, patient, doctor, visitor, boss, child, driver.\n"
            "2. \"ta\" is 6 to 12 words and may ONLY contain: the colour and type of their "
            "single garment, the colour and simple shape of their hair blob, and at most one "
            "simple accessory (cap, glasses, beard, ponytail, bald). Nothing else — no face, "
            "no build, no age, no personality.\n"
            "3. Every character must differ from the others in BOTH garment colour AND hair, "
            "so they are told apart at a glance as small stick figures.\n"
            "4. The first entry is the lead, the person the episode follows.")
    if not doo:
        manh = manh.replace("stick-figure explainer cartoon", "animated explainer film").replace(
            "the colour and simple shape of their hair blob", "hair colour and style")
    t = _goi(manh, f"SHOW WORLD: {the}\nEPISODE: {tieu_de}", keys)
    ra = []
    for o in (_tach_json(t) or []):
        v = str(o.get("vai") or "").strip().lower()
        ta = " ".join(str(o.get("ta") or "").split())[:90]
        if v and ta and len(v.split()) <= 2:
            ra.append({"vai": v, "ta": ta})
    return ra[:4]


def nhan_vat_tap(ma: str, tieu_de: str, the: str, doo: bool = False) -> str:
    """MỘT câu tả nhân vật chính, dùng lại ở mọi nhịp có người.

    Đây là thứ bộ cũ cố ý bỏ ("kênh giải thích không có vai nào cả, chỉ có 'một người'"), và
    đó là lý do 40 khung của một tập trông như 40 ảnh nhặt về. Một cái áo khoác xanh và một
    kiểu tóc là đủ để mắt nối các khung lại thành một bộ phim — mà giá của nó là 25 từ."""
    keys = _khoa_groq()
    if not keys:
        return ""
    # Kiểu doodle vẽ nhân vật bằng một đầu tròn trắng và một mảng màu ở thân — nó KHÔNG vẽ
    # được "tóc vàng cát" hay "áo khoác cargo bạc màu". Tả dài ở đó là tả cho một thứ không
    # tồn tại trong khung, và phần thừa ấy đẩy mô hình về lối vẽ có khối.
    # Nên bản doodle chỉ giữ đúng thứ NHÌN THẤY ĐƯỢC: màu áo và kiểu tóc dạng khối.
    if doo:
        # ── CHỈ MÀU ÁO, TUYỆT ĐỐI KHÔNG TẢ TÓC  (sửa 6/9/2026) ────────────────────────
        # Bản trước xin thêm "kiểu tóc dạng khối". Kết quả đo trên 8 khung: **5/8 khung ra
        # một cô gái hoạt hình có tóc, có dáng người thật — không còn là hình que**, trong
        # khi 3 khung kia vẫn là hình que. Một tập, hai kiểu vẽ.
        # Gốc: hình que theo định nghĩa có **đầu tròn trắng trơn**. Nhắc tới tóc là nhắc tới
        # một cái đầu THẬT, và mô hình vẽ nốt phần còn lại của một người thật. Đây lần thứ
        # năm trong ngày cùng một họ lỗi — một câu tả NỘI DUNG phá một câu tả PHONG CÁCH.
        # Nay xin đúng ba đến sáu chữ, chỉ màu và loại áo, và nó được ghép THẲNG vào câu
        # hình que chứ không đứng thành câu riêng (xem `phim.prompt_anh`).
        t = _goi("Name the single garment one character wears for a whole cartoon episode. "
                 "Answer with 3 to 6 words only: a colour and a garment. No hair, no face, "
                 "no body, no accessories, no punctuation. Example: 'blue hospital scrubs'.",
                 f"SHOW WORLD: {the}\nEPISODE: {tieu_de}", keys)
        t = (t or "").strip().split("\n")[0].strip(" .\"'")
        return " ".join(t.split()[:6])[:48]
    t = _goi("You cast one character for an American animated explainer episode. "
             "Answer with ONE sentence, 20-30 words: age range, build, hair, and the exact "
             "clothes they wear for the whole episode. No name. No text on the clothes.",
             f"SHOW WORLD: {the}\nEPISODE: {tieu_de}", keys)
    t = (t or "").strip().split("\n")[0]
    return t[:220]
