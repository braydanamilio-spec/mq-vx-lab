#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIỂM GÁN — mọi giá trị bảng nhân vật gán, ENGINE có vẽ không. (30/8/2026)

VÌ SAO CẦN TỆP NÀY
------------------
Anh xem khung GYM LIES và thấy huấn luyện viên nữ trông ra đàn ông. Soi JSON thì dữ liệu ĐÚNG
hết: `kieuToc="duoi_ngua"`, `mu="luoi_trai"`, `phuKien="khan_quang"`. Soi engine thì mới ra:

    · `mu` — kiểu `Kieu` khai trường ấy từ lâu, bảng gán nó, JSON mang nó sang tận nơi —
      mà **engine chưa bao giờ vẽ mũ**. Không một dòng nào đọc `kieu.mu`.
    · `khan_quang` — engine có sáu phụ kiện, không có cái này. Gán vào thì rơi qua hết sáu
      nhánh `if` rồi biến mất.

Đây là dạng lỗi tốn nhất trong cả dây chuyền, vì **mọi cổng đều báo xanh**: JSON hợp lệ,
TypeScript hợp lệ (trường có trong kiểu), esbuild dịch được, video render xong. Chỉ có KHUNG
HÌNH là thiếu, và chỉ mắt người mới thấy — mà mắt người thì không chạy được hằng đêm.

