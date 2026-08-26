"""
radar_dethai.py — RADAR ĐỀ TÀI cho 50 kênh thế hệ 2.

VÌ SAO CÓ TỆP NÀY. Đo thật ngày 26/8: kho đề tài của gen-2 là `KHO_XOAY`, chỉ **6-12 giá trị mỗi
trục** viết cứng trong `the_he_2.py`. Một bộ ăn 6 chương, nên kênh trục `nam` (6 năm) làm đúng
MỘT bộ là cạn kho. Đó là nút thắt sản lượng lớn nhất còn lại, lớn hơn cả tốc độ render.

`trend_scout.py` đã có và làm đúng cách an toàn (chỉ đọc tiêu đề công khai, không tải video), nhưng
kết quả của nó chỉ chảy vào nhánh viết bằng Gemini (`run_render.py:503`). 50 kênh gen-2 dựng từ dữ
liệu mở, không đi qua đó — nên xu hướng có mà kênh mới không dùng được.

RADAR NÀY LÀM GÌ:
  1. đọc tín hiệu NHU CẦU từ nguồn mở, 100% free, KHÔNG cần khoá:
       • Google Trends RSS (geo=US)        — người Mỹ đang tìm gì HÔM NAY
       • Wikimedia pageviews top (en)      — người ta thật sự ĐỌC gì (khác hẳn "tìm gì")
     Reddit đã thử và bị chặn khi gọi từ máy chủ lạ (403) — bỏ, không cắm khoá vào cho thêm việc.
  2. chấm điểm + khớp từ khoá với NICHE của từng kênh;
  3. ghi kết quả vào `tham_so["kho_" + truc]` của chính kênh đó.

Điểm mấu chốt của cách nối này: `_kho_xoay_cua()` VỐN ĐÃ ưu tiên kho riêng của kênh hơn `KHO_XOAY`
chung. Nên radar chỉ cần ghi đúng chỗ đó là toàn bộ khâu xoay đề tài, chống trùng, dựng bộ chạy y
nguyên — KHÔNG sửa một dòng nào trong đường render. Thêm đường mới vào một dây chuyền đang chạy là
cách nhanh nhất để làm hỏng nó.

KHÔNG LÀM: không tải video, không lấy phụ đề, không viết lại kịch bản của ai. Sự thật và công thức
thì không ai sở hữu; lời kể thì có, và 50 kênh cùng chạy một quy trình chép lời là đúng dấu hiệu
"reused content" mà YouTube dùng để đánh trượt duyệt kiếm tiền.

Chạy: python radar_dethai.py [--dry-run] [--kenh TEN]
"""
from __future__ import annotations
import io
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)

UA = {"User-Agent": "Mozilla/5.0 (compatible; MM0-radar/1.0; +https://mm0-auto-publisher.web.app)"}
TRAN_KHO = 24          # trần mỗi kho riêng: đủ 4 bộ (6 chương/bộ) mà không phình bản ghi kênh
# Trục nào NHẬN được từ khoá. Trục thời gian (`nam`, `ngay`, `tu_nam`, `tu_ngay`) không nhận:
# xu hướng không sinh ra năm mới, và nhét từ khoá vào trục năm là gửi rác xuống hàm dựng story.
TRUC_TU_KHOA = ("tu_khoa", "mon", "loc", "giong", "bangs", "mua")


def _tai(url: str, n: int = 400_000) -> bytes:
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30)
    return r.read(n)


def tin_hieu_trends() -> list[tuple[str, float]]:
    """Google Trends RSS (geo=US) -> [(từ khoá, điểm)]. Điểm = lượt tìm ước tính do Google công bố."""
    try:
        goc = ET.fromstring(_tai("https://trends.google.com/trending/rss?geo=US"))
    except Exception as e:
        print(f"   ⚠️ Trends lỗi: {str(e)[:80]}")
        return []
    ra = []
    for it in goc.iter("item"):
        ten = (it.findtext("title") or "").strip()
        if not ten:
            continue
        # `approx_traffic` nằm trong namespace ht: — lấy bằng đuôi thẻ để khỏi phụ thuộc URI.
        luot = 0.0
        for c in it:
            if c.tag.rsplit("}", 1)[-1] == "approx_traffic":
                luot = float(re.sub(r"[^\d]", "", c.text or "0") or 0)
        ra.append((ten, luot or 1000.0))
    return ra


