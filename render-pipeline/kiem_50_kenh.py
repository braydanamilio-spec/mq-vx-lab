import sys, time, collections; sys.path.insert(0, "/Users/mrquyenbk/Documents/MM0 YOUTUBE 2026/render-pipeline")
import the_he_2 as T, concurrent.futures as cf
F = {"ranked": T.dung_story_ranked, "race": T.dung_story_race, "cinematic": T.dung_story_cinematic,
     "scaled": T.dung_story_scaled, "mapped": T.dung_story_mapped,
     "longshot": T.dung_story_longshot, "thennow": T.dung_story_thennow}
KY = {"bai_duoc_doc": {"nam": 2026, "thang": 8, "ngay": 20},
      "luot_doc_bai": {"nam": 2026, "thang": 8, "ngay": 20},
      "tieu_hanh_tinh": {"tu_ngay": "2026-08-20", "den_ngay": "2026-08-22"}}
def thu(k):
    t0 = time.monotonic()
    try:
        st = F[k["dinh_dang"]](k, KY.get(k["ham"], {}))
    except Exception as e:
        return dict(k=k, ok=False, t=0, tit=f"{type(e).__name__}: {str(e)[:40]}")
    return dict(k=k, ok=bool(st), t=time.monotonic() - t0, tit=(st or {}).get("title", "BỎ LƯỢT"))
with cf.ThreadPoolExecutor(8) as ex:
    kq = list(ex.map(thu, T.doc_kenh()))
ok = [x for x in kq if x["ok"]]
print(f"\n{'='*78}\nKẾT QUẢ: {len(ok)}/50 kênh dựng được kịch bản từ dữ liệu THẬT\n{'='*78}")
for x in sorted(kq, key=lambda z: (z["k"]["dinh_dang"], z["k"]["ten"])):
    print(f"  {'✅' if x['ok'] else '❌'} {x['k']['dinh_dang']:9} {x['k']['ten']:18} {x['t']:5.0f}s  {x['tit'][:46]}")
tit = [x["tit"] for x in ok]
trung = sorted({t for t in tit if tit.count(t) > 1})
print(f"\n📌 tiêu đề trùng nhau: {trung if trung else 'KHÔNG CÓ — 50 kênh, 50 nội dung khác nhau'}")
print(f"📌 chậm nhất: {max(kq, key=lambda z: z['t'])['k']['ten']} {max(x['t'] for x in kq):.0f}s")
c = collections.Counter(x["k"]["niche"] for x in ok)
print(f"📌 phủ {len(c)} niche")
