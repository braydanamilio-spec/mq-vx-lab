#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KLING STUDIO — sinh BẢNG CHỤP cho phim ngắn hài, để người bấm Kling và máy lo phần còn lại.

VÌ SAO LÀM KIỂU NÀY (28/8/2026)
--------------------------------
Anh có TÀI KHOẢN WEB Kling trả phí, KHÔNG có API. Hai gói đó Kling tách có chủ đích, nên hệ này
KHÔNG tự động hoá trình duyệt của anh — đường đó dễ mất tài khoản trả phí nhất, mà anh có mấy
tài khoản nên rủi ro nhân lên.

Nhưng phần lớn thời gian anh mất KHÔNG phải lúc bấm nút. Đo theo lần thử 09/08: cái tốn thời gian
là nghĩ phân cảnh, viết prompt sao cho Kling không trôi, sửa tới sửa lui, rồi ghép lại. Máy làm
được cả ba phần đó. Anh chỉ còn việc dán và tải về.

BÀI HỌC 09/08 ĐÃ TRẢ GIÁ, ĐỪNG HỌC LẠI
--------------------------------------
Thử thật trên gói Ultra: ảnh Kling đẹp, NHƯNG prompt chữ thuần TRÔI — xin "Pompeii năm 79, góc
nhìn người đứng dưới đất" thì ra làng Ý hiện đại chụp từ trên cao. Hai thứ trôi mạnh nhất là
GÓC MÁY và THỜI ĐẠI. Nên mọi prompt sinh ra ở đây BẮT BUỘC ghim cả hai bằng chữ, ngay đầu câu.

ĐIỂM MẠNH / ĐIỂM YẾU CỦA KLING (dùng để chấm prompt, không phải để trang trí)
    mạnh : một chủ thể rõ · một hành động rõ · khí quyển, khói, ánh sáng, chuyển động chậm
           · động vật · đồ vật · vật lý siêu thực
    yếu  : chữ đọc được (ra ký tự loằng ngoằng) · mặt người cận cảnh diễn xuất · bàn tay
           · thoại/khớp miệng · đám đông chuyển động nhanh
Hài hình ảnh hợp Kling; hài thoại thì không. Nên bộ sinh này chỉ đẻ ra GAG HÌNH.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))

# Số cảnh và độ dài — theo đúng thứ anh chốt: mỗi cảnh 3-6 giây, ghép lại thành short.
CANH_MIN, CANH_MAX = 5, 8
GIAY_MIN, GIAY_MAX = 3, 6

SYS = """You write VISUAL-GAG comedy shot sheets for Kling AI video generation.

HARD LIMITS OF KLING — every shot you write must live inside them:
- NO readable text anywhere (signs, labels, phone screens). Kling renders text as gibberish.
- NO close-up human faces performing expressions. NO hands as the subject. NO dialogue or lip-sync.
- ONE clear subject doing ONE clear action per shot. Two interacting people is already risky.
- Kling is strong at: animals, objects, surreal physics, atmosphere, smoke, light, slow motion.

CAMERA AND SETTING DRIFT IS THE #1 FAILURE. A prompt that does not pin the camera drifts to
aerial drone shots; a prompt that does not pin the era/place drifts to generic modern stock.
So EVERY prompt must start by naming the shot type and the exact setting.

COMEDY RULES:
- Shot 1 IS the hook: open ON the absurd image. No setup shot, no establishing shot. The viewer
  must see something wrong in the first second.
- Then: normal beat -> escalation -> bigger escalation -> payoff.
- The humor must be VISIBLE. If the joke needs a caption or a line of dialogue to land, it is the
  wrong joke for this format.
- American everyday settings work best: drive-thru, gym, big-box store parking lot, suburban lawn,
  laundromat, office break room, gas station.

Answer with JSON only."""

SCHEMA = """Return exactly this JSON shape:
{
  "title": "short punchy English title, under 60 chars, no clickbait punctuation",
  "logline": "one sentence describing the gag",
  "hook_line": "the on-screen caption for the first 1.5s, under 8 words, ALL CAPS",
  "scenes": [
    {
      "n": 1,
      "beat": "hook | setup | turn | escalate | payoff | button",
      "sec": 4,
      "prompt": "Kling prompt. MUST begin with the shot type and setting, e.g. 'Static eye-level shot inside a suburban American garage:' then the subject and the single action. Describe light and mood. English only.",
      "caption": "optional on-screen text, under 8 words, or empty string"
    }
  ],
  "self_score": {"total": 0-100, "kling_safe": 0-100, "funny": 0-100}
}
Rules: 5-8 scenes. Each sec between 3 and 6. Scene 1 beat must be "hook". Last scene beat must be
"payoff" or "button"."""

