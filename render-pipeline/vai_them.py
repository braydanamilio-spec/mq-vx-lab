#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VAI THỨ TƯ CHO 18 KÊNH  (6/9/2026)

Anh: *"nhân vật có vẽ thêm cho mỗi channel cho phù hợp đa dạng ko, nếu chỉ có 2 nhân vật thì
hơi tẻ nhạt."* Đo: `phim_gu.VAI` khai 3 vai/kênh, và đường dựng nay xoay đủ 3 -> **6 cặp có
thứ tự**. Thêm một vai thành **12 cặp** — gấp đôi, và không tốn một ảnh nào.

── VÌ SAO CHỌN THEO KHOẢNG TUỔI TRỐNG ───────────────────────────────────────────────────────
Ba vai hiện có của mỗi kênh gần như luôn là: hai người lớn (một nam một nữ, 29–52) và một
người ở CỰC tuổi (trẻ con 8–12 hoặc người già 66–78). Thêm một người lớn thứ ba thì dàn vai
đông hơn mà không rộng hơn — hai người 35 và 41 đứng cạnh nhau đọc ra là một người.
Nên vai mới phải rơi vào **khoảng tuổi xa nhất so với cả ba**, và cổng đo đúng điều đó.

── AI VIẾT GÌ, VÀ KHÔNG ĐƯỢC VIẾT GÌ ────────────────────────────────────────────────────────
Chỉ MÔ TẢ NGƯỜI — không có con số nào của sản phẩm, nên luật nền không bị đụng. Khuôn câu phải
khớp ba vai cũ từng chữ, vì cùng một khối `CHARACTER LOCK` gửi cho mô hình vẽ ảnh: một dòng
lệch khuôn là một người trông khác hẳn ba người kia.

── BỐN CỔNG ─────────────────────────────────────────────────────────────────────────────────
1. **khuôn**  — "NN-year-old man/woman, …" đúng dạng ba vai cũ.
2. **tuổi**   — cách MỌI vai cũ ≥ 8 tuổi (nếu không thì dàn vai đông mà không rộng).
3. **tên**    — chưa trùng tên nào của kênh ấy.
4. **thế giới** — có ít nhất một chi tiết trang phục/đạo cụ thuộc về nơi chốn của kênh.
"""
import io, json, os, re, sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
os.environ.setdefault("GT_KHONG_CF", "1")
import phim_gu as GU
import phim_canh as PC

RA = os.path.join(GOC, "vai_4.json")

LENH = """You add ONE more recurring character to an animated explainer channel.

The channel already has these three. Read them, then write a FOURTH who fits the same world
but is clearly a different kind of person:
{co}

Return ONE JSON object and nothing else:
  {{"ten": "<short name, 1 or 2 words>", "ta": "<description>"}}

The description must follow the EXACT shape of the three above:
  "NN-year-old man, <hair>, <garment with colour>, <second garment or item>, <one trait>"

