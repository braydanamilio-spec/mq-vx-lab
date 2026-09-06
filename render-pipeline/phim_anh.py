#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HỒ ẢNH AI CHO BỘ PHIM — Cloudflare FLUX.2 + Gemini 3.x.  (6/9/2026)

MỘT CỬA DUY NHẤT đi tới mọi lệnh gọi vẽ ảnh: `ve()`. Bộ cũ có ba cửa (`nen_gt.sinh`,
`datastory_ci._generate_image_ai`, `_cf_flux_image`) và mỗi cửa có một bộ luật riêng — nên
một bản vá ở cửa này không tới được cửa kia. Cửa duy nhất là điều kiện để cổng có nghĩa.

── VÌ SAO KHÔNG DÙNG LẠI `datastory_ci` ───────────────────────────────────────────────────
Nó xếp FLUX.1-schnell trước Gemini và ép mọi ảnh về 1024×1024 vuông. Cả hai giả định đều
thuộc về thời chưa có FLUX.2. Sửa tại chỗ thì phải sửa trong một hàm 200 dòng đang phục vụ
bốn bộ khác — §10 của CLAUDE.md: hai bộ, hai xưởng, đừng trộn.

── THỨ TỰ NHÀ CUNG CẤP: CLOUDFLARE TRƯỚC, HẾT CẢ BA MODEL RỒI MỚI TỚI GEMINI ──────────────
    1  cf:flux-2-klein-9b      768×1344 nguyên bản · 37 ảnh/tài khoản/ngày · 97 tài khoản
    2  cf:flux-2-klein-4b      768×1344 · ≥90 ảnh/tài khoản/ngày · chất gần bằng 9b
    3  cf:flux-1-schnell       tầng chót của CF: vuông 1024, phải cắt, nhưng gần như vô tận
    4  gemini-3.1-flash-image  hai lớp chặn, và lớp thứ hai mới là lớp quyết định:
                               (a) từ VN mọi khoá trả 429 `quota_limit_value: 0` @asia-east1 —
                                   và đo được cả model CHỮ cũng vậy, nên đó là chuyện VÙNG;
                               (b) trang giá chính thức ghi **"Not available"** cho free tier ở
                                   cả gemini-2.5-flash-image, gemini-3-pro-image và
                                   gemini-3.1-flash-image. Sinh ảnh qua API BẮT BUỘC trả phí.
                               => hồ Gemini đóng góp 0 ảnh Ở MỌI VÙNG, kể cả runner Mỹ.
                               Giữ tầng này vì nó hỏng mềm và vì khoá bật thanh toán sẽ dùng
                               được ngay, nhưng MỌI phép tính sản lượng chỉ được dựa vào CF.
    5  gemini-2.5-flash-image  (Google khai ngừng phục vụ 2/10/2026)
KHÔNG xen kẽ, KHÔNG ngẫu nhiên. Trong mỗi tầng CF, tài khoản chọn theo BĂM của (kênh, tập,
nhịp, lần thử) nên 97 tài khoản được trải đều; và mỗi luồng chỉ nhìn thấy một lát cắt RỜI NHAU
`cf[w::số_luồng]` nên hai luồng không bao giờ bốc trúng một tài khoản.

Bản đầu của chính docstring này ghi thứ tự là "1 CF · 2 Gemini · 3 klein-4b · 4 schnell" trong
khi mã thử hết ba model CF rồi mới sang Gemini. §15.25 — *chú thích và mã nói hai điều khác
nhau thì đừng tin cái nào, đi ĐO*. Mã đang đúng ý đồ hơn, nên sửa chú thích theo mã.