# Chữ báo hiệu prompt sẽ trôi hoặc chạm điểm yếu — đo bằng chữ vì không đo được bằng ảnh trước khi vẽ.
CAM_KY = [
    ("text", "chữ đọc được — Kling vẽ ra ký tự loằng ngoằng"),
    ("sign", "biển chữ — cùng lỗi với text"),
    ("label", "nhãn chữ"),
    ("writing", "chữ viết"),
    ("close-up of his face", "mặt cận cảnh diễn xuất"),
    ("close-up of her face", "mặt cận cảnh diễn xuất"),
    ("facial expression", "biểu cảm mặt — Kling yếu nhất chỗ này"),
    ("talking", "thoại/khớp miệng"),
    ("speaking", "thoại/khớp miệng"),
    ("says", "thoại"),
    ("crowd running", "đám đông chuyển động nhanh"),
    ("hands typing", "bàn tay làm chủ thể"),
]
# Prompt phải GHIM GÓC MÁY. Thiếu là trôi lên drone — lỗi đã trả giá 09/08.
GHIM_MAY = ["static", "eye-level", "low angle", "high angle", "over-the-shoulder", "wide shot",
            "medium shot", "tracking", "handheld", "locked-off", "close shot", "top-down",
            "dolly", "pan", "tilt", "slow push"]


def _validate(d: dict) -> list[str]:
    """Chấm bảng chụp theo ĐÚNG giới hạn của Kling. Trả danh sách lỗi để bắt model viết lại."""
    e = []
    if not isinstance(d, dict):
        return ["không phải JSON object"]
    sc = d.get("scenes")
    if not isinstance(sc, list):
        return ["thiếu mảng scenes"]
    if not (CANH_MIN <= len(sc) <= CANH_MAX):
        e.append(f"cần {CANH_MIN}-{CANH_MAX} cảnh, đang có {len(sc)}")
    if not str(d.get("hook_line") or "").strip():
        e.append("thiếu hook_line (chữ 1,5 giây đầu)")
    for i, s in enumerate(sc, 1):
        if not isinstance(s, dict):
            e.append(f"cảnh {i}: không phải object"); continue
        p = str(s.get("prompt") or "")
        low = p.lower()
        try:
            giay = float(s.get("sec") or 0)
        except Exception:
            giay = 0
        if not (GIAY_MIN <= giay <= GIAY_MAX):
            e.append(f"cảnh {i}: sec={s.get('sec')} — phải trong {GIAY_MIN}-{GIAY_MAX} giây")
        if len(p) < 40:
            e.append(f"cảnh {i}: prompt quá ngắn ({len(p)} ký tự) — Kling cần mô tả cụ thể")
        if not any(k in low for k in GHIM_MAY):
            e.append(f"cảnh {i}: prompt KHÔNG ghim góc máy -> sẽ trôi thành cảnh drone "
                     f"(thêm 'static eye-level shot', 'low angle'…)")
        for tu, ly in CAM_KY:
            if tu in low:
                e.append(f"cảnh {i}: có '{tu}' — {ly}")
                break
        cap = str(s.get("caption") or "")
        if cap and len(cap.split()) > 8:
            e.append(f"cảnh {i}: caption {len(cap.split())} chữ — quá 8 chữ thì đọc không kịp")
    if sc and str((sc[0] or {}).get("beat", "")).lower() != "hook":
        e.append("cảnh 1 phải là beat 'hook' — mở thẳng vào hình ảnh sai trái, không dựng bối cảnh")
    if sc and str((sc[-1] or {}).get("beat", "")).lower() not in ("payoff", "button"):
        e.append("cảnh cuối phải là 'payoff' hoặc 'button'")
    tong = sum(float((s or {}).get("sec") or 0) for s in sc if isinstance(s, dict))
    if not (20 <= tong <= 45):
        e.append(f"tổng {tong:.0f}s — short nên nằm trong 20-45 giây")
    return e


