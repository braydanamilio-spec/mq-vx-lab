#!/usr/bin/env python3
"""Tải kho ICON từ Iconify về, khoá theo TỪ trong lời, xuất mô-đun TS cho engine.

── VÌ SAO ĐỔI SANG ICON  (5/9/2026) ────────────────────────────────────────────────────
Anh chê sáu vòng liền, và cả sáu lần đều là NHÂN VẬT: hình que · người lơ lửng · người
lặp · con gấu tím · dấu hỏi khổng lồ. Không lần nào anh chê khung so sánh, biểu đồ hay số
liệu. Tra ra thì ba công cụ mạnh nhất thế giới cho phim giải thích sinh từ code (Manim ·
Motion Canvas · Remotion) đều **không vẽ nhân vật** — không phải thiếu tính năng, mà vì
nhân vật vẽ bằng code trông rẻ tiền.

Gốc thật của cả "hình que" lẫn "lặp đi lặp lại" nằm ở một con số: `_bt_canh` ánh xạ câu
vào **23 biểu tượng tự vẽ**. Kho quá nhỏ so với số lần rút (§15.15), và chất vẽ là trần
của một người viết code, không phải của một hoạ sĩ.

Iconify gom 238 bộ icon mã nguồn mở. Đo ngày 5/9: **252.576 icon** có giấy phép
MIT/Apache/CC0 — dùng thương mại tự do, không phải ghi nguồn. API công khai, KHÔNG cần
khoá, nên chạy được trên Actions y như ở máy.

── PHÉP ĐO TRƯỚC KHI LÀM ───────────────────────────────────────────────────────────────
60 từ hay gặp nhất trong lời thật của 18 kênh -> **46 từ có icon (76%)**. 14 từ trượt đều
là từ TRỪU TƯỢNG (`nothing` · `everyone` · `against` · `billion` · `compared`), tức thứ
vốn không nên có hình. Nên 24% ấy không phải lỗ hổng phải vá — nó là đường phân chia tự
nhiên: danh từ cụ thể thì có hình, từ trừu tượng thì để con số và chữ nói.

── HAI ĐIỀU KHÁC HẲN ĐƯỜNG unDraw (đã thử và bị anh bác) ───────────────────────────────
1. Icon KHÔNG mang mặt đất riêng. Bức unDraw là cả một cảnh có đất ở ~0,55 khung nó, nên
   dán lên sàn của mình là lơ lửng — không hằng số nào chữa được vì mỗi bức một khác.
   Icon là một vật phẳng: mình đặt đâu nó nằm đấy.
2. Icon nhẹ ~1KB (unDraw ~16KB), nên nạp 400 từ chỉ tốn ~0,4MB thay vì 5,1MB.
"""
import json, os, re, sys, urllib.parse, urllib.request

API = "https://api.iconify.design"
RA = os.path.join(os.path.dirname(__file__), "..", "engine-remotion", "src", "gt", "KhoIcon.ts")

# Bộ icon ưu tiên: đều MIT/Apache, và đều vẽ theo lối NÉT ĐẬM ĐỀU — cùng chất với nét mực
# của cảnh mình vẽ. Trộn bộ nét mảnh vào là hai chất liệu trong một khung (§12.10).
BO = "ph,mdi,tabler,solar,material-symbols,fluent,lucide,carbon,hugeicons"
CAN_TU = 420

DUNG = {"the", "and", "for", "you", "your", "that", "this", "with", "from", "are", "was",
        "not", "but", "all", "one", "out", "get", "got", "its", "has", "had", "who", "why",
        "how", "what", "when", "where", "them", "they", "does", "did", "will", "can",
        "still", "then", "than", "just", "more", "most", "been", "into", "over", "only",
        "same", "some", "every", "never", "also", "here", "there", "would", "could",
        "about", "after", "before", "because", "which", "while", "their", "other",
        # Động từ và từ trừu tượng hay lọt qua phép khớp tên: chúng CÓ icon cùng tên nhưng
        # hình ấy nói về giao diện phần mềm (`close` là dấu X, `first` là nút tua đầu),
        # không nói về câu đang đọc. Chặn ở khâu TẢI thì kho sạch, khỏi phải lọc lúc dựng.
        "gets", "ends", "feels", "first", "close", "break", "start", "stop", "open",
        "next", "back", "down", "left", "right", "list", "menu", "check", "plus",
        "minus", "share", "link", "edit", "save", "send", "view", "help", "info",
        "daily", "awake", "dark", "light", "full", "half", "even", "less", "much"}


def _goi(u):
    rq = urllib.request.Request(u, headers={"User-Agent": "mm0/1.0"})
    return json.loads(urllib.request.urlopen(rq, timeout=30).read().decode())


