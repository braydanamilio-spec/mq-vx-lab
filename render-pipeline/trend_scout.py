"""
trend_scout.py — Quét TITLE (KHÔNG tải video) của kênh lớn tham khảo bằng yt-dlp -> đưa cho Gemini
(quota chữ có sẵn, 40+ key, KHÔNG tốn gì thêm) tự tóm tắt GÓC ĐỘ/CÔNG THỨC đang ăn khách -> lưu
Firestore -> content_brain/run_render tự đọc thêm khi viết kịch bản (giống hệt top_titles() đã có,
áp dụng thêm cho kênh NGOÀI thay vì chỉ kênh của mình).

100% FREE: yt-dlp free + open-source, Gemini dùng quota chữ đang dư (không mở account/key gì mới).
KHÔNG copy chủ đề/title — chỉ học GU (hook/twist/cách đặt câu), Gemini luôn viết chủ đề MỚI.

Thêm kênh tham khảo mới: thêm 1 dòng vào SOURCES bên dưới, không cần sửa code nào khác.

Chạy: python trend_scout.py [--dry-run]
Cron: .github/workflows/trend_scout.yml (hàng tuần — xu hướng đổi chậm, khỏi tốn quota/CI phí quét mỗi ngày).
"""
from __future__ import annotations
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firestore_bridge as FB

OWNER = os.environ.get("OWNER_UID")

# Kênh THAM KHẢO (chỉ đọc title public, KHÔNG tải video/vi phạm bản quyền) -> áp dụng cho kênh MM0 nào.
SOURCES = [
    {"handle": "Zack D Films", "url": "https://www.youtube.com/@ZackDFilms/videos",
     "applies_to": ["FUTUREUSA", "UNSEENUSA", "COSMOS", "THEDEEP", "UNSOLVED"]},
    {"handle": "Kurzgesagt", "url": "https://www.youtube.com/@kurzgesagt/videos",
     "applies_to": ["COSMOS", "UNSEENUSA", "WHYUSA"]},
    {"handle": "The Infographics Show", "url": "https://www.youtube.com/@TheInfographicsShow/videos",
     "applies_to": ["WHYUSA", "EMPIREUSA", "GRIDUSA", "RULEDUSA", "VAULTUSA", "LEDGERUSA", "SIGNALUSA", "MARGINUSA"]},
]
N_TITLES = 30   # đủ thấy xu hướng, không cần quét hết kênh -> nhanh + đỡ tốn token tóm tắt


def fetch_titles(url: str, n: int = N_TITLES) -> list[str]:
    """yt-dlp CHỈ lấy title (flat-playlist, KHÔNG tải video) -> nhẹ, nhanh, free, không đụng bản quyền."""
    try:
        out = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--playlist-end", str(n), "--print", "%(title)s", url],
            capture_output=True, text=True, timeout=120)
        titles = [t.strip() for t in out.stdout.splitlines() if t.strip()]
        if not titles:
            print(f"   ⚠️ yt-dlp không lấy được title ({out.stderr[:150]})")
        return titles
    except FileNotFoundError:
        print("   ❌ chưa cài yt-dlp — pip install yt-dlp"); return []
    except Exception as e:
        print(f"   ⚠️ yt-dlp lỗi: {e}"); return []


def summarize(titles: list[str], api_key: str) -> str:
    """Gemini đọc titles -> tóm tắt GU VIẾT (hook/twist/cách đặt câu) — KHÔNG phải chủ đề cụ thể,
    tránh copy nội dung. 2-3 câu ngắn gọn, đưa thẳng vào niche prompt được."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = (
        "Here are recent video titles from a large, highly successful YouTube channel:\n"
        + "\n".join(f"- {t}" for t in titles)
        + "\n\nIn 2-3 short sentences, summarize the STYLE/ANGLE pattern that makes these titles work — "
          "hook structure, twist/reveal pattern, phrasing tricks, what makes someone click. "
          "Do NOT summarize the specific topics/subjects, do NOT mention the channel name or any titles "
          "verbatim. Output plain text only, no markdown, no preamble."
    )
    resp = model.generate_content(prompt, generation_config={"temperature": 0.4})
    return (resp.text or "").strip()


def main():
    dry = "--dry-run" in sys.argv
    if not OWNER:
        sys.exit("❌ Thiếu OWNER_UID.")
    try:
        keys = FB.read_keys(OWNER)
    except Exception as e:
        print(f"⏸ Firestore nghẽn tạm ({e}) — bỏ qua lần này, tuần sau tự chạy lại."); return   # KHÔNG crash CI vì lỗi tạm thời
    if not keys:
        sys.exit("❌ Chưa có Gemini key.")
    key = keys[0]["key"]

    digest: dict[str, list[str]] = {}   # {kênh MM0: [câu tóm tắt xu hướng, ...]}
    for src in SOURCES:
        print(f"🔎 {src['handle']} …")
        titles = fetch_titles(src["url"])
        if not titles:
            print("   ⏭ bỏ qua (không lấy được title)"); continue
        try:
            trend = summarize(titles, key)
        except Exception as e:
            print(f"   ⚠️ Gemini tóm tắt lỗi: {e}"); continue
        if not trend:
            print("   ⏭ Gemini trả rỗng, bỏ qua"); continue
        print(f"   ✅ {trend[:110]}")
        for ch in src["applies_to"]:
            digest.setdefault(ch, []).append(trend)

    if dry:
        print("\n(dry) sẽ lưu:\n" + json.dumps(digest, ensure_ascii=False, indent=2)); return
    for ch, trends in digest.items():
        FB.save_trend_scout(OWNER, ch, trends)
    print(f"\n✅ đã cập nhật xu hướng cho {len(digest)} kênh MM0.")


if __name__ == "__main__":
    main()
