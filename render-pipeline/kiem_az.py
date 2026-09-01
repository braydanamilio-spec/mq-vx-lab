#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG A-Z — dựng xong phải đi được tới khâu đăng (1/9/2026)

Anh: *"nó chưa đồng bộ là mày xây pepline sai rồi"* và *"còn đăng bài đồng bộ auto a-z nữa chứ"*.

Hai workflow render mới dựng đúng, gói artifact đúng, và **dừng ở đó**. Nhìn từ trong workflow
thì mọi bước đều xanh; nhìn từ ngoài thì không một video nào đăng được. Đó là kiểu hỏng tệ
nhất: mỗi mắt xích đều ổn, chỉ thiếu mắt xích cuối, mà không ai báo vì không mắt xích nào biết
mình là cuối.

Cổng kiểm ba điều — đủ ba mới gọi là A-Z:
  1. workflow render có gọi `day_kho.py` (mắt xích sang khâu đăng);
  2. mọi kênh pipeline dựng ra đều CÓ TÊN trong `channels.yaml` của repo đăng — thiếu là
     `enqueue.py` ném KeyError và video nằm lại vĩnh viễn;
  3. `day_kho.py` chạy với `--that` (không có cờ thì nó chỉ in ra cho xem, không đẩy gì).
"""
import io
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(GOC, "..", ".github", "workflows")
YAML_KENH = os.path.join(GOC, "..", "MM0-AutoPublisher", "config", "channels.yaml")
# Danh sách này TỪNG là bảng cứng, và bảng cứng thì thêm workflow mới là cổng im lặng bỏ qua
# nó — đúng họ lỗi đã gặp ở `RS_PRESETS` và `kiem_workflow.CAP` hôm nay. Nay đọc thẳng thư mục:
# mọi `render_*.yml` đang bật cron đều phải có mắt xích sang khâu đăng.
def _render_dang_bat() -> list:
    import os as _o, io as _i
    d = _o.path.join(_o.path.dirname(GOC), ".github", "workflows")
    if not _o.path.isdir(d):
        return []
    ra = []
    for f in sorted(_o.listdir(d)):
        if not (f.startswith("render_") and f.endswith(".yml")):
            continue
        y = _i.open(_o.path.join(d, f), encoding="utf-8").read()
        # Chỉ đòi workflow CÒN CHẠY. Hệ thế hệ 1 đã tắt cron thì không cần mắt xích nữa, và
        # đòi nó chỉ tạo ra một lỗi đỏ vĩnh viễn mà không ai sửa được.
        ma = "\n".join(l for l in y.split("\n") if not l.lstrip().startswith("#"))
        if "cron:" in ma:
            ra.append(f)
    return ra


RENDER = _render_dang_bat()


def _nuot_loi() -> list:
    """Mắt xích A-Z nào đang bị `|| true` nuốt lỗi.

    ── VÌ SAO (1/9/2026) ───────────────────────────────────────────────────────────────────
    `render_giai_thich_18.yml` có `python day_kho.py ... || true`. Đẩy kho hỏng thì luồng BÁO
    XANH rồi đi tiếp, và 18 video nằm lại artifact mà không ai biết. Đo thật hôm nay: lượt
    33521077570 xanh 18/18 luồng, `⚠️ 0/2 video vào hàng đợi đăng`, dashboard hiện 0 — và không
    một dấu hiệu nào nói rằng có gì đó đã hỏng.

    `|| true` ở bước GÓI ARTIFACT hay bước CHẤM ĐIỂM thì đúng: chúng hỏng cũng không mất video.
    Ở bước ĐẨY KHO thì sai: đó là mắt xích cuối, hỏng ở đó là video không tới đích.
    """
    if not os.path.isdir(WF):
        return []
    XUNG_YEU = ("day_kho.py", "enqueue.py", "sieu_gt.py")
    ra = []
    # CHỈ LUỒNG CÒN CHẠY. `RENDER` ở trên đã lọc theo `cron:` — đòi luồng đã nghỉ sửa `|| true`
    # là tạo dòng đỏ vĩnh viễn cho việc không ai làm, và dòng đỏ ấy che mất lỗi thật (đã trả giá
    # đúng hôm nay: ba cổng sai phạm vi che mất lỗi SHARD_PUBLISH).
    for f in RENDER:
        p = os.path.join(WF, f)
        if not os.path.exists(p):
            continue
        y = io.open(p, encoding="utf-8").read()
        for ln in y.split("\n"):
            if ln.lstrip().startswith("#"):
                continue
            if "|| true" in ln and any(x in ln for x in XUNG_YEU):
                ra.append(f"{f}: {ln.strip()[:72]}")
    return ra


def main() -> int:
    loi = []
    for d in _nuot_loi():
        loi.append(f"nuốt lỗi ở mắt xích xung yếu -> {d}")
    for w in RENDER:
        p = os.path.join(WF, w)
        if not os.path.exists(p):
            continue
        s = io.open(p, encoding="utf-8").read()
        ma = "\n".join(l for l in s.split("\n") if not l.lstrip().startswith("#"))
        if "day_kho.py" not in ma:
            loi.append(f"{w}: dựng xong KHÔNG đẩy sang khâu đăng — artifact hết hạn là mất trắng")
        elif "--that" not in ma:
            loi.append(f"{w}: gọi day_kho.py nhưng thiếu `--that` — nó chỉ in ra, không đẩy gì")
        else:
            print(f"  ✅ {w:28s} có mắt xích sang khâu đăng")

    # kênh pipeline dựng ra vs kênh repo đăng biết
    try:
        import yaml
        d = yaml.safe_load(io.open(YAML_KENH, encoding="utf-8"))
        biet = {k.upper() for k in (d.get("channels") or {})}
    except Exception as e:
        print(f"  ℹ️ không đọc được channels.yaml ({str(e)[:50]}) — bỏ qua phần đối chiếu kênh")
        biet = None

    if biet is not None:
        import sys
        sys.path.insert(0, GOC)
        # ĐẾM KÊNH CỦA BỘ CÒN CHẠY, không đếm mọi kênh khai trong repo. Bản trước gom cả
        # `kich_hai.KENH` và `kich_v2.KENH` bất kể luồng của chúng còn cron hay không, nên sau
        # khi cho hai bộ ấy nghỉ (1/9) nó vẫn báo đỏ 76 kênh — một lỗi không ai sửa được, vì
        # không có gì để sửa. Cổng báo đỏ vĩnh viễn thì người ta thôi đọc nó, và đó là cách mất
        # một cổng mà không hề gỡ nó đi.
        #
        # `_render_dang_bat()` ở trên đã đọc thư mục workflow và chỉ giữ tệp CÒN `cron:`. Ở đây
        # chỉ nạp bảng kênh của những bộ ấy.
        BO = {                       # workflow còn chạy -> cách lấy danh sách kênh của nó
            "render_hai.yml":            ("kich_hai", "KENH", "ten"),
            "render_phan_tich_18.yml":   ("kich_v2", "KENH", "ten"),
            "render_phan_tich.yml":      ("kich_v2", "KENH", "ten"),
            "render_giai_thich_18.yml":  ("giai_thich", "KENH", "ma"),
        }
        can = set()
        for wf in RENDER:
            if wf not in BO:
                continue
            mod, bang, khoa = BO[wf]
            try:
                M = __import__(mod)
                can |= {str(k[khoa]).replace(" ", "").upper() for k in getattr(M, bang)}
            except Exception:
                pass
        if "render_phan_tich_18.yml" in RENDER or "render_phan_tich.yml" in RENDER:
            try:
                import duyet_lo
                can |= {t.replace(" ", "").upper() for t in duyet_lo.ds_gen2()}
            except Exception:
                pass
        thieu = sorted(can - biet)
        if thieu:
            loi.append(f"{len(thieu)} kênh dựng ra mà repo đăng KHÔNG biết: "
                       + ", ".join(thieu[:8]) + ("…" if len(thieu) > 8 else "")
                       + " — enqueue sẽ ném KeyError, video nằm lại vĩnh viễn")
        else:
            print(f"  ✅ {len(can)} kênh pipeline dựng ra đều có trong channels.yaml")

    if loi:
        print("\n❌ " + "\n❌ ".join(loi))
        return 1
    print("\n✅ dây chuyền A-Z liền mạch: dựng -> đẩy kho -> hàng đợi đăng")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
