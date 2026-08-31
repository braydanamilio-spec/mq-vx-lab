#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""In tên các kênh thuộc một LÔ hoặc một LUỒNG, mỗi dòng một kênh — để shell lặp qua.

Tách khỏi YAML có lý do: bản trước nhúng thẳng đoạn Python này vào `run: |` bằng heredoc, và
dấu `EOF` phải nằm ở cột 0 — đúng chỗ phá thụt lề của khối YAML. Workflow thành không phân
tích được, mà lỗi ấy chỉ lộ ra khi Actions từ chối chạy. Code thuộc về tệp code.
"""
import sys

import duyet_lo


def kenh_cua(lo: int) -> list:
    if lo <= 1:
        # Lô 1 là mười kênh GỐC, không nằm trong `kenh_the_he_2.json`.
        import kich_v2
        K = getattr(kich_v2, "KENH", [])
        return [k["ten"] for k in K]
    g = duyet_lo.ds_gen2()
    return g[(lo - 2) * 10:(lo - 1) * 10]


def tat_ca() -> list:
    """56 kênh: 10 kênh gốc trước, rồi 46 kênh thế hệ 2."""
    return kenh_cua(1) + duyet_lo.ds_gen2()


def la_gen2(ten: str) -> bool:
    return ten in set(duyet_lo.ds_gen2())


def luong(n: int, tong: int) -> list:
    """Chia 56 kênh thành `tong` luồng, trả phần của luồng thứ `n` (đếm từ 1).

    Chia XEN KẼ (`[n-1::tong]`) chứ không cắt khối liền: các kênh nặng nhẹ khác nhau và chúng
    nằm cạnh nhau theo chủ đề trong danh sách, nên cắt khối làm một luồng ôm trọn cụm nặng còn
    luồng khác xong sớm ngồi không. Xen kẽ thì mỗi luồng nhận đều cả nặng lẫn nhẹ.
    """
    ds = tat_ca()
    return ds[(n - 1)::tong]


if __name__ == "__main__":
    ap = None
    if "--luong" in sys.argv:
        i = sys.argv.index("--luong")
        n = int(sys.argv[i + 1])
        tong = int(sys.argv[sys.argv.index("--tong") + 1]) if "--tong" in sys.argv else 18
        ds = luong(n, tong)
        if "--gen2" in sys.argv:
            ds = [x for x in ds if la_gen2(x)]
        elif "--goc" in sys.argv:
            ds = [x for x in ds if not la_gen2(x)]
        print("\n".join(ds))
        raise SystemExit(0)
    try:
        n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    except ValueError:
        n = 1
    print("\n".join(kenh_cua(n)))
