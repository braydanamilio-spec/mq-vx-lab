#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ẢNH BÌA + CHỮ ĐĂNG cho bộ PHIM v10.  (6/9/2026)

§10.3 của CLAUDE.md: bộ giao hàng của một tập là **ngắn · dài · ảnh bìa · `.tai.json`**.
Thiếu `.tai.json` là có video mà không đăng được — tức cả lượt render thành công vẫn ra số 0
ở đầu kia. Bộ v10 dựng xong video từ sáng và chưa có hai thứ này, nên nó chưa giao hàng được.

── HAI QUYẾT ĐỊNH, CẢ HAI ĐỀU LÀ ĐỂ KHÔNG TỐN LƯỢT AI NÀO ─────────────────────────────────
1. **Ảnh bìa lấy khung ở NHỊP HOOK**, không lấy ở 62% thời lượng. §13.27 đã trả giá: 62% đúng
   cho video dài (lúc biểu đồ đã cao) và SAI cho short (rơi trúng cú lật, lộ kết). Bộ này thì
   khác cả hai — nhịp 0 đã được đạo diễn ép thành *hình sai trái nhất tập*, tức nó vốn đã là
   khung được thiết kế để chặn ngón tay người xem. Ảnh bìa chính là khung ấy.
2. **Chữ đăng viết bằng CODE**, không gọi AI. Tiêu đề, con số, đơn vị, tên kênh đều đã nằm sẵn
   trong kịch bản — gọi AI là tiêu một lượt để lấy về đúng thứ đang cầm trong tay (§15.10, bộ
   thiên nhiên đã đi đường này).
