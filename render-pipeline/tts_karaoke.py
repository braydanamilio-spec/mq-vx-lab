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

DEFAULT_VOICE = (os.environ.get('TTS_VOICE') or 'en-US-AndrewNeural')   # warm/confident US male
DEFAULT_RATE = (os.environ.get('TTS_RATE') or '+6%')                    # nhanh nhẹ cho hợp nhịp viral


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


TTS_TIMEOUT = 120     # giây cho MỘT lần gọi
TTS_TRIES = 3         # số lần thử lại khi mạng chập


async def _run(text: str, mp3_path: str, voice: str, rate: str):
    """Ghi mp3 + gom SentenceBoundary — CÓ trần thời gian và thử lại.

    edge-tts là dịch vụ MẠNG của Microsoft. Trước đây gọi trần trụi: không timeout, không retry.
    Mỗi video gọi hàm này hàng chục lần (intro + từng cảnh + outro) nên qua hàng nghìn lượt, mạng
    chập là chuyện chắc chắn xảy ra. Hậu quả cũ:
      - kết nối treo -> KHÔNG có timeout -> job đứng im tới khi hết giờ workflow (đúng loại lỗi
        treo đã hành cả ngày 20/8)
      - lỗi mạng -> ném lên tận run_one -> nó thử lại CẢ VIDEO, tức gọi Gemini viết lại từ đầu:
        tốn quota Gemini chỉ vì một cú nghẽn mạng vài giây.
    Nay: mỗi lần gọi có trần 120s, hỏng thì thử lại tối đa 3 lần với giãn cách tăng dần, chỉ khi
    hết lượt mới báo lỗi ra ngoài."""
    import asyncio as _a
    last = None
    for att in range(1, TTS_TRIES + 1):
        try:
            return await _a.wait_for(_synth_once(text, mp3_path, voice, rate), timeout=TTS_TIMEOUT)
        except Exception as e:
            last = e
            if att < TTS_TRIES:
                print(f"   ↻ giọng đọc lỗi lần {att} ({str(e)[:60]}) — thử lại sau {att * 2}s")
                await _a.sleep(att * 2)
    raise last


async def _synth_once(text: str, mp3_path: str, voice: str, rate: str):
    import edge_tts
    # 23/8 (user: "sub giật giật, không khớp giọng"): xin MỐC TỪNG TỪ THẬT từ máy đọc.
    # Trước đây edge-tts chỉ trả SentenceBoundary (1 mốc/câu) -> hệ phải CHIA ĐỀU theo số ký tự,
    # nên từ dài/ngắn lệch nhịp và phụ đề nhảy giật. Bật boundary="WordBoundary" là có thời điểm
    # + thời lượng CHÍNH XÁC của từng từ (đo thật: 13 từ, sai số 0). Máy đọc cũ không hỗ trợ thì
    # tự lùi về kiểu cũ (không làm hỏng gì).
    try:
        comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    except TypeError:
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

# mp3 đã tổng hợp -> mốc từng từ của nó. Xem subs_tu_clips().
_NHO: dict[str, list] = {}


def subs_tu_clips(clips) -> list[dict]:
    """Mốc karaoke của CẢ TRACK, ghép từ danh sách `[(đường_dẫn_mp3, giây_bắt_đầu), …]`.

    24/8 tối (anh: "short cũng nên có sub karaoke") — soi ra 9 định dạng short (pulse/swarm/ranked/
    mapped/scaled/thennow/longshot/clockwork/guess) **không có phụ đề nào cả**: `subs` có trong khai
    báo props của component nhưng không lớp nào vẽ, còn phía Python thì mọi builder đều viết
    `du, _, _ = TK.synth(...)` — vứt thẳng mốc từng từ mà edge-tts đã trả sẵn.

    Vì sao gom ở đây chứ không sửa từng builder: mỗi builder đã có sẵn danh sách `clips` đúng cặp
    (mp3, mốc bắt đầu) để trộn track — chính là thứ cần để dời mốc. Dùng lại nó thì mỗi builder chỉ
    thêm MỘT dòng, và không thể lệch offset so với tiếng (hai bên đọc chung một nguồn)."""
    ra = []
    for c in (clips or []):
        try:
            duong, moc = c[0], float(c[1])
        except Exception:
            continue
        for w in _NHO.get(os.path.abspath(str(duong)), []):
            try:
                ra.append({"t": round(float(w["t"]) + moc, 3), "d": round(float(w["d"]), 3),
                           "w": w["w"]})
            except Exception:
                pass
    ra.sort(key=lambda x: x["t"])
    return ra

def _expand_words(sentences: list[dict], si_offset: int = 0) -> list[dict]:
    """Mỗi câu -> chia thời lượng ra từng TỪ theo độ dài chữ + có nhịp nghỉ ở dấu câu (siết sync)."""
    words = []
    # 23/8: mốc trả về ĐÃ LÀ TỪNG TỪ (WordBoundary) -> dùng THẲNG thời điểm thật, tuyệt đối khớp
    # giọng; chỉ khi máy đọc trả mốc theo CÂU mới phải ước lượng như cũ.
    if sentences and all(len(x["w"].split()) == 1 for x in sentences):
        si = 0
        for k, x in enumerate(sentences):
            words.append({"t": round(max(0.0, x["t"] - LEAD), 3), "d": round(x["d"], 3),
                          "w": x["w"], "si": si + si_offset})
            if re.search(r"[.!?]$", x["w"]):
                si += 1
        return words
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
    # 23/8 — GỐC CỦA "VIDEO 13 GIÂY CÂM": edge-tts trục trặc (mạng/chặn tạm) thì `sentences` rỗng,
    # hàm này lặng lẽ trả dur=0.0. Người gọi cộng 0 vào timeline -> ra video ngắn tũn KHÔNG CÓ LỜI,
    # mà QC cũ chỉ hỏi "có luồng audio không" nên vẫn chấm đạt rồi đẩy lên kho. Nay: thử lại, vẫn
    # rỗng thì NÉM LỖI để lane đánh dấu hỏng và render lại, thay vì đẻ ra video câm.
    import time as _t
    last = None
    for i, wait in enumerate((0, 2, 5)):
        if wait:
            _t.sleep(wait)
        try:
            sentences = asyncio.run(_run(text, mp3_path, voice, rate))
            subs = _expand_words(sentences)
            dur = (subs[-1]["t"] + subs[-1]["d"]) if subs else 0.0
        except Exception as e:
            last, dur, subs = e, 0.0, []
        if dur > 0.05 or not str(text or "").strip():
            _NHO[os.path.abspath(mp3_path)] = subs      # để subs_tu_clips() ghép lại sau
            return round(dur, 3), subs, _to_srt(subs)
        print(f"   🔁 TTS trả 0 giây (lần {i + 1}/3) — thử lại: {str(text)[:40]}…")
    raise RuntimeError(f"TTS rỗng sau 3 lần thử ({str(last)[:60] if last else 'không có tiếng'}) — "
                       f"không dựng video câm.")


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