def tin_hieu_wiki(lui: int = 2) -> list[tuple[str, float]]:
    """Wikimedia pageviews top (en) -> [(tên bài, lượt xem)].

    Khác Trends ở chỗ quan trọng: Trends là NGƯỜI TA GÕ GÌ, pageviews là NGƯỜI TA THẬT SỰ ĐỌC GÌ.
    Một từ khoá bùng lên rồi tắt trong ngày sẽ cao ở Trends mà thấp ở đây — thứ mình cần là loại
    còn sống được vài ngày, vì render + duyệt + đăng cũng mất chừng đó."""
    ng = datetime.now(timezone.utc) - timedelta(days=max(1, lui))
    u = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/"
         f"{ng.year}/{ng.month:02d}/{ng.day:02d}")
    try:
        d = json.loads(_tai(u))
    except Exception as e:
        print(f"   ⚠️ Wikimedia lỗi: {str(e)[:80]}")
        return []
    ra = []
    for a in (d.get("items") or [{}])[0].get("articles", []):
        ten = str(a.get("article") or "").replace("_", " ")
        # Trang điều hướng/tra cứu nội bộ không phải đề tài — loại thẳng, nếu không nó chiếm top.
        if not ten or ten.startswith(("Main Page", "Special:", "Wikipedia:", "Portal:")):
            continue
        ra.append((ten, float(a.get("views") or 0)))
    return ra[:200]


_BANG = ["Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware",
         "Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky",
         "Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi",
         "Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey","New Mexico",
         "New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania",
         "Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont",
         "Virginia","Washington","West Virginia","Wisconsin","Wyoming"]


def _lay_ten(rows) -> list:
    """Rút TÊN từ danh sách bản ghi của nguồn bất kỳ, thử lần lượt các khoá thường gặp.

    Mỗi nguồn trong `du_lieu_mo.py` đặt tên khoá theo cách riêng (`ten`, `giong`, `name`, `label`,
    `state`, `title`). Đoán một khoá rồi dùng cho mọi nguồn là cách sinh ra danh sách rỗng mà
    không có gì báo — đúng lỗi vừa mắc."""
    ra = []
    for r in (rows or []):
        if not isinstance(r, dict):
            continue
        for k in ("ten", "giong", "name", "label", "state", "title", "mon"):
            v = str(r.get(k) or "").strip()
            if len(v) > 1:
                ra.append(v)
                break
    return ra


def ung_vien(truc: str, kenh: dict, tin: list) -> list:
    """Danh sách đề tài ỨNG VIÊN cho một trục — lấy từ CHÍNH miền dữ liệu, không từ xu hướng.

    26/8 — bản radar đầu của em lấy ứng viên từ Google Trends + Wikipedia top, và anh nói đúng
    ngay: "tiêu đề quá chung chung, không sâu". Kết quả chạy thật tự tố cáo — nó nhả ra
    `File:WhatsApp.svg`, `Don't Say Good Luck`. Hai lỗi cùng lúc:
      • từ khoá xu hướng KHÔNG CÓ DỮ LIỆU đi kèm, mà engine gen-2 dựng video từ SỐ. Không số thì
        không có gì để vẽ, không có gì để hook.
      • xu hướng là thứ ai cũng thấy; bám vào đó là chạy đua với hàng nghìn kênh khác.

    Chiều sâu nằm ở chỗ ngược lại: 30+ nguồn mở anh đã nối SẴN có danh mục riêng của chúng — 50
    bang, danh sách giống chó, nhóm món, thể loại game, loại sản phẩm bị thu hồi. Đó vừa là kho
    đề tài lớn hơn nhiều lần, vừa **chắc chắn có số để dựng**."""
    import du_lieu_mo as D
    try:
        if truc == "bangs":
            return list(_BANG)
        # 26/8 — ĐỌC ĐÚNG KHOÁ, VÀ ĐỪNG ĐOÁN. Bản đầu em lấy `x["name"]` cho cả hai nguồn; đo thật
        # thì `giong_cho` trả khoá `giong`, `game_steam` trả khoá `ten`. Kết quả: 24 đề tài RỖNG
        # được nạp cho 3 kênh — và chúng lọt CẢ HAI cửa kiểm (xem `diem_nhu_cau`).
        if truc == "giong":
            return _lay_ten(D.giong_cho(60))
        if truc == "loc":
            return _lay_ten(D.game_steam(60))
        if truc == "mon":
            # nhóm món phổ biến ở Mỹ — miền hẹp mà sâu, mỗi món ra một bảng thành phần riêng
            return ["breakfast cereal", "instant noodles", "frozen pizza", "energy drink", "soda",
                    "protein bar", "peanut butter", "ice cream", "potato chips", "yogurt",
                    "canned soup", "hot dog", "salad dressing", "granola", "iced tea",
                    "chocolate bar", "cheese", "bacon", "orange juice", "bread"]
        if truc == "mua":
            return [f"{n}-{str(n + 1)[-2:]}" for n in range(2015, 2026)]
    except Exception as e:
        print(f"      ⚠️ không dựng được ứng viên trục `{truc}`: {str(e)[:70]}")
        return []
    # `tu_khoa`: miền quá rộng để liệt kê -> đây mới là chỗ tín hiệu xu hướng CÓ ÍCH, vì nó thu hẹp
    # miền. Nhưng vẫn phải qua bước kiểm chứng bên dưới, y như mọi ứng viên khác.
    mo = _tu(kenh.get("niche", "")) | _tu(kenh.get("goc_nhin", ""))
    ra = [t for t, _ in tin if (_tu(t) & mo) and not t.startswith(("File:", "Special:", "Portal:"))]
    return ra[:60]


