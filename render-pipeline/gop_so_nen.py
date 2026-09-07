#!/usr/bin/env python3
"""GỘP SỔ KHO NỀN KHI HAI LƯỢT ĐỤNG NHAU  (8/9/2026)

VÌ SAO CÓ TỆP NÀY
  `kho_nen.yml` commit ba thứ: ảnh `.webp`, `nen_kho.json` (kênh -> DANH SÁCH mô tả nơi chốn)
  và `nen_tag.json` (`{kênh}_{NNN}` -> nhóm chủ đề). Đo ngày 7/9: ba lượt cron chạy CHỒNG NHAU
  (18:09–18:47 · 18:30–19:28 · 18:58–20:02) dù workflow có `concurrency: kho-nen`, nên hai lượt
  cùng lấp một chỗ trống và cùng sinh `dayinlife_157.webp` -> rebase đụng độ NHỊ PHÂN.

  Sổ kho KHÔNG gộp được bằng phép hợp tuỳ tiện: **chỉ số trong danh sách CHÍNH LÀ số trong tên
  tệp** (`nen_kho["dayinlife"][157]` <-> `dayinlife_157.webp`). Chèn thêm một mục vào giữa là
  đẩy lệch mọi ảnh phía sau — hỏng im lặng, đúng họ §12.5.

QUY TẮC GIẢI
  nen_kho.json  danh sách CHỈ ĐƯỢC NỐI THÊM ĐUÔI. Bên ngắn phải là TIỀN TỐ của bên dài; khi
                đúng thế thì bên dài thắng. Không phải tiền tố = hai lượt đã ghi khác nhau ở
                cùng một chỉ số -> KHÔNG tự giải, báo ra (§15.6: không biết ≠ được phép đoán).
  nen_tag.json  bảng tra phẳng theo khoá -> hợp hai phía; khoá trùng thì bản TRÊN REMOTE thắng
                (nó đã được commit, có thể đã có thứ khác trỏ tới).

Dùng: gop_so_nen.py <đường-dẫn>   — đọc hai phía từ index của git (:2 = remote, :3 = lượt này),
ghi bản đã gộp ra chính tệp ấy. Thoát 1 và KHÔNG ghi gì nếu không tự giải được.
"""
import json, subprocess, sys


def _ben(stage: int, duong: str):
    r = subprocess.run(["git", "show", f":{stage}:{duong}"], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"không đọc được phía {stage} của {duong}")
    return json.loads(r.stdout.decode("utf-8"))


def gop_kho(xa: dict, ta: dict) -> dict:
    """kênh -> danh sách mô tả. Chỉ nối đuôi; bên ngắn phải là tiền tố của bên dài."""
    ra = {}
    for k in sorted(set(xa) | set(ta)):
        a, b = xa.get(k) or [], ta.get(k) or []
        ngan, dai = (a, b) if len(a) <= len(b) else (b, a)
        if dai[:len(ngan)] != ngan:
            i = next(j for j in range(len(ngan)) if dai[j] != ngan[j])
            raise RuntimeError(f"«{k}» lệch ở chỉ số {i} — hai lượt ghi khác nhau cho CÙNG một "
                               f"số ảnh, không tự giải được")
        ra[k] = list(dai)
    return ra


def gop_tag(xa: dict, ta: dict) -> dict:
    """bảng tra phẳng: hợp hai phía, khoá trùng thì bản trên remote thắng."""
    ra = dict(ta); ra.update(xa)
    return ra


def main(duong: str) -> int:
    ten = duong.rsplit("/", 1)[-1]
    try:
        xa, ta = _ben(2, duong), _ben(3, duong)          # :2 = remote · :3 = lượt này
        if ten == "nen_kho.json":
            ra = gop_kho(xa, ta)
        elif ten == "nen_tag.json":
            ra = gop_tag(xa, ta)
        else:
            print(f"   ❌ không biết cách gộp «{ten}»"); return 1
    except Exception as e:
        print(f"   ❌ gộp {ten} hỏng: {e}"); return 1
    with open(duong, "w", encoding="utf-8") as f:
        json.dump(ra, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"   ✅ gộp {ten}: {len(ra)} mục")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
