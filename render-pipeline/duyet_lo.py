#!/usr/bin/env python3
"""Dây chuyền DUYỆT THEO LÔ — dựng, chấm, soi khung, rồi mới đưa anh xem.

31/8 — Anh dặn "cho a videos demo 60 channel phân tích, lần lượt nha để a duyệt, nhớ xây
pipeline, methord chuẩn". Chữ "lần lượt" là phần quan trọng nhất: sáu mươi video đổ một lượt
thì không ai duyệt nổi, và một lỗi hệ thống sẽ nhân lên sáu mươi lần trước khi bị phát hiện.

Nên chia lô mười kênh. Mỗi lô đi qua ĐÚNG bốn bước, không bỏ bước nào:

  1. DỰNG      — kênh nào nguồn không đủ dữ liệu thì bỏ lượt, không bịa số.
  2. CHẤM      — qc_kenh (ngưỡng 90) và kiem_bo_cuc (tràn khung). Điểm lấy MIN, không lấy
                 trung bình: một trục hỏng thì cả video hỏng, trung bình chỉ giấu nó đi.
  3. SOI KHUNG — trích ba khung mỗi video ra ảnh. Bắt buộc, không thay bằng điểm số.
                 Sổ lỗi 30/8: bộ mười video được chấm 95–100 và tôi suýt gửi anh duyệt; trích
                 một khung ra nhìn thì thấy nguyên si lỗi anh đã chê ba lần. Cổng đọc chữ và
                 đo nhịp — nó mù hoàn toàn về hình.
  4. BÁO CÁO   — một bảng: kênh · điểm · lý do trừ · đường dẫn video và ảnh khung.

Lô sau chỉ chạy khi anh đã duyệt lô trước. Đó là lý do có tệp `.duyet/<lô>.json` ghi lại kết
quả từng lô: để biết đang ở đâu, và để không dựng lại thứ anh đã xem.
"""
import io, json, os, subprocess, sys, glob

GOC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(GOC, "out")
SO = os.path.join(GOC, ".duyet")
KHUNG = os.path.join(OUT, "_khung")


def _chay(cmd: list, phut: int = 90) -> str:
    r = subprocess.run(cmd, cwd=GOC, capture_output=True, text=True, timeout=phut * 60)
    return (r.stdout or "") + (r.stderr or "")


def ds_gen2() -> list:
    d = json.load(io.open(os.path.join(GOC, "kenh_the_he_2.json"), encoding="utf-8"))
    ks = d if isinstance(d, list) else list((d.get("kenh", d)).values())
    # Bỏ dạng `cinematic`: nó kể bằng cảnh, KHÔNG có bảng số nào để rút. Đưa vào lô chỉ để nó
    # bỏ lượt là làm loãng báo cáo và làm anh tưởng hệ hỏng. Thiếu thật thì ghi là thiếu.
    return [k["ten"] for k in ks if k.get("dinh_dang") != "cinematic"]


def soi(mp4: str, n: int = 3) -> list:
    """Trích n khung trải đều. Trả đường dẫn ảnh."""
    os.makedirs(KHUNG, exist_ok=True)
    ten = os.path.splitext(os.path.basename(mp4))[0]
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", mp4], capture_output=True, text=True)
        dai = float((r.stdout or "0").strip() or 0)
    except Exception:
        dai = 0.0
    if dai < 1:
        return []
    ra = []
    for i in range(n):
        t = dai * (i + 1) / (n + 1)
        f = os.path.join(KHUNG, f"{ten}-{i+1}.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.1f}", "-i", mp4,
                        "-frames:v", "1", "-vf", "scale=460:-1", f], capture_output=True)
        if os.path.exists(f):
            ra.append(f)
    return ra