def _do_lon(st: dict) -> float:
    """Số LỚN NHẤT trong story — dùng làm điểm hấp dẫn. Đề tài không có số nào thì không có hook."""
    lon = 0.0
    def _di(x):
        nonlocal lon
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            lon = max(lon, abs(float(x)))
        elif isinstance(x, str):
            for m in re.findall(r"\d[\d,\.]*", x):
                try: lon = max(lon, abs(float(m.replace(",", ""))))
                except Exception: pass
        elif isinstance(x, dict):
            for v in x.values(): _di(v)
        elif isinstance(x, list):
            for v in x[:12]: _di(v)
    _di(st)
    return lon


_GOI_Y_CACHE: dict = {}


def goi_y_yt(q: str) -> list:
    """Gợi ý tìm kiếm CỦA CHÍNH YOUTUBE cho một cụm — free, không khoá, không giới hạn thực tế.

    26/8 — anh chỉ ra chỗ radar còn thiếu: "phải phân tích keyword hay thị hiếu người dùng chứ
    không phải cứ có nội dung là làm". Đúng. Bản trước em mới chứng minh được đề tài CÓ DỮ LIỆU,
    chưa chứng minh CÓ NGƯỜI TÌM. Hai chuyện khác hẳn nhau, và làm video trúng vế đầu mà trượt vế
    sau thì vẫn không ai xem.

    Đây là nguồn nhu cầu đúng nhất cho YouTube, vì nó là **câu người ta gõ thật vào ô tìm kiếm của
    YouTube** — không phải suy đoán từ Google Trends (đo cả web, lệch hẳn hành vi xem video). Đo
    thật: `food recall` -> `food recalls this week`, `food recall 2025`; `why is texas` -> `why is
    texas so hot`, `why is texas so big`. Đó vừa là thang đo nhu cầu, vừa là kho câu hỏi để đặt
    tiêu đề và dòng hook bằng ĐÚNG chữ khán giả dùng."""
    import urllib.parse
    q = str(q or "").strip().lower()
    if not q:
        return []
    if q in _GOI_Y_CACHE:
        return _GOI_Y_CACHE[q]
    u = ("https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=en&gl=us&q="
         + urllib.parse.quote(q))
    try:
        d = json.loads(_tai(u, 200_000).decode("utf-8", "ignore"))
        ra = [str(x) for x in (d[1] if len(d) > 1 else []) if str(x).strip()]
    except Exception:
        ra = []
    _GOI_Y_CACHE[q] = ra
    return ra


def goc_kenh(kenh: dict) -> str:
    """GÓC của kênh, dạng một từ để ghép vào truy vấn gợi ý.

    26/8 — đo thật cho thấy hỏi DANH TỪ TRẦN là vô dụng: `breakfast cereal`, `salad dressing`,
    `granola` đều trả đúng 10 gợi ý, điểm phẳng lì, không phân biệt được gì. Ghép GÓC vào mới ra
    tín hiệu thật:
        peanut butter recall     8 gợi ý      salad dressing recall    4
        breakfast cereal recall  0 gợi ý      iced tea recall          0
    Tức người ta tìm "thu hồi bơ đậu phộng", không ai tìm "thu hồi ngũ cốc ăn sáng". Đó chính là
    thị hiếu, và nó chỉ hiện ra khi hỏi đúng góc.

    Tên kênh thường CHÍNH LÀ góc (`RECALL PLATE`, `SALARY TRUTH`, `BREED FILE`) nên lấy từ đó
    trước; không dùng được thì lùi về từ đặc trưng nhất trong mô tả niche."""
    bo = [w for w in _BO.sub(" ", str(kenh.get("ten") or "").lower()).split()
          if len(w) > 2 and w not in _RAC and w not in ("file", "plate", "truth", "say", "log")]
    if bo:
        return bo[0]
    for w in _BO.sub(" ", str(kenh.get("niche") or "").lower()).split():
        if len(w) > 3 and w not in _RAC:
            return w
    return ""


