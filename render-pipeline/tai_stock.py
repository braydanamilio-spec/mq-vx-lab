#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TẢI TOÀN BỘ kho hình của một hoạ sĩ qua API CHÍNH THỨC của sàn stock.

── VÌ SAO TỆP NÀY TỒN TẠI  (5/9/2026) ────────────────────────────────────────────────────
Anh muốn đủ 4.396 hình của @zdeneksasek. Đo ngày 5/9 thì Canva **không có đường script**:

    · trang hình chỉ có "Use in a design", KHÔNG có nút tải
    · Canva Connect API (API chính thức) chỉ trả tài sản/thiết kế CỦA CHÍNH MÌNH,
      không có endpoint nào liệt kê hay tải hình Elements
    · click tổng hợp bằng JS -> không chèn (Canva chỉ nhận sự kiện chuột thật)
    · Tab + Enter trên tile  -> mở thẻ thông tin, không chèn
    · giấy phép Pro gắn với việc dùng hình BÊN TRONG thiết kế Canva

Nhưng chính hoạ sĩ ấy bán cùng bộ hình ở sàn stock CÓ API tải hàng loạt. Đó là đường
script hợp lệ duy nhất, và tệp này đi đường đó.

── ĐIỂM QUAN TRỌNG NHẤT: DÒ TRƯỚC KHI TRẢ TIỀN ──────────────────────────────────────────
Bậc API miễn phí của Shutterstock CHO tìm kiếm nhưng KHÔNG cho tải (ảnh trả về có
watermark). Nên script chạy `--do` bằng khoá miễn phí sẽ đếm CHÍNH XÁC bao nhiêu hình
lấy được, trước khi anh mua gói. Không đoán, không trả tiền cho một con số chưa đo.

── DÙNG ───────────────────────────────────────────────────────────────────────────────
    export SS_TOKEN=...              # khoá API Shutterstock (bậc nào cũng chạy `--do`)
    python3 tai_stock.py --do                       # ĐẾM, không tải, không tốn hạn mức tải
    python3 tai_stock.py --tai --toi 4400           # tải thật (cần gói có quyền license)

Tải xong ra `kho_stock/` + `kho_stock/_kho.json` — đúng khuôn mà `tai_canva.py` đã đọc,
nên nối vào engine không phải viết thêm gì.
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(GOC, "kho_stock")
API = "https://api.shutterstock.com/v2"

# `User-Agent` BẮT BUỘC ở mọi lệnh gọi. Đã trả giá đúng chuyện này ở §13.15: gọi trần thì
# CDN trả 403 mã 1010 và nó đọc y hệt "khoá sai" — suýt kết luận 83 khoá đã chết.
UA = "MM0-AutoPublisher/1.0 (+https://github.com/braydanamilio-spec/mq-vx-lab)"

# Tên hoạ sĩ. Script TỰ TÌM id từ tên, không chép tay id — id chép tay là một nguồn sự
# thật thứ hai, và nó sẽ sai lặng lẽ vào ngày sàn đổi định danh (§13.5).
HOA_SI = "Zdenek Sasek"