def bang_chup(d: dict) -> str:
    """Xuất bảng chụp dạng markdown — thứ anh mở ra, dán từng prompt vào Kling."""
    r = [f"# {d.get('title', '(chưa có tên)')}", ""]
    r.append(f"**Gag:** {d.get('logline', '')}")
    r.append(f"**Chữ hook (1,5s đầu):** `{d.get('hook_line', '')}`")
    sc = d.get("scenes") or []
    tong = sum(float((s or {}).get('sec') or 0) for s in sc)
    r.append(f"**{len(sc)} cảnh · {tong:.0f} giây**")
    r.append("")
    r.append("> Mỗi cảnh: dán `prompt` vào Kling, để đúng số giây, tải về đặt tên "
             "`scene-01.mp4`, `scene-02.mp4`… rồi thả cả thư mục vào Drive. Hệ tự ghép.")
    r.append("")
    for s in sc:
        if not isinstance(s, dict):
            continue
        n = int(s.get("n") or 0)
        r.append(f"## Cảnh {n:02d} — {s.get('beat', '')} · {s.get('sec', '?')}s")
        if s.get("caption"):
            r.append(f"*Chữ trên màn hình:* `{s['caption']}`")
        r.append("")
        r.append("```")
        r.append(str(s.get("prompt", "")).strip())
        r.append("```")
        r.append(f"→ lưu thành `scene-{n:02d}.mp4`")
        r.append("")
    return "\n".join(r)


def sinh(y_tuong: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh một bảng chụp hài cho Kling. Viết lại tới khi qua được mọi giới hạn của Kling."""
    import content_brain as CB
    genai = CB._genai(api_key)
    mname = model_name or CB.MODEL
    model = genai.GenerativeModel(mname, system_instruction=SYS)
    tranh = ("\nAvoid these ideas already used: " + " | ".join(list(avoid)[-40:])) if avoid else ""
    base = f'Idea: "{y_tuong}".\n{SCHEMA}{tranh}'
    fb, cuoi = "", None
    for lan in range(1, CB.MAX_TRIES + 1):
        p = base + (f"\n\nPrevious attempt rejected for: {fb}\nFix every point." if fb else "")
        try:
            resp = model.generate_content(
                p, generation_config={"temperature": 0.95, "response_mime_type": "application/json"},
                request_options=CB.GEN_OPTS)
        except Exception as ex:
            msg = str(ex).lower()
            if CB._loi_tam_thoi(msg) and lan < CB.MAX_TRIES:
                CB._tam_nghi(lan); fb = ""; continue
            raise
        try:
            d = CB._extract_json(resp.text)
        except Exception as ex:
            fb = f"JSON lỗi ({ex})."; continue
        loi = _validate(d)
        d["_attempt"] = lan
        cuoi = d
        if loi:
            fb = "; ".join(loi[:6])
            print(f"   ↻ kling vòng {lan}: {fb[:110]}")
            continue
        print(f"   ✅ KLING đạt vòng {lan}: {len(d.get('scenes') or [])} cảnh — {d.get('title')!r}")
        return d
    # Hết vòng: trả bản cuối kèm lỗi còn lại, để người xem còn sửa tay được — hơn là ném đi sạch.
    if cuoi is not None:
        cuoi["_con_loi"] = _validate(cuoi)
        print(f"   ⚠️ kling: {CB.MAX_TRIES} vòng chưa sạch lỗi — trả bản cuối kèm "
              f"{len(cuoi['_con_loi'])} điểm cần sửa tay")
        return cuoi
    raise Exception("Kling: không sinh được bảng chụp nào.")


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Sinh bảng chụp Kling cho phim ngắn hài")
    ap.add_argument("y_tuong", nargs="+", help="ý tưởng, ví dụ: 'chó đi làm ca đêm ở cửa hàng tiện lợi'")
    ap.add_argument("--ra", default="", help="thư mục ghi kết quả (mặc định: out/kling/<slug>)")
    a = ap.parse_args()
    yt = " ".join(a.y_tuong)
    d = sinh(yt)
    slug = re.sub(r"[^a-z0-9]+", "-", str(d.get("title") or yt).lower()).strip("-")[:48] or "kling"
    ra = a.ra or os.path.join(GOC, "out", "kling", slug)
    os.makedirs(ra, exist_ok=True)
    io.open(os.path.join(ra, "shots.json"), "w", encoding="utf-8").write(
        json.dumps(d, ensure_ascii=False, indent=2))
    io.open(os.path.join(ra, "BANG_CHUP.md"), "w", encoding="utf-8").write(bang_chup(d))
    print(f"\n📁 {ra}")
    print("   BANG_CHUP.md — mở cái này, dán từng prompt vào Kling")
    print("   shots.json   — hệ đọc để ghép video sau khi anh thả clip vào")
    return 0


if __name__ == "__main__":
    sys.exit(main())
