#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VẼ KHO NỀN CHO 18 KÊNH, MỘT LẦN, RỒI NÉN WEBP  (6/9/2026)

── VÌ SAO TÁCH KHỎI `nen_kho.py` ────────────────────────────────────────────────────────────
`nen_kho.py` gọi Groq (rẻ, hỏng thì chạy lại). Tệp này gọi Cloudflare và tiêu **neuron thật** —
hỏng giữa chừng không lấy lại được. Hai bản chất khác nhau thì hai lệnh khác nhau, để một lượt
soạn hỏng không kéo theo nửa kho ảnh.

── VÌ SAO WEBP ──────────────────────────────────────────────────────────────────────────────
Nền cartoon phẳng nén WebP rất tốt: đo được **416 KB -> 32 KB (−93%)** mà mắt không thấy khác.
1.755 nền × ~35 KB ≈ **60 MB** — vừa đủ nhẹ để commit thẳng vào git, tức kho nền đi theo repo và
Actions không phải sinh lại gì. Giữ JPEG thì cũng chừng ấy ảnh là ~730 MB, quá nặng cho git.

── VÌ SAO KHÔNG BAO GIỜ VẼ LẠI ──────────────────────────────────────────────────────────────
Bỏ qua ảnh đã có, nên chạy lại tốn 0 lượt gọi. Đây là điều kiện để câu "vẽ một lần, dùng mãi"
là sự thật chứ không phải một lời hứa: khi kho đã đủ, chi phí ảnh của MỘT TẬP bằng 0, và trần
sản lượng chuyển từ hạn mức ảnh sang thời gian máy.

