# -*- coding: utf-8 -*-
"""50 kênh thế hệ 2 — xuất phát từ NICHE VIRAL Ở MỸ, không xuất phát từ nguồn dữ liệu.
Chất liệu: A = số liệu thật + đồ hoạ code · B = ảnh AI theo style riêng của kênh · C = lai (số làm xương, ảnh làm da)."""
import io, json
from collections import Counter

# (niche, ten, handle, chat_lieu, nguon, ham, dinh_dang, goc_nhin, style_anh)
K = [
("Đồ ăn & đồ uống","WHAT IS IN IT","@whatisinitusa","C","usda","thanh_phan_mon","ranked","Thành phần thật trong món quen","ảnh sản phẩm sạch, nền giấy gói"),
("Đồ ăn & đồ uống","RECALL PLATE","@recallplate","A","openfda","thu_hoi_fda","ranked","Đồ ăn bị thu hồi tuần này",""),
("Đồ ăn & đồ uống","CALORIE SHOCK","@calorieshockusa","C","usda","thanh_phan_mon","scaled","Món này bằng mấy bữa cơm","ảnh món ăn chụp trên cao"),
("Sức khoẻ & gym","ONE STUDY","@onestudyusa","C","pubmed","nghien_cuu","cinematic","Một nghiên cứu thật, giải thích gọn","minh hoạ giải phẫu nét mảnh"),
("Sức khoẻ & gym","PILL FACTS","@pillfactsusa","A","openfda","thu_hoi_fda","ranked","Thuốc bị thu và lý do thật",""),
("Tiền cá nhân","PAYCHECK GAP","@paycheckgap","A","bls","chuoi_bls","scaled","Lương tăng chậm hơn giá bao nhiêu",""),
("Tiền cá nhân","RENT REALITY","@rentrealityusa","A","bls","chuoi_bls","thennow","Tiền thuê nhà xưa và nay",""),
("Tiền cá nhân","PRICE OF NOW","@priceofnow","A","bls","chuoi_bls","race","Món nào tăng giá nhanh nhất",""),
("Tội phạm có thật","COURT RECORD","@courtrecordusa","C","court","ban_an","cinematic","Một vụ án kể từ hồ sơ toà","phác thảo phòng xử, than chì"),
("Tội phạm có thật","SUED FOR THIS","@suedforthis","A","court","ban_an","ranked","Công ty bị kiện vì cái gì",""),
("Tội phạm có thật","COLD FILE","@coldfileusa","C","court","ban_an","cinematic","Vụ cũ chưa khép lại","ảnh tài liệu ố vàng"),
("Bí ẩn chưa lời giải","UNSOLVED LOG","@unsolvedlog","B","wikipedia","bai_duoc_doc","cinematic","Bí ẩn nước Mỹ đang tra lại","tranh khắc gỗ đen trắng"),
("Bí ẩn chưa lời giải","MISSING PIECE","@missingpieceusa","B","wikipedia","bai_duoc_doc","cinematic","Thứ biến mất không lời giải","ảnh sương mù đơn sắc"),
("Thể thao","DIAMOND NUMBERS","@diamondnumbers","A","mlb","thong_ke_mlb","race","Bóng chày qua con số thật",""),
("Thể thao","COURT KINGS","@courtkingsusa","A","nba","thong_ke_nba","race","Bóng rổ: ai thật sự dẫn đầu",""),
("Thể thao","PAID VS PLAYED","@paidvsplayed","C","nba","thong_ke_nba","ranked","Lương so với màn trình diễn","chân dung vận động viên phẳng"),
("Người nổi tiếng","AMERICA LOOKED UP","@americalookedup","A","wikipedia","bai_duoc_doc","race","Hôm qua nước Mỹ tra ai nhiều nhất",""),
("Người nổi tiếng","FAME CURVE","@famecurveusa","C","wikipedia","luot_doc_bai","longshot","Đường cong nổi tiếng của một người","chân dung nét đơn sắc"),
("Phim & truyền hình","SHOW NUMBERS","@shownumbersusa","C","tvmaze","phim_truyen","ranked","Phim bộ qua số tập, mùa, điểm","poster giả lập phong cách in lụa"),
("Phim & truyền hình","GONE TOO SOON","@gonetoosoonusa","C","tvmaze","phim_truyen","ranked","Phim bị cắt giữa chừng","ảnh màn hình tối, chữ neon"),
("Nhạc","SONG FILE","@songfileusa","C","musicbrainz","ho_so_nhac","cinematic","Một bài hát: ai viết, ai hát, khi nào","bìa đĩa vector"),
("Nhạc","ONE HIT","@onehitusa","C","musicbrainz","ho_so_nhac","longshot","Nghệ sĩ một bản hit","ảnh sân khấu hạt phim"),
("Game","STEAM TRUTH","@steamtruthusa","A","steamspy","game_steam","race","Game nào THẬT SỰ có người chơi",""),
("Game","GAME GRAVEYARD","@gamegraveyard","C","steamspy","game_steam","ranked","Game chết yểu và số người còn lại","pixel art u tối"),
("Xe","CAR RECALL","@carrecallusa","A","nhtsa","trieu_hoi_xe","ranked","Dòng xe bị triệu hồi vì bộ phận gì",""),
("Xe","MPG TRUTH","@mpgtruthusa","C","epa","muc_tieu_thu","race","Xe nào thật sự tiết kiệm xăng","xe cắt lớp isometric"),
("Thú cưng & động vật","BREED FILE","@breedfileusa","B","dogceo","giong_cho","ranked","Hồ sơ từng giống chó","tranh màu nước"),
("Thú cưng & động vật","WILD NUMBERS","@wildnumbersusa","C","worldbank","chi_so_the_gioi","scaled","Động vật hoang dã qua con số","tranh khắc tự nhiên học"),
("Du lịch","COST TO GO","@costtogousa","C","worldbank","chi_so_the_gioi","ranked","Đi đâu rẻ, đi đâu đắt","bưu thiếp cũ"),
("Du lịch","SKY RIGHT NOW","@skyrightnow","C","opensky","may_bay","mapped","Bầu trời Mỹ ngay lúc này","bản đồ radar phát sáng"),
("Công nghệ & AI","FILINGS SAY","@filingssay","A","sec","tim_ho_so","ranked","Công ty tự khai gì về AI trong hồ sơ",""),
("Công nghệ & AI","QUIET LAYOFFS","@quietlayoffs","A","sec","tim_ho_so","ranked","Hồ sơ SEC nhắc chữ sa thải",""),
("Kinh dị & rùng rợn","REAL PLACE","@realplaceusa","B","wikipedia","bai_duoc_doc","cinematic","Nơi có thật, chuyện có thật","ảnh đêm tương phản mạnh"),
("Kinh dị & rùng rợn","NIGHT SHIFT","@nightshiftusa","B","wikipedia","bai_duoc_doc","cinematic","Chuyện xảy ra ca đêm","tranh sơn dầu tối màu"),
("Quan hệ & hẹn hò","MARRIAGE MATH","@marriagemath","C","worldbank","chi_so_the_gioi","scaled","Hôn nhân Mỹ qua con số","biểu tượng phẳng ấm màu"),
("Quan hệ & hẹn hò","WHAT THEY SEARCH","@whattheysearch","C","wikipedia","bai_duoc_doc","ranked","Người ta lén tra điều gì","ảnh màn hình đêm"),
("Nghề nghiệp","SALARY TRUTH","@salarytruthusa","A","bls","chuoi_bls","ranked","Nghề này thật sự trả bao nhiêu",""),
("Nghề nghiệp","JOB DYING","@jobdyingusa","A","bls","chuoi_bls","longshot","Nghề đang biến mất",""),
("Nhà ở","WHERE TO MOVE","@wheretomoveusa","A","bls","chuoi_bls","mapped","Bang nào đáng chuyển tới",""),
("Nhà ở","HOUSE MATH","@housemathusa","C","bls","chuoi_bls","scaled","Cần bao nhiêu năm lương mua một căn","mặt cắt nhà isometric"),
("Lịch sử","ARCHIVE REEL","@archivereelusa","C","archive","phim_tu_lieu","cinematic","Phim tư liệu công cộng, kể lại","khung phim xước"),
("Lịch sử","THEN AND NOW","@thenandnowusa","C","archive","phim_tu_lieu","thennow","Cùng một chỗ, cách nhau 100 năm","ảnh ghép hai thời"),
("Vũ trụ","NEAR EARTH","@nearearthusa","A","nasa","tieu_hanh_tinh","ranked","Thiên thạch sát Trái Đất tháng này",""),
("Vũ trụ","SPACE INVOICE","@spaceinvoice","A","usaspending","hop_dong_lon","race","NASA trả tiền cho ai",""),
("Thời tiết & thảm hoạ","ALERT NOW","@alertnowusa","A","nws","canh_bao","mapped","Cảnh báo đang bật ở bang nào",""),
("Thời tiết & thảm hoạ","QUAKE LOG","@quakelogusa","A","usgs","dong_dat","mapped","Động đất mạnh nhất và ở đâu",""),
("Quân sự","PENTAGON LEDGER","@pentagonledger","A","usaspending","hop_dong_lon","race","Nhà thầu quốc phòng đua theo năm",""),
("Quân sự","WEAPON PRICE","@weaponpriceusa","C","usaspending","hop_dong_lon","scaled","Một quả đạn giá bao nhiêu","kỹ thuật hoạ bản vẽ xanh"),
("Luật & quyền công dân","YOUR RIGHTS CASE","@yourrightscase","C","court","ban_an","cinematic","Án lệ đổi đời sống thường ngày","tranh minh hoạ phiên toà"),
("Giáo dục","DEGREE WORTH","@degreeworthusa","A","bls","chuoi_bls","ranked","Bằng này đáng bao nhiêu tiền",""),
]
assert len(K) == 50, len(K)
assert len({k[2] for k in K}) == 50, "handle trùng"
assert len({k[1] for k in K}) == 50, "tên trùng"
out = [{"id": i+1, "niche": ni, "ten": t, "handle": h, "chat_lieu": c, "nguon": n, "ham": f,
        "dinh_dang": d, "goc_nhin": g, "style_anh": st, "the_he": 2, "footage": False}
       for i, (ni, t, h, c, n, f, d, g, st) in enumerate(K)]
io.open("/Users/mrquyenbk/Documents/MM0 YOUTUBE 2026/render-pipeline/kenh_the_he_2.json","w",encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=1))
print("niche:", len({k[0] for k in K}), "· kênh:", len(K))
print("chất liệu:", dict(Counter(k[3] for k in K)))
print("nguồn   :", len({k[4] for k in K}), "loại")
print("dạng    :", dict(Counter(k[6] for k in K)))
