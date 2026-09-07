#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BẢNG GẮN KÊNH — mỗi kênh còn thiếu đúng cái gì để đăng được.  (7/9/2026)

Anh: *"xây pipeline trước, anh gắn channel chọn lịch là mượt"*. Dây chuyền đã có đủ bốn
khâu (dựng · ảnh bìa · đẩy kho · đăng) và `main.resolve_channel_env` đã ưu tiên token kết
nối qua dashboard rồi mới lùi về GitHub Secrets — tức "bấm Kết nối là chạy" vốn là thiết kế.

Thứ THIẾU không phải một cơ chế mà là một CÂU TRẢ LỜI: kênh nào đã gắn, kênh nào chưa, và
chưa thì thiếu đúng cái gì. Không có nó thì mỗi lần thêm kênh là một vòng dò, và một kênh
gắn thiếu một trường sẽ im lặng không đăng — đúng họ lỗi "hỏng mà không để lại tệp nào".

Bảng này KHÔNG BAO GIỜ in giá trị khoá, chỉ in CÓ hay KHÔNG. Và mọi ô nó không kiểm được
thì ghi thẳng "chưa kiểm được" kèm lý do, không ghi "không" — §15.2: một số 0 không có mẫu
số có hai nghĩa ngược nhau, và ở đây hai nghĩa ấy dẫn tới hai hành động khác hẳn.

    python3 kiem_gan_kenh.py            # bảng đầy đủ
    python3 kiem_gan_kenh.py --thieu    # chỉ những kênh chưa đăng được