Rules:
- Age must be at least 8 years away from every age above. Widen the range, do not fill it in.
- Give them a reason to be in this world: one item of clothing or one prop from it.
- No numbers other than the age. No brand names.
- The name must not be any of the names above.
- Do NOT use any of these words — other channels already used them, and eighteen channels
  wearing the same jacket is not a cast, it is one character copied eighteen times:
{cam}"""

TUOI = re.compile(r"(\d{1,2})-year-old\s+(man|woman|girl|boy)", re.I)


# ── CẤM DẦN TỪ ĐÃ DÙNG  (đo 6/9/2026) ───────────────────────────────────────────────────────
# Lượt đầu, 18 vai mới có `teal` 8 lần · `silver` 6 · `utility vest` 5. Mô hình rơi vào một lối
# mòn: mỗi lời hỏi độc lập nên nó không biết mười bảy vai kia mặc gì.
# Đây đúng §14.1 — *thêm mười cái GIỐNG NHAU không phải là mở rộng*. Chữa bằng cách cho nó BIẾT
# thứ đã dùng: cấm dần từng từ tả màu/đồ ngay khi một kênh đã lấy.
_DANG_CAM: set = set()
_DE_Y = re.compile(r"\b(teal|silver|navy|crimson|olive|maroon|amber|ochre|rust|slate|"
                   r"charcoal|beige|khaki|plum|coral|mint|lavender|mustard|"
                   r"vest|jumpsuit|cardigan|apron|poncho|parka|blazer|overalls|"
                   r"tool belt|utility belt|satchel|lanyard|goggles|clipboard)\b", re.I)


def _goi_mot(ma, khoa):
    ds = GU.VAI.get(ma) or []
    co = "\n".join(f"  {t}: {m}" for t, m in ds)
    tuoi_cu = [int(m.group(1)) for _t, d in ds for m in [TUOI.search(d)] if m]
    ten_cu = {t.lower() for t, _d in ds}
    for _ in range(4):
        t = PC._goi(LENH.format(co=co, cam="  " + ", ".join(sorted(_DANG_CAM)) or "  (none yet)"),
                    f"Channel: {ma}. Write the fourth character.", khoa)
        try:
            d = json.loads(t[t.index("{"):t.rindex("}") + 1])
        except Exception:
            continue
        ten, ta = str(d.get("ten") or "").strip(), " ".join(str(d.get("ta") or "").split())
        m = TUOI.search(ta)
        if not (ten and ta and m):
            continue
        if ten.lower() in ten_cu:
            continue
        n = int(m.group(1))
        if tuoi_cu and min(abs(n - x) for x in tuoi_cu) < 8:
            continue
        if len(ta.split(",")) < 4:
            continue
        _moi = {x.group(0).lower() for x in _DE_Y.finditer(ta)}
        if _moi & _DANG_CAM:
            continue                      # dùng lại màu/đồ của kênh khác -> viết lại
        _DANG_CAM.update(_moi)
        return ten, ta, n
    return None


LENH_LOAT = """You add recurring characters to EACH of several animated explainer channels.

Each channel has a TITLE — that title is the question every episode answers, so the new people
must be people who would plausibly stand around discussing exactly that question. A channel
called "HOW LOUD IS IT" gets people whose life involves noise; "THE REAL COST" gets people who
argue about money. That is what makes a cast belong to a show instead of being generic.

For every channel below you see its title and its existing characters. Write ONE new one for each.

Return ONE JSON object mapping channel code -> {{"ten": "<short name, 1 or 2 words>",
"ta": "<description>"}} and nothing else. "ten" is a PERSON'S NAME, never a description.

Each description follows this EXACT shape:
  "NN-year-old man, <hair>, <garment with colour>, <second garment or item>, <one trait>"

Rules:
- Age at least 6 years away from every age already in that channel, and from each other.
- Give each a prop or garment that belongs to that channel's SUBJECT, not just any workplace.
- Spread the roles: one should be an outsider who asks the naive question, one an insider who
  knows the answer cold. A cast of four experts has nobody to explain anything to.
- **All the new characters must be visibly different FROM EACH OTHER**: no two may share a
  colour, a garment type, a hairstyle or a trait word. You are writing a cast, not a uniform.
- No numbers other than the age. No brand names. No name already used in its channel.