def diem_nhu_cau(cum: str, niche_tu: set, goc: str = "") -> tuple:
    """(điểm nhu cầu, các cụm tìm kiếm thật) cho một đề tài.

    Điểm gồm ba phần, cộng lại chứ không nhân: có gợi ý nào không (0/1 — quan trọng nhất, không có
    nghĩa là KHÔNG AI TÌM), số gợi ý, và số gợi ý dính tới niche của kênh (lọc trùng tên vô tình)."""
    # 26/8 — HAI CHỐT, ĐỀU RÚT TỪ MỘT LỖI ĐO ĐƯỢC.
    # Bản đầu ghép `f"{cum} {goc}"` rồi tin vào số gợi ý trả về. Khi `cum` là chuỗi rỗng (do đọc
    # sai khoá nguồn), truy vấn co lại còn đúng từ GÓC — `"steam"`, `"breed"` — và từ góc tự nó
    # bao giờ cũng có gợi ý. Thế là 24 đề tài rỗng đậu cửa nhu cầu với điểm cao.
    cum = str(cum or "").strip()
    if len(cum) < 2:
        return 0.0, []
    g = goi_y_yt(f"{cum} {goc}".strip() if goc else cum)
    if not g:
        return 0.0, []
    # Gợi ý phải nhắc tới CHÍNH ứng viên, không phải chỉ nhắc tới góc. Thiếu chốt này thì mọi ứng
    # viên của cùng một kênh đều được chấm ngang nhau bởi cùng một nhúm gợi ý về từ góc.
    tu_cum = _tu(cum)
    dung = [x for x in g if (_tu(x) & tu_cum)]
    if not dung:
        return 0.0, []
    hop = [x for x in dung if (_tu(x) & niche_tu)] or dung
    return 1.0 + len(dung) * 0.2 + len(hop) * 0.3, hop[:8]


def kiem_chung(kenh: dict, truc: str, uv: list, can: int, tran_thu: int = 40) -> list:
    """Dựng thử story cho từng ứng viên, CHỈ giữ cái ra được dữ liệu. Xếp theo số lớn nhất.

    Đây là điểm khác căn bản so với bản radar đầu: kho đề tài không phải danh sách chữ, mà là danh
    sách đã CHỨNG MINH dựng được video. Nạp một đề tài không có số vào kho nghĩa là hẹn một lượt
    render hỏng ở phiên sau — và lúc đó log chỉ ghi "nguồn thiếu dữ liệu", không ai lần ra là do
    radar nạp rác."""
    import the_he_2 as T
    import contextlib
    dung = T.DUNG_STORY.get(kenh.get("dinh_dang"))
    if not dung:
        return []
    ts = dict(kenh.get("tham_so") or {})
    ra = []
    for v in uv[:tran_thu]:
        if len(ra) >= can:
            break
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                st = dung(kenh, {**ts, truc: v})
        except Exception:
            continue
        if st and (st.get("items") or st.get("data") or st.get("pairs") or st.get("frames")):
            ra.append((v, _do_lon(st)))
    ra.sort(key=lambda x: -x[1])
    return [v for v, _ in ra]


_BO = re.compile(r"[^a-z0-9 ]+")
_RAC = {"the", "a", "an", "of", "and", "in", "on", "for", "to", "is", "are", "was", "were",
        "with", "by", "at", "from", "his", "her", "their", "s", "us", "usa", "new", "list"}


def _tu(s: str) -> set:
    return {w for w in _BO.sub(" ", str(s or "").lower()).split() if len(w) > 2 and w not in _RAC}


def khop_kenh(tin: list[tuple[str, float]], kenh: dict) -> list[tuple[str, float]]:
    """Chấm điểm từng tín hiệu theo mức khớp với NICHE của kênh.

    Khớp bằng từ chung giữa tín hiệu và mô tả niche/góc nhìn của kênh. Thô nhưng đúng việc: radar
    chỉ cần LOẠI thứ lạc đề, còn chọn cái nào trong số hợp đề là việc của hàm dựng story — nó mới
    biết nguồn dữ liệu có số cho từ khoá đó hay không."""
    mo = _tu(kenh.get("niche", "")) | _tu(kenh.get("goc_nhin", "")) | _tu(kenh.get("ten", ""))
    ra = []
    for ten, diem in tin:
        chung = _tu(ten) & mo
        if not chung:
            continue
        ra.append((ten, diem * (1 + len(chung))))
    ra.sort(key=lambda x: -x[1])
    return ra


