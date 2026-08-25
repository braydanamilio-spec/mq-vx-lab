#!/usr/bin/env python3
"""DỰNG VIDEO HOẠT HÌNH 2D từ rig nhân vật + sân khấu đa tầng (25/8/2026).

Khác bản toon cũ ở đúng một điểm cốt tử: **KHÔNG vẽ lại nhân vật cho mỗi cảnh**.
Nhân vật và bối cảnh đã nằm sẵn trong `engine-remotion/public/` (mascot_rig.py dựng một lần),
nên ở đây chỉ còn ba việc rẻ: viết skit → thu 2 giọng → xếp cảnh, rồi giao Remotion diễn.

Hệ quả tính được bằng số:
  • quota/video : 0 lượt vẽ (bản cũ: 5-8 ảnh FLUX/video)
  • drift       : 0 (không vẽ thì không lệch)
  • chuyển động : do `MascotStage` nội suy TỪNG KHUNG ở 30fps, không phải ảnh tĩnh đổi nhịp

NHÉP MỒM
--------
Đo RMS của chính file tiếng, 12 mẫu/giây, chuẩn hoá 0..1 -> `mouth[]`. `MascotStage` lấy mảng này
đổi giữa `talk_closed`/`talk_open` và nhún người theo. Vì đo từ tiếng THẬT nên mồm khớp lời thật,
không phải mở-đóng ngẫu nhiên.
"""
from __future__ import annotations

import json
import math
import os
import subprocess

FPS = 30
MOUTH_HZ = 12
NGHI_CAU = 0.22          # khoảng lặng giữa hai câu thoại (giây) — nhịp hài cần nhịp thở