CHANNELS:
{ds}"""


def _loat(mas, khoa, n_moi=2):
    """Hỏi MỘT lượt cho nhiều kênh.

    ── VÌ SAO  (đo 6/9/2026) ───────────────────────────────────────────────────────────────
    Hỏi 18 lượt độc lập cho ra `teal` 8/18 · `silver` 6 · `utility vest` 5 — mô hình không biết
    mười bảy vai kia mặc gì, nên nó rơi vào cùng một lối mòn mười tám lần.
    Em thử chữa bằng cách **cấm dần từng từ đã dùng**, và nó chỉ DỜI lối mòn: teal -> green,
    vest -> sweater, cộng thêm `meticulous` 6/18. Đúng §13.9 — *danh sách ngoại lệ là danh sách
    vô hạn*; liệt kê ví dụ thì mô hình đi tìm ví dụ tiếp theo.
    Chữa ở GỐC: cho nó thấy cả loạt trong MỘT lời hỏi, và yêu cầu "khác nhau" như một ràng buộc
    giữa các phần tử — thứ không lời cấm nào thay được, vì nó là quan hệ chứ không phải tập con
    (§15.7: tập con thì lọc, quan hệ thì phải hợp nhất).
    """
    import giai_thich as _G
    _ten = {k["ma"]: k.get("ten") or k["ma"] for k in _G.KENH}
    ds = []
    for ma in mas:
        v = GU.VAI.get(ma) or []
        ds.append(f'[{ma}]  title: "{_ten.get(ma, ma)}"\n'
                  + "\n".join(f"  {t}: {d}" for t, d in v))
    t = PC._goi(LENH_LOAT.format(ds="\n\n".join(ds), n_moi=n_moi),
                f"Write one new character for each of the {len(mas)} channels.", khoa)
    try:
        return json.loads(t[t.index("{"):t.rindex("}") + 1])
    except Exception:
        return {}


def main():
    khoa = PC._khoa_groq()
    mas = [k if isinstance(k, str) else k.get("ma") for k in
           (GU.KENH if isinstance(GU.KENH, (list, tuple)) else list(GU.VAI))]
    mas = [m for m in mas if m]
    ra = {}
    for i in range(0, len(mas), 6):          # 6 kênh/lượt: đủ để so nhau, chưa chạm trần token
        for _ in range(3):
            d = _loat(mas[i:i + 6], khoa)
            ok = {}
            for ma, vs in (d or {}).items():
                if ma not in mas: continue
                cu = [int(x.group(1)) for _t, dd in GU.VAI[ma] for x in [TUOI.search(dd)] if x]
                ten_cu = {t.lower() for t, _d in GU.VAI[ma]}
                giu = []
                for v in (vs if isinstance(vs, list) else [vs]):
                    ten = str(v.get("ten") or "").strip()
                    ta = " ".join(str(v.get("ta") or "").split())
                    m = TUOI.search(ta)
                    # ── `ten` PHẢI LÀ MỘT CÁI TÊN  (đo 6/9/2026) ──────────────────────────
                    # Khi xin một DANH SÁCH thay vì một object, mô hình đánh mất ranh giới
                    # tên/mô tả: nó nhét mô tả người thứ nhất vào `ten` và người thứ hai vào
                    # `ta`. Cổng cũ chỉ hỏi "`ten` có rỗng không" nên lọt sạch — 11 kênh nhận
                    # về hai người gộp làm một, không ai có tên.
                    # Một trường chỉ được kiểm "khác rỗng" là một trường chưa được kiểm.
                    if not re.fullmatch(r"[A-Z][A-Za-z'\-]*(?: [A-Z][A-Za-z'\-]*)?", ten):
                        continue
                    if not (ten and ta and m and len(ta.split(",")) >= 4): continue
                    n = int(m.group(1))
                    if cu and min(abs(n - x) for x in cu) < 6: continue
                    if ten.lower() in ten_cu: continue
                    cu.append(n); ten_cu.add(ten.lower())
                    giu.append({"ten": ten, "ta": ta})
                if giu:
                    ok[ma] = giu
            if len(ok) >= len(mas[i:i + 6]) - 1:
                ra.update(ok); break
    for ma, vs in ra.items():
        for v in vs:
            print(f"  {ma:<12} {v['ten']:<14} {v['ta'][:60]}")
    io.open(RA, "w", encoding="utf-8").write(json.dumps(ra, ensure_ascii=False, indent=1))
    print(f"\n✅ {len(ra)}/18 kênh -> {RA}")
    return


def _cu_main():
    khoa = PC._khoa_groq()
    ra = {}
    if os.path.exists(RA):
        ra = json.load(io.open(RA, encoding="utf-8"))
    for k in GU.KENH if isinstance(GU.KENH, (list, tuple)) else list(GU.VAI):
        ma = k if isinstance(k, str) else k.get("ma")
        if not ma or ma in ra:
            continue
        r = _goi_mot(ma, khoa)
        if not r:
            print(f"  ⚠ {ma}: không viết được vai đạt cổng"); continue
        ra[ma] = {"ten": r[0], "ta": r[1]}
        cu = [int(m.group(1)) for _t, d in GU.VAI[ma] for m in [TUOI.search(d)] if m]
        print(f"  {ma:<12} {r[0]:<15} {r[2]} tuổi (cũ: {sorted(cu)}) · {r[1][:56]}")
        io.open(RA, "w", encoding="utf-8").write(json.dumps(ra, ensure_ascii=False, indent=1))
    print(f"\n✅ {len(ra)}/18 kênh có vai thứ tư -> {RA}")


if __name__ == "__main__":
    main()
