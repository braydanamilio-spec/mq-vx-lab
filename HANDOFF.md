# MM0 — HANDOFF (cho phiên Claude Code sau)

Mục tiêu: **30 video long + short/kênh** cho 3 kênh faceless USA. Hiện **52/90 long** đã xong. Chỉ cần "chạy tiếp" là soạn + render nốt.

## 3 kênh (motion-graphics + footage Pexels thật, 100% free)
| KEY (OUTBOX) | Tên | Accent | metric | handle | music mặc định |
|---|---|---|---|---|---|
| SAY_THIS | SAY THIS (giao tiếp/EQ) | GOLD #F5B301 | RESPECT | @saythis | music/inspired.mp3 |
| MONEY_MOVES | MONEY MOVES (tiền) | GREEN #2FD98A | WEALTH | @moneymoves | music/forecast.mp3 (xen wallpaper.mp3) |
| REWIRED | REWIRED (tâm lý/self) | VIOLET #8B5CF6 | FOCUS | @rewired | music/carefree.mp3 |

## Tiến độ hiện tại (2026-08-17)
- **SAY_THIS: 18 long** (ep001–018), 37 short
- **MONEY_MOVES: 17 long** (ep001–017), 34 short
- **REWIRED: 17 long** (ep001–017), 35 short
- ep001 mỗi kênh nằm trong `pipeline/mg_outbox.py`; ep002+ trong `pipeline/mg_ep.py` (dict `EP[(prefix, ep)]`).
- Tất cả long ≥ 8:00 (đủ mid-roll ads). Đã QC frame vài ep = footage khớp, không overlap.

## File chính
- `pipeline/mg_ep.py` — chứa dict `EP[(prefix,ep)]` các tập ep002+. Chạy: `python3 pipeline/mg_ep.py <prefix> <ep> [all|long|shorts]` (prefix = say-this|money-moves|rewired).
- `pipeline/mg_outbox.py` — helpers dùng chung: `L()` (1 lesson = chapter + 2 beat icon), `B()`, `_IC()`, `h()` (hook), `cta()`, `fetch_bg()`, `render()`, `make_thumb()`, `package()` (ghi OUTBOX + credit nhạc CC-BY). Có `GOLD/GREEN/VIOLET`, `MUSIC_TITLE`.
- `engine-remotion/src/SayThisMG.tsx` — engine Remotion (KHÔNG cần sửa). Comp `SayThisMGWide` (16:9 long) + `SayThisMG` (9:16 short). Scene kinds: hook/line/wrong/right/stat/bars/cta/chapter/icon/meter/split; PhotoBg = footage Pexels + Ken Burns. Icon có sẵn: arrowUp/Down, speech, shield, crown, flame, bolt, eye, coin, heart, target, mic, clock, brain, growth, lock, phone, battery, hourglass, bag, ban, handshake.

## Cách 1 tập được viết (dict EP)
```python
EP[("say-this", N)] = {
  "key": "SAY_THIS", "accent": GOLD, "handle": "@saythis", "music": "music/inspired.mp3",
  "slug": "how-to-...", "thumb": ["DÒNG 1","DÒNG 2","DÒNG 3"],
  "meta": {"topic","title","desc","hashtags":[3-5],"tags":[...]},
  "long": [ B(h("hook nar", ["3 DÒNG","THUMB","HOOK"], 1, {"stat":"X","text":"..."}), "bgq footage"),
            *L("1","TAG","Title", "icon1","label1","nar1(~30 từ)", "icon2","label2","nar2", "bgq_chapter","bgq_beat1","bgq_beat2"),
            ... ~40-44 lesson ...,
            B(cta("2 DÒNG\nCTA","...Follow SAY THIS."), "bgq sunset") ],
  "shorts": [ ("slug-short", {meta}, [ B(h(...),"bgq"), B(_IC(...),"bgq"), {"nar":"...","kind":"meter","dir":"up","target":85,"caption":"...","metric":"RESPECT"}, ..., B(cta(...),"bgq") ]), (short 2...) ],
}
```
**Chuẩn độ dài:** cần ~40-44 lesson để long ≥8:00 (say-this ~13s/lesson, money ~14s, rewired ~12s). Short 5-6 beat ≈ 25-30s. bgq = query ảnh Pexels khớp 100% nội dung; cảnh "kẻ xấu"/aggressor dùng query KHÔNG mặt người (legal). pill dict PHẢI có key `"text"`: `{"stat":"1","text":"..."}`.

