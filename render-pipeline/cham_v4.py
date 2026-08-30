#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHẤM 10 KÊNH HÀI THẾ HỆ 4 — đo được, không cảm tính (30/8/2026).

Cùng nguyên tắc `cham_v3.py`: nói "đạt 90" mà không có thước thì mỗi lần nhìn lại một khác. Nhưng
CÁC TRỤC KHÁC HẲN, vì hỏng của phim hài không giống hỏng của video số liệu:

  25đ  NHỊP HÀI     — lượt ≤ 14 từ · hai người nói xen kẽ · cú chốt nằm ở 3 giây cuối
  20đ  KHỚP TIẾNG   — mốc lượt bám đúng số từ, không lượt nào rớt/thừa chữ của người kia
  20đ  KHÔNG TRÙNG  — cặp nhân vật, bộ nền, bảng màu, cặp giọng: không kênh nào chung
  15đ  ĐỘ SÁNG      — khung thật ≥ 75/255, dưới 8% điểm gần như đen
  10đ  CHỮ TRONG KHUNG — hai dòng phụ đề không dòng nào tràn mép
  10đ  ĐỘ DÀI       — 15–60 giây (anh chốt), và có đủ ba nền phân biệt

    python cham_v4.py
    python cham_v4.py --kenh NEIGHBORWATCH
