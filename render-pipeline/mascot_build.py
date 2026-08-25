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


def dung_video(kenh: str, cfg: dict, story: dict, out: str, dai: bool = False,
               on_status=None) -> tuple[bool, dict]:
    """Dựng MỘT video mascot. Trả (ok, info). `story` = kết quả generate_toon (title/dialog/frames)."""
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
    ten_stage = (MC.ten_san_khau(kenh) or ["stage"])[0]
    if not MR.da_co_san_khau(kenh, ten_stage):
        return False, {"loi": f"{kenh}: sân khấu '{ten_stage}' chưa dựng"}
    # CHỈ DÙNG LỚP CÓ FILE THẬT. 25/8 — pilot 11:07Z chết ở đây: sân khấu khai 4 lớp nhưng `far`
    # tách nền hụt (FLUX vẽ nền có chi tiết) nên không có file, code vẫn bảo Remotion nạp
    # `stages/.../far.png` -> "Error loading image" giết cả lượt render. Khai báo là Ý ĐỊNH,
    # thư mục mới là SỰ THẬT — luôn lọc theo sự thật trước khi đưa vào props.
    _goc_stage = os.path.join(DS.ENG, "public", "stages", kenh.upper(), ten_stage)
    stage_lop = [L for L in MC.san_khau_cua(kenh, ten_stage)
                 if os.path.exists(os.path.join(_goc_stage, f"{L['lop']}.png"))]
    if len(stage_lop) < 2:
        return False, {"loi": f"{kenh}/{ten_stage}: chỉ có {len(stage_lop)} lớp nền — hết chiều sâu"}
    _thieu = [L["lop"] for L in MC.san_khau_cua(kenh, ten_stage)
              if L not in stage_lop]
    if _thieu:
        print(f"   ℹ️ sân khấu {ten_stage}: thiếu lớp {_thieu} (tách nền hụt) — dựng bằng "
              f"{len(stage_lop)} lớp còn lại, vẫn đủ chiều sâu.")

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
    clips, subs, moc, t = [], [], [], 0.0
    for i, d in enumerate(story.get("dialog") or []):
        who = (d.get("who") or "A").upper()
        mp3 = os.path.join(pub, f"line{i:02d}.mp3")
        dur, w, _ = TK.synth(d.get("line", ""), mp3, voice=giong.get(who), rate=nhip.get(who),
                             pitch=cao.get(who))
        clips.append((mp3, t))
        for x in w:
            subs.append({"t": round(x["t"] + t, 3), "d": x["d"], "w": x["w"]})
        moc.append((t, t + dur))
        t += dur + NGHI_CAU
    if not clips:
        return False, {"loi": "không có câu thoại nào"}
    tong = t
    tong_frame = int(tong * FPS) + FPS // 2

    st("rendering", "Trộn tiếng")
    track = os.path.join(pub, "voice.mp3")
    DS._mix_track(clips, tong, track)
    mouth = _rms_12hz(track, tong)

    # ── XẾP CẢNH + DỰNG ─────────────────────────────────────────────────────────────────
    shots = _xep_canh(story, moc, tong_frame, cast, stage_lop, ten_stage)
    if not shots:
        return False, {"loi": "không xếp được cảnh nào"}
    # vị trí đứng: 1 nhân vật thì giữa, 2 nhân vật thì hai bên và quay mặt vào nhau
    if len(cast) >= 2:
        dan = [{"id": cast[0]["id"], "x": 30, "scale": 1.0},
               {"id": cast[1]["id"], "x": 70, "scale": 0.96, "flip": True}]
    else:
        dan = [{"id": cast[0]["id"], "x": 50, "scale": 1.05}]

    props = {"channel": kenh.upper(), "cast": dan, "shots": shots, "mouth": mouth,
             "title": story.get("title", ""), "accent": cfg.get("accent", "#F5B301"),
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
    # ghép tiếng vào hình
    subprocess.run(["ffmpeg", "-y", "-i", v, "-i", track, "-c:v", "copy", "-c:a", "aac",
                    "-shortest", out], capture_output=True, timeout=900, check=True)
    ok, info = DS.qc(out)
    info["shots"] = len(shots)
    info["mouth_mau"] = len(mouth)
    return ok, info