## Quy trình render (LUÔN 1 tiến trình/lần)
```bash
cd "/Users/mrquyenbk/Documents/MM0 YOUTUBE 2026"
python3 -c "import ast; ast.parse(open('pipeline/mg_ep.py').read()); print('OK')"  # check syntax trước
for i in $(seq 1 40); do n=$(ps aux|grep chrome-headless-shell|grep -v grep|wc -l|tr -d ' '); [ "$n" -le 1 ] && break; sleep 20; done
rm -rf /private/var/folders/p2/*/T/react-motion-render* 2>/dev/null
nice -n 19 python3 pipeline/mg_ep.py <prefix> <ep> > OUTBOX/_log.log 2>&1
# verify: ffprobe -v error -show_entries format=duration -of csv=p=0 OUTBOX/<KEY>/long/<slug>.mp4  (phải ≥ 495s)
```
**BẪY quan trọng:** KHÔNG chạy 2 render cùng lúc (kể cả bản đang trong vòng chờ-memory) — 2 tiến trình `mg_ep.py` cùng ep đụng nhau ở `engine-remotion/public/story/<name>/` → file long hỏng (ra ~3:35 thay vì 8'). Nếu lỡ: `pkill -f 'mg_ep.py'; pkill -f 'remotion render'`, xoá `public/story/<prefix><ep>-*`, render lại sạch. Disk hay đầy → luôn `rm -rf .../T/react-motion-render*` trước/sau.

## Output chuẩn (auto-publisher đọc)
`OUTBOX/<KEY>/<long|short>/<slug>.mp4` + `.json` (title/desc/hashtags/tags/platforms/thumbnail/publish_at) + long thêm `.jpg` (thumb 1280×720). `package()` tự thêm credit: 🎵 Kevin MacLeod CC-BY + "Footage: Pexels". Slug = `<prefix>-ep<NNN>-<topic>`.

## Còn phải làm: ep018→ep030 (SAY_THIS từ ep019)
Cần thêm: SAY_THIS 12 long, MONEY 13 long, REWIRED 13 long (mỗi long + 2 short). Làm **xen kẽ** say-this→money→rewired.

**Chủ đề ĐÃ dùng** (tránh trùng) — xem đầy đủ trong memory `mm0-ch8-saythis` UPDATE "PROGRESS 45/90". Tóm tắt:
- SAY_THIS(1-18): disrespect-replies, command-respect, toxic-people, likable, confident, body-language, persuasive, start-conversation, boundaries, criticism, first-impression, arguments, read-anyone, charisma, respect-at-work, apology, rejection, public-speaking.
- MONEY(1-17): money-they-never-taught, broke-habits, money-rules, passive-income, investing-beginners, side-hustles, debt, save-money, credit-score, retire-early-FIRE, salary-negotiation, paycheck-to-paycheck, build-wealth, real-estate, start-a-business, psychology-of-money, budgeting.
- REWIRED(1-17): brain-glitches, discipline, master-mind, focus, overthinking, habits, procrastination, stop-caring, phone-addiction, mental-toughness, negative-thinking, self-sabotage, decisions, happiness, self-confidence, overcome-fear, anxiety.

**Pool ý tưởng còn lại:**
- SAY_THIS: networking, humor/wit, difficult-people, storytelling, give-feedback, dating-communication, leadership-communication, handling-awkward, small-talk-mastery, negotiation-personal, active-listening, likability-deep, saying-no.
- MONEY: index-funds, frugal-living, financial-mistakes, net-worth, taxes-basics, insurance, millionaire-habits, make-money-online, dividend-investing, retirement-accounts, teaching-kids-money, stock-investing-deep, emergency-fund-deep.
- REWIRED: anger, mindfulness, morning-routine, dopamine-detox, willpower, self-love, resilience, growth-mindset, stop-comparing, emotional-intelligence, life-purpose, master-emotions, gratitude-deep.

## Yêu cầu user (ghi nhớ)
Chất lượng cao nhất, footage khớp 100% nội dung, QC visual trước+sau render, báo cáo NGẮN GỌN / âm thầm tiết kiệm token. Long ≥8' (mid-roll), short 25-40s. 100% free.

Chi tiết lịch sử: memory `mm0-ch8-saythis`, `mm0-mg-longform`, `mm0-autopublisher`.