"""
from __future__ import annotations

import glob
import io
import json
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
NGUONG = 90


def _dai(v: str):
    try:
        return float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v],
            capture_output=True, text=True, timeout=30).stdout.strip())
    except Exception:
        return None


def _sang(v: str, dur: float):
    """Sáng trung bình + tỉ lệ điểm gần-đen, đo ở BỐN mốc rải đều — không đo mỗi khung đầu.
    Khung đầu là khung có tiêu đề, sáng nhất phim; đo mỗi nó thì mọi video đều 'đủ sáng'."""
    try:
        from PIL import Image
    except ImportError:
        return (None, None)
    ss = tt = 0.0
    n = 0
    for m in (0.12, 0.38, 0.64, 0.9):
        p = os.path.join("/tmp", f"_v4c{int(m*100)}.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{dur*m:.2f}", "-i", v,
                        "-vframes", "1", "-vf", "scale=160:-1", p], capture_output=True, timeout=60)
        if not os.path.exists(p):
            continue
        px = list(Image.open(p).convert("L").getdata())
        ss += sum(px) / len(px)
        tt += sum(1 for x in px if x < 40) / len(px)
        n += 1
    return (ss / n, tt / n) if n else (None, None)


def _rgb(h):
    h = str(h or "").lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else (0, 0, 0)


def _sang_tuong_doi(c):
    f = [x / 255 for x in c]
    f = [(v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4) for v in f]
    return .2126 * f[0] + .7152 * f[1] + .0722 * f[2]


def hai_ao_co_khac_nhau(k: dict) -> str:
    """Áo hai nhân vật phải khác nhau ĐỦ để mắt tách được. Trả lý do hỏng, "" nếu đạt.

    30/8 — Anh: *"2 nhân vật nói thì nên có 2 lời thoại 2 nhân vật có sự khác biệt"*. Đã cho
    phụ đề mang màu áo người đang nói — nhưng phép ấy chỉ có nghĩa nếu HAI MÀU ÁO KHÁC NHAU.
    Đo mười kênh thì năm kênh trượt, tệ nhất là DATING APP lệch màu **9 trên 255**: hai người
    mặc gần y hệt nhau, nên cả thẻ phụ đề lẫn hai nhân vật đều không phân biệt được.
    Đây đúng là kiểu lỗi chỉ lộ ra khi ĐO: nhìn từng kênh riêng thì không ai thấy gì sai.

    Hai ngưỡng, vì hai kiểu giống nhau khác nhau:
      · lệch màu ≥ 120 — hai màu phải khác SẮC;
      · tương phản sáng ≥ 1,9 — hai màu phải khác ĐỘ SÁNG, để người xem mù màu (khoảng 8% nam
        giới, tức một phần đáng kể khán giả Mỹ) vẫn tách được hai nhân vật.
    """
    import kich_hai as H
    a, b = H._hai_bong(k)
    ca, cb = a.get("ao"), b.get("ao")
    if not ca or not cb:
        return "hai nhân vật chưa được gán màu áo riêng"
    ra, rb = _rgb(ca), _rgb(cb)
    d = sum((x - y) ** 2 for x, y in zip(ra, rb)) ** 0.5
    la, lb = _sang_tuong_doi(ra), _sang_tuong_doi(rb)
    cr = (max(la, lb) + .05) / (min(la, lb) + .05)
    if d < 120:
        return f"áo hai người lệch màu chỉ {d:.0f}/255 ({ca} vs {cb}) — mắt đọc ra là một người"
    if cr < 1.9:
        return f"áo hai người tương phản sáng chỉ {cr:.2f} ({ca} vs {cb}) — người mù màu không tách được"
    return ""


def _sang_nen(luot):
    """(sáng trung bình, tỉ lệ điểm gần-đen) của TẤM NỀN mà tập này dùng.

    Đo trên tệp nền chứ không trên khung đã render: ở đó không có một nét vẽ nhân vật nào làm
    nhiễu, nên con số trả lời đúng câu hỏi "bối cảnh có tối không" thay vì "có bao nhiêu mực đen
    trên màn hình".
    """
    try:
        from PIL import Image
    except ImportError:
        return (None, None)
    ns = {l.get("nen") for l in luot if l.get("nen")}
    if not ns:
        return (None, None)
    PUB = os.path.join(GOC, "..", "engine-remotion", "public")
    ss = tt = 0.0
    n = 0
    for x in ns:
        f = os.path.join(PUB, x)
        if not os.path.exists(f):
            continue
        px = list(Image.open(f).convert("L").resize((160, 160)).getdata())
        ss += sum(px) / len(px)
        tt += sum(1 for v in px if v < 40) / len(px)
        n += 1
    return (ss / n, tt / n) if n else (None, None)


def cham_mot(k: dict) -> dict:
    import kich_hai as H

    ten_tep = H._ten_tep(k)
    pj = os.path.join(GOC, "out", f"v4_{ten_tep}.json")
    pv = os.path.join(GOC, "out", f"v4_{ten_tep}.mp4")
    if not os.path.exists(pj) or not os.path.exists(pv):
        return {"diem": 0, "bo_qua": True, "loi": ["chưa dựng — render rồi chấm lại"]}

    d = json.load(io.open(pj, encoding="utf-8"))
    luot, tu = d.get("luot") or [], d.get("tu") or []
    loi, diem = [], 100
    # Thời lượng tính NGAY ĐẦU: nhiều phép đo bên dưới cần nó, và bản trước tính ở giữa hàm nên
    # phép đo khung-đen chèn vào phía trên đọc phải một biến chưa có. Cùng họ lỗi "dùng biến
    # trước khi khai báo" đã dính hai lần bên TypeScript đêm nay (luật 7ae) — ở Python thì nó nổ
    # ngay nên rẻ hơn, nhưng gốc thì y hệt: thứ tự KỂ không phải thứ tự TÍNH.
    dur = _dai(pv) or 0

    # ── 25đ NHỊP HÀI ───────────────────────────────────────────────────────────────────
    qua_dai = [l for l in luot if len(str(l.get("nar") or "").split()) > 14]
    if qua_dai:
        diem -= 10
        loi.append(f"{len(qua_dai)} lượt dài quá 14 từ — nhịp hài chết ở lượt dài")
    lien = sum(1 for a, b in zip(luot, luot[1:]) if a.get("ai") == b.get("ai"))
    if lien:
        diem -= 8
        loi.append(f"{lien} chỗ một người nói hai lượt liền — mất cú va giữa hai người")
    if luot and not luot[-1].get("chot"):
        diem -= 7
        loi.append("lượt cuối không được đánh dấu là cú chốt")

    # ── 20đ KHỚP TIẾNG ─────────────────────────────────────────────────────────────────
    # Phép đo thật: gán từng từ về lượt chứa ĐIỂM BẮT ĐẦU của nó (đúng luật `PhuDe` đang dùng),
    # rồi so với số từ kịch bản. Lệch một từ nghĩa là một câu đọc ra sai người nói.
    lech = 0
    for l in luot:
        n_kb = len(str(l.get("nar") or "").split())
        n_that = len([w for w in tu if l["s"] - 0.02 <= w["t"] < l["e"] - 0.02])
        lech += abs(n_kb - n_that)
    if lech:
        diem -= min(20, 4 * lech)
        loi.append(f"lệch {lech} từ giữa kịch bản và mốc tiếng — phụ đề sẽ gán nhầm người nói")

    # ── KHÔNG ĐƯỢC CÓ KHUNG ĐEN Ở ĐẦU HAY CUỐI ────────────────────────────────────────
    # Anh dặn từ sớm: "tránh… kết thúc khung đen". Khung đen ở cuối là lỗi hay gặp nhất của mọi
    # dây chuyền dựng phim — thời lượng khai dài hơn nội dung một hai khung là ra ngay một nháy
    # đen, và trên YouTube Shorts (phát lặp vô hạn) thì cái nháy ấy chớp mỗi vòng lặp.
    # Đo ở 0,05 giây đầu và 0,12 giây trước hết phim, ngưỡng 60/255.
    for _ten, _ss in (("đầu", 0.05), ("cuối", max(0.0, (dur or 18) - 0.12))):
        _p = os.path.join("/tmp", f"_v4den{int(_ss*100)}.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{_ss:.2f}", "-i", pv,
                        "-vframes", "1", "-vf", "scale=120:-1", _p], capture_output=True, timeout=60)
        if not os.path.exists(_p):
            continue
        try:
            from PIL import Image
        except ImportError:
            break
        _px = list(Image.open(_p).convert("L").getdata())
        _tb = sum(_px) / len(_px)
        if _tb < 60:
            diem -= 10
            loi.append(f"khung {_ten} gần như ĐEN ({_tb:.0f}/255) — Shorts phát lặp nên cái nháy "
                       f"đen ấy chớp mỗi vòng")
            break

    # ── mốc lượt phải TRÙNG mốc từ ─────────────────────────────────────────────────────
    # 30/8 — Đây là phép đo bắt được một lỗi im lặng: mốc lượt từng lấy theo BIÊN ĐOẠN TIẾNG,
    # mà edge-tts chèn thêm im lặng ở đầu/cuối mỗi đoạn nó đọc. Kết quả là thẻ phụ đề nằm lại
    # gần một giây sau khi người ta nói xong, và thẻ sau bật lên trước khi người kia mở miệng.
    # Không gì hỏng, không gì báo — chỉ là tiếng và hình lệch nhau.
    # Phép đo: mốc mở lượt phải bằng thời điểm TỪ ĐẦU TIÊN của lượt ấy, mốc đóng phải bám từ
    # cuối. Lệch quá 0,25 giây là mắt bắt được.
    for l in luot:
        # BỎ QUA LƯỢT CHỐT. Mốc đóng của nó CỐ Ý dài ra để làm nhịp đuôi (quãng người nghe phản
        # ứng sau câu chốt) — đo nó bằng thước "tiếng phải khớp hình" là bắt nhầm một thiết kế.
        # Đây đúng là bẫy của mọi cổng kiểm: một ngoại lệ có chủ ý trông y hệt một lỗi.
        if l.get("chot"):
            continue
        ws = [w for w in tu if l["s"] - 0.02 <= w["t"] < l["e"] - 0.02]
        if not ws:
            continue
        lech_dau = abs(ws[0]["t"] - l["s"])
        lech_cuoi = abs((ws[-1]["t"] + ws[-1]["d"]) - l["e"])
        if lech_dau > 0.25 or lech_cuoi > 0.35:
            diem -= 10
            loi.append(f"tiếng lệch hình: lượt {str(l.get('nar'))[:26]!r} mở lệch "
                       f"{lech_dau:.2f}s, đóng lệch {lech_cuoi:.2f}s")
            break

    # ── nhịp máy quay không được GIẬT ở khe lặng ───────────────────────────────────────
    # 30/8 — Mỗi khe im lặng giữa hai lượt là một chỗ mã tra-cứu-theo-thời-gian có thể trượt.
    # Đo bằng cách đi qua TỪNG khe và hỏi: lượt nào đang có hiệu lực ở đây, và cỡ máy của nó có
    # phải cỡ của lượt vừa kết thúc không. Lệch nghĩa là khung sẽ giật.
    for _a, _b in zip(luot, luot[1:]):
        khe = _b["s"] - _a["e"]
        if khe <= 0:
            continue
        giua = _a["e"] + khe / 2
        # lượt cuối cùng đã BẮT ĐẦU trước `giua` — đúng luật `KichHai` đang dùng
        hl = max((x for x in luot if x["s"] <= giua), key=lambda x: x["s"], default=None)
        if hl is not None and hl.get("co") != _a.get("co"):
            diem -= 8
            loi.append(f"khe lặng ở giây {giua:.2f} nhảy cỡ máy {_a.get('co')} → {hl.get('co')} "
                       f"— khung sẽ giật")
            break

    # ── 10đ CHỮ TRONG KHUNG ────────────────────────────────────────────────────────────
    # `PhuDe` tự co cỡ chữ xuống tới 30. Nếu ở cỡ 30 mà dòng vẫn rộng hơn 920 thì mới là tràn.
    for l in luot:
        ws = str(l.get("nar") or "").split()
        nua = (len(ws) + 1) // 2
        for d2 in (ws[:nua], ws[nua:]):
            if sum(len(w) + 1 for w in d2) * 0.55 * 30 > 920:
                diem -= 10
                loi.append(f"phụ đề tràn mép ở lượt {str(l.get('nar'))[:34]!r}")
                break
        else:
            continue
        break

    # ── 10đ ĐỘ DÀI + LOGIC BỐI CẢNH ────────────────────────────────────────────────────
    # 30/8 — BỎ SÀN 15 GIÂY. Nó là con số TÔI TỰ ĐẶT, không phải luật của nền tảng: YouTube
    # Shorts không có độ dài tối thiểu. Và cái sàn tự đặt ấy đã kéo cả hệ thống đi sai — để đạt
    # nó, tôi cho nhịp đuôi giãn tới 5 giây, tức thêm 5 giây CHẾT HÌNH vào cuối mỗi video.
    # Anh xem và bắt ngay: "đoạn cuối đang bị hơi dài ko có ý nghĩa".
    # Một cây thước đặt sai làm sản phẩm xấu đi mà bảng điểm lại đẹp lên — nguy hiểm hơn nhiều so
    # với không đo gì cả. Nay chỉ chặn trần 60 giây (đây mới là luật thật của nền tảng) và chặn
    # sàn 8 giây (dưới mức ấy thì một cú va + một cú chốt không kịp diễn ra).
    if not (8 <= dur <= 60):
        diem -= 5
        loi.append(f"dài {dur:.0f}s — ngoài khoảng 8–60s")
    # 30/8, sửa lần HAI. Phép đo ở đây đã đổi chiều hai lần trong một ngày, và cả hai lần đều
    # đúng với thiết kế lúc ấy:
    #   · bản đầu  — thưởng cho "ba nền khác nhau" trong một video;
    #   · bản hai  — phạt vì "hai người không dịch chuyển tức thời giữa câu" (luật 7x);
    #   · bản này  — nền đổi mỗi lượt nhưng CÙNG MỘT ĐỊA ĐIỂM, chỉ khác GÓC NHÌN. Không ai
    #     dịch chuyển; máy quay đổi chỗ đứng, đúng như một cảnh phim thật được dựng.
    # Nên phép đo "nhiều nền là hỏng" phải GỠ ĐI, không phải nới ngưỡng — nó thuộc về một thiết
    # kế không còn nữa. Trục nền nay đo ở phần bổ sung bên dưới: THIẾU nền mới là hỏng.
    # Bài học: khi đổi luật thiết kế, việc đầu tiên là đi tìm phép đo cũ của luật ấy và gỡ nó.
    # Để lại thì hai phép đo chống nhau, và cây thước không bao giờ cho điểm nữa.

    # Nhịp thị giác vì thế phải do CỠ MÁY gánh: một tập phải có đủ ba cỡ, không thì khung nào
    # cũng như khung nào.
    _co = {l.get("co") for l in luot}
    if len(_co) < 3:
        diem -= 5
        loi.append(f"chỉ {len(_co)} cỡ máy ({', '.join(sorted(str(x) for x in _co))}) — "
                   f"một bối cảnh mà máy không đổi cỡ thì mọi khung như nhau")

    # ── phần của trục KHÔNG TRÙNG: hai nhân vật trong CÙNG một kênh ────────────────────
    _ao = hai_ao_co_khac_nhau(k)
    if _ao:
        diem -= 10
        loi.append(_ao)

    # ══════════════════════════════════════════════════════════════════════════════════
    # BỐN TRỤC BỔ SUNG — 30/8/2026
    # ----------------------------------------------------------------------------------
    # Anh hỏi thang điểm, và câu trả lời thật là: thước cũ cho 100/100 trong khi anh nhìn
    # thấy chưa đạt. Vì nó chỉ đo những thứ TÔI ĐÃ NGHĨ RA ĐỂ ĐO — khớp tiếng, độ sáng,
    # chữ trong khung, khung đen. Bốn thứ anh chỉ ra thì nó mù hoàn toàn.
    # Một cây thước chỉ đo được phần mình biết; chỗ nó im lặng KHÔNG có nghĩa là chỗ ấy tốt.
    # Nên mỗi lần anh chỉ ra một lỗi mà thước cho 100, việc đầu tiên là THÊM TRỤC, không
    # phải sửa mã rồi chạy lại thước cũ.
    # ══════════════════════════════════════════════════════════════════════════════════

    # ── 10đ NGỮ ĐIỆU: mỗi câu phải có nhịp/cao độ riêng ────────────────────────────────
    # Đo gián tiếp mà chắc: nếu ngữ điệu có đổi theo cảm xúc thì TỐC ĐỘ ĐỌC (từ/giây) của
    # các lượt phải khác nhau. Sáu lượt cùng một tốc độ nghĩa là giọng phẳng.
    _td = []
    for l in luot:
        ws = [w for w in tu if l["s"] - 0.02 <= w["t"] < l["e"] - 0.02]
        _dt = l["e"] - l["s"]
        if ws and _dt > 0.3:
            _td.append(len(ws) / _dt)
    if len(_td) >= 4:
        _tb = sum(_td) / len(_td)
        _lech = (sum((x - _tb) ** 2 for x in _td) / len(_td)) ** 0.5 / max(0.01, _tb)
        if _lech < 0.06:
            diem -= 10
            loi.append(f"giọng PHẲNG: tốc độ đọc các lượt chỉ lệch {_lech*100:.0f}% "
                       f"— câu hỏi, câu bực, câu chốt đọc như nhau")

    # ── 10đ NỀN PHẢI ĐỔI THEO LƯỢT ────────────────────────────────────────────────────
    # Ngược hẳn luật cũ (một tập một nền): nay mỗi lượt một GÓC của cùng địa điểm, nên số
    # nền phân biệt phải xấp xỉ số lượt. Một nền cho sáu lượt là khung đứng yên hai mươi giây.
    _nen = {l.get("nen") for l in luot if l.get("nen")}
    if len(_nen) < max(3, len(luot) - 2):
        diem -= 10
        loi.append(f"chỉ {len(_nen)} nền cho {len(luot)} lượt — khung gần như đứng yên")

    # ── 5đ ĐẠO CỤ KHÔNG ĐƯỢC CẦM SUỐT PHIM ────────────────────────────────────────────
    # Đạo cụ chỉ có nghĩa khi nó CÓ VIỆC (lượt mở, lượt chốt). Cầm ở mọi lượt thì nó đọc ra
    # là món đồ dán vào tay.
    _cam = sum(1 for l in luot if l.get("vatA") or l.get("vatB"))
    if _cam > max(2, len(luot) // 2):
        diem -= 5
        loi.append(f"đạo cụ cầm ở {_cam}/{len(luot)} lượt — đọc ra là đồ dán vào tay")

    # ── 5đ CÂU MỞ PHẢI LÀ HOOK ────────────────────────────────────────────────────────
    # Hook = mâu thuẫn lộ ngay, hoặc một con số cụ thể. Câu mở chỉ nêu tình trạng ("tôi đã
    # ở đây năm tháng") không cho người xem lý do nào để ở lại giây thứ ba.
    _mo = str((luot[0].get("nar") if luot else "") or "")
    _co_so = any(c.isdigit() for c in _mo)
    _co_va = any(w in _mo.lower() for w in (" but ", " never ", " already ", " still ",
                                            " and ", ". ", " for a ", " since "))
    if not (_co_so or _co_va):
        diem -= 5
        loi.append(f"câu mở không có hook (không số, không mâu thuẫn): {_mo[:44]!r}")

    # ── 15đ ĐỘ SÁNG ────────────────────────────────────────────────────────────────────
    # 30/8 — ĐỔI PHÉP ĐO, KHÔNG NỚI NGƯỠNG.
    # Bản cũ đếm "tỉ lệ điểm gần như đen" trên CẢ KHUNG, ngưỡng 8%. Với bộ hài thì phép ấy đo sai
    # thứ, và số đo chứng minh: khung OFFICE SMALL TALK có 12,8% điểm đen, trong khi chính tấm
    # NỀN của nó chỉ có 0,1% và sáng 212/255. Tức là gần như toàn bộ điểm đen đến từ NHÂN VẬT —
    # nét bao dày, tóc, quần, giày. Đó là ĐẶC TRƯNG TẠO HÌNH của phong cách hoạt hình nét dày,
    # không phải khung tối.
    # Nới ngưỡng cho qua thì là sửa thước để lấy điểm. Đường đúng là đo ĐÚNG THỨ MÌNH MUỐN BIẾT:
    #   · khung có đủ sáng để xem trên điện thoại không  -> sáng trung bình của khung (chặt hơn: 100)
    #   · nền có phải một cái hang tối không             -> đo TRÊN CHÍNH TẤM NỀN, nơi không có
    #     một nét vẽ nhân vật nào để làm nhiễu số đo.
    s, t = _sang(pv, dur or 18)
    if s is None:
        loi.append("(không đo được độ sáng)")
    elif s < 100:
        diem -= 10
        loi.append(f"khung tối: sáng trung bình {s:.0f}/255 (ngưỡng 100)")
    sn, tn = _sang_nen(luot)
    if sn is not None:
        if tn > 0.06:
            diem -= 5
            loi.append(f"nền tối: {tn*100:.0f}% điểm gần như đen (ngưỡng 6%)")
        elif sn < 110:
            diem -= 5
            loi.append(f"nền xám xịt: sáng trung bình {sn:.0f}/255 (ngưỡng 110)")

    return {"diem": max(0, diem), "bo_qua": False, "loi": loi,
            "giay": round(dur, 1), "luot": len(luot), "sang": round(s or 0)}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    a = ap.parse_args()

    import kich_hai as H
    chon = H.KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in H.KENH if x["ten"].replace(" ", "").upper() in vt]

    # ── 20đ KHÔNG TRÙNG — đo trên CẢ BỘ ────────────────────────────────────────────────
    # Trùng lặp là thuộc tính của một TẬP, không của một phần tử: một kênh không tự trùng nó.
    trung: dict = {}
    # Bốn kịch bản của một kênh phải nằm ở BỐN chỗ khác nhau — anh: "ko clip nào trùng lặp".
    for x in H.KENH:
        _b = [kb["boi"] for kb in H.KHO[x["de"]]]
        if len(set(_b)) < len(_b):
            trung.setdefault("boi_trong_kenh", {})[x["ten"]] = [x["ten"]]
    # 30/8 — HAI MƯƠI NHÂN VẬT PHẢI CÓ HAI MƯƠI KHUÔN MẶT.
    # Sau khi dựng lại mặt kiểu hoạt hình Mỹ, cả mười kênh dùng CHUNG một khuôn — chỉ khác chiều
    # cao, bề ngang, cỡ mắt, độ bạnh hàm. Bốn trục ấy đổi được DÁNG NGƯỜI nhưng không đổi được
    # KHUÔN MẶT: xem mười khung cạnh nhau vẫn ra một người tô lại, đúng thứ anh dặn tránh.
    # Trong hoạt hình, thứ tách hai nhân vật là BA NÉT — mũi, mắt, lông mày. Phép đo này chốt
    # rằng không hai nhân vật nào (kể cả ở hai kênh khác nhau) dùng chung một tổ hợp.
    _mat = {}
    for x in H.KENH:
        a, b = H._hai_bong(x)
        for ben, y in ((0, a), (1, b)):
            khoa = (y.get("kieuMui"), y.get("kieuMat"), y.get("kieuMay"), y.get("tiLeDau"))
            if None in khoa[:3]:
                trung.setdefault("net_mat_thieu", {})[x["ten"]] = [x["ten"]]
                continue
            _mat.setdefault(khoa, []).append(f"{x['ten']}/{'AB'[ben]}")
    _lap = {k: v for k, v in _mat.items() if len(v) > 1}
    if _lap:
        trung["net_mat"] = {k: v for k, v in list(_lap.items())[:3]}

    for truc in ("cap", "nen", "mau"):
        d: dict = {}
        for x in H.KENH:
            v = (x["a"], x["b"]) if truc == "cap" else (
                tuple(x["nen"]) if truc == "nen" else x["mau"])
            d.setdefault(v, []).append(x["ten"])
        lap = {v: t for v, t in d.items() if len(t) > 1}
        if lap:
            trung[truc] = lap

    print(f"\n{'ĐIỂM':>5}  {'KÊNH':<20} {'GIÂY':>5} {'LƯỢT':>5} {'SÁNG':>5}")
    print("─" * 92)
    bang, dat, hong, bo = {}, 0, 0, 0
    for k in chon:
        r = cham_mot(k)
        for truc, lap in trung.items():
            for _v, tens in lap.items():
                if k["ten"] in tens and not r.get("bo_qua"):
                    r["diem"] = max(0, r["diem"] - 20)
                    r["loi"].append(f"TRÙNG `{truc}` với: "
                                    f"{', '.join(t for t in tens if t != k['ten'])}")
                    break
        bang[k["ten"]] = r
        if r.get("bo_qua"):
            bo += 1
            mui = "⏭"
        elif r["diem"] >= NGUONG:
            dat += 1
            mui = "✅"
        else:
            hong += 1
            mui = "❌"
        print(f"{mui} {r['diem']:>3}  {k['ten']:<20} {r.get('giay', 0):>5} "
              f"{r.get('luot', 0):>5} {r.get('sang', 0):>5}")
        for x in r["loi"][:2]:
            print(f"         └ {str(x)[:84]}")

    print(f"\n  ✅ đạt {dat}  ·  ❌ hỏng {hong}  ·  ⏭ chưa dựng {bo}   (ngưỡng {NGUONG}/100)")
    if trung:
        for truc, lap in trung.items():
            print(f"  🚨 trùng `{truc}`: {lap}")
    else:
        print("  ✓ không trục nào (cặp nhân vật · bộ nền · bảng màu) bị hai kênh dùng chung")
    io.open(os.path.join(GOC, "chat_luong_v4.json"), "w", encoding="utf-8").write(
        json.dumps({"nguong": NGUONG, "kenh": bang}, ensure_ascii=False, indent=1))
    return 0 if hong == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
