#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SINH khối biến môi trường theo kênh cho `publish.yml` từ `config/channels.yaml`.  (7/9/2026)

── VÌ SAO SINH, KHÔNG CHÉP TAY ────────────────────────────────────────────────────────────
`publish.yml` đang truyền khoá cho ĐÚNG BA kênh thế hệ 1 (`BROKE`, `HUH`, `INSIDE_YOU`) —
không một kênh nào trong 18 kênh đang chạy. Khối ấy chép tay, nên nó đứng yên trong khi
`channels.yaml` đi tiếp; đúng §13.5 (*danh sách kênh nằm ở nhiều nơi thì phải SINH ra từ một
nguồn, đừng chép*) và §13.2 (*cổng/khối cầm danh sách chép tay là chỗ che lỗi thật*).

Đây là đường LÙI, không phải đường chính: `main.resolve_channel_env` ưu tiên token đã bấm
"Kết nối" trên dashboard (`connections/`) rồi mới đọc các biến này. Nhưng đường lùi mà thiếu
thì nó im lặng không tồn tại, và người vận hành không có cách nào biết.

Thêm một dòng `${{ secrets.X }}` cho một secret CHƯA ĐẶT là vô hại: Actions thay bằng chuỗi
rỗng, và `resolve_channel_env` xử lý rỗng y như trước. Nên khối này an toàn để sinh đủ 18
kênh ngay cả khi anh chưa đặt secret nào.

    python3 dong_bo_khoa_kenh.py --kiem    # chỉ báo lệch, không sửa (dùng làm cổng)
    python3 dong_bo_khoa_kenh.py --viet    # ghi lại publish.yml
"""
import io
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
DU_AN = os.path.dirname(GOC)
DAU = "          # ---- KÊNH (SINH TỰ ĐỘNG bởi dong_bo_khoa_kenh.py — ĐỪNG SỬA TAY) ----"
CUOI = "          # ---- HẾT KHỐI KÊNH ----"


def _duong(ten: str) -> str:
    for g in ("MM0-AutoPublisher", "_autopublisher"):
        p = os.path.join(DU_AN, g, ten)
        if os.path.exists(p):
            return p
    return ""


def khoi() -> str:
    import yaml
    p = _duong(os.path.join("config", "channels.yaml"))
    if not p:
        raise RuntimeError("không thấy config/channels.yaml")
    d = yaml.safe_load(io.open(p, encoding="utf-8")) or {}
    ks = d.get("channels") or d
    it = ks.items() if isinstance(ks, dict) else [(x.get("display_name"), x) for x in ks]
    d_ra = [DAU]
    for ten, v in it:
        ds = [v.get("drive_folder_id_env")]
        for nen, tr in (("youtube", ("client_id_env", "client_secret_env", "refresh_token_env")),
                        ("facebook", ("page_id_env", "page_token_env")),
                        ("instagram", ("ig_user_id_env", "ig_token_env"))):
            if (v.get(nen) or {}).get("enabled"):
                ds += [(v.get(nen) or {}).get(t) for t in tr]
        ds = [x for x in ds if x]
        if not ds:
            continue
        d_ra.append(f"          # {ten}")
        rong = max(len(x) for x in ds) + 1
        for x in ds:
            d_ra.append(f"          {(x + ':').ljust(rong)} ${{{{ secrets.{x} }}}}")
    d_ra.append(CUOI)
    return "\n".join(d_ra)


def main() -> int:
    p = _duong(os.path.join(".github", "workflows", "publish.yml"))
    if not p:
        print("❌ không thấy publish.yml"); return 1
    s = io.open(p, encoding="utf-8").read()
    moi = khoi()
    if DAU in s and CUOI in s:
        i, j = s.index(DAU), s.index(CUOI) + len(CUOI)
        cu = s[i:j]
        ra = s[:i] + moi + s[j:]
    else:
        # Lần đầu: thay khối chép tay cũ (từ dòng `# ---- KÊNH: ` đầu tiên tới hết khối env).
        m = re.search(r"(?m)^          # ---- KÊNH: .*$", s)
        if not m:
            print("❌ không tìm được chỗ chèn"); return 1
        n = s.index("\n        run: |", m.start())
        cu = s[m.start():n]
        ra = s[:m.start()] + moi + s[n:]
    if cu.strip() == moi.strip():
        print("✅ khối kênh đã khớp channels.yaml"); return 0
    _cu_k = len(re.findall(r"DRIVE_FOLDER_ID:", cu))
    _moi_k = len(re.findall(r"DRIVE_FOLDER_ID:", moi))
    print(f"⚠ LỆCH: publish.yml có {_cu_k} kênh · channels.yaml có {_moi_k} kênh")
    if "--viet" not in sys.argv:
        print("   (chạy lại với --viet để ghi)"); return 1
    io.open(p, "w", encoding="utf-8").write(ra)
    print(f"✅ đã ghi {p} — {_moi_k} kênh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