def main() -> int:
    dry = "--dry-run" in sys.argv
    chi = None
    if "--kenh" in sys.argv:
        chi = sys.argv[sys.argv.index("--kenh") + 1]
    ks = json.load(io.open(os.path.join(GOC, "kenh_the_he_2.json"), encoding="utf-8"))
    ks = ks if isinstance(ks, list) else list(ks.values())

    print("🔭 RADAR ĐỀ TÀI — nguồn mở, không khoá, không tải video")
    tr = tin_hieu_trends()
    wi = tin_hieu_wiki()
    print(f"   Google Trends US : {len(tr)} từ khoá")
    print(f"   Wikimedia top    : {len(wi)} bài")
    if not (tr or wi):
        print("❌ không lấy được tín hiệu nào — bỏ lượt, KHÔNG ghi đè kho đang có")
        return 1
    # Trộn hai nguồn sau khi chuẩn hoá về cùng thang: cộng thẳng lượt tìm với lượt đọc là để nguồn
    # nào số to hơn thì nuốt nguồn kia, chứ không phải trộn.
    def _chuan(xs):
        m = max([d for _, d in xs] or [1]) or 1
        return [(t, d / m) for t, d in xs]
    tin = _chuan(tr) + _chuan(wi)

    ra, trong = {}, 0
    for k in ks:
        if chi and k.get("ten") != chi:
            continue
        truc = str((k.get("tham_so") or {}).get("xoay") or "")
        if truc not in TRUC_TU_KHOA:
            continue
        uv = ung_vien(truc, k, tin)
        if not uv:
            trong += 1
            continue
        kho = kiem_chung(k, truc, uv, TRAN_KHO * 2)
        # HAI CỬA, PHẢI QUA CẢ HAI. `kiem_chung` chứng minh đề tài CÓ SỐ để dựng; vòng dưới chứng
        # minh CÓ NGƯỜI TÌM. Qua cửa một mà trượt cửa hai là video đúng nhưng không ai xem — đúng
        # thứ anh cảnh báo: "cứ có nội dung là làm thành video thì không đánh trúng khán giả".
        goc = goc_kenh(k)
        nt = _tu(k.get("niche", "")) | _tu(k.get("goc_nhin", ""))
        cham, cum_tim = [], []
        for v in kho:
            d, cs = diem_nhu_cau(v, nt, goc)
            if d <= 0:
                continue                 # không gợi ý nào = không ai tìm -> loại thẳng
            cham.append((v, d))
            cum_tim += cs
        cham.sort(key=lambda x: -x[1])
        kho2 = [v for v, _ in cham][:TRAN_KHO]
        print(f"      {k['ten']:18s} [{truc}] {len(uv)} ứng viên -> {len(kho)} có DỮ LIỆU "
              f"-> {len(kho2)} có NGƯỜI TÌM (góc `{goc}`)")
        if not kho2:
            trong += 1
            continue
        ra[k["ten"]] = {"truc": truc, "kho": kho2,
                        "cum_tim": list(dict.fromkeys(cum_tim))[:12]}
    print(f"\n   kênh nhận được đề tài mới: {len(ra)} · không ra đề tài nào: {trong}")
    for ten, v in list(ra.items())[:10]:
        print(f"      {ten:18s} [{v['truc']}] {len(v['kho']):2d} đề tài · vd: {', '.join(v['kho'][:3])}")
    if dry:
        print("\n   ⚠️ --dry-run: KHÔNG ghi Firestore")
        return 0
    import firestore_bridge as FB
    owner = os.environ.get("OWNER_UID") or ""
    n = 0
    for ten, v in ra.items():
        # Ghi vào `tham_so["kho_" + truc]` — đúng chỗ `_kho_xoay_cua()` vốn đã ưu tiên hơn KHO_XOAY
        # chung. Nhờ vậy KHÔNG phải sửa một dòng nào trong đường render.
        # `cum_tim` = ĐÚNG CHỮ khán giả gõ vào YouTube -> dùng đặt tiêu đề và dòng hook, thay vì
        # câu do mình nghĩ ra. Đây là phần đắt nhất của radar, đừng vứt đi.
        FB.update_channel(owner, ten, {f"tham_so.kho_{v['truc']}": v["kho"],
                                       "tham_so.cum_tim": v.get("cum_tim", [])})
        n += 1
    print(f"\n✅ đã cập nhật kho đề tài cho {n} kênh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