def _von_tu():
    """Vốn từ THẬT của 18 kênh, đọc từ `kich_ban` — không chép tay (§13.2)."""
    import collections
    import giai_thich as G
    c = collections.Counter()
    for k in G.KENH:
        for idx in range(1930, 1940):
            for n in G.kich_ban(k["ma"], idx)[4]:
                for w in re.findall(r"[a-z]{3,}", (n.get("loi") or "").lower()):
                    if w not in DUNG:
                        c[w] += 1
    return c


def _tim(tu):
    """Tên icon khớp nhất cho một từ, hoặc None.

    Iconify xếp hạng theo độ khớp tên, nên lấy cái đầu là đủ — NHƯNG phải kiểm tên icon có
    thật sự chứa từ ấy không. Truy vấn `calories` trả về `calendar` ở vài bộ: gần giống về
    chuỗi, sai hẳn về nghĩa. Một hình sai nghĩa chiếm chỗ hình đúng còn tệ hơn không có
    hình, vì nó nói một điều SAI về câu đang đọc.
    """
    try:
        d = _goi(f"{API}/search?query={urllib.parse.quote(tu)}&limit=8&prefixes={BO}")
    except Exception:
        return None
    # ── KHỚP TRỌN TỪ, KHÔNG KHỚP CHUỖI CON  (5/9/2026, ngay sau lượt đo đầu) ────────────
    # Bản đầu dùng `tu in ten.replace("-","")`. Đo 120 nhịp thật thì lọt ra `gets` (khớp
    # icon **widgets**), `ends`, `feels`, `first` — toàn hình sai nghĩa hoàn toàn.
    # Đúng §13.9 và §15.3, lần thứ n trong tuần: *một danh sách/phép so theo chuỗi con không
    # bắt được ngôn ngữ*. Tên icon là các từ nối bằng gạch ngang, nên tách ra rồi so TRỌN TỪ
    # (kèm dạng số nhiều đơn giản) là phép so đúng đơn vị.
    dang = {tu, tu + "s", tu.rstrip("s")} if len(tu) > 3 else {tu}
    for ten in d.get("icons", []):
        if dang & set(ten.split(":")[-1].split("-")):
            return ten
    return None


def _than(ten):
    """(viewBox, ruột) của một icon."""
    tien, n = ten.split(":", 1)
    try:
        d = _goi(f"{API}/{tien}.json?icons={urllib.parse.quote(n)}")
    except Exception:
        return None
    ic = (d.get("icons") or {}).get(n)
    if not ic or not ic.get("body"):
        return None
    w = ic.get("width", d.get("width", 24))
    h = ic.get("height", d.get("height", 24))
    body = ic["body"]
    # Icon Iconify dùng `currentColor`; đổi thành biến để engine thay bằng màu kênh.
    body = body.replace("currentColor", "{MUC}")
    # Chèn `pathLength="1"` để hiệu ứng nét tự vẽ (`TuVe.tsx`) chạy được trên icon nhập —
    # thiếu nó thì icon hiện bụp một cái trong khi cảnh quanh nó đang được vẽ dần.
    body = re.sub(r"<(path|rect|circle|ellipse|line|polyline|polygon)\b",
                  lambda m: f'<{m.group(1)} pathLength="1"', body)
    return f"0 0 {w} {h}", body


def main() -> int:
    von = _von_tu()
    print(f"   vốn từ 18 kênh: {len(von)} từ")
    kho, bo = {}, 0
    for i, (tu, _) in enumerate(von.most_common(CAN_TU)):
        ten = _tim(tu)
        if not ten:
            bo += 1
            continue
        t = _than(ten)
        if not t:
            bo += 1
            continue
        kho[tu] = {"ten": ten, "vb": t[0], "ruot": t[1]}
        if (i + 1) % 80 == 0:
            print(f"      … {i + 1}/{min(CAN_TU, len(von))} · có hình {len(kho)}")
    if len(kho) < 60:
        raise RuntimeError(f"chỉ lấy được {len(kho)} icon — KHÔNG ghi đè kho cũ")
    with open(RA, "w", encoding="utf-8") as f:
        f.write("/* SINH TỰ ĐỘNG bởi `render-pipeline/tai_icon.py` — ĐỪNG SỬA TAY.\n"
                "   Nguồn: Iconify (các bộ MIT/Apache — dùng thương mại tự do, không ghi nguồn).\n"
                "   Khoá là TỪ trong lời; `{MUC}` là chỗ engine thay màu. */\n")
        f.write("export type Icon = { ten: string; vb: string; ruot: string };\n")
        f.write("export const KHO_ICON: Record<string, Icon> = ")
        f.write(json.dumps(kho, ensure_ascii=False))
        f.write(";\n")
    mb = os.path.getsize(RA) / 1e6
    print(f"   ✅ {len(kho)} từ có icon · {bo} từ không có · {mb:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