── VÀ NHÀ CUNG CẤP PHẢI KHOÁ THEO TẬP, KHÔNG THEO ẢNH ─────────────────────────────────────
Thứ tự trên áp cho TỪNG ảnh, nên một tập có thể vẽ nửa đầu bằng CF rồi hồ cạn giữa chừng và
nửa sau rơi sang Gemini — hai nửa lệch chất vẽ, mà §13.4 đã đo rằng *lệch phong cách giữa các
ảnh* mới là đòn bẩy thật, không phải chỉnh màu. `_CHOT` ghi lại model đã vẽ thành công ảnh ĐẦU
TIÊN của tập và ưu tiên nó cho mọi ảnh sau; chỉ khi model ấy cạn hẳn mới tụt tầng, và lúc ấy
cả phần còn lại của tập cùng tụt theo chứ không so le.
"""
import base64
import hashlib
import io
import json
import os
import re
import subprocess
import time

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(GOC), "engine-remotion")
THU = os.path.join(ENG, "public", "phim_nen")

# ── KHUNG ẢNH ───────────────────────────────────────────────────────────────────────────────
# 768×1344 và 1344×768: đúng 9:16 và 16:9, và là cỡ FLUX.2 nhận. Không lấy 1080×1920 vì mô
# hình từ chối cạnh > 1440 và vì render 1080p chỉ cần nguồn ≥ 768 để không thấy mềm nét.
CO_DOC = (768, 1344)
CO_NGANG = (1344, 768)

# Trần prompt. ĐO 6/9/2026 trên chính `flux-2-klein-9b`: 2.000 · 2.600 · 3.200 · 4.000 ký tự
# đều trả về ảnh bình thường. Con số 1.900 cũ là trần của **schnell** (API từ chối ở 2.048) mà
# em chép sang mà không đo lại — đúng §13.6, *hằng số sống lâu hơn ngữ cảnh sinh ra nó*.
#
# Nhưng KHÔNG lấy 4.000. Trần này không phải "dài nhất API chịu" mà là "dài nhất còn có tác
# dụng": prompt càng dài thì mỗi mệnh đề càng bị pha loãng, và bộ này đã có bốn khối bắt buộc
# (phong cách · bố cục · cảnh · an toàn) phải được nghe đủ. 2.600 chừa chỗ cho một cảnh 45 từ
# cộng hai vai, và vẫn cách trần đo được 35%.
KY_TU_MAX = 2600
_DA_CAT: list = []          # [(mã, chỉ số nhịp, số ký tự bị cắt)] — `kiem_phim` đọc

_CHOT: dict = {}            # (mã kênh, số tập) -> model đã vẽ được ảnh đầu tiên của tập
_NGHI: dict = {}            # khoá -> mốc thời gian được dùng lại
_LOG: dict = {}             # lý do -> số lần, để bản tổng kết nói ĐƯỢC VÌ SAO


def _ghi(ly: str) -> None:
    _LOG[ly] = _LOG.get(ly, 0) + 1


def tong_ket() -> dict:
    return dict(_LOG)


# ══ HỒ KHOÁ ══════════════════════════════════════════════════════════════════════════════════
# ══ TRẦN ẢNH CỦA MỘT LƯỢT CHẠY ═══════════════════════════════════════════════════════════════
# Hồ CF là tài nguyên DÙNG CHUNG giữa 18 luồng (§13.7). Không có trần thì luồng chạy sớm ăn
# hết hạn mức và mười bảy luồng sau ra video không ảnh — mà nhìn từ dashboard vẫn xanh.
#
# Bộ đếm sống ở TỆP chứ không ở biến, vì workflow chạy mỗi tập một tiến trình `python` riêng:
# §17.7 đã đo được đúng cái lỗi này ở bộ cũ — trần khai là "120 ảnh mỗi luồng" mà thực tế
# thành "120 ảnh mỗi TẬP", và một lượt chạy vẽ 8.059 ảnh thay vì 2.160.
#
# Mặc định 0 = không giới hạn (chạy tay ở máy anh). Workflow đặt `PHIM_TRAN_ANH`.
_SO_DEM = os.path.join(os.environ.get("TMPDIR") or "/tmp", "mm0_phim_dem.json")


def _da_ve(cong: int = 0) -> int:
    n = 0
    try:
        n = int(json.load(io.open(_SO_DEM, encoding="utf-8")).get("n", 0))
    except Exception:
        pass
    if cong:
        n += cong
        try:
            json.dump({"n": n}, io.open(_SO_DEM, "w", encoding="utf-8"))
        except Exception:
            pass
    return n


# ── MỐC HỒI HẠN MỨC CF: KHÔNG GHIM MỘT GIỜ NÀO  (đo 6/9/2026) ───────────────────────────────
# Ba tài khoản bị bơm cạn trong ngày, kiểm lại lúc 06:25 UTC: #95 ĐÃ hồi, #94 và #96 CHƯA —
# cùng một thời điểm, ba kết quả không giống nhau. Nên hạn mức KHÔNG hồi đồng loạt ở một mốc
# chung, và mọi con số giờ em có thể viết ra ở đây đều là bịa.
# §13.1: một giới hạn phải có đơn vị và nguồn. Không có nguồn thì đừng ghim — cho nghỉ một
# khoảng rồi THĂM DÒ, và để chính câu trả lời của API quyết định.
#
# 90 phút, không phải 6 giờ: nghỉ 6 giờ là tự khoá mình khỏi những tài khoản có thể đã hồi từ
# lâu (đúng cảnh #95 ở trên). Một lượt thăm dò tốn một vòng mạng và ~270 neuron NẾU nó vẽ
# được — mà vẽ được thì đó là ảnh dùng luôn, không phí.
NGHI_CAN = 90 * 60
# Nghỉ NGẮN cho lỗi tạm thời (429 mỗi phút · máy chủ bận). 45 giây: đủ để cửa sổ hạn mức
# mỗi phút trôi qua, mà không vứt tài khoản đi cả tiếng rưỡi. Xem `_het_han` để biết vì sao
# hai loại lỗi này KHÔNG được dùng chung một thời gian nghỉ.
NGHI_BAN = 45


def suc_khoe(ks: dict = None) -> tuple:
    """Trả (số tài khoản còn dùng được, tổng). Dùng để BÁO trước khi dựng, không để chặn."""
    ks = ks or khoa()
    _nap_nghi()
    song = sum(1 for c in ks["cf"] if _song(("cf", c[0])))
    return song, len(ks["cf"])


def con_ngan_sach() -> bool:
    tran = int(os.environ.get("PHIM_TRAN_ANH") or 0)
    return tran <= 0 or _da_ve() < tran


def khoa() -> dict:
    """Trả {"cf": [(acc, token)], "gem": [key]}.

    Đọc theo ĐÚNG thứ tự mà mã thật chạy ở hai môi trường: biến môi trường (Actions) trước,
    tệp `.keys.local` (máy anh) sau. §15.4 — tệp phụ thuộc phải tìm bằng đường mặc định."""
    tho = []
    for bien in ("CF_KEYS", "GEMINI_KEYS", "MM0_KEYS"):
        for d in (os.environ.get(bien, "") or "").replace(",", "\n").splitlines():
            d = d.strip()
            if d and not d.startswith("#"):
                tho.append(d)
    if not tho:
        p = os.path.join(GOC, ".keys.local")
        if os.path.exists(p):
            tho = [l.strip() for l in io.open(p, encoding="utf-8").read().splitlines()
                   if l.strip() and not l.strip().startswith("#")]
    # ── KHỬ TRÙNG THEO TÀI KHOẢN  (đo 6/9/2026) ─────────────────────────────────────────
    # Hạn mức 10.000 neuron/ngày thuộc về TÀI KHOẢN, không thuộc về token. Khai một tài khoản
    # hai lần không cho thêm một neuron nào — nó chỉ làm:
    #   · mọi phép đếm sức chứa nói dối (đo được 97 dòng cf mà chỉ 94 tài khoản thật),
    #   · vòng xoay khoá đâm lại vào một tài khoản đã cạn, tốn một vòng mạng mỗi lần,
    #   · và `suc_khoe()` báo "97 tài khoản" trong khi trần thật thấp hơn 3%.
    # Cùng họ §15.2: một con số không có mẫu số đúng thì mọi kế hoạch dựng trên nó đều lệch.
    cf, gem, da = [], [], set()
    for k in tho:
        if k.startswith("cf:") and k.count(":") >= 2:
            a, t = k[3:].split(":", 1)
            if a in da:
                continue
            da.add(a)
            cf.append((a, t))
        elif k.startswith("AIza") or k.startswith("AQ."):
            gem.append(k)
    return {"cf": cf, "gem": gem}


# Sổ nghỉ nằm ở TỆP, không ở biến mô-đun. §17.7 đã trả giá cho đúng chuyện này: workflow chạy
# MỖI TẬP một tiến trình `python` riêng, nên biến mô-đun chết theo tiến trình và tập sau lại
# đi khám phá lại 97 tài khoản đã chết — mỗi tài khoản một vòng mạng.
# Tệp nằm ở thư mục tạm của máy chạy: nó là trạng thái của MỘT lượt chạy, không phải dữ liệu
# cần đi theo git. Hỏng tệp thì rơi về sổ trong bộ nhớ, không bao giờ làm chết đường vẽ.
_SO_NGHI = os.path.join(os.environ.get("TMPDIR") or "/tmp", "mm0_phim_nghi.json")


def _nap_nghi() -> None:
    try:
        d = json.load(io.open(_SO_NGHI, encoding="utf-8"))
        n = time.time()
        _NGHI.update({k: v for k, v in d.items() if v > n})
    except Exception:
        pass


def _song(k) -> bool:
    return _NGHI.get(str(k), 0) <= time.time()


def _cho(k, giay: float) -> None:
    _NGHI[str(k)] = time.time() + giay
    try:
        json.dump(_NGHI, io.open(_SO_NGHI, "w", encoding="utf-8"))
    except Exception:
        pass


# ══ GỌI CLOUDFLARE ═══════════════════════════════════════════════════════════════════════════
# Dùng `curl` chứ không `urllib`: phản hồi của CF là chunked và urllib đã ném `IncompleteRead`
# ngay ở lượt thử đầu tiên khi tải danh sách model. Đây là số đo, không phải sở thích.
def _cf(model: str, body: dict, acc: str, tok: str, multipart: bool, tam: str):
    u = f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{model}"
    cmd = ["curl", "-s", "--max-time", "180", "-H", "Authorization: Bearer " + tok,
           "-o", tam, "-w", "%{http_code}"]
    if multipart:
        for k, v in body.items():
            cmd += ["-F", f"{k}={v}"]
    else:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    cmd.append(u)
    subprocess.run(cmd, capture_output=True, text=True)
    raw = open(tam, "rb").read() if os.path.exists(tam) else b""
    if raw[:2] in (b"\x89P", b"\xff\xd8"):
        return raw, ""
    try:
        d = json.loads(raw)
    except Exception:
        return None, f"phản hồi lạ ({len(raw)} byte)"
    if d.get("success") and isinstance(d.get("result"), dict) and d["result"].get("image"):
        return base64.b64decode(d["result"]["image"]), ""
    return None, json.dumps(d.get("errors") or d)[:180]


def _het_han(msg: str) -> bool:
    """CẠN HẠN MỨC NGÀY — tài khoản không dùng lại được cho tới mốc hồi (00:00 UTC).

    ── VÌ SAO TÁCH KHỎI `_ban()`  (đo 6/9/2026) ────────────────────────────────────────────
    Bản cũ gộp bốn thứ vào một rổ: `daily free allocation` · `10,000 neurons` · `capacity` ·
    `429`/`rate limit`. Hai cái đầu là CẠN THẬT; hai cái sau là **tạm thời** — `capacity` là
    "máy chủ đang bận", `429` là hạn mức MỖI PHÚT, hồi sau vài giây.

    Gộp chúng lại thì một cú 429 tạm thời cũng cho tài khoản nghỉ **90 phút** — mà 429 hồi sau
    vài giây. Tách ra là đúng, và nó sẽ có giá vào ngày hồ CÒN hạn mức.

    ── NHƯNG ĐỪNG TIN NÓ LÀ LỜI GIẢI CHO "CẠN HỒ"  (đính chính, cùng ngày) ─────────────────
    Em đã kết luận sai một lần ở đây, ghi lại để phiên sau không đi lại: thấy 1.081 ảnh trên
    97 tài khoản (**11 ảnh/tài khoản**) trong khi số đo klein-9b là 52, em kết luận "hồ tự huỷ
    vì phân loại sai". ĐO LẠI thì bác: xoá sạch sổ nghỉ, chạy lại bằng chính bộ phân loại chặt
    này -> **94 tài khoản rơi vào nghỉ DÀI, 0 vào nghỉ ngắn**, tức chúng trả đúng câu
    *"daily free allocation"*. Hồ cạn THẬT.

    Chênh lệch 11 vs 52 có lời giải khác: nền comic vẽ ở **1344×768** (`flux-2` nhận
    `width`/`height`), còn con số 52 đo ở cỡ mặc định. Ảnh to hơn thì tốn nhiều neuron hơn —
    ~870 neuron/ảnh ở cỡ này, tức **một tài khoản ≈ 11 nền/ngày**. Con số ấy mới là con số để
    lập kế hoạch, và nó khác con số cũ **chín lần**.

    Bài học đúng vẫn là §13.15, chỉ khác chiều: em đi nghi bài kiểm khi thứ hỏng là **giả định
    về giá của một ảnh**. Trước khi đổ cho cơ chế, hãy đo lại chính đại lượng đang bất thường.
    """
    m = msg.lower()
    return "daily free allocation" in m or "10,000 neurons" in m


def _ban(msg: str) -> bool:
    """BẬN TẠM THỜI — cùng tài khoản dùng lại được sau vài chục giây."""
    m = msg.lower()
    return "capacity" in m or "429" in m or "rate limit" in m or "too many request" in m


# ══ GỌI GEMINI ═══════════════════════════════════════════════════════════════════════════════
# `quota_limit_value: "0"` + `quota_location: asia-east1` = Google KHÔNG phục vụ bậc free ở
# vùng này. Đó là câu trả lời "khoá này vô dụng Ở ĐÂY", không phải "khoá hỏng" — nên cho khoá
# nghỉ tới hết lượt chạy thay vì đánh dấu chết. §13.15: đừng kết luận hạ tầng của anh hỏng.
KHONG_VUNG = "quota_limit_value"


def _gemini(model: str, prompt: str, key: str, ar: str, tam: str):
    u = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
         f":generateContent?key={key}")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"],
                                 "imageConfig": {"aspectRatio": ar}}}
    p = subprocess.run(["curl", "-s", "--max-time", "180", "-H", "Content-Type: application/json",
                        "-H", "User-Agent: mm0-phim/1.0", "-o", tam,
                        "-d", json.dumps(body), u], capture_output=True, text=True)
    raw = open(tam, "rb").read() if os.path.exists(tam) else b""
    try:
        d = json.loads(raw)
    except Exception:
        return None, "phản hồi lạ"
    for c in d.get("candidates", []):
        for part in (c.get("content", {}) or {}).get("parts", []):
            b = part.get("inlineData") or part.get("inline_data")
            if b and b.get("data"):
                return base64.b64decode(b["data"]), ""
    e = json.dumps(d.get("error") or d)[:220]
    return None, e


# ══ CỔNG ẢNH ═════════════════════════════════════════════════════════════════════════════════
# Ba cổng, và cả ba đo thứ ĐÃ TỪNG hỏng thật, không đo thứ nghe có vẻ nên đo:
#   1 đúng ảnh và đúng khung  — SDXL trên CF từng trả về một tấm ĐEN THUI đúng cỡ
#   2 đủ sáng                 — ảnh dưới 60/255 đọc ra là một mảng đen trên điện thoại
#   3 đủ "có nội dung"        — đây là cổng MỚI, sinh ra từ đúng lời chê của anh
#
# Cổng 3 đo ĐỘ GIÀU: số ô màu khác nhau + độ lệch chuẩn độ sáng. Một khung "sơ sài" (một người
# đứng giữa nền be trơn) cho cả hai số rất thấp; một khung phim có bối cảnh thì không. Đây là
# phép đo NGƯỢC với `do_phang` của bộ cũ — bộ cũ THƯỞNG cho ảnh phẳng, và đó chính là lý do
# nó chọn ra những khung trống nhất.
# Sàn 52, không phải 62. Kênh dựng theo kỹ thuật `muc` (graphic-novel, chiaroscuro) và `ani`
# (một nguồn sáng gắt trên nền đen) cố ý tối — đo lượt dựng `realcost`: 16/36 ảnh bị cổng
# đánh trượt rồi vẽ lại, và nhìn tận mắt thì cả 16 đều ĐẸP và đúng chất kênh.
# Cổng đang phạt một QUYẾT ĐỊNH THIẾT KẾ như thể nó là lỗi (§16.1). Sàn tồn tại để chặn ảnh
# ra một mảng đen, không phải để ép mọi kênh sáng như nhau.
SAN_SANG = 52
SAN_GIAU = 0.055


def do_anh(duong: str) -> dict:
    from PIL import Image
    im = Image.open(duong).convert("RGB")
    w, h = im.size
    nho = im.resize((96, 96))
    px = list(nho.getdata())
    sang = [(r * 299 + g * 587 + b * 114) / 1000 for r, g, b in px]
    tb = sum(sang) / len(sang)
    do_lech = (sum((s - tb) ** 2 for s in sang) / len(sang)) ** 0.5
    o = len({(r >> 4, g >> 4, b >> 4) for r, g, b in px})     # 4096 ô màu tối đa
    return {"w": w, "h": h, "sang": tb, "lech": do_lech, "o": o,
            "giau": (o / 4096.0) * 0.5 + (do_lech / 128.0) * 0.5}


def _viet(raw: bytes, duong: str, co) -> str:
    """Ghi ảnh, ép đúng khung, trả "" nếu không phải ảnh dùng được."""
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return "không phải ảnh"
    W, H = co
    if abs(im.width / im.height - W / H) > 0.02:
        # Cắt giữa về đúng tỉ lệ. Chỉ xảy ra với tầng chót (schnell 1024²) và với ảnh
        # Gemini lệch vài pixel — nói ra để không im lặng mất 44% bề ngang như bộ cũ.
        r = W / H
        if im.width / im.height > r:
            nw = int(im.height * r)
            im = im.crop(((im.width - nw) // 2, 0, (im.width + nw) // 2, im.height))
        else:
            nh = int(im.width / r)
            im = im.crop((0, (im.height - nh) // 2, im.width, (im.height + nh) // 2))
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    im.save(duong, "JPEG", quality=92)
    return ""


# ══ SIẾT PROMPT KHI VẼ LẠI ═══════════════════════════════════════════════════════════════════
# §16.4 — một vòng thử lại phải ĐỔI ĐẦU VÀO. Bộ cũ gọi lại y hệt prompt và đo được 0,18 cả ba
# lần: ba lượt vẽ lại cho đúng một kết quả. Mỗi mức siết nhắm vào đúng cổng vừa trượt.
SIET = {
    "toi":  "Bright, well-exposed image with clear daylight or strong practical lights. ",
    "ngheo": ("A fully dressed set: furniture, props, background architecture, distant "
              "landscape layers and secondary characters all visible. "),
    "chu":  "Completely textless. Every sign, screen and label is blank. ",
}


def _fp(p: str) -> str:
    return hashlib.sha1(p.encode("utf-8")).hexdigest()[:16]


def _clamp(p: str, ma: str, i: int) -> str:
    if len(p) <= KY_TU_MAX:
        return p
    _DA_CAT.append((ma, i, len(p) - KY_TU_MAX))
    return p[:KY_TU_MAX].rsplit(". ", 1)[0] + "."


def ve(prompt: str, ma: str, idx: int, i: int, doc: bool = True,
       ks: dict = None, lan_toi_da: int = 3) -> str:
    """Vẽ MỘT cảnh. Trả đường tương đối trong `public/` hoặc "" nếu không vẽ được.

    Có sẵn trong cache (cùng vân tay prompt) thì trả ngay, không gọi mạng — nên chạy lại một
    tập đã dựng tốn 0 lượt. Đây là điều kiện để soi khung bằng mắt nhiều vòng mà không đốt hồ.
    """
    os.makedirs(THU, exist_ok=True)
    ks = ks or khoa()
    co = CO_DOC if doc else CO_NGANG
    ten = f"{ma}_{idx:04d}_{i:03d}_{_fp(prompt)}.jpg"
    dest = os.path.join(THU, ten)
    rel = "phim_nen/" + ten
    if os.path.exists(dest) and os.path.getsize(dest) > 8000:
        _ghi("dùng lại cache")
        return rel
    if not con_ngan_sach():
        _ghi("chạm trần ảnh của lượt chạy")
        return ""
    tam = dest + ".tmp"
    siet = ""
    for lan in range(1, lan_toi_da + 1):
        p = _clamp(siet + prompt, ma, i)
        raw, loi = None, "không còn nhà cung cấp nào"
        # ── TẦNG 1–3: CLOUDFLARE ────────────────────────────────────────────────────────
        # Model đã vẽ được ảnh đầu tiên của tập này đứng TRƯỚC — xem `_CHOT` ở docstring.
        _tang = [("@cf/black-forest-labs/flux-2-klein-9b", True, {}),
                 ("@cf/black-forest-labs/flux-2-klein-4b", True, {}),
                 ("@cf/black-forest-labs/flux-1-schnell", False, {"steps": 8})]
        # ── ĐẢO THANG CHO VIỆC RẺ TIỀN  (6/9/2026) ──────────────────────────────────────
        # Giá thật, tra tài liệu Cloudflare (không phải suy đoán) cho một ảnh 1344×768:
        #     flux-2-klein-9b  1.363 neuron cho megapixel ĐẦU TIÊN  ->    7 ảnh/tài khoản
        #     flux-1-schnell   4,8/tile + 9,6/bước                  ->  175 ảnh/tài khoản
        # Chênh **24 lần**. Thang trên đặt klein-9b đầu vì nó viết cho CẢNH PHIM v10 — có nhân
        # vật, có biểu cảm, chỗ chất lượng đáng tiền. Nền comic thì ngược hẳn: phòng phẳng,
        # không người, không chữ, lại bị nhân vật vector che một phần ba giữa khung.
        # Đúng §12.5 — lựa chọn đúng ở ngữ cảnh nó sinh ra, sai ở ngữ cảnh mới. Nên chỗ gọi
        # tự khai mình cần gì thay vì thừa hưởng mặc định của bộ khác.
        if os.environ.get("PHIM_MODEL_RE"):
            _tang.reverse()
        _ch = _CHOT.get((ma, idx))
        if _ch:
            _tang.sort(key=lambda t: 0 if t[0] == _ch else 1)
        for model, mp, extra in _tang:
            cfs = [c for c in ks["cf"] if _song(("cf", c[0]))]
            if not cfs:
                continue
            # Xoay theo BĂM của (kênh, nhịp) chứ không lấy phần tử đầu: 18 luồng chạy song song
            # trên Actions, lấy phần tử đầu là cả 18 cùng đâm vào một tài khoản.
            b = int(hashlib.sha1(f"{ma}{idx}{i}{lan}".encode()).hexdigest()[:8], 16)
            for j in range(min(8, len(cfs))):
                acc, tok = cfs[(b + j) % len(cfs)]
                body = {"prompt": p}
                if "flux-2" in model:
                    body["width"], body["height"] = co
                body.update(extra)
                raw, loi = _cf(model, body, acc, tok, mp, tam)
                if raw:
                    _CHOT.setdefault((ma, idx), model)
                    break
                if _het_han(loi):
                    # NGHỈ THEO TÀI KHOẢN, KHÔNG THEO (MODEL, TÀI KHOẢN). Đo dứt điểm 6/9:
                    # bơm cạn tài khoản 96 bằng klein-9b rồi gọi schnell VÀ klein-4b trên
                    # chính nó — cả hai đều trả *"used up your daily free allocation of
                    # 10.000 neurons"*. Tức 10.000 neuron là MỘT ngân sách chung cho mọi
                    # model, không phải mỗi model một ngân sách.
                    # Bản trước khoá theo (model, tài khoản) nên một tài khoản đã chết vẫn bị
                    # thử lại ở hai model sau: 3 vòng mạng phí cho mỗi tài khoản chết, mỗi
                    # ảnh. Với 97 tài khoản cạn dần trong ngày và 18 luồng chạy song song thì
                    # đó đúng cái bẫy §12.1 — hỏng CHẬM, nhìn từ ngoài y hệt "mạng chậm".
                    _cho(("cf", acc), NGHI_CAN)
                    _ghi("CF cạn hạn mức")
                    continue
                if _ban(loi):
                    _cho(("cf", acc), NGHI_BAN)
                    _ghi("CF bận (nghỉ ngắn)")
                    continue
                _ghi("CF lỗi: " + loi[:40])
            if raw:
                break
        # ── TẦNG 2: GEMINI (chỉ sống ở runner Mỹ) ───────────────────────────────────────
        if not raw:
            ar = "9:16" if doc else "16:9"
            for model in ("gemini-3.1-flash-image", "gemini-2.5-flash-image"):
                gs = [g for g in ks["gem"] if _song(("gem", g))]
                for g in gs[:10]:
                    raw, loi = _gemini(model, p, g, ar, tam)
                    if raw:
                        break
                    if KHONG_VUNG in loi or "RESOURCE_EXHAUSTED" in loi:
                        _cho(("gem", g), NGHI_CAN)
                        _ghi("Gemini không có hạn mức ở vùng này")
                        continue
                    _ghi("Gemini lỗi")
                if raw:
                    break
        if not raw:
            _ghi("không nhà cung cấp nào vẽ được")
            break
        e = _viet(raw, dest, co)
        if e:
            _ghi(e)
            continue
        d = do_anh(dest)
        if d["sang"] < SAN_SANG:
            os.remove(dest); siet = SIET["toi"]; _ghi("ảnh quá tối -> vẽ lại"); continue
        if d["giau"] < SAN_GIAU:
            os.remove(dest); siet = SIET["ngheo"]; _ghi("ảnh sơ sài -> vẽ lại"); continue
        for t in (tam,):
            if os.path.exists(t):
                os.remove(t)
        json.dump({"ve": prompt, "do": d}, io.open(dest + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False)
        _da_ve(1)
        return rel
    if os.path.exists(tam):
        os.remove(tam)
    return ""


# ══ VẼ NHIỀU CẢNH SONG SONG ══════════════════════════════════════════════════════════════════
# Anh: *"nếu chạy được đa luồng thì chạy đa luồng xử lý cho nhanh, tránh xung đột chồng chéo."*
#
# Vẽ ảnh là việc CHỜ MẠNG: một lượt FLUX.2 mất 6–12 giây và CPU gần như không làm gì. Chạy
# tuần tự 38 cảnh là 4–7 phút chờ; tám luồng đưa nó về dưới một phút.
#
# ── BA CHỖ CÓ THỂ CHỒNG CHÉO, VÀ CÁCH CHẶN TỪNG CHỖ ────────────────────────────────────────
#  1 HAI LUỒNG CÙNG BỐC MỘT TÀI KHOẢN CF -> tài khoản ấy nhận hai lượt cùng lúc và cả hai
#    cùng ăn 429. Chặn bằng cách CHIA HỒ: luồng w chỉ được nhìn thấy `cf[w::luong]`. Hai luồng
#    khác nhau nhìn hai tập tài khoản RỜI NHAU, nên va chạm không còn chỗ để xảy ra — khác hẳn
#    cách "xoay theo băm rồi hy vọng" mà bộ cũ dùng.
#  2 HAI LUỒNG CÙNG GHI MỘT TỆP -> không thể: tên tệp mang chỉ số nhịp và vân tay prompt.
#    Tệp tạm cũng vậy (`dest + ".tmp"`), nên mỗi luồng có tệp tạm riêng.
#  3 SỔ NGHỈ `_NGHI` VÀ SỔ ĐẾM `_LOG` DÙNG CHUNG -> chỉ có phép gán và cộng trên dict, mà cả
#    hai đều nguyên tử trong CPython. Mất một lượt đếm khi đua nhau là chấp nhận được; đây là
#    sổ báo cáo, không phải sổ chặn.
#
# KHÔNG chạy quá 8 luồng: quá đó thì các lượt gọi bắt đầu chờ nhau ở phía Cloudflare và tổng
# thời gian không giảm nữa, trong khi mỗi lượt hỏng lại tốn thêm một tài khoản.
LUONG_MAX = 8


def ve_nhieu(viec: list, ma: str, idx: int, doc: bool = True, ks: dict = None,
             luong: int = 6, bao=None) -> list:
    """`viec` = [(chỉ số nhịp, prompt)]. Trả danh sách đường ảnh theo ĐÚNG thứ tự đưa vào."""
    from concurrent.futures import ThreadPoolExecutor
    ks = ks or khoa()
    _nap_nghi()
    luong = max(1, min(LUONG_MAX, luong, len(viec) or 1))
    ra = [""] * len(viec)
    xong = [0]

    def chay(w: int):
        # Hồ RIÊNG của luồng này. Gemini không chia vì nó chỉ sống ở runner Mỹ và ở đó hạn mức
        # tính theo khoá chứ không theo tài khoản — chia thêm chỉ làm mỗi luồng ít khoá đi.
        rieng = {"cf": ks["cf"][w::luong] or ks["cf"], "gem": ks["gem"]}
        for j in range(w, len(viec), luong):
            i, p = viec[j]
            ra[j] = ve(p, ma, idx, i, doc, rieng)
            xong[0] += 1
            if bao:
                bao(xong[0], len(viec))

    with ThreadPoolExecutor(max_workers=luong) as ex:
        list(ex.map(chay, range(luong)))
    return ra
