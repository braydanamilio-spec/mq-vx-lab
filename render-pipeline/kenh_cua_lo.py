#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""In tên các kênh thuộc một lô, mỗi dòng một kênh — để shell lặp qua.

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


if __name__ == "__main__":
    try:
        n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    except ValueError:
        n = 1
    print("\n".join(kenh_cua(n)))