Cây kiểm này đọc CHÍNH mã engine để biết nó vẽ được những gì, rồi đối chiếu với bảng gán. Không
chép danh sách sang đây — chép là lại đẻ ra bản thứ hai của một sự thật, đúng cái bệnh đã trả giá
bốn lần trong ngày (luật 7bf · 7bs).
"""
from __future__ import annotations

import io
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(GOC), "engine-remotion", "src")


def _doc(p: str) -> str:
    try:
        return io.open(p, encoding="utf-8").read()
    except Exception:
        return ""


def engine_ve() -> dict[str, set]:
    """Đọc mã engine, trả về những giá trị nó THẬT SỰ vẽ cho mỗi trường."""
    s = _doc(os.path.join(ENG, "v4", "DienVienHai.tsx"))
    return {
        "phuKien": set(re.findall(r'kieu\.phuKien === "(\w+)"', s)),
        "mu": set(re.findall(r'm === "(\w+)"', s)) | ({"len"} if "mũ len trùm" in s else set()),
        # "ngan" là nhánh MẶC ĐỊNH của `Toc` (không có `if`), nên nó không xuất hiện trong mã
        # dưới dạng so sánh — thêm tay, kèm lý do, thay vì nới lỏng phép đo.
        "kieuToc": set(re.findall(r'k === "(\w+)"', s)) | {"ngan"},
        "rau": set(re.findall(r'kieu\.rau === "(\w+)"', s)),
        # ── CỬ CHỈ: LẤY TỪ `TenCuChi` CỦA ENGINE  (6/9/2026) ────────────────────────────
        # `DienVien.tsx` dùng `CU_CHI[cuChi] || CU_CHI.nghi` — một tên cử chỉ SAI không ném lỗi,
        # nó lặng lẽ thành "đứng yên". Đo được: vòng xoay trong `kich_hai.cu_chi_cua` gọi
        # `chong_nanh` và `ngan_ngam`, cả hai KHÔNG có trong `TenCuChi`, nên vòng sáu chỗ thật
        # ra chỉ có ba cử chỉ và ba chỗ còn lại đều đứng yên.
        # Triệu chứng duy nhất là "nhân vật hay đứng yên" — thứ người ta đổ cho thẩm mỹ, không
        # ai nghĩ là một tên viết sai. Đúng dạng nguy nhất: nhánh dự phòng che mất lỗi gán.
        # Đọc thẳng khai báo kiểu, KHÔNG chép danh sách sang đây (xem đầu tệp).
        "cuChi": set(re.findall(r'"(\w+)"',
                     (re.search(r"export type TenCuChi\s*=([^;]+);",
                                _doc(os.path.join(ENG, "v2", "DienVien.tsx")))
                      or type("x", (), {"group": lambda *_: ""})()).group(1))),
    }


def bang_gan() -> dict[str, set]:
    """Những giá trị THẬT SỰ đi tới engine — đọc từ JSON đã dựng, không đoán qua mã nguồn.

    Bản đầu quét mã nguồn bằng biểu thức chính quy và báo `phuKien` là "—" trong khi bảng gán
    bảy giá trị: bảng gán qua BIẾN (`_b["phuKien"] = _pk`) và qua từ điển tra cứu, hai lối viết
    không có chuỗi nào để bắt.
    Một cây thước mù nửa mắt nguy hơn không có thước, vì nó BÁO XANH ở đúng chỗ mình cần nó
    lên tiếng. Nên bỏ hẳn lối quét mã: đọc chính tệp JSON mà bộ dựng vừa ghi ra — đó là dữ liệu
    thật đi tới engine, không phải suy đoán về nó.
    Đổi lại, cây kiểm chỉ chạy được sau khi đã dựng ít nhất một lượt. Chấp nhận: nó là cổng
    KIỂM SẢN PHẨM, không phải cổng dịch mã.
    """
    import glob, json
    ra: dict[str, set] = {"phuKien": set(), "mu": set(), "kieuToc": set(), "rau": set(),
                          "cuChi": set()}
    n = 0
    for f in sorted(glob.glob(os.path.join(GOC, "out", "v*.json"))):
        try:
            d = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        # `out/` chứa nhiều loại tệp; một số có MẢNG ở cấp trên cùng. `d.get` trên một list
        # ném `AttributeError`, và `selftest` bọc cổng này nên nó hiện ra thành một lời tố
        # RỖNG: *"có giá trị được gán mà engine không vẽ:"* — không kèm một tên nào.
        # Cổng đỏ không kèm bằng chứng thì không ai sửa được, và nó dạy người ta bỏ qua báo
        # động (§15.12 lật ngược). Bỏ qua tệp sai hình dạng, đừng chết theo nó.
        if not isinstance(d, dict):
            continue
        for khoa in ("kieuTuyA", "kieuTuyB", "kieu"):
            nv = d.get(khoa)
            if isinstance(nv, dict):
                n += 1
                for t in ra:
                    if nv.get(t):
                        ra[t].add(str(nv[t]))
        # `cuChi` không nằm trong hồ sơ nhân vật mà trong TỪNG LƯỢT — nó đổi theo panel, đó
        # chính là lý do nó tồn tại. Quét cả `luot` thì mới thấy giá trị thật đi tới engine.
        for l in (d.get("luot") or []):
            if isinstance(l, dict) and l.get("cuChi"):
                ra["cuChi"].add(str(l["cuChi"])); n += 1
    ra["_dem"] = n
    return ra


def main() -> int:
    ve, gan = engine_ve(), bang_gan()
    dem = gan.pop("_dem", 0)
    if not dem:
        print("  ⏭ chưa có JSON nhân vật nào trong out/ — dựng một lượt rồi chạy lại")
        return 0
    print(f"  đọc {dem} hồ sơ nhân vật từ out/*.json\n")
    loi = []
    print("  trường      engine vẽ được                              bảng gán")
    # Danh sách trường viết TAY ở đây là nguồn sự thật thứ hai — thêm trường vào `bang_gan`
    # mà quên thêm ở đây thì cổng vẫn in ✅ và im lặng bỏ qua trường mới. Đúng bệnh mà đầu tệp
    # này đã cảnh báo. Duyệt thẳng những trường HAI BÊN cùng khai.
    for t in sorted(k for k in gan if k in ve):
        thieu = {x for x in gan[t] if x and x not in ve[t]}
        print(f"  {t:<11} {', '.join(sorted(ve[t])) or '(không cái nào)':<42} "
              f"{', '.join(sorted(x for x in gan[t] if x)) or '—'}")
        for x in sorted(thieu):
            loi.append(f"{t}={x!r} được gán nhưng ENGINE KHÔNG VẼ — sẽ mất lặng lẽ trên khung")
    print()
    if loi:
        for l in loi:
            print(f"  ❌ {l}")
        return 1
    print("  ✅ mọi giá trị được gán đều có nhánh vẽ trong engine")
    return 0


if __name__ == "__main__":
    sys.exit(main())