"""
import io
import json
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
DU_AN = os.path.dirname(GOC)


def _duong_channels() -> str:
    for p in (os.path.join(DU_AN, "MM0-AutoPublisher", "config", "channels.yaml"),
              os.path.join(DU_AN, "_autopublisher", "config", "channels.yaml")):
        if os.path.exists(p):
            return p
    return ""


def _doc_kenh() -> list:
    p = _duong_channels()
    if not p:
        raise RuntimeError("không tìm thấy config/channels.yaml — không kiểm được gì")
    import yaml
    d = yaml.safe_load(io.open(p, encoding="utf-8")) or {}
    ks = d.get("channels") or d
    return list(ks.items()) if isinstance(ks, dict) else [(x.get("display_name"), x) for x in ks]


def _secret_repo(repo: str) -> set:
    """Tên secret của một repo. Trả None khi KHÔNG HỎI ĐƯỢC — khác hẳn với rỗng."""
    try:
        r = subprocess.run(["gh", "secret", "list", "--repo", repo, "--json", "name",
                            "--jq", ".[].name"], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return None
        return {x.strip() for x in r.stdout.splitlines() if x.strip()}
    except Exception:
        return None


def _ket_noi() -> dict:
    """{(kênh, loại): True} lấy từ Firestore `connections`. Trả None khi không mở được.

    Đây là đường CHÍNH mà `main.resolve_channel_env` dùng; secret chỉ là đường lùi. Kiểm
    thiếu đường này thì bảng sẽ tố oan mọi kênh anh đã bấm Kết nối trên dashboard.
    """
    try:
        sys.path.insert(0, GOC)
        import firestore_bridge as FB
        db = FB._db_ghi()
        ra = {}
        for d in db.collection("connections").stream():
            x = d.to_dict() or {}
            ten = (x.get("channel") or x.get("slug") or "").upper()
            if ten:
                ra[(ten, (x.get("kind") or "").lower())] = True
        return ra
    except Exception:
        return None


def _co_ho_kho():
    """Hồ kho Drive chung có tài khoản nào không. None = chưa kiểm được.

    `enqueue` chạy `pool == "auto"`: có hồ thì dùng hồ, hồ rỗng mới cần secret theo kênh.
    """
    try:
        sys.path.insert(0, GOC)
        import firestore_bridge as FB
        d = FB._db_ghi().collection("connections").where("kind", "==", "drive").limit(1).stream()
        return bool(list(d))
    except Exception:
        return None


def _ho_kho_chi_tiet():
    """(số kho, số kho token CHẾT). None khi không đọc được.

    ── VÌ SAO PHẢI IN RA  (7/9/2026) ──────────────────────────────────────────────────
    Anh nói hồ kho có hơn 100 tài khoản; em đi tìm bằng chứng trong log CI thì **không
    workflow nào in con số ấy ra**. Đúng §13.1 ở dạng quen thuộc: cơ chế có sẵn, chạy tốt,
    và không ai báo cáo nó — nên mỗi lần cần biết là một lần đi mò, và hai người có thể
    tin hai con số khác nhau mà không ai sai.
    Thứ đáng lo hơn con số tổng: log `publish` ngày 7/9 có `⚠️ list_queue kho ADISONDURHAM:
    invalid_grant` — một kho token đã CHẾT. Kho chết không làm hỏng lượt đẩy (hệ xoay sang
    kho khác) nên nó im lặng mòn dần, đúng họ lỗi "hỏng mà vẫn báo xanh".
    """
    try:
        sys.path.insert(0, GOC)
        import firestore_bridge as FB
        n = hong = 0
        for d in FB._db_ghi().collection("connections").where("kind", "==", "drive").stream():
            n += 1
            x = d.to_dict() or {}
            if x.get("health") in ("bad", "invalid_grant") or x.get("last_error"):
                hong += 1
        return n, hong
    except Exception:
        return None


def _o(co) -> str:
    return "✅" if co is True else ("—" if co is False else "?")


def main() -> int:
    chi_thieu = "--thieu" in sys.argv
    kenh = _doc_kenh()
    sec_ngoai = _secret_repo("braydanamilio-spec/mq-vx-lab")
    sec_trong = _secret_repo("braydanamilio-spec/mm0-auto-publisher")
    sec = None if (sec_ngoai is None and sec_trong is None) else (sec_ngoai or set()) | (sec_trong or set())
    kn = _ket_noi()
    _ho_kho = _co_ho_kho()

    print(f"nguồn: {os.path.relpath(_duong_channels(), DU_AN)} · {len(kenh)} kênh")
    print(f"  secret  : {'đọc được, ' + str(len(sec)) + ' tên' if sec is not None else 'CHƯA KIỂM ĐƯỢC (gh không trả lời)'}")
    print(f"  kết nối : {'đọc được, ' + str(len(kn)) + ' bản ghi' if kn is not None else 'CHƯA KIỂM ĐƯỢC (không mở được Firestore ở máy này)'}")
    _hk = _ho_kho_chi_tiet()
    if _hk is None:
        print("  hồ kho  : CHƯA KIỂM ĐƯỢC")
    else:
        _n, _h = _hk
        print(f"  hồ kho  : {_n} tài khoản Drive"
              + (f" — ⚠ {_h} kho có token CHẾT, cần nối lại" if _h else " — tất cả còn sống"))
    print()
    print(f"{'kênh':13s} {'bật':>4s} {'drive':>6s} {'youtube':>8s} {'facebook':>9s} {'instagram':>10s}   việc cần làm")

    can_lam = []
    _chua_ro = []
    for ten, v in kenh:
        ma = str(ten).upper()
        def _co_sec(*truong):
            if sec is None:
                return None
            ds = [x for x in truong if x]
            return bool(ds) and all(n in sec for n in ds)
        def _co_kn(loai):
            return None if kn is None else bool(kn.get((ma, loai)))
        def _gop(loai, *truong):
            """CÓ khi một trong hai nguồn nói có; CHƯA BIẾT khi nguồn còn lại chưa đọc được.

            Bản đầu trả False khi secret thiếu mà `connections` chưa đọc được — tức tuyên bố
            "chưa gắn" cho một kênh có thể đã bấm Kết nối trên dashboard. Đó đúng là §15.2,
            cái lỗi bảng này sinh ra để chống, mắc ngay bên trong chính nó: chỉ được kết luận
            KHÔNG khi đã hỏi ĐỦ CẢ HAI nguồn."""
            a, b = _co_kn(loai), _co_sec(*truong)
            if a is True or b is True:
                return True
            if a is None or b is None:
                return None
            return False

        yt, fb, ig = (v.get("youtube") or {}), (v.get("facebook") or {}), (v.get("instagram") or {})
        # Kho Drive có HAI đường, và đòi đường thứ hai là tố oan: `enqueue.use_pool` dùng
        # HỒ KHO chung (các tài khoản Drive đã kết nối) và chỉ lùi về `<KENH>_DRIVE_FOLDER_ID`
        # khi hồ rỗng. Nên một kênh không có secret riêng vẫn đẩy kho được bình thường.
        o_dr = True if _ho_kho else _co_sec(v.get("drive_folder_id_env"))
        if o_dr is False and _ho_kho is None:
            o_dr = None
        o_yt = _gop("youtube", yt.get("client_id_env"), yt.get("client_secret_env"), yt.get("refresh_token_env")) if yt.get("enabled") else False
        o_fb = _gop("facebook", fb.get("page_id_env"), fb.get("page_token_env")) if fb.get("enabled") else False
        o_ig = _gop("instagram", ig.get("ig_user_id_env"), ig.get("ig_token_env")) if ig.get("enabled") else False

        viec = []
        if o_dr is False: viec.append("kho Drive (nối 1 tài khoản là đủ cho MỌI kênh)")
        if o_yt is False: viec.append("YouTube")
        if o_fb is False: viec.append("Facebook")
        if o_ig is False: viec.append("Instagram")
        chua = [n for n, x in (("drive", o_dr), ("yt", o_yt), ("fb", o_fb), ("ig", o_ig)) if x is None]
        mo_ta = ("gắn: " + ", ".join(viec)) if viec else ("đủ" if not chua else "")
        if chua:
            mo_ta = (mo_ta + " · " if mo_ta else "") + "chưa kiểm được: " + ",".join(chua)
        if viec:
            can_lam.append(ma)
        _chua_ro.append(bool(chua))
        if chi_thieu and not viec:
            continue
        print(f"{ma[:13]:13s} {_o(bool(v.get('enabled'))):>4s} {_o(o_dr):>6s} {_o(o_yt):>8s} "
              f"{_o(o_fb):>9s} {_o(o_ig):>10s}   {mo_ta}")

    print()
    if sec is None and kn is None:
        print("⚠ KHÔNG kiểm được cả hai nguồn — bảng trên không kết luận được gì. "
              "Chạy trong Actions (có khoá dịch vụ) hoặc `gh auth login` ở máy.")
        return 0
    # "0 kênh thiếu" và "chưa kết luận được kênh nào" là hai câu khác hẳn nhau (§15.2) —
    # in kèm số kênh CHƯA KIỂM ĐƯỢC, nếu không thì dòng tổng kết tự nó nói dối.
    _mo = sum(1 for x in _chua_ro if x)
    if _mo:
        print(f"⚠ {_mo}/{len(kenh)} kênh CHƯA KẾT LUẬN ĐƯỢC từ máy này — chạy trong Actions "
              f"(có khoá dịch vụ) mới đọc được `connections`.")
    print(f"kênh chắc chắn chưa đăng được: {len(can_lam)}/{len(kenh)}"
          + (f" — {', '.join(can_lam[:6])}{' …' if len(can_lam) > 6 else ''}" if can_lam else ""))
    print("Cách gắn: dashboard → Kết nối (ghi vào `connections`, không cần secret), "
          "hoặc đặt secret đúng tên đã khai trong channels.yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
