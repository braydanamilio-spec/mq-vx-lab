#!/usr/bin/env python3
"""SOI TOÀN DỰ ÁN — tìm những dạng lỗi ĐÃ CẮN mình, ở mọi chỗ khác chưa bị phát hiện.

31/8 — Anh dặn: "sau đừng để anh nhắc nữa, có rule pipeline rõ ràng, phân tích lỗi tiềm ẩn
toàn bộ dự án". Đúng — trong hai ngày qua anh phải chỉ ra bảy tám lỗi mà lẽ ra tôi tự thấy,
và gần như lỗi nào cũng đã xuất hiện ở một chỗ khác trước đó.

Nguyên tắc của bộ soi này: KHÔNG đi tìm lỗi mới bằng trực giác. Chỉ lấy những dạng đã có bằng
chứng thật trong dự án — mỗi mẫu dò dưới đây gắn với một sự cố cụ thể — rồi hỏi "chỗ nào khác
cũng viết như thế". Đó là cách rẻ nhất để không phải trả giá lần hai cho cùng một bài học.

BẢY DẠNG, mỗi dạng một sự cố có thật:
 1. `> 0` trên một con số đếm — SỐ KHÔNG bị coi là "chưa có dữ liệu".
    (31/8: kho dọn sạch, tong=0, worker và dashboard đều bỏ qua rồi hiện số cũ 2067/2088)
 2. Bắt lỗi rồi NUỐT im lặng — `catch (_) {}` / `except: pass`.
    (31/8: worker ghi Firestore hụt mà vẫn trả ok, "đồng bộ xong mà số không đổi")
 3. Hằng số bốc đại trong code vẽ — không suy từ kích thước khung.
    (31/8 lưới ô 42px tràn bảng · 30/8 nhân vật ±292 tràn khung · nửa người 115 đo ở tư thế nghỉ)
 4. Đọc một đại lượng GẦN GIỐNG thứ mình cần.
    (31/8: `usage` là dung lượng cả tài khoản Google, không phải riêng Drive → thừa 127 GB)
 5. Đường vòng lách qua quy tắc dọn dữ liệu — cắt chuỗi thô ngay tại nguồn.
    (31/8: mười mấy nhánh tự cắt `[:26]` trước khi tới bộ dọn nhãn)
 6. Cùng một phép so/hằng số lặp ở nhiều nơi — sửa một chỗ thì chỗ kia vẫn sai.
    (31/8: `tong > 0` ở worker và dashboard; 30/8: hằng 292 ở engine và cổng)
 7. Bắt lỗi quá rộng ở nơi phân biệt "không có" và "lỗi".
    (29/8: 429 bị đọc thành "thư mục rỗng" → báo dọn sạch trong khi chưa dọn được gì)
"""
import io, os, re, sys, glob

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BO_QUA = ("node_modules", ".git", "out/", "public/geo", "dist", ".venv", "__pycache__")


def _tep(duoi: tuple) -> list:
    ra = []
    for r, d, fs in os.walk(GOC):
        d[:] = [x for x in d if not any(b.strip("/") == x for b in BO_QUA)]
        if any(b in r.replace(os.sep, "/") for b in BO_QUA):
            continue
        for f in fs:
            if f.endswith(duoi):
                ra.append(os.path.join(r, f))
    return ra


def soi() -> list:
    """Trả [(mức, tệp, dòng, mô tả)]. `mức` 1 = gần chắc chắn hỏng, 2 = đáng xem."""
    ra = []
    # ── 1. `> 0` trên con số đếm ────────────────────────────────────────────────────────────
    DEM = r"(tong|total|count|used|so_luong|n_|len|dem|size|luot)"
    for f in _tep((".py", ".js", ".ts", ".tsx", ".html")):
        try:
            src = io.open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for i, d in enumerate(src.splitlines(), 1):
            if re.search(rf"\b\w*{DEM}\w*\s*>\s*0\b", d, re.I) and "//" not in d[:d.find(">")]:
                # `x > 0` để CHIA hoặc để lặp thì đúng; chỉ nghi khi nó quyết định "có dữ liệu hay không"
                if re.search(r"(if|\?|&&|\|\||return)", d):
                    ra.append((2, f, i, f"`> 0` trên số đếm — số KHÔNG có phải là 'không có dữ liệu'? {d.strip()[:88]}"))
    # ── 2. nuốt lỗi im lặng — CHỈ quanh thao tác dữ liệu ────────────────────────────────
    # Bản đầu tố 220 chỗ `catch {}` và 196 chỗ `except: pass`. Phần lớn vô hại: bọc một phép
    # đọc localStorage, một lần parse JSON hỏng, một cú focus() — nuốt ở đó không giấu gì cả.
    # Chỗ NGUY HIỂM là nuốt quanh thao tác GHI hoặc ĐỌC dữ liệu thật: hỏng mà vẫn báo xong.
    # Đó chính là ca 31/8 — worker `catch (_) {}` quanh fsPatch, ghi hụt mà trả ok.
    GHI = r"(fsPatch|setDoc|addDoc|updateDoc|deleteDoc|\.run\(|\.execute\(|fetch\(|urlopen|upload|files\(\)|batch\.)"
    for f in _tep((".py",)):
        src = io.open(f, encoding="utf-8", errors="ignore").read()
        d = src.splitlines()
        for m in re.finditer(r"except[^\n:]*:\s*\n\s*pass\b", src):
            ln = src[:m.start()].count("\n")
            truoc = "\n".join(d[max(0, ln - 12):ln])
            if re.search(GHI, truoc):
                ra.append((1, f, ln + 1, "except: pass quanh thao tác GHI/ĐỌC — hỏng mà vẫn báo xong"))
    for f in _tep((".js", ".ts", ".tsx", ".html")):
        src = io.open(f, encoding="utf-8", errors="ignore").read()
        d = src.splitlines()
        for m in re.finditer(r"catch\s*\(\s*_?\w*\s*\)\s*\{\s*\}", src):
            ln = src[:m.start()].count("\n")
            truoc = "\n".join(d[max(0, ln - 12):ln])
            if re.search(GHI, truoc):
                ra.append((1, f, ln + 1, "catch {} quanh thao tác GHI/ĐỌC — hỏng mà vẫn báo xong"))
    return ra


def main() -> int:
    kq = soi()
    if not kq:
        print("\n  ✅ không thấy mẫu nào\n"); return 0
    theo: dict = {}
    for muc, f, d, mo in kq:
        theo.setdefault(mo.split("—")[0].strip()[:44], []).append((f, d, mo))
    print(f"\n  SOI DỰ ÁN — {len(kq)} chỗ đáng xem, {len(theo)} dạng\n")
    for ten, ds in sorted(theo.items(), key=lambda x: -len(x[1])):
        print(f"  ── {ten}  ({len(ds)} chỗ)")
        for f, d, mo in ds[:6]:
            n = os.path.relpath(f, GOC) if os.path.exists(f) else f
            print(f"     {n}{':' + str(d) if d else ''}")
        if len(ds) > 6:
            print(f"     … và {len(ds)-6} chỗ nữa")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
