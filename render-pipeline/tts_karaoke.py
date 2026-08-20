"""
tts_karaoke.py — Sinh GIỌNG + KARAOKE word-timing từ edge-tts (FREE, không key).

Fix lỗi #1: "karaoke không chạy" — vì race_long.py chưa sinh word-timing.
edge-tts trả WordBoundary (offset/duration theo đơn vị 100ns) -> đổi ra giây
-> đúng format Word{t,d,w,si} mà RaceLong/KaraokeCaption cần.

Dùng:
    from tts_karaoke import synth
    dur, subs, srt = synth("California leads. Texas is catching up fast.",
                           "voice.mp3", voice="en-US-AndrewNeural", rate="+6%")
    # subs = [{"t":0.0,"d":0.42,"w":"California","si":0}, ...]  (giây)

CLI test:
    python tts_karaoke.py --text "Your text" --out voice.mp3
"""
from __future__ import annotations
import argparse
import asyncio
import json
import os
import re

DEFAULT_VOICE = os.environ.get("TTS_VOICE", "en-US-AndrewNeural")   # warm/confident US male
DEFAULT_RATE = os.environ.get("TTS_RATE", "+6%")                    # nhanh nhẹ cho hợp nhịp viral


def _sentence_bounds(text: str) -> list[int]:
    """Trả mảng cumulative word-count theo từng câu -> để gán si (chỉ số câu) cho từng từ."""
    sents = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    bounds, run = [], 0
    for s in sents:
        run += len([w for w in s.split() if w])
        bounds.append(run)
    return bounds or [10**9]


def _si_for(word_index: int, bounds: list[int]) -> int:
    for si, b in enumerate(bounds):
        if word_index < b:
            return si
    return len(bounds) - 1


async def _run(text: str, mp3_path: str, voice: str, rate: str):
    """Ghi mp3 + gom SentenceBoundary (edge-tts 7.x không có WordBoundary)."""
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate)
    sentences = []
    with open(mp3_path, "wb") as f:
        async for chunk in comm.stream():
            t = chunk.get("type")
            if t == "audio":
                f.write(chunk["data"])
            elif t in ("SentenceBoundary", "WordBoundary"):
                sentences.append({
                    "t": chunk["offset"] / 1e7,      # 100ns -> giây
                    "d": chunk["duration"] / 1e7,
                    "w": chunk["text"],
                })
    return sentences


LEAD = 0.10   # hiện chữ SỚM hơn giọng ~0.1s (mắt đọc trước tai nghe -> cảm giác khớp)

def _expand_words(sentences: list[dict], si_offset: int = 0) -> list[dict]:
    """Mỗi câu -> chia thời lượng ra từng TỪ theo độ dài chữ + có nhịp nghỉ ở dấu câu (siết sync)."""
    words = []
    for si, s in enumerate(sentences):
        toks = [w for w in re.split(r"\s+", s["w"].strip()) if w]
        if not toks:
            continue
        # trọng số = số ký tự chữ; dấu ,/.!? thêm nhịp nghỉ nhỏ sau từ
        weights = [max(1.0, len(re.sub(r"[^\w]", "", w)) + (1.2 if re.search(r"[,.!?;:]$", w) else 0)) for w in toks]
        total = sum(weights)
        # ~90% thời lượng câu là NÓI, ~10% là khoảng lặng cuối -> highlight không lê tới câu sau
        speak = s["d"] * 0.9
        cur = s["t"]
        for w, wt in zip(toks, weights):
            share = s["d"] * (wt / total)          # bước NHẢY (căn đều toàn câu)
            hl = min(share, speak * (wt / total) + 0.12)  # thời gian HIGHLIGHT (ngắn hơn -> gọn)
            t = max(0.0, cur - LEAD)
            words.append({"t": round(t, 3), "d": round(hl, 3), "w": w, "si": si + si_offset})
            cur += share
    return words


def _to_srt(subs: list[dict]) -> str:
    """Gộp theo câu -> .srt (cho enqueue --subtitle upload lên YouTube)."""
    def ts(sec):
        h = int(sec // 3600); m = int((sec % 3600) // 60); s = sec % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
    if not subs:
        return ""
    lines, n = [], 1
    # nhóm các từ cùng si thành 1 dòng phụ đề
    cur_si = subs[0]["si"]; buf = []
    def flush(buf):
        nonlocal n
        if not buf:
            return
        start = buf[0]["t"]; end = buf[-1]["t"] + buf[-1]["d"]
        text = " ".join(x["w"] for x in buf).strip()
        lines.append(f"{n}\n{ts(start)} --> {ts(end)}\n{text}\n")
        n += 1
    for s in subs:
        if s["si"] != cur_si:
            flush(buf); buf = []; cur_si = s["si"]
        buf.append(s)
    flush(buf)
    return "\n".join(lines)


_ACTIVE = {"voice": None, "rate": None}


def set_voice(voice: str = None, rate: str = None):
    """Đặt GIỌNG + TỐC ĐỘ cho kênh đang render (gọi 1 lần ở đầu mỗi kênh trong run_render.py).
    Mọi TK.synth() sau đó tự dùng — khỏi phải sửa 20+ điểm gọi rải rác.

    VÌ SAO CẦN: trước đây CẢ 40 kênh dùng CHUNG 1 giọng (en-US-AndrewNeural) + 21 kênh dùng chung
    engine Cinematic -> video 40 kênh nghe/nhìn gần như y hệt nhau. Đây đúng là thứ chính sách
    "inauthentic / mass-produced content" của YouTube nhắm tới (rủi ro bật kiếm tiền lớn nhất của
    hệ 40 kênh cùng chủ). Mỗi kênh 1 giọng riêng = khác biệt THẬT, 100% free (edge-tts)."""
    _ACTIVE["voice"] = voice or None
    _ACTIVE["rate"] = rate or None


def synth(text: str, mp3_path: str, voice: str = None, rate: str = None):
    """Trả (duration_giây, subs[Word], srt_text). subs đúng format RaceLong.
    voice/rate=None -> lấy theo kênh đang render (set_voice), không có thì về mặc định."""
    voice = voice or _ACTIVE["voice"] or DEFAULT_VOICE
    rate = rate or _ACTIVE["rate"] or DEFAULT_RATE
    sentences = asyncio.run(_run(text, mp3_path, voice, rate))
    subs = _expand_words(sentences)
    dur = (subs[-1]["t"] + subs[-1]["d"]) if subs else 0.0
    return round(dur, 3), subs, _to_srt(subs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--out", default="voice.mp3")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--rate", default=DEFAULT_RATE)
    a = ap.parse_args()
    dur, subs, srt = synth(a.text, a.out, a.voice, a.rate)
    base = a.out.rsplit(".", 1)[0]
    json.dump(subs, open(base + ".subs.json", "w"), ensure_ascii=False, indent=2)
    open(base + ".srt", "w", encoding="utf-8").write(srt)
    print(f"✅ {a.out}  ({dur:.2f}s, {len(subs)} từ, {subs[-1]['si']+1 if subs else 0} câu)")
    print(f"   subs -> {base}.subs.json | srt -> {base}.srt")


if __name__ == "__main__":
    main()