def _goi(duong: str, tham: dict, token: str, thu: int = 4) -> dict:
    """Một lệnh gọi API, có thử lại và ĐỌC ĐƯỢC mã lỗi thật."""
    url = f"{API}{duong}?" + urllib.parse.urlencode(tham, doseq=True)
    for lan in range(1, thu + 1):
        rq = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}", "User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(rq, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            than = (e.read() or b"")[:300].decode("utf-8", "replace")
            if e.code == 429:                      # chạm trần tốc độ -> lùi rồi thử lại
                cho = min(60, 5 * lan * lan)
                print(f"   ⏳ 429 — chờ {cho}s (lần {lan}/{thu})", file=sys.stderr)
                time.sleep(cho); continue
            if e.code in (401, 403):
                raise RuntimeError(
                    f"HTTP {e.code} — khoá không dùng được cho lệnh này.\n"
                    f"   {than}\n"
                    f"   401 = token sai/hết hạn · 403 = gói hiện tại KHÔNG có quyền này\n"
                    f"   (bậc miễn phí tìm kiếm được nhưng KHÔNG license/tải được).")
            if e.code >= 500 and lan < thu:
                time.sleep(3 * lan); continue
            raise RuntimeError(f"HTTP {e.code} tại {duong}: {than}")
        except urllib.error.URLError as e:
            if lan < thu: time.sleep(3 * lan); continue
            raise RuntimeError(f"mạng hỏng tại {duong}: {e}")
    raise RuntimeError(f"bỏ cuộc sau {thu} lần tại {duong}")


def tim_hoa_si(token: str, ten: str) -> list[dict]:
    """Tìm id hoạ sĩ theo TÊN. Trả về MỌI ứng viên — không tự chọn hộ.

    §13.12 dạy: máy chỉ được tự chuẩn hoá KHI KHỚP DUY NHẤT. Hai hoạ sĩ trùng tên mà
    script tự chọn bừa thì nó tải nhầm cả một kho và không có gì báo.
    """
    d = _goi("/contributors/search", {"query": ten, "per_page": 20}, token)
    return d.get("data", [])


def quet(token: str, cid: str, toi: int) -> list[dict]:
    """Duyệt HẾT kho của hoạ sĩ. Phân trang tới khi hết, không cắt ở trang đầu.

    §15.1: phép CẮT không được đặt trước phép LỌC. Ở đây không lọc gì trong lúc duyệt —
    lấy đủ rồi mới lọc, để cái mình cần không bao giờ nằm ngoài lằn cắt.
    """
    ra, trang = [], 1
    while len(ra) < toi:
        d = _goi("/images/search", {
            "contributor": cid, "image_type": "vector,illustration",
            "per_page": 100, "page": trang, "sort": "newest",
            "view": "full",
        }, token)
        lo = d.get("data", [])
        tong = d.get("total_count", 0)
        if not lo:
            break
        ra.extend(lo)
        print(f"   trang {trang:3d} · lấy {len(lo):3d} · cộng dồn {len(ra)}/{tong}")
        if len(lo) < 100:
            break
        trang += 1
        time.sleep(0.35)                 # lịch sự với trần 100 lệnh/giờ của bậc miễn phí
    return ra[:toi]


def _tu(ten: str) -> list[str]:
    """Chữ dùng để khớp nội dung. Cắt đúng những chữ khuôn mẫu của tiêu đề stock —
    'vector cartoon stick figure illustration' có ở gần như MỌI hình của hoạ sĩ này, nên
    giữ lại thì mọi hình trông giống mọi hình (§13.4: cắt phần GIỐNG NHAU LÀ ĐÚNG ra
    trước, rồi mới đo phần còn lại)."""
    khuon = {"vector", "cartoon", "stick", "figure", "illustration", "conceptual",
             "drawing", "doodle", "stickman", "isolated", "white", "background", "eps"}
    return sorted({w for w in re.findall(r"[a-z]{3,}", ten.lower()) if w not in khuon})


def tai(token: str, anh: list[dict], that: bool) -> None:
    os.makedirs(KHO, exist_ok=True)
    so_kho = os.path.join(KHO, "_kho.json")
    kho = json.load(open(so_kho, encoding="utf-8")) if os.path.exists(so_kho) else []
    xong = {x["id"] for x in kho}
    moi = ok = bo = 0

    for i, a in enumerate(anh, 1):
        ma = a["id"]
        if ma in xong:                    # RESUME: chạy lại không tải lại thứ đã có
            bo += 1
            continue
        moi += 1
        ten = (a.get("description") or a.get("alt") or "").strip()
        if not that:
            continue
        try:
            # license -> API trả thẳng link tải trong cùng phản hồi.
            rq = urllib.request.Request(
                f"{API}/images/licenses",
                data=json.dumps({"images": [{"image_id": ma}],
                                 "format": "vector", "size": "vector"}).encode(),
                headers={"Authorization": f"Bearer {token}", "User-Agent": UA,
                         "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(rq, timeout=60) as r:
                kq = json.loads(r.read().decode())
            mot = (kq.get("data") or [{}])[0]
            link = (mot.get("download") or {}).get("url")
            if not link:
                print(f"   ⚠️ {ma}: license không trả link — {json.dumps(mot)[:120]}",
                      file=sys.stderr)
                continue
            rq2 = urllib.request.Request(link, headers={"User-Agent": UA})
            with urllib.request.urlopen(rq2, timeout=180) as r:
                du = r.read()
            duoi = ".eps" if du[:4] == b"%!PS" else (".zip" if du[:2] == b"PK" else ".bin")
            tep = f"ss_{ma}{duoi}"
            open(os.path.join(KHO, tep), "wb").write(du)
            kho.append({"id": ma, "tep": tep, "ten": ten, "tu": _tu(ten)})
            ok += 1
            if ok % 25 == 0:
                json.dump(kho, open(so_kho, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
                print(f"   💾 đã lưu sổ · {ok} tệp mới")
            time.sleep(0.3)
        except Exception as e:
            print(f"   ⚠️ {ma}: {e}", file=sys.stderr)

    json.dump(kho, open(so_kho, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # Mọi con số đi kèm MẪU SỐ (§15.2): "0" một mình luôn có hai nghĩa ngược nhau.
    print(f"\n📊 {len(anh)} hình trong kho hoạ sĩ · {bo} đã có sẵn (bỏ qua) · "
          f"{moi} cần lấy · {ok} tải xong")
    if not that:
        print("   (chế độ DÒ — chưa tải gì. Thêm --tai để tải thật.)")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--do", action="store_true", help="chỉ ĐẾM, không tải (chạy được bằng khoá miễn phí)")
    p.add_argument("--tai", action="store_true", help="tải thật (cần gói có quyền license)")
    p.add_argument("--hoa-si", default=HOA_SI)
    p.add_argument("--id", default="", help="id hoạ sĩ, nếu đã biết")
    p.add_argument("--toi", type=int, default=5000, help="trần số hình")
    a = p.parse_args()

    token = os.environ.get("SS_TOKEN", "").strip()
    if not token:
        sys.exit("❌ chưa có SS_TOKEN. Tạo khoá ở https://www.shutterstock.com/account/developers/apps\n"
                 "   rồi:  export SS_TOKEN=...")

    cid = a.id
    if not cid:
        ung = tim_hoa_si(token, a.hoa_si)
        if not ung:
            sys.exit(f"❌ không tìm thấy hoạ sĩ tên {a.hoa_si!r}")
        if len(ung) > 1:
            print(f"⚠️ {len(ung)} hoạ sĩ trùng tên — script KHÔNG tự chọn hộ (§13.12).")
            for x in ung[:10]:
                print(f"   --id {x.get('id')}   {x.get('display_name') or x.get('username')}")
            sys.exit("   Chạy lại kèm --id <id> đúng người.")
        cid = str(ung[0]["id"])
        print(f"→ hoạ sĩ {a.hoa_si!r} = id {cid}")

    print(f"→ duyệt kho của hoạ sĩ {cid}")
    anh = quet(token, cid, a.toi)
    if not anh:
        sys.exit("❌ 0 hình — kiểm lại id hoạ sĩ trước khi kết luận kho rỗng.")
    tai(token, anh, that=a.tai and not a.do)


if __name__ == "__main__":
    main()