"""
import io
import json
import os
import re
import subprocess

GOC = os.path.dirname(os.path.abspath(__file__))
RA = os.path.join(GOC, "out")

# Trần độ dài của từng nền tảng — có ĐƠN VỊ và có nguồn, không phải một con số nghe hợp lý.
# YouTube tiêu đề 100 ký tự (cắt hiển thị ~60 trên di động) · Instagram chú thích 2.200 ·
# Facebook không giới hạn thực tế nhưng 3 dòng đầu là thứ duy nhất hiện trước nút "xem thêm".
TRAN_TIEU_DE = 95

# Khuôn tiêu đề cho BẢN DÀI. Chỉ dùng khi `tieu` rơi về dạng tên-kênh (xem `viet_bai`). Mỗi
# khuôn là một CÂU HỎI về chủ thể — thứ người xem gõ vào ô tìm kiếm — và không khuôn nào chứa
# một con số, nên không khuôn nào có thể cấp một số sai.
_KHUON_TIEU = (
    "What actually happened to {x}?",
    "Why did {x} really collapse?",
    "What does nobody say about {x}?",
    "How did {x} run out of time?",
    "Which decision ended {x}?",
    "What went wrong at {x}?",
    "How did {x} actually end?",
    "Why does nobody talk about {x} any more?",
)
TRAN_IG = 2100

# Reels Instagram nhận tối đa 90 giây. Bản dài 7–11 phút KHÔNG lên được, và `dang_duoc` phải
# nói ra điều đó thay vì để khâu đăng tự phát hiện bằng một lượt tải lên hỏng.
IG_MAX_GIAY = 90


def _hoa_dau(s: str) -> str:
    s = (s or "").strip()
    return s[:1].upper() + s[1:] if s else s


def _the(ma: str, tieu: str, ten: str) -> list:
    """Thẻ: 3 thẻ thương hiệu + thẻ rút từ chính tiêu đề. Không nhồi thẻ rác — YouTube bỏ
    trọng số thẻ từ lâu, chúng chỉ còn dùng để bắt lỗi chính tả tên kênh."""
    goc = re.findall(r"[A-Za-z][A-Za-z'\-]{3,}", tieu.lower())
    bo = {"the", "and", "for", "with", "your", "that", "this", "what", "when", "does",
          "would", "really", "every", "much", "many", "from", "into", "over"}
    # ── BỎ DANH TỪ RỖNG  (đo 6/9/2026) ──────────────────────────────────────────────────
    # Phép cắt theo TỪ cho ra `#vehicle #surface #shield` từ tựa *"the reentry vehicle heat
    # shield surface"*. Chúng đúng ngữ pháp và vô dụng làm thẻ: không ai tìm `#surface`, và
    # chúng làm loãng ba thẻ thật. Danh sách này là danh từ CHUNG — thứ luôn xuất hiện vì
    # khuôn câu, chưa bao giờ mang chủ đề (cùng nguyên tắc "từ mà khuôn bắt phải có thì không
    # mang bản sắc" đã trả giá ba lần ở `bang_van.py`).
    bo |= {"vehicle", "surface", "thing", "things", "stuff", "part", "parts", "kind",
           "type", "amount", "number", "level", "size", "area", "unit", "value", "piece"}
    # ── VÀ CHỮ CỦA CHÍNH KHUÔN TIÊU ĐỀ  (8/9/2026) ──────────────────────────────────────
    # Thẻ nay rút từ tiêu đề đã sửa, mà tiêu đề bản dài dựng từ `_KHUON_TIEU`. Tám khuôn ấy
    # dùng chung một bộ chữ (`actually` · `happened` · `collapse` · `nobody`…), nên chúng sẽ
    # là thẻ của MỌI tập — đúng thứ §13.4 dạy phải cắt trước khi đo: phần giống nhau vì tay
    # nghề chung thì không mang bản sắc. Chỉ chủ thể mới đáng làm thẻ.
    bo |= {"actually", "happened", "really", "collapse", "collapsed", "nobody", "anymore",
           "decision", "ended", "wrong", "talk", "talks", "more", "does", "did", "run",
           "which", "about", "went", "time", "say"}
    rieng = [w for w in dict.fromkeys(goc) if w not in bo][:8]
    return [ten.lower().replace(" ", ""), ma, "explained"] + rieng


_NEN_KENH: dict = {}


def _co_nen(ma: str, nen: str) -> bool:
    """Kênh `ma` đã nối nền tảng `nen` chưa — đọc thẳng `config/channels.yaml`.

    Không tìm thấy tệp thì trả True cho `youtube` và False cho hai nền còn lại: đó là hiện
    trạng đo được, và đoán "có" cho một nền chưa nối là đúng cái lỗi hàm này sinh ra để chữa.
    """
    if not _NEN_KENH:
        import yaml as _y, io as _io, os as _o
        _NEN_KENH["_"] = {}
        for _p in (_o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))),
                                "MM0-AutoPublisher", "config", "channels.yaml"),
                   _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))),
                                "_autopublisher", "config", "channels.yaml")):
            try:
                _d = _y.safe_load(_io.open(_p, encoding="utf-8")) or {}
            except Exception:
                continue
            _ks = _d.get("channels") or _d
            _it = _ks.items() if isinstance(_ks, dict) else [(x.get("display_name"), x) for x in _ks]
            for _k, _v in _it:
                _NEN_KENH[str(_k).upper()] = {
                    n: bool((_v.get(n) or {}) and any((_v.get(n) or {}).values()))
                    for n in ("youtube", "facebook", "instagram")}
            break
    h = _NEN_KENH.get(str(ma).upper())
    return bool(h[nen]) if h else (nen == "youtube")


def _chu_the_tu_nhip(nhip: list) -> str:
    """Suy CHỦ THỂ từ lời thoại — lưới an toàn khi đường gọi không truyền `chu_the`.

    Chữ hoa ĐẦU CÂU là ngữ pháp, không phải tên riêng (§13.9), nên phải bỏ trước khi đếm.
    Nhưng bỏ thẳng thì mất luôn chữ đầu của một tên riêng thật: bản đầu cho «Suisse» thay vì
    «Credit Suisse», vì «Credit» đứng đầu một câu. Luật đúng hẹp hơn và không cần danh sách
    ngoại lệ nào: **chỉ bỏ khi chính chữ ấy còn xuất hiện VIẾT THƯỜNG ở chỗ khác** — một tên
    riêng thật thì không bao giờ viết thường. Đo trên 6 tập đã biết đáp án: 4/6 -> 6/6."""
    txt = " ".join(str(n.get("nar") or n.get("loi") or n.get("cua") or "") for n in (nhip or []))
    if not txt.strip():
        return ""
    thuong = set(re.findall(r"\b[a-z]{2,}\b", txt))
    bo = {m.group(1) for m in re.finditer(r"(?:^|(?<=[.!?])\s+)([A-Z][a-z]+)", txt)
          if m.group(1).lower() in thuong}
    dem: dict = {}
    for g in re.findall(r"\b[A-Z][A-Za-z&.\-]+(?:\s+[A-Z][A-Za-z&.\-]+){0,2}", txt):
        w = g.split()
        while w and w[0] in bo:
            w = w[1:]
        if not w:
            continue
        k = " ".join(w)
        if len(k) >= 3:
            dem[k] = dem.get(k, 0) + 1
    if not dem:
        return ""
    top = sorted(dem.items(), key=lambda x: -x[1])[:10]
    m = top[0][1]
    uu = [g for g, n in top if n >= m * 0.6]
    return max(uu, key=lambda g: (len(g.split()), dem[g]))


def viet_bai(ma: str, ten: str, tieu: str, hook: str, hook_phu: str,
             dai_giay: float, long: bool, nhip: list, chu_the: str = "", slug_tap: str = "") -> dict:
    """Ba bộ chữ RIÊNG cho ba nền tảng — không phải một bộ dùng chung.

    Ba nền tảng đọc ba kiểu: YouTube đọc tiêu đề như một câu hỏi tìm kiếm, Facebook đọc ba
    dòng đầu như một status, Instagram đọc chú thích như một lời thoại. Dùng chung một bộ chữ
    là chấp nhận sai ở hai trong ba chỗ."""
    so = ""
    for n in nhip:
        l = n.get("lop") or {}
        if l.get("k") == "so":
            so = (str(l.get("so", "")) + " " + str(l.get("don", ""))).strip()
            break
    so = so or hook_phu or ""

    # ── TIÊU ĐỀ: BA LỖI ĐO ĐƯỢC TRÊN 140 TỆP ĐÃ GIAO  (8/9/2026) ────────────────────────
    # 1. `tieu` của BẢN DÀI là chuỗi «<tên kênh> — N answers» (`giai_thich` dựng thế), nên mọi
    #    bản dài ra cùng một tiêu đề: đo được 43/140 tệp trùng nhau, mới nhất là hôm nay. Tiêu
    #    đề trùng giữa các tập đúng là trục §13.17 nêu tên, và nó nói với người xem đúng con số
    #    KHÔNG: «The Rules Nobody Reads — 1 answers?» (còn sai cả số nhiều).
    # 2. `so` nối vào không kèm ĐƠN VỊ: «(300)» · «(1.2)». Một con số trần trong ngoặc không
    #    nói gì — §14.16, ràng buộc "phải có số" bị thoả bằng cách rẻ nhất.
    # 3. cắt `[:TRAN_TIEU_DE]` giữa TỪ: «…to fund the development of S».
    #
    # Chủ thể luôn có và luôn khác nhau giữa các tập, nên nó là vật liệu chắc chắn nhất. Khuôn
    # câu xoay theo băm của (chủ thể, kênh) — băm TƯỜNG MINH, không dùng `hash()` (§13.13).
    tde = _hoa_dau(tieu)
    _ten_kenh = (ten or "").strip().lower()
    _la_ten_kenh = bool(_ten_kenh) and (tde.lower().startswith(_ten_kenh)
                                        or re.search(r"—\s*\d+\s+answers?$", tde.strip(), re.I))
    chu_the = (chu_the or "").strip() or _chu_the_tu_nhip(nhip)
    if _la_ten_kenh and chu_the:
        # Chỉ số khuôn chạy theo SỐ THỨ TỰ TẬP, không theo băm của chủ thể: cùng một chủ
        # thể đi qua nhiều khuôn hỏi là ĐÚNG thiết kế (§19.6), nhưng hai tập KHÔNG được mang
        # cùng một tiêu đề. Băm theo chủ thể thì hai tập cùng chủ thể luôn ra cùng khuôn; đo
        # trên 14 tập mẫu (một chủ thể lặp 3 lần) thì băm cho 13/14 tiêu đề riêng, còn bước
        # theo số thứ tự cho 14/14 — vì hai số liền nhau không bao giờ cùng dư.
        _n = re.findall(r"\d+", slug_tap or "")
        _k = int(_n[-1]) if _n else sum(ord(c) * (i + 1) for i, c in enumerate(chu_the + ma))
        tde = _KHUON_TIEU[_k % len(_KHUON_TIEU)].format(x=chu_the.strip())
    yt = (f"{tde}?" if not tde.endswith("?") else tde)
    # số chỉ đáng nối khi nó mang ĐƠN VỊ — «(25 billion)» nói được, «(300)» thì không
    if so and re.search(r"[a-zA-Z]", so) and len(yt) + len(so) + 3 <= TRAN_TIEU_DE:
        yt = f"{yt} ({so})"
    if len(yt) > TRAN_TIEU_DE:                      # cắt theo TỪ, không giữa từ
        yt = yt[:TRAN_TIEU_DE].rsplit(" ", 1)[0].rstrip(" ,;:—-") + "?"

    cau = [str(n.get("cua") or n.get("loi") or "").strip() for n in nhip]
    mo = " ".join(cau[:3])[:180]
    het = " ".join(cau[-2:])[:160]

    # ── `#Shorts` LÀ THỨ PHÂN LOẠI VIDEO, KHÔNG PHẢI MỘT THẺ TRANG TRÍ  (6/9/2026) ───────
    # Video dọc dưới 3 phút chỉ vào kệ Shorts của YouTube khi được nhận ra là Shorts, và thẻ
    # `#Shorts` trong MÔ TẢ là đường nhận ra ấy. Thiếu nó thì clip 38 giây nằm chung kệ với
    # video dài — đúng chỗ nó thua mọi thứ khác. Đây là một dòng chữ, không tốn gì, và bỏ quên
    # nó là bỏ toàn bộ nguồn xem lớn nhất của định dạng này.
    # YouTube hiện BA hashtag đầu ngay trên tiêu đề, nên ba thẻ ấy phải là ba thẻ đáng hiện.
    _sh = " #Shorts" if not long and dai_giay <= 180 else ""
    mo_ta = (f"{mo}\n\n{tde}. {('The answer: ' + so + '.') if so else ''}\n\n"
             f"Every number in this video is calculated, not guessed.\n\n"
             f"#{ten.lower().replace(' ', '')} #{ma} #explained{_sh}")
    # ══ HỢP ĐỒNG VỚI `day_kho.py` — ĐỌC MÃ CỦA NÓ, ĐỪNG ĐOÁN  (6/9/2026) ═════════════════
    # Bản đầu của hàm này viết `youtube.tieu_de` · `loai` không có · `dang_duoc` là DANH SÁCH.
    # Đọc `day_kho.py` thì nó lấy `yt.get("title")`, `d.get("loai")`, và duyệt `dang_duoc`
    # bằng `.items()` — tức một DICT. Ba chỗ lệch, và cả ba đều hỏng CÂM: video vẫn được nhặt,
    # vẫn đẩy đi, chỉ là tiêu đề rỗng và không nền tảng nào được bật.
    # Đúng §15.5 — *đọc client cũ trước khi viết client mới*; chú thích trong nó là những lần
    # đã trả giá. Giữ cả tên tiếng Việt lẫn tên hợp đồng: tên Việt để đọc, tên Anh để chạy.
    nen = ["youtube", "facebook"] + (["instagram"] if dai_giay <= IG_MAX_GIAY else [])
    # Thẻ rút từ TIÊU ĐỀ ĐÃ SỬA, không từ `tieu` gốc. Bản trước dùng `tieu`, mà `tieu` của
    # bản dài là tên kênh — nên thẻ ra «rules · nobody · reads · answers»: bốn chữ của chính
    # tên kênh, không chữ nào nói về nội dung. Cùng một gốc với lỗi tiêu đề, ở nhánh song song.
    the = _the(ma, yt, ten)
    return {
        "ma": ma, "kenh": ma, "ten": ten, "dai": round(dai_giay, 1),
        "loai": "long" if long else "short", "long": bool(long),
        "thumbnail": "",                       # `day_kho` tự lùi về `<slug>.jpg` nếu rỗng
        "youtube": {"title": yt, "description": mo_ta, "tags": the,
                    "tieu_de": yt, "mo_ta": mo_ta, "the": the},
        # Facebook cũng nhận hashtag, và ba thẻ là mức trang fanpage dùng — nhiều hơn đọc ra
        # là spam, không có thì bài không vào được luồng chủ đề nào.
        "facebook": {"noi_dung": f"{mo}\n\n{tde}{'' if tde.endswith('?') else '?'} "
                                 f"{('→ ' + so) if so else ''}\n\n{het}\n\n"
                                 + " ".join("#" + t for t in the[:3])},
        # Instagram: hashtag nằm TRONG chú thích, không phải một trường riêng — khâu đăng chỉ
        # gửi `chu_thich`, nên thẻ để ở `the` mà không ghép vào là thẻ không bao giờ tới nơi
        # (§15.12: một trường chỉ được ghi mà không được đọc là chưa tồn tại).
        "instagram": {"chu_thich": (f"{tde}{'' if tde.endswith('?') else '?'} "
                                    f"{so}\n\n{mo}\n\n"
                                    + " ".join("#" + t for t in the))[:TRAN_IG],
                      "the": the},
        # DICT, không phải danh sách: `day_kho` duyệt bằng `.items()` và lọc theo giá trị.
        # Nói RA nền tảng nào nhận được, thay vì để khâu đăng phát hiện bằng một lượt hỏng.
        # ── MỘT NỀN TẢNG "NHẬN ĐƯỢC" KHI CẢ HAI ĐIỀU KIỆN CÙNG ĐÚNG  (7/9/2026) ──────────
        # Bản trước ghi cứng `facebook: True` và chỉ xét ĐỘ DÀI cho Instagram — tức mã hoá
        # đúng MỘT trong hai ràng buộc (§17.2). Ràng buộc còn lại là: KÊNH CÓ NỐI nền tảng
        # ấy chưa. Đo `config/channels.yaml`: youtube 18/18, facebook **0/18**,
        # instagram **0/18**. Nên mọi video đang được đẩy kèm `--platforms
        # youtube,facebook,instagram` sang hai nền tảng không kênh nào đăng nổi.
        #
        # Hại không phải "một dòng thừa": mỗi dòng ấy là một lượt ĐỌC + một lượt GHI Firestore
        # ở mỗi lượt `publish_social` (12 lượt/ngày) chỉ để đánh dấu "Page chưa kết nối".
        # Chú thích ngay trên đã nói đúng ý định — *"nói RA nền tảng nào nhận được, thay vì
        # để khâu đăng phát hiện bằng một lượt hỏng"* — mã chỉ làm được một nửa.
        #
        # Đọc `channels.yaml` chứ không khai bảng thứ hai (§13.5): thêm khoá FB/IG vào tệp ấy
        # là hai nền tảng tự bật, không phải sửa mã.
        "dang_duoc": {"youtube": _co_nen(ma, "youtube"),
                      "facebook": _co_nen(ma, "facebook"),
                      "instagram": _co_nen(ma, "instagram") and dai_giay <= IG_MAX_GIAY},
        "dang_duoc_ds": nen,
    }


def moc_bia(nhip: list, mac_dinh: float = 0.9) -> float:
    """Giây nên trích ảnh bìa: 70% NHỊP ĐẦU, không phải một mốc cố định.

    ── VÌ SAO KHÔNG DÙNG HẰNG SỐ  (đo 6/9/2026) ────────────────────────────────────────────
    Con số trên bảng ĐẾM LÊN từ 0 và chỉ tới giá trị thật ở khoảng nửa nhịp. Đo tập
    `v11_howhot_0040`: nhịp đầu dài **4,18 giây**, số đếm xong ở **2,09 giây** — mà `lam_bia`
    trích ở **0,9 giây**. Ảnh bìa của tập ấy tình cờ vẫn ra số đủ, nhưng đó là MAY: nhịp đầu
    dài ngắn theo lời thoại (đo 9 nhịp: 1,8–7,9 giây), nên cùng hằng số ấy sẽ rơi vào giữa cú
    đếm ở những tập có nhịp đầu dài hơn — và ảnh bìa hiện một con số SAI, thứ tệ nhất một ảnh
    bìa có thể làm với kênh sống bằng con số.
    Một hằng đúng nhờ may là một hằng đang chờ để sai (§13.7). Mốc phải suy từ chính nhịp.
    70%: sau cú đếm (50%) một khoảng an toàn, và trước khi nhịp kết thúc."""
    try:
        n0 = (nhip or [])[0]
        s0, e0 = float(n0.get("s", 0)), float(n0.get("e", 0))
        if e0 > s0:
            return round(s0 + (e0 - s0) * 0.70, 2)
    except Exception:
        pass
    return mac_dinh


def lam_bia(mp4: str, ra_jpg: str, giay: float = 0.9) -> bool:
    """Ảnh bìa = khung ở NHỊP HOOK. Không vẽ chữ đè lên.

    §16.3 đã trả giá ba vòng cho việc đặt chữ hook lên ảnh bìa: cả ba lần đều đè lên đồ hoạ,
    và câu hỏi đúng ở vòng thứ ba không còn là *"đặt chữ ở đâu"* mà là *"có cần lớp chữ thứ
    hai không"*. Khung hook của bộ này ĐÃ mang con số bằng lớp dữ liệu, nên không cần."""
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{giay:.2f}", "-i", mp4,
                        "-frames:v", "1", "-q:v", "2", ra_jpg], capture_output=True, text=True)
    if r.returncode or not os.path.exists(ra_jpg) or os.path.getsize(ra_jpg) < 8000:
        print(f"   ⚠ ảnh bìa hỏng: {r.stderr[:90]}")
        return False
    return True