def lo(ten_lo: str, kenh: list, gen2: bool) -> dict:
    print(f"\n  ══ LÔ {ten_lo}: {len(kenh)} kênh ══")
    print("  [1/4] dựng…")
    if gen2:
        # 31/8 — QUAY LẠI đường KichV2 cho kênh gen-2. Lượt trước tôi đổi sang `the_he_2.py` vì
        # hiểu nhầm lựa chọn của anh: anh chọn "trộn hình thức", tôi hiểu thành "bỏ nhân vật,
        # dùng lại bảy dạng gốc". Anh nói rõ ngay sau đó — vẫn muốn CÓ người và CÓ nền AI mờ,
        # chỉ cần đa dạng thêm cho đỡ nhàm.
        # Nên sự đa dạng nằm BÊN TRONG khung có người: nay chín dạng biểu đồ (cột · thanh ·
        # chấm · ô vuông · thẻ dọc · vòng · lưới ô · khung thước · điểm phân tán · bản đồ Mỹ),
        # sáu kiểu kể, mười hai bố cục. Không kênh nào phải bỏ nhân vật để khác kênh khác.
        log = _chay([sys.executable, "-u", "kich_v2.py", "--gen2", ",".join(kenh)], phut=90)
    else:
        log = _chay([sys.executable, "-u", "kich_v2.py", "--demo"])

    xong, bo = [], []
    for d in log.splitlines():
        if "✅" in d and ".mp4" in d:
            xong.append(d.split(":")[-1].strip().split()[0] if ":" in d else d)
        if "BỎ LƯỢT" in d:
            bo.append(d.strip())

    _mau = "v3_*.mp4"
    mp4 = sorted(glob.glob(os.path.join(OUT, _mau)), key=os.path.getmtime)[-len(kenh):]
    print(f"        {len(mp4)} video · {len(bo)} bỏ lượt")

    print("  [2/4] chấm…")
    diem = _chay([sys.executable, "qc_kenh.py"])
    bocuc = _chay([sys.executable, "kiem_bo_cuc.py"])

    print("  [3/4] soi khung…")
    anh = {}
    for f in mp4:
        anh[os.path.basename(f)] = soi(f)
    print(f"        {sum(len(v) for v in anh.values())} khung")

    kq = {"lo": ten_lo, "kenh": kenh, "video": [os.path.basename(f) for f in mp4],
          "bo_luot": bo, "khung": anh,
          "diem": [l for l in diem.splitlines() if l.strip().startswith(("✅", "❌"))],
          "bo_cuc": [l for l in bocuc.splitlines() if "❌" in l or "lành" in l]}
    os.makedirs(SO, exist_ok=True)
    io.open(os.path.join(SO, f"{ten_lo}.json"), "w", encoding="utf-8").write(
        json.dumps(kq, ensure_ascii=False, indent=2))

    print("  [4/4] báo cáo:")
    for l in kq["diem"][:12]:
        print("       ", l.strip())
    for l in bo[:4]:
        print("        ⏭", l[:96])
    return kq


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Dựng + chấm + soi khung theo LÔ để anh duyệt.")
    ap.add_argument("--lo", type=int, default=1, help="số thứ tự lô (1 = 10 kênh v3 gốc)")
    ap.add_argument("--co", type=int, default=10, help="mấy kênh một lô")
    ap.add_argument("--liet-ke", action="store_true")
    a = ap.parse_args()

    g2 = ds_gen2()
    los = [("1-goc", [], False)]
    for i in range(0, len(g2), a.co):
        los.append((f"{len(los)+1}-gen2", g2[i:i + a.co], True))

    if a.liet_ke:
        for i, (t, k, _) in enumerate(los, 1):
            print(f"  lô {i}: {t:9} {len(k) or 10:2} kênh   {', '.join(k[:4])}{'…' if len(k) > 4 else ''}")
        print(f"\n  tổng {sum(len(k) or 10 for _, k, _ in los)} kênh trong {len(los)} lô")
        return 0

    if not 1 <= a.lo <= len(los):
        print(f"  ❌ chỉ có {len(los)} lô"); return 1
    t, k, g = los[a.lo - 1]
    lo(t, k, g)
    return 0


if __name__ == "__main__":
    sys.exit(main())