── MỘT RÀNG BUỘC CHỈ SỐNG Ở MỘT CHỖ ─────────────────────────────────────────────────────────
Ba mệnh lệnh bố cục (sàn liền mạch · ngang tầm mắt · đồ dồn hai mép) KHÔNG viết lại ở đây — gọi
thẳng `pilot_hai.ve_nen`, nơi chúng đã được ghép từ `kich_hai.SAN_NEN`. Viết lại là tạo nguồn
sự thật thứ hai, và cổng `kiem_nen.py` quét mọi tệp dựng prompt nền nên nó sẽ bắt ngay.
"""
import argparse, io, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
os.environ.setdefault("GT_KHONG_CF", "1")
import pilot_hai as PH
import phim_anh as A

KHO = os.path.join(GOC, "nen_kho.json")
NEN = PH.NEN


# Trần ảnh cho MỘT lượt chạy. Có nó thì việc bổ sung kho nền không bao giờ nuốt mất hạn mức
# mà đường render 18 kênh đang cần — §13.7: "số nhỏ" không phải bảo vệ, chỉ TRẦN CỨNG mới là.
TRAN = [int(os.environ.get("NEN_TRAN_LUOT") or 0)]


def _co_anh(ma: str, i: int) -> str:
    """Đường dẫn ảnh nền thứ `i` của kênh nếu đã có trên đĩa, "" nếu chưa.
    WebP trước (kho mới), JPEG sau (kho cũ) — một nguồn sự thật cho cả bộ vẽ lẫn bộ đếm."""
    for ten in (f"{ma}_{i:03d}.webp", f"{ma}_{i:03d}.jpg"):
        d = os.path.join(NEN, ten)
        if os.path.exists(d) and os.path.getsize(d) > 4000:
            return d
    return ""


def nen_webp(jpg: str, xoa_goc=True) -> int:
    """JPEG -> WebP. Trả về số byte tiết kiệm được, hoặc 0 nếu không đổi được."""
    try:
        from PIL import Image
    except Exception:
        return 0
    out = os.path.splitext(jpg)[0] + ".webp"
    if os.path.exists(out) and os.path.getsize(out) > 4000:
        if xoa_goc and os.path.exists(jpg):
            os.remove(jpg)
        return 0
    try:
        cu = os.path.getsize(jpg)
        # ── q82 -> q55  (anh dặn tối ưu lưu trữ, đo 6/9/2026) ──────────────────────────
        # Đo trên 12 mẫu, và đo ĐÚNG THỨ NGƯỜI XEM THẤY chứ không đo tệp: mô phỏng lại đúng
        # phép của engine (cover vào 1080×1920 rồi `blur(2.4px)`) cho cả bản cũ và bản nén,
        # rồi lấy hiệu từng điểm ảnh:
        #
        #     q=55  →  35% nhỏ hơn · lệch trung bình 0,52/255  (0,2%)
        #     q=45  →  41% nhỏ hơn · lệch 0,59/255
        #     q=35  →  47% nhỏ hơn · lệch 0,70/255
        #
        # Chọn 55 chứ không 35: chênh lệch dung lượng giữa chúng chỉ còn 12 điểm phần trăm,
        # trong khi q thấp là chỗ nhiễu khối bắt đầu hiện ra ở những nền có mảng màu lớn —
        # và kho này dùng suốt đời kênh nên không có đường lùi.
        #
        # CHỈ ÁP CHO ẢNH VẼ MỚI. 1.585 ảnh đã commit thì nén lại là SAI: git giữ cả bản cũ
        # trong lịch sử, nên "tiết kiệm 50 MB" thật ra là CỘNG THÊM 37 MB vào `.git` và không
        # bớt một byte nào ở bản đã có. Tối ưu một kho có lịch sử phải hỏi *"thứ này thêm hay
        # bớt vào lịch sử?"* trước khi hỏi nó nhỏ hơn bao nhiêu.
        Image.open(jpg).convert("RGB").save(out, "WEBP", quality=55, method=6)
        moi = os.path.getsize(out)
        if moi < 4000:                      # nén hỏng -> giữ nguyên JPEG, đừng mất ảnh
            os.remove(out); return 0
        if xoa_goc:
            os.remove(jpg)
        return cu - moi
    except Exception:
        return 0


def _la_ngang(ma: str, i: int) -> bool:
    """Ảnh của nền này có phải bản NGANG đời đầu không (rộng > cao)."""
    try:
        from PIL import Image
    except Exception:
        return False
    for e in (".webp", ".jpg"):
        f = os.path.join(NEN, f"{ma}_{i:03d}{e}")
        if os.path.exists(f):
            try:
                w, h = Image.open(f).size
                return w > h
            except Exception:
                return False
    return False


def mot_kenh(ma: str, ds: list, luong: int, ks, tran: int = 0) -> tuple:
    """Vẽ những nền còn thiếu của một kênh. Trả (số vẽ mới, số đã có, số hỏng)."""
    from kich_hai import SAN_NEN
    os.makedirs(NEN, exist_ok=True)
    thieu = []
    cu_ngang = []
    co = 0
    for i, p in enumerate(ds):
        if _co_anh(ma, i):
            co += 1
            if _la_ngang(ma, i):
                cu_ngang.append((i, p))
            continue
        thieu.append((i, p))
    # ── NÂNG CẤP NỀN NGANG CŨ — CHỈ SAU KHI ĐÃ PHỦ ĐỦ  (6/9/2026) ────────────────────────
    # 1.585 nền đầu vẽ ở 1344×768 (ngang) trong khi panel là khung dọc, nên chỉ 32% mỗi ảnh
    # tới được màn hình. Vẽ lại chúng ở 768×1344 cho gấp 3,1 lần điểm ảnh thật — nhưng KHÔNG
    # được tranh hạn mức với việc phủ nền còn thiếu: một kênh có 30/300 nền thì thứ nó cần là
    # 270 nền nữa, không phải 30 nền nét hơn.
    # Nên xếp sau, và chỉ chạy khi `thieu` đã rỗng. Kho tự về MỘT CHẤT qua vài ngày mà không
    # phải xoá gì và không phải quyết định gì (anh dặn: bổ sung dần cả tuần cũng được).
    if not thieu and cu_ngang:
        thieu = cu_ngang
        print(f"      {ma}: đã phủ đủ — nâng cấp {len(cu_ngang)} nền ngang sang dọc")
    if tran:
        thieu = thieu[:tran]
    if not thieu:
        return 0, co, 0

    hong = [0]
    lam = [0]

    def ve(cap):
        i, p = cap
        dest = os.path.join(NEN, f"{ma}_{i:03d}.jpg")
        try:
            # `chi_cf=True` — KHO NỀN CHỈ ĐƯỢC MỘT CHẤT VẼ  (6/9/2026)
            # Anh chốt sáng nay: *"đổi model là đổi CHẤT"*, và 1.081 nền đầu đã vẽ bằng
            # klein-9b. Nhánh Gemini của `A.ve` hỏng mềm nên nó IM LẶNG nhận việc khi CF cạn —
            # tức đúng lúc kho đang được bổ sung nhiều nhất. Hậu quả không phải một lỗi báo ra
            # mà là một TẬP có phòng vẽ bằng model này đứng cạnh phòng vẽ bằng model kia, và
            # kho nền thì dùng suốt đời kênh nên không sửa lại được.
            # Ảnh TỪNG TẬP thì ngược lại: ở đó Gemini là tầng cứu, vì phương án còn lại là
            # cảnh vẽ bằng code — một bước nhảy thị giác lớn hơn nhiều.
            # ── VẼ DỌC, KHÔNG VẼ NGANG  (đo 6/9/2026) ──────────────────────────────────
            # Kho nền vẽ `doc=False` -> 1344×768. Panel comic là khung DỌC 1080×1920, và
            # `NenPanel` đặt ảnh bằng `objectFit: cover`. Đo phép cover ấy:
            #
            #     ngang 1344×768 -> phóng 2,50x · dùng 432/1344 px =  32% ảnh
            #     dọc   768×1344 -> phóng 1,43x · dùng 756/768  px =  98% ảnh
            #
            # Tức 68% mỗi ảnh bị cắt bỏ, và dải còn lại bị phóng to 2,5 lần. Tính bằng pixel
            # THẬT tới được màn hình: 432×768 = 0,33 MP so với 756×1344 = 1,02 MP — **gấp 3,1
            # lần** cho CÙNG một giá neuron (flux-2 tính theo megapixel, hai cỡ bằng nhau).
            #
            # Không lỗi nào báo vì ảnh vẫn đúng, vẫn hiện ra; chỉ là hai phần ba nó chưa bao
            # giờ được ai nhìn thấy. Cùng họ §15.12 — thứ được sinh ra mà không ai đọc — chỉ
            # khác là ở đây "không ai đọc" là 68% số điểm ảnh của mọi tệp trong kho.
            #
            # `doc=True` cũng là mặc định của `A.ve`; chỗ này truyền `doc=False` một cách tường
            # minh, tức nó là một QUYẾT ĐỊNH đã ghi ra — và là quyết định sai cho khung dọc.
            rel = A.ve(f"{PH.GU_NEN} {SAN_NEN}. The room is: {p}.", ma, 0, 900 + i,
                       doc=True, ks=ks, chi_cf=True)
        except Exception:
            rel = None
        if not rel:
            hong[0] += 1
            return
        src = os.path.join(PH.PUB, rel)
        os.replace(src, dest)
        if os.path.exists(src + ".json"):
            os.remove(src + ".json")
        nen_webp(dest)
        lam[0] += 1
        if lam[0] % 10 == 0:
            print(f"      {ma}: {lam[0]}/{len(thieu)}", flush=True)

    with ThreadPoolExecutor(max_workers=luong) as ex:
        list(ex.map(ve, thieu))
    return lam[0], co, hong[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="", help="mã kênh, phẩy; rỗng = cả 18")
    ap.add_argument("--so", type=int, default=0, help="chỉ vẽ N nền đầu mỗi kênh (0 = hết)")
    ap.add_argument("--luong", type=int, default=8)
    ap.add_argument("--vong", type=int, default=12,
                    help="mỗi VÒNG vẽ tối đa N nền cho MỖI kênh rồi sang kênh khác (0 = tắt)")
    a = ap.parse_args()

    # ── VÌ SAO KHÔNG ĐỔI SANG MODEL RẺ  (anh quyết, 6/9/2026) ──────────────────────────
    # Em đã đề nghị đổi sang `flux-1-schnell`: giá tra tài liệu Cloudflare cho ảnh 1344×768 là
    # **1.369 neuron (klein-9b) so với 57 (schnell)** — chênh 24 lần, và cùng số neuron đã tiêu
    # hôm nay sẽ mua được 16.400 nền thay vì 1.081.
    #
    # Anh bác, và lý do của anh nặng hơn cái giá: **1.081 nền ĐÃ vẽ bằng klein-9b.** Đổi model
    # giữa chừng thì trong cùng một kênh — thậm chí cùng một tập, vì ba panel xoay qua ba phòng
    # — có phòng của model này đứng cạnh phòng của model kia. Kho nền là thứ dùng suốt đời
    # kênh, nên MỘT CHẤT VẼ quan trọng hơn tiết kiệm một tuần hạn mức.
    #
    # Đây cùng họ với §12.4 (nhất quán quanh một mốc) nhưng ngược chiều: chỗ này nhất quán mới
    # là thứ phải giữ, còn hạn mức thì mua lại được bằng THỜI GIAN — 4.319 nền còn thiếu ở
    # 7 nền/tài khoản với 113 tài khoản là ~5 ngày, và anh đã nói "cả tuần cũng được".
    #
    # Ghi ra đây để phiên sau đừng "tối ưu" lại: đổi model là đổi CHẤT, không phải đổi giá.

    kho = json.load(io.open(KHO, encoding="utf-8"))
    ds = [x.strip() for x in a.kenh.split(",") if x.strip()] or sorted(kho)
    ks = A.khoa()
    print(f"🔑 {len(ks)} tài khoản CF · {A.suc_khoe() if hasattr(A, 'suc_khoe') else ''}")

    # ── THỨ TỰ: KÊNH THIẾU NHIỀU NHẤT TRƯỚC  (đo 6/9/2026) ─────────────────────────────
    # Bản đầu chạy theo THỨ TỰ CHỮ CÁI. Hồ cạn giữa chừng, và kết quả là 11 kênh đầu bảng đủ
    # 94–100 nền trong khi **sáu kênh cuối bảng có ĐÚNG 0 nền** — chúng rơi về hai phòng mặc
    # định, tức đúng cái lỗi cả việc này sinh ra để chữa.
    # Không lỗi nào báo: mỗi kênh vẽ xong đều in "vẽ mới N · hỏng 0".
    # Sắp theo số nền CÒN THIẾU giảm dần thì hạn mức chảy về chỗ đói nhất trước, và dừng ở đâu
    # cũng để lại một kho CÂN — thay vì một kho đầy nửa trên, trống nửa dưới.
    def _thieu(ma):
        pp = (kho.get(ma) or [])[:a.so] if a.so else (kho.get(ma) or [])
        return sum(1 for i in range(len(pp)) if not _co_anh(ma, i))

    ds = sorted(ds, key=lambda m: -_thieu(m))
    print("   đói nhất: " + " · ".join(f"{m}:{_thieu(m)}" for m in ds[:6]) + " …")

    t0 = time.time()
    tong = dict(moi=0, co=0, hong=0)

    # ── RẢI VÒNG TRÒN, KHÔNG VẼT CẠN TỪNG KÊNH  (6/9/2026) ─────────────────────────────
    # Bản đầu chạy hết kênh này rồi mới sang kênh khác. Hồ CF cạn giữa chừng — và cạn là
    # chuyện BÌNH THƯỜNG ở đây, không phải sự cố — nên kết quả là 11 kênh đủ 94–100 nền trong
    # khi **sáu kênh có đúng 0 nền**, phải rơi về hai phòng mặc định.
    # Mỗi vòng cấp cho mỗi kênh nhiều nhất `--vong` nền rồi chuyển kênh. Dừng ở bất kỳ điểm
    # nào cũng để lại một kho CÂN, và đó là tính chất phải có của một việc chạy nhiều ngày:
    # người ta không điều khiển được lúc nào hồ cạn, chỉ điều khiển được *cạn thì còn lại gì*.
    hết = set()
    while len(hết) < len(ds):
        if TRAN[0] and tong["moi"] >= TRAN[0]:
            print(f"   ⏸ chạm trần {TRAN[0]} ảnh/lượt — dừng, phần còn lại để lượt sau")
            break
        tien = 0
        for ma in ds:
            if ma in hết:
                continue
            if TRAN[0] and tong["moi"] >= TRAN[0]:
                break
            p = kho.get(ma) or []
            if a.so:
                p = p[:a.so]
            con = (TRAN[0] - tong["moi"]) if TRAN[0] else 0
            lo = a.vong or 0
            gh = min(x for x in (lo, con) if x) if (lo or con) else 0
            m, c, h = mot_kenh(ma, p, a.luong, ks, gh)
            tong["moi"] += m; tong["co"] += c; tong["hong"] += h
            tien += m
            if m == 0:
                hết.add(ma)          # kênh đủ nền, HOẶC hồ đã cạn — cả hai đều nên chuyển tiếp
            else:
                print(f"   🏠 {ma:<12} +{m:>3}  (còn thiếu {_thieu(ma)})")
        if tien == 0:
            print("   ⛔ một vòng trọn vẹn không vẽ được ảnh nào — hồ cạn, dừng ở đây")
            break

    # số đo kho, có MẪU SỐ — "0 file" một mình có hai nghĩa ngược nhau (§15.2)
    n = b = 0
    for f in os.listdir(NEN):
        if f.endswith(".webp"):
            n += 1; b += os.path.getsize(os.path.join(NEN, f))
    print(f"\n✅ vẽ mới {tong['moi']} · sẵn có {tong['co']} · hỏng {tong['hong']}"
          f"  ({time.time() - t0:.0f}s)")
    print(f"   kho: {n} tệp .webp · {b / 1e6:.1f} MB · trung bình {b / max(1, n) / 1024:.0f} KB/ảnh")


if __name__ == "__main__":
    main()