def giao_hang(slug: str, mp4: str, ma: str, ten: str, tieu: str, hook: str, hook_phu: str,
              dai_giay: float, long: bool, nhip: list, chu_the: str = "") -> dict:
    """Sinh ảnh bìa + `.tai.json`. Trả sổ những gì THẬT SỰ có trên đĩa.

    §15.3 — bước nào có sản phẩm đầu ra thì cổng của nó phải kiểm SẢN PHẨM, không kiểm mã
    thoát. Nên hàm này `os.path.exists` từng tệp thay vì tin vào việc mình vừa gọi hàm ghi."""
    os.makedirs(RA, exist_ok=True)
    jpg = os.path.join(RA, f"{slug}.jpg")
    tai = os.path.join(RA, f"{slug}.tai.json")
    lam_bia(mp4, jpg, moc_bia(nhip))
    d = viet_bai(ma, ten, tieu, hook, hook_phu, dai_giay, long, nhip, chu_the, slug)
    json.dump(d, io.open(tai, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    co = {"mp4": os.path.exists(mp4), "jpg": os.path.exists(jpg),
          "tai": os.path.exists(tai)}
    thieu = [k for k, v in co.items() if not v]
    if thieu:
        print(f"   ❌ bộ giao hàng THIẾU: {', '.join(thieu)}")
    return co