def _rms_12hz(mp3: str, tong_giay: float) -> list[float]:
    """Biên độ tiếng theo 1/12 giây, chuẩn hoá 0..1. Hỏng thì trả mảng rỗng (mồm sẽ mấp máy nhẹ)."""
    n = max(1, int(tong_giay * MOUTH_HZ) + 2)
    try:
        raw = subprocess.run(
            ["ffmpeg", "-v", "quiet", "-i", mp3, "-ac", "1", "-ar", "8000",
             "-f", "s16le", "-"], capture_output=True, timeout=180, check=True).stdout
    except Exception as e:
        print(f"   ⚠️ đo biên độ mồm hỏng ({str(e)[:60]}) — mồm sẽ chỉ mấp máy nhẹ")
        return []
    import array
    mau = array.array("h")
    mau.frombytes(raw[: len(raw) // 2 * 2])
    moi_o = max(1, int(8000 / MOUTH_HZ))
    ra = []
    for i in range(n):
        a, b = i * moi_o, min(len(mau), (i + 1) * moi_o)
        if a >= b:
            ra.append(0.0); continue
        s = 0
        for v in mau[a:b]:
            s += v * v
        ra.append(math.sqrt(s / (b - a)))
    dinh = max(ra) or 1.0
    # nén nhẹ (căn bậc hai) để âm nhỏ vẫn làm mồm động — nói khẽ mà mồm đứng im trông như hỏng
    return [round(min(1.0, math.sqrt(v / dinh)), 3) for v in ra]


def _xep_canh(story: dict, moc: list, tong_frame: int, cast: list, stage_lop: list,
              ten_stage: str) -> list:
    """Biến kịch bản + mốc thời gian từng câu thành danh sách CẢNH cho MascotStage.

    Một 'cảnh' = một góc máy giữ trong vài câu thoại. Lấy `frames[].line_idx` của kịch bản làm
    mốc đổi cảnh (đó chính là chỗ tác giả thấy nên đổi khung), rồi xoay vòng kiểu máy quay
    in/left/out/right cho khỏi đơn điệu. Câu CUỐI luôn shake = cú chốt punchline."""
    dl = story.get("dialog") or []
    moc_doi = sorted({int(f.get("line_idx") or 0) for f in (story.get("frames") or [])} | {0})
    kieu = ["in", "left", "still", "right", "out"]
    shots = []
    for k, li in enumerate(moc_doi):
        if li >= len(dl):
            continue
        het = moc_doi[k + 1] if k + 1 < len(moc_doi) else len(dl)
        f0 = int(moc[li][0] * FPS)
        f1 = int((moc[het - 1][1] if het - 1 < len(moc) else moc[-1][1]) * FPS)
        who = (dl[li].get("who") or "A").upper()
        # id nhân vật theo vai A/B đã khai trong mascot_cast
        speaker = next((c["id"] for c in cast if str(c.get("vai", "A")).upper() == who), cast[0]["id"])
        pose = {}
        for c in cast:
            if c["id"] != speaker:
                # người KHÔNG nói vẫn phải có thái độ: nghe → phản ứng → đắc chí, xoay theo cảnh
                pose[c["id"].upper()] = ["idle", "smug", "react", "idle", "point"][k % 5]
        shots.append({
            "stage": ten_stage,
            "layers": [{"lop": L["lop"], "xa": L["xa"]} for L in stage_lop],
            "speaker": speaker, "pose": pose,
            "from": f0, "dur": max(FPS // 2, f1 - f0),
            "cam": kieu[k % len(kieu)],
            "shake": het >= len(dl),
            "line": dl[li].get("line", ""),
        })
    if shots:
        shots[-1]["dur"] = max(shots[-1]["dur"], tong_frame - shots[-1]["from"])
    return shots


def dung_video(kenh: str, cfg: dict, story, out: str, dai: bool = False,
               on_status=None) -> tuple[bool, dict]:
    """Dựng MỘT video mascot. Trả (ok, info).

    `story` = một skit (dict) HOẶC danh sách skit (list) cho bản dài.

    25/8 — vì sao long phải là TUYỂN TẬP: `generate_toon` viết skit 18-30 giây (đúng thiết kế cho
    short). Dùng thẳng nó cho long thì ra 22 giây, QC chặn "quá ngắn < 45s" — mất trắng lượt render.
    Long đúng nghĩa là 3 skit nối nhau, MỖI SKIT MỘT SÂN KHẤU: vừa đủ dài, vừa đổi cảnh nên không
    chán, và không tốn thêm lượt vẽ nào (sân khấu đã dựng sẵn trong rig)."""
    import datastory_ci as DS
    import mascot_cast as MC
    import mascot_rig as MR
    import tts_karaoke as TK
    st = on_status or (lambda *a, **k: None)

    cast = MC.cast_cua(kenh)
    if not cast:
        return False, {"loi": f"{kenh}: chưa khai dàn nhân vật (mascot_cast.py)"}
    if not MR.da_co_rig(kenh, cast):
        return False, {"loi": f"{kenh}: rig nhân vật chưa dựng — chạy mascot_rig.py trước"}
    stories = story if isinstance(story, list) else [story]
    stories = [x for x in stories if isinstance(x, dict) and x.get("dialog")]
    if not stories:
        return False, {"loi": "không có skit nào"}
    # mỗi skit một sân khấu (xoay vòng qua các sân khấu đã dựng) -> long đổi cảnh, không chán
    _sk_co = [t for t in MC.ten_san_khau(kenh) if MR.da_co_san_khau(kenh, t)]
    if not _sk_co:
        return False, {"loi": f"{kenh}: chưa sân khấu nào dựng xong"}
    ten_stage = _sk_co[0]
    # CHỈ DÙNG LỚP CÓ FILE THẬT. 25/8 — pilot 11:07Z chết ở đây: sân khấu khai 4 lớp nhưng `far`
    # tách nền hụt (FLUX vẽ nền có chi tiết) nên không có file, code vẫn bảo Remotion nạp
    # `stages/.../far.png` -> "Error loading image" giết cả lượt render. Khai báo là Ý ĐỊNH,
    # thư mục mới là SỰ THẬT — luôn lọc theo sự thật trước khi đưa vào props.
    def _lop_cua(ten: str) -> list:
        goc = os.path.join(DS.ENG, "public", "stages", kenh.upper(), ten)
        return [L for L in MC.san_khau_cua(kenh, ten)
                if os.path.exists(os.path.join(goc, f"{L['lop']}.png"))]
    if len(_lop_cua(ten_stage)) < 2:
        return False, {"loi": f"{kenh}/{ten_stage}: dưới 2 lớp nền — hết chiều sâu"}

    # ── THU TIẾNG: mỗi câu một giọng theo vai, nối lại có nhịp nghỉ ──────────────────────
    st("writing", "Thu tiếng 2 vai")
    sl = DS.slug(kenh)
    pub = os.path.join(DS.PUB, sl)
    os.makedirs(pub, exist_ok=True)
    giong = {str(c.get("vai", "A")).upper(): (cfg.get(f"voice_{str(c.get('vai','a')).lower()}")
                                              or cfg.get("voice") or "en-US-GuyNeural")
             for c in cast}
    nhip = {str(c.get("vai", "A")).upper(): (cfg.get(f"rate_{str(c.get('vai','a')).lower()}") or "+0%")
            for c in cast}
    # CAO ĐỘ RIÊNG TỪNG VAI — thứ khiến hai nhân vật KHÔNG lẫn vào nhau. Giọng neural mặc định đều
    # là giọng đọc bản tin; lệch cao độ 20-40Hz giữa hai vai là khán giả phân biệt được ngay giây
    # đầu, không cần nhìn hình. Miễn phí, không tốn thêm lượt gọi nào.
    cao = {str(c.get("vai", "A")).upper(): (cfg.get(f"pitch_{str(c.get('vai','a')).lower()}") or "+0Hz")
           for c in cast}
    clips, subs, t = [], [], 0.0
    moc_theo_skit = []          # mốc thời gian từng câu, tách theo skit
    NGHI_SKIT = 0.7             # nhịp nghỉ giữa hai skit — khán giả cần một nhịp để "sang chuyện"
    for si, sk in enumerate(stories):
        moc = []
        for i, d in enumerate(sk.get("dialog") or []):
            who = (d.get("who") or "A").upper()
            mp3 = os.path.join(pub, f"s{si}_line{i:02d}.mp3")
            dur, w, _ = TK.synth(d.get("line", ""), mp3, voice=giong.get(who), rate=nhip.get(who),
                                 pitch=cao.get(who))
            clips.append((mp3, t))
            for x in w:
                subs.append({"t": round(x["t"] + t, 3), "d": x["d"], "w": x["w"]})
            moc.append((t, t + dur))
            t += dur + NGHI_CAU
        moc_theo_skit.append(moc)
        t += NGHI_SKIT
    if not clips:
        return False, {"loi": "không có câu thoại nào"}
    tong = t
    tong_frame = int(tong * FPS) + FPS // 2

    st("rendering", "Trộn tiếng")
    track = os.path.join(pub, "voice.mp3")
    DS._mix_track(clips, tong, track)
    mouth = _rms_12hz(track, tong)

    # ── XẾP CẢNH + DỰNG ─────────────────────────────────────────────────────────────────
    shots = []
    for si, sk in enumerate(stories):
        sk_ten = _sk_co[si % len(_sk_co)]          # xoay sân khấu theo skit
        sk_lop = _lop_cua(sk_ten)
        if len(sk_lop) < 2:
            sk_ten, sk_lop = ten_stage, _lop_cua(ten_stage)
        het_skit = int((moc_theo_skit[si][-1][1] + NGHI_SKIT) * FPS) if moc_theo_skit[si] else tong_frame
        shots += _xep_canh(sk, moc_theo_skit[si], het_skit, cast, sk_lop, sk_ten)
    if not shots:
        return False, {"loi": "không xếp được cảnh nào"}
    shots[-1]["dur"] = max(shots[-1]["dur"], tong_frame - shots[-1]["from"])
    # vị trí đứng: 1 nhân vật thì giữa, 2 nhân vật thì hai bên và quay mặt vào nhau
    if len(cast) >= 2:
        dan = [{"id": cast[0]["id"], "x": 30, "scale": 1.0},
               {"id": cast[1]["id"], "x": 70, "scale": 0.96, "flip": True}]
    else:
        dan = [{"id": cast[0]["id"], "x": 50, "scale": 1.05}]

    props = {"channel": kenh.upper(), "cast": dan, "shots": shots, "mouth": mouth,
             "title": stories[0].get("title", ""), "accent": cfg.get("accent", "#F5B301"),
             "subs": subs}
    pf = os.path.join(DS.PUB, f"{sl}_mascot.json")
    json.dump(props, open(pf, "w"), ensure_ascii=False)

    comp = "MascotLong" if dai else "MascotShort"
    st("rendering", f"Render {comp} ({len(shots)} cảnh · {tong:.0f}s)")
    v = os.path.join(DS.PUB, sl, "_silent.mp4")
    DS.run_render_cmd(["npx", "remotion", "render", "src/index.ts", comp, v,
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=3600, label=f"{comp}({kenh})")
    # GHÉP TIẾNG — PHẢI CHỈ ĐỊNH LUỒNG. 25/8: bản đầu không có `-map`, mà Remotion xuất video KÈM
    # một track âm CÂM; ffmpeg khi không được chỉ định thì tự "chọn luồng tốt nhất" và vớ đúng
    # track câm đó -> video ra đủ hình, đủ độ dài, có luồng audio, nhưng -91dB. QC bắt được
    # ("CÂM (mức âm -91.0dB)") nhưng mất trắng cả lượt render. Chỉ định rõ: hình lấy từ input 0,
    # tiếng lấy từ input 1.
    subprocess.run(["ffmpeg", "-y", "-i", v, "-i", track,
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", out], capture_output=True, timeout=900, check=True)
    # KIỂM NGAY TẠI CHỖ: đo mức âm của file vừa ghép. Sai `-map` là lỗi im lặng — file vẫn đúng
    # mọi mặt trừ việc không có tiếng — nên phải đo, đừng tin là đã ghép đúng.
    try:
        _o = subprocess.run(["ffmpeg", "-i", out, "-af", "volumedetect", "-f", "null", "-"],
                            capture_output=True, timeout=300).stderr.decode("utf-8", "ignore")
        import re as _re
        _m = _re.search(r"mean_volume:\s*(-?[\d.]+) dB", _o)
        if _m and float(_m.group(1)) < -60:
            return False, {"loi": f"ghép tiếng hỏng: mức âm {_m.group(1)}dB (câm)"}
    except Exception:
        pass
    ok, info = DS.qc(out)
    info["shots"] = len(shots)
    info["skit"] = len(stories)
    info["mouth_mau"] = len(mouth)
    return ok, info
