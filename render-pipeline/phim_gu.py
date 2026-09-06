#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GU HÌNH CỦA 18 KÊNH GIẢI THÍCH — bộ PHIM (v10, 6/9/2026).

Anh: *"100% các cảnh trong videos đều generate từ gemini + cloudflare, ko dùng generate code
tạo ảnh xấu — chỉ dùng cho phần chart và số liệu động"* và *"đẹp như 1 phim hoạt hình 2D 3D
có đầy đủ nhân vật bối cảnh, màu sắc đẹp"*.

── VÌ SAO BỘ CŨ RA ẢNH SƠ SÀI, VÀ VÌ SAO TỆP NÀY TỒN TẠI ───────────────────────────────────
Soi 12 ảnh mới nhất của `gt_nen/`: nhân vật KHÔNG CÓ MẶT, đứng một mình giữa nền be trơn, cả
mười hai ảnh cùng một tông cát. Không phải mô hình yếu — là prompt BẮT nó vẽ như thế:

    CHUA_CHO   "top third empty sky, bottom fifth empty ground"    -> 45% khung phải TRỐNG
    SAN_NGOAI  "the centre of the frame is open empty ground"      -> giữa khung cũng trống
    GU         "flat, no gradients, no texture"                    -> cấm mọi chiều sâu

Ba câu ấy sinh ra để chừa chỗ cho chữ và để 250 khung cùng một chất. Cả hai mục tiêu đều
ĐÚNG, nhưng chúng được trả bằng thứ đắt nhất: nội dung của khung hình. Chừa chỗ cho chữ là
việc của LỚP PHỦ trong engine (một dải mờ dưới chân khung), không phải việc của mô hình vẽ.

── CHỌN MÔ HÌNH: ĐO, KHÔNG ĐOÁN  (6/9/2026) ────────────────────────────────────────────────
Cloudflare đã mở FLUX.2. Đo thật trên tài khoản thật, cùng một prompt, cùng 768×1344:

    @cf/black-forest-labs/flux-1-schnell   1024×1024 CỐ ĐỊNH (400 -> không nhận width/height)
                                           => cắt xuống 9:16 mất 44% bề ngang
    @cf/black-forest-labs/flux-2-klein-9b  768×1344 NGUYÊN BẢN · 37 ảnh/tài khoản/ngày
    @cf/black-forest-labs/flux-2-dev       768×1344 · chất cao nhất, hay tự thêm VIỀN TRẮNG
    @cf/leonardo/lucid-origin              768×1344 · đẹp, đắt hơn

"37 ảnh/tài khoản/ngày" là số ĐẾM ĐƯỢC: bơm một tài khoản tới khi nó trả
*"you have used up your daily free allocation of 10,000 neurons"* — dừng ở lượt 38. Tức
~270 neuron/ảnh, KHÔNG phải 1.364 như bảng giá suy ra. 97 tài khoản => ~3.589 ảnh/ngày, và
lượt vượt trần bị TỪ CHỐI chứ không bị tính tiền — nên bộ này vẫn free 100%.

Hai thứ chỉ có ở FLUX.2 và cả hai đều xoá một họ lỗi cũ:
  · khung 9:16 / 16:9 NGUYÊN BẢN  -> không còn phép cắt 44%, nên mọi luật "đừng đặt đồ ở
    hai mép" biến mất cùng với nó
  · bám prompt dài -> tả được NHÂN VẬT + BỐI CẢNH + ÁNH SÁNG trong một câu, thứ schnell
    luôn bỏ bớt

── GEMINI ────────────────────────────────────────────────────────────────────────────────────
`gemini-3.1-flash-image` có mặt trong danh sách model của cả 68 khoá. NHƯNG đo từ máy anh:
mọi khoá trả 429 với `quota_limit_value: "0"`, `quota_location: "asia-east1"` — tức Google
KHÔNG cấp hạn mức free cho vùng châu Á. Trên GitHub Actions (runner ở Mỹ) thì có.
Nên hồ ảnh xếp CF trước, Gemini sau: ở máy anh chạy được bằng CF; trên Actions có cả hai.
Đây là số đo, không phải phỏng đoán — xem `phim_anh`.
"""

# ══ SÁU KỸ THUẬT DỰNG HÌNH ═══════════════════════════════════════════════════════════════════
# Mỗi kỹ thuật là một CÁCH LÀM PHIM có thật, không phải một tính từ. Lý do: mô hình học từ ảnh
# có chú thích, và chú thích của ảnh phim luôn nói về kỹ thuật ("cel-shaded", "stop-motion"),
# không nói "đẹp" hay "chi tiết". Bảo nó "chi tiết hơn" thì nó thêm chi tiết ngẫu nhiên; bảo nó
# "một khung phim hoạt hình cel" thì chi tiết đi theo cả gói: ánh sáng, bối cảnh, biểu cảm.
#
# KHÔNG nêu tên hãng phim hay hoạ sĩ đang sống. Vừa là chuyện bản quyền, vừa là chuyện chất
# lượng: tên riêng kéo mô hình về đúng một bộ phim, và mười tám kênh sẽ giống nhau qua nó.
KY_THUAT = {
    "cel": ("modern 2D cel-animated feature film still, hand-painted background layers, "
            "clean confident line work, characters with expressive readable faces, "
            "cinematic key light with soft rim light, rich saturated colour"),
    "goa": ("painterly gouache animation still from an independent animated feature, visible "
            "brush texture, luminous layered colour, characters with strong silhouettes and "
            "expressive faces, atmospheric depth haze in the far background"),
    "cg":  ("stylised 3D animated feature film still, soft global illumination, appealing "
            "rounded character design with expressive face, detailed props and set dressing, "
            "physically based materials, cinematic depth of field"),
    "ani": ("modern anime film background art with cel-shaded characters, luminous skies, "
            "precise architectural detail, volumetric light shafts, high contrast between "
            "lit and shadowed planes, expressive faces"),
    "cat": ("stop-motion paper diorama film still, layered cut-paper sets with visible edges "
            "and real cast shadows, felt and cardboard textures, hand-made miniature props, "
            "warm practical lighting from small lamps inside the set"),
    "muc": ("cinematic graphic-novel illustration, heavy confident ink line, bold flat colour "
            "over textured paper, dramatic chiaroscuro, characters drawn with strong "
            "expressive faces, deep editorial composition"),
    # ══ DOODLE — KỸ THUẬT THỨ BẢY, VÀ NÓ XOÁ HẲN MỘT HỌ LỖI  (6/9/2026) ═════════════════════
    # Anh gửi bốn khung tham chiếu: nhân vật là hình que, đầu tròn trắng, hai chấm mắt, chi là
    # nét mực. Điều đáng giá nhất ở kiểu này KHÔNG phải nó đẹp hơn — mà là **nó không có giải
    # phẫu để mà sai**. Không bàn tay, không ngón, không khuỷu, không mặt cận. Đúng ba thứ vừa
    # làm hỏng 3/8 khung của bản short.
    #
    # Đo thật trước khi tin: sinh hai khung kiểu này ở 1344×768 — nhân vật sạch tuyệt đối, và
    # bối cảnh (hành lang bệnh viện có lưới trần, cửa hai bên, xe đẩy vệ sinh) GIÀU HƠN HẲN
    # bốn khung tham chiếu, nơi nền chỉ là một mảng nâu phẳng với vài hòn đá.
    #
    # Đó cũng là chỗ khác biệt: kênh doodle nào cũng có nhân vật que, nhưng nền của họ sơ sài
    # vì người ta phải vẽ tay. Mình để mô hình vẽ nền — giữ nhân vật que, nâng thế giới lên.
    # ── HAI CHỖ SỬA SAU KHI ANH SOI KHUNG  (6/9/2026, cùng ngày) ───────────────────────────
    # Anh chỉ một khung: nhân vật là que ĐEN TRẦN không áo, đứng trên một cái khay có ống nghe
    # lơ lửng giữa phòng khách. Đọc sổ cảnh thì lộ ra cả hai đều là lỗi của CHÍNH CÂU NÀY:
    #
    # 1. Câu cảnh của nhịp ấy viết `"...no person in the frame"` — nó là một cảnh ĐỒ VẬT theo
    #    đúng thang cỡ cảnh em vừa thêm. Nhưng câu kỹ thuật lại mở đầu bằng *"The people ARE
    #    simple stick figures"* — một câu KHẲNG ĐỊNH TRONG KHUNG CÓ NGƯỜI. Hai câu đánh nhau,
    #    và câu đứng trước thắng: mô hình nhét một hình que vào một cảnh không được có người.
    #    Đây là lần thứ TƯ trong ngày cùng một họ lỗi — trường tả PHONG CÁCH đang tả NỘI DUNG
    #    (§12.5). Sửa: "Any person in the frame is drawn as…" — tả CÁCH VẼ, không khẳng định
    #    có ai.
    # 2. Hình que không có áo vì câu này chỉ tả đầu và chi, không tả thân. Mô hình vẽ đúng thứ
    #    được bảo. Thêm một mảng màu phẳng ở thân — đó cũng chính là thứ giữ nhận diện nhân
    #    vật qua các khung, vì đầu tròn trắng thì khung nào cũng như khung nào.
    # ── NÉT VẼ HÌNH QUE: THÊM ÍT, KHÔNG THÊM NHIỀU  (đo 6/9/2026) ──────────────────────────
    # Anh: *"người que cần vẽ đẹp hơn"*. Em tả kỹ hơn — tóc, lông mày, miệng theo cảm xúc, nét
    # đều tay, khuỷu gối, bàn tay bo tròn, giày. Khoảng 90 chữ về NHÂN VẬT.
    # Kết quả đo: **8/8 khung ra một hình que trần trên NỀN TRẮNG**, mất sạch bối cảnh. Khối
    # phong cách phình to đã nuốt khối cảnh — mô hình vẽ một bài nghiên cứu hình người, không
    # vẽ một cảnh phim. Cùng họ lỗi cả ngày, chỉ ngược chiều: lần trước trường phong cách tả
    # nội dung, lần này nó DÀI tới mức đè mất nội dung.
    # Nên chỉ giữ hai thứ rẻ nhất mà tham chiếu của anh có và bản cũ thiếu: **mảng tóc phẳng**
    # và **bàn tay là cục bo tròn**. Hai vế, không phải hai câu.
    "doo": ("hand-drawn doodle animation still from a whiteboard explainer cartoon. Any person "
            "in the frame is drawn as a simple stick figure: a plain round white head with a "
            "flat blob of hair on top, two dot eyes, two short eyebrow strokes and a small "
            "mouth that carries the mood, thin black stick arms and legs ending in small "
            "rounded stubs, no nose, no ears, no fingers, and one flat-coloured garment "
            "filling the torso. Thick wobbly hand-inked black outlines on everything, large "
            "flat blocks of colour, no gradients and no soft shading, but a fully built "
            "environment with real furniture, props and perspective. The only shadow anywhere "
            "is one simple flat ellipse directly beneath each figure's feet: no cast shadows "
            "on floors or walls, no reflections of people"),
}
# ── VÌ SAO PHẢI CẤM BÓNG ĐỔ Ở KIỂU DOODLE  (6/9/2026) ──────────────────────────────────────
# Anh chỉ vào nền nhà của khung cuối: *"hình như nền nhà hơi lỗi hay nó thế e nhỉ"*. Phóng to
# thì thấy — nước là CỐ Ý (sổ cảnh viết *"a broken IV bag sprays water across a flooded
# midnight hallway"*), nhưng **cái bóng đổ trên mặt nước là một cánh tay GIƠ LÊN có bàn tay
# xoè ngón**, trong khi nhân vật đang buông thõng cả hai tay.
#
# Mô hình vẽ hình que rất sạch vì hình que không có giải phẫu. Nhưng BÓNG ĐỔ thì nó vẽ như vẽ
# bóng của một người thật — và một cái bóng người thật cạnh một hình que là chỗ duy nhất còn
# lại để giải phẫu quay về. Bốn khung tham chiếu anh gửi không có lấy một cái bóng đổ nào.
#
# Câu cấm viết theo lối KHẲNG ĐỊNH ("the only shadow is one simple flat ellipse") vì FLUX
# không có negative prompt — vế phủ định đứng sau chỉ để bắt phần dư (§17.6).

# ══ 18 KÊNH ══════════════════════════════════════════════════════════════════════════════════
# Mỗi kênh khai SÁU trường hình, và sáu trường ấy trả lời sáu câu hỏi khác nhau. Bản cũ chỉ có
# `mau` + một câu `sac_thai`, nên mười tám kênh khác nhau ở đúng một tính từ — và tính từ là
# thứ mô hình bỏ qua đầu tiên khi prompt dài.
#
#   kt     kỹ thuật dựng hình (bảng trên)       -> khác nhau ở CHẤT BỀ MẶT, nhìn 0,5 giây là ra
#   mau    ba màu, viết bằng TÊN MÀU tiếng Anh  -> mô hình vẽ được; mã hex thì không
#   sang   CHẤT ánh sáng                        -> hướng và độ gắt, KHÔNG nói nơi chốn
#   may    CHẤT quang học                       -> góc rộng/hẹp, độ sâu trường ảnh
#   the    THẾ GIỚI: ai, ở đâu, lặp lại         -> chỉ dùng cho ĐẠO DIỄN CẢNH, không vào prompt
#   chinh/phu  màu thương hiệu (đồ hoạ code)    -> phải ĐỌC ĐƯỢC ở 48px, không phải màu phim
#
# ══ `sang` VÀ `may` KHÔNG ĐƯỢC CHỨA NỘI DUNG  (sửa gốc 6/9/2026, sau lượt dựng đầu) ═════════
# Lượt demo đầu tiên: bảng phân cảnh viết ĐÚNG tám cảnh khác nhau (buồng ICU · sân thượng lúc
# rạng · quầy trực · căn hộ), mà tám khung dựng ra là TÁM CÚ CẬN MẶT TRONG MỘT PHÒNG KHÁCH.
# Không phải đạo diễn cảnh hỏng — sổ cảnh đọc lên vẫn đúng từng chữ. Hỏng ở chỗ ghép prompt:
#
#     may  = "intimate 40mm lens AT THE CHARACTER'S EYE LEVEL, CLOSE ENOUGH TO READ THE FACE"
#     sang = "soft storybook light …, WARM INTERIORS, blue evenings"
#
# Hai trường lẽ ra tả PHONG CÁCH lại đang tả CỠ CẢNH và NƠI CHỐN — tức chúng ra lệnh về đúng
# hai thứ mà bảng phân cảnh vừa quyết. Và vì khối phong cách đứng ĐẦU prompt, mô hình nghe nó
# trước; câu cảnh đứng sau thành lời đề nghị.
#
# Đây là họ lỗi §12.5 ở dạng thuần nhất: *một câu luật đúng trong ngữ cảnh nó sinh ra* (ở bộ
# cũ, nơi mỗi kênh có đúng một kiểu khung) *sai ở ngữ cảnh mới* (nơi cỡ cảnh đổi từng nhịp).
# Chữa ở GỐC chứ không nới: cắt mọi danh từ nơi chốn và mọi từ chỉ khoảng cách ra khỏi hai
# trường này, và đảo thứ tự để CÂU CẢNH đứng trước (xem `phim.prompt_anh`).
#
# `chinh` KHÔNG lấy từ bảng màu phim. §14.5 đã trả giá: màu không khí đẹp trong một khung phim
# và biến mất trong một hình tròn 48 điểm ảnh. Cổng tương phản canh sàn 3,0 (xem `kiem_phim`).
KENH = {
 "howlong": dict(
   ten="HOW LONG WOULD IT TAKE", kt="goa", chinh="#E0642B", phu="#4FB3C7", nen="#12212B",
   mau="burnt orange, deep teal and pale wheat",
   sang="low golden key light raking in from one side, long soft shadows, clear air",
   may="wide-angle optics, deep focus, low horizon line",
   the="one ordinary American traveller with a worn daypack, crossing wide open American "
       "country: two-lane highways, rest stops, plains, mountain passes"),
 "howbig": dict(
   ten="HOW BIG IS IT REALLY", kt="cg", chinh="#31B0C9", phu="#F08A3C", nen="#0E2530",
   mau="clear cyan, warm sand and off-white",
   sang="bright even daylight from high above, crisp defined shadows, high clarity",
   may="very wide-angle optics with strong perspective, deep focus",
   the="a small human figure standing beside enormous familiar objects in open American "
       "civic spaces: parking lots, stadium fields, harbours, city plazas"),
 "realcost": dict(
   ten="THE REAL COST", kt="muc", chinh="#3FB87E", phu="#E0644A", nen="#101E19",
   mau="deep green, oxblood red and bone white",
   sang="cool soft light from one side, gentle falloff, quiet low-contrast shadow",
   may="normal lens, controlled symmetrical framing, moderate depth of field",
   the="American middle-class interiors and the counters where money changes hands: kitchen "
       "tables, dealership desks, hospital billing windows, garage bays"),
 "howmuch": dict(
   ten="HOW MUCH IS A BILLION", kt="cat", chinh="#9B72D9", phu="#F0B63C", nen="#1B1430",
   mau="deep violet, honey gold and paper cream",
   sang="warm practical light from small sources close by, visible soft shadows",
   may="slightly raised three-quarter viewpoint, tabletop scale, deep focus",
   the="a paper-model America where quantity is built physically: stacked bills, filled "
       "stadiums, warehouses, counting tables, tiny paper crowds"),
 "whatif": dict(
   ten="WHAT IF EVERYONE", kt="cel", chinh="#EE6352", phu="#3FA9C4", nen="#221016",
   mau="tomato red, sky blue and cream",
   sang="open bright daylight, light bouncing everywhere, clean high-key feel",
   may="wide-angle optics, deep focus, horizon kept low",
   the="ordinary American streets and neighbourhoods suddenly doing one thing all at once — "
       "everybody out of their houses, every tap open, every car moving"),
 "survive": dict(
   ten="COULD YOU SURVIVE", kt="goa", chinh="#D9713F", phu="#6FA86A", nen="#191410",
   mau="rust orange, moss green and cold slate",
   sang="hard raking low sun or thin storm light, harsh contrast, cold shadows",
   may="handheld feel, normal lens, slight tilt, medium depth of field",
   the="one prepared but ordinary person against real American wilderness and weather: "
       "high desert, blizzard road, flooded street, night forest"),
 "dayinlife": dict(
   ten="A DAY IN THE LIFE OF", kt="cel", chinh="#EBAA47", phu="#5590B5", nen="#1E1710",
   mau="amber, dusty blue and warm cream",
   sang="soft warm key light with a gentle cool fill, hour-of-day colour shifts",
   may="normal lens, shallow depth of field, soft background falloff",
   the="one American worker followed through a single shift — the same face all episode: "
       "night nurse, long-haul driver, line cook, air traffic controller"),
 "wheregoes": dict(
   ten="WHERE DOES IT GO", kt="cat", chinh="#4FA3D9", phu="#EB9440", nen="#0F2231",
   mau="industrial blue, safety orange and concrete grey",
   sang="cool overhead light with warm accents far behind, industrial contrast",
   may="clean side-on framing, deep focus, strong left-to-right lines",
   the="the American systems that swallow things: sorting plants, sewer mains, recycling "
       "belts, data centres, cargo yards — always something travelling through"),
 "therules": dict(
   ten="THE RULES NOBODY READS", kt="cel", chinh="#E76A44", phu="#6FA86A", nen="#1D1712",
   mau="suburban brick red, lawn green and bleached beige",
   sang="flat bright overhead light, short shadows, deliberately undramatic",
   may="dead-centre symmetrical framing, normal lens, flat deadpan staging",
   the="American suburbia and its small print: HOA lawns, parking lots, community pools, "
       "airport queues, rental counters — an unbothered person breaking a rule"),
 "speedof": dict(
   ten="THE SPEED OF EVERYTHING", kt="ani", chinh="#43A0D1", phu="#F5762F", nen="#0B1A26",
   mau="electric blue, hot orange and deep indigo",
   sang="dusk light plus strong point sources, light streaking through the background",
   may="wide-angle optics low to the ground, motion blur in the background",
   the="American things in motion at their own speed: freight trains, dragstrips, "
       "hummingbirds, elevators, jet runways at dusk"),
 "odds": dict(
   ten="THE ODDS OF THAT", kt="cat", chinh="#9366CE", phu="#E3B33A", nen="#171030",
   mau="royal purple, brass gold and card-table green",
   sang="a warm pool of light from directly above, everything outside it falling away",
   may="slightly overhead viewpoint, normal lens, shallow depth of field",
   the="American games of chance built as paper models: diners with scratch cards, county "
       "fairs, bowling alleys, lottery counters, casino felt"),
 "hiddenfee": dict(
   ten="WHAT IS INSIDE THE PRICE", kt="muc", chinh="#3EA877", phu="#DC6A44", nen="#0F1E17",
   mau="ledger green, receipt cream and stamped red",
   sang="cold flat overhead light, unflattering and even, hard small shadows",
   may="long lens, very shallow depth of field, compressed perspective",
   the="the moment an American price is broken apart: checkout screens, itemised bills, "
       "airline seat maps, ticket windows, contract signing desks"),
 "yearsof": dict(
   ten="YEARS OF YOUR LIFE", kt="goa", chinh="#D5813F", phu="#5B94A3", nen="#1C1512",
   mau="sepia amber, faded teal and old-paper cream",
   sang="warm late light with dust in the beam, long quiet shadows, aged colour",
   may="normal lens, static framing, medium depth of field",
   the="one American life measured out in rooms: the same person aging across kitchens, "
       "cars, waiting rooms, front porches"),
 "howloud": dict(
   ten="HOW LOUD IS IT", kt="ani", chinh="#E8493B", phu="#4A82BE", nen="#12111C",
   mau="siren red, night blue and bleached white",
   sang="one hard bright source against deep black, extreme contrast",
   may="wide-angle optics, deep focus, strong foreground presence",
   the="American places that hurt to stand in: stadium tunnels, runways, factory floors, "
       "fire scenes, race pits — people covering their ears"),
 "whatweighs": dict(
   ten="WHAT IT WEIGHS", kt="cg", chinh="#8FA84A", phu="#DC8055", nen="#171A10",
   mau="olive green, rust brown and pale concrete",
   sang="heavy overcast light, dense shadows sitting directly under everything",
   may="wide-angle optics looking slightly upward, ground plane always visible",
   the="American heavy things and the ground under them: loading docks, scales, tow yards, "
       "grain silos, bridge decks"),
 "rightnow": dict(
   ten="HOW MANY RIGHT NOW", kt="ani", chinh="#2FAEC9", phu="#F09443", nen="#0B1F26",
   mau="teal, sodium orange and midnight blue",
   sang="blue-hour ambient light with thousands of tiny warm points",
   may="very wide high viewpoint looking down, deep focus",
   the="America counted in a single instant: airspace over a city, hospital floors, "
       "highway interchanges, phone-lit crowds at night"),
 "howhot": dict(
   ten="HOW HOT IS IT", kt="cg", chinh="#EE6B29", phu="#5A87AC", nen="#20120C",
   mau="furnace orange, ash grey and cool steel blue",
   sang="light emitted by the hot thing itself, glowing sources, visible heat shimmer",
   may="normal lens, deep focus, rippling air in the foreground",
   the="American heat where people actually meet it: foundries, desert asphalt, wildfire "
       "lines, engine bays, kitchen ranges"),
 "smallest": dict(
   ten="THE SMALLEST THING", kt="cg", chinh="#5C74D6", phu="#B4CE4C", nen="#0D1024",
   mau="clinical indigo, lime accent and clean white",
   sang="clean even light with a soft coloured backlight separating the subject",
   may="macro optics, extremely shallow depth of field, background dissolving to colour",
   the="American everyday objects opened up to microscopic scale: a fingertip, a coin edge, "
       "a phone screen, tap water, a grain of table salt"),
}

# ══ CÂU AN TOÀN — ĐẶT CUỐI, KHÔNG BAO GIỜ BỊ CẮT ═════════════════════════════════════════════
# Chữ trong ảnh là chỗ mô hình hỏng nặng nhất và người xem đọc ra "nghiệp dư" trong nửa giây
# (§12.7). FLUX.2 bám prompt tốt hơn hẳn schnell nên câu cấm chữ NAY CÓ TÁC DỤNG — schnell thì
# gần như bỏ qua. Vẫn giữ cổng đọc chữ ở `phim_anh` làm hàng rào thứ hai.
#
# Viết KHẲNG ĐỊNH ở vế đầu ("clean and unmarked"), vì FLUX không có negative prompt và mọi
# danh từ trong câu đều là thứ nó có thể vẽ (§17.6). Vế phủ định đứng sau chỉ để bắt phần dư.
AN_TOAN = ("Every surface is clean and unmarked. No text, no letters, no numbers, no signage, "
           "no logos, no watermark, no subtitles, no borders or frames — the picture bleeds "
           "to all four edges.")

# ══ GIẢI PHẪU — ĐẶT NGAY TRƯỚC CÂU AN TOÀN  (6/9/2026) ══════════════════════════════════════
# Anh: *"nhiều ảnh hơi lỗi nha e, sau nhớ soi lại prompt để tránh tạo ra ảnh lỗi."*
#
# Đếm tay cả 8 ảnh của bản short: **3 ảnh hỏng rõ, 5 ảnh hỏng nhẹ**. Và cả tám cùng MỘT nguyên
# nhân — chỗ hỏng luôn là BÀN TAY ĐANG THAO TÁC và CHI TRẦN ở cỡ trung:
#
#     S2  tựa xe đẩy      cánh tay dính liền vào xe · chân trần, lệch giày
#     S5  cầm cốc         ngón tay dính thành khối · nửa thân thứ hai lộ dưới mặt bàn
#     S6  cúi bên giường  cánh tay mọc ra từ hông, bàn tay thành cái găng
#
# Đây không phải mô hình yếu chung chung. `kling_studio.py` đã ghi từ 9/8: *yếu = bàn tay ·
# mặt người cận cảnh*. Prompt của em đang gọi thẳng vào đúng chỗ yếu ấy ở gần như mọi nhịp, vì
# lệnh đạo diễn bảo *"nói rõ họ đang làm gì VỚI BÀN TAY"*. Tự tay em đặt hàng cái lỗi này.
#
# Chữa ở HAI chỗ, và cả hai đều không tốn thêm một lượt vẽ nào:
#   · ở đây — một câu KHẲNG ĐỊNH về giải phẫu (FLUX không có negative prompt, §17.6)
#   · ở `phim_canh.LENH` — cấm mô tả bàn tay thao tác, tả bằng TOÀN THÂN
GIAI_PHAU = ("Character anatomy is clean and simple: arms clearly separated from the body with "
             "a visible elbow, hands relaxed and empty at the sides or out of view, five normal "
             "fingers, both feet fully shod, natural human proportions, one head one torso two "
             "arms two legs.")

# Ảnh KHÔNG cần chừa chỗ trống nữa: engine phủ một dải tối chuyển dần ở chân khung cho phụ đề
# và một dải mảnh ở đỉnh cho nhãn. Nhưng vẫn phải dặn MỘT điều về bố cục — mặt nhân vật không
# được nằm đúng chỗ dải phụ đề, vì dải ấy che 22% chiều cao dưới cùng.
# ── LƯỢT ĐO THỨ BA: CHÍNH CÂU NÀY LÀ THỦ PHẠM  (6/9/2026) ──────────────────────────────────
# Sau khi dọn `sang`/`may`, tám khung VẪN ra chân dung cận. Biến còn lại chưa ai đụng là câu
# bố cục, và đọc lại thì nó viết:
#
#     "The FACE and the main action sit in the upper two thirds"
#
# Câu ấy làm đúng ba việc cùng lúc: khẳng định trong khung CÓ một cái mặt, đòi cái mặt ấy CHIẾM
# hai phần ba trên, và không nói gì về khoảng cách. Mô hình gộp lại thành một cách duy nhất
# thoả được cả ba: cắt cận nửa người. Lần thứ BA trong một buổi, cùng một họ lỗi — một trường
# lẽ ra nói về KHUNG lại đang nói về NỘI DUNG.
#
# Nay bố cục chỉ nói đúng thứ nó có quyền nói: tỉ lệ khung, và dải nào phải để trống cho phụ
# đề. Cỡ cảnh là việc của bảng phân cảnh, và bảng ấy đã tự đổi wide/medium/close mỗi nhịp.
# ── ĐÃ THỬ THÊM LUẬT CHỪA ĐẦU VÀO ĐÂY, VÀ ĐÃ GỠ  (6/9/2026) ────────────────────────────────
# Ba khung anh gửi bị cắt mất đầu. Em chữa HAI chỗ cùng lúc: gốc phóng trong engine, VÀ một câu
# ở đây — *"Every person is framed whole with clear empty space above their head; never crop a
# head at the top edge."*
# Dựng lại: đầu hết bị cắt thật, nhưng **nội dung bay sạch** — tập y tá ra tám khung người đứng
# giữa một ngôi làng Địa Trung Hải, không có bệnh viện nào. Khối bố cục phình lên 45 chữ và
# lại nuốt khối cảnh, đúng như khi em tả nét vẽ hình que dài 90 chữ.
#
# **Lần thứ ba cùng một họ lỗi trong một ngày**, nên nó thành luật cứng của tệp này:
#     KHỐI BỐ CỤC CHỈ NÓI VỀ KHUNG. Không nói về người, không nói về cỡ cảnh, không khẳng định
#     trong khung có gì. Mỗi câu thêm vào đây là một câu lấy đi khỏi khối cảnh.
# Cổng `t_khoi_ngan` canh độ dài để lần sau không ai lặng lẽ nới nó ra.
#
# Và lỗi cắt đầu đã được chữa ĐÚNG CHỖ rồi: `Phim.tsx` phóng từ mép trên (`transformOrigin
# 50% 8%`) và hạ biên độ 0,055 -> 0,038, nên phần bị cắt dồn xuống đáy nơi dải phụ đề đã phủ.
# Một biến, một bản sửa — thêm bản sửa thứ hai chỉ để "chắc ăn" là cách phá bản sửa thứ nhất.
BO_CUC_DOC = ("Vertical 9:16 cinematic composition, full environment visible around the "
              "subject. Keep the lowest fifth of the frame free of important detail.")
BO_CUC_NGANG = ("Wide 16:9 cinematic composition, full environment visible around the "
                "subject. Keep the lowest sixth of the frame free of important detail.")


def gu(ma: str) -> dict:
    k = KENH.get(ma)
    if not k:
        raise RuntimeError(f"chưa có kênh {ma!r} trong phim_gu.KENH")
    return k


def khoi_look(ma: str, kt: str = "") -> str:
    """Khối art-direction của kênh — phần ĐẦU prompt, và phần không bao giờ được cắt.

    Thứ tự cố ý: kỹ thuật -> bảng màu -> ánh sáng -> ống kính. Đây là thứ tự của một bản chỉ
    đạo hình ảnh thật, và cũng là thứ tự mô hình đọc nặng ký nhất -> nhẹ dần."""
    k = gu(ma)
    # `kt` ép kỹ thuật khác với khai báo của kênh — chỉ dùng để DỰNG THỬ một tập rồi so bằng
    # mắt (§4: pilot một kênh, anh duyệt, rồi mới nhân ra). Không ghi đè vào `KENH`, nên bỏ cờ
    # là kênh trở lại đúng bản sắc của nó.
    t = KY_THUAT.get(kt or k["kt"], KY_THUAT[k["kt"]])
    # Kiểu doodle KHÔNG nhận câu ánh sáng: nó không có đổ bóng mềm, và câu "long soft shadows"
    # kéo thẳng mô hình về lối vẽ có khối. Cùng luật §12.5 — câu đúng ở ngữ cảnh cũ, sai ở đây.
    if (kt or k["kt"]) == "doo":
        return f"{t}. Colour palette: {k['mau']}. Camera: {k['may']}."
    return (f"{t}. Colour palette: {k['mau']}. "
            f"Lighting: {k['sang']}. Camera: {k['may']}.")


def the_gioi(ma: str) -> str:
    return gu(ma)["the"]


def bang_ky_thuat() -> dict:
    """Đếm số kênh dùng mỗi kỹ thuật — cổng đa dạng đọc cái này (xem `kiem_phim`)."""
    d = {}
    for k in KENH.values():
        d[k["kt"]] = d.get(k["kt"], 0) + 1
    return d


# ══ DÀN VAI KHAI SẴN — KHOÁ CỨNG CẢ LOẠT  (6/9/2026) ═════════════════════════════════════════
# Anh gửi mẫu `GLOBAL CHARACTER LOCK` của bộ Kling (Mike · Lisa · Tommy · Grandpa Joe · Buddy)
# và dặn: *"nhiều nhân vật thì phải xây nhiều nhân vật — bác sĩ khác, bệnh nhân khác, gái khác
# trai khác"* và *"xây dựng sẵn các nhân vật cho chuẩn để cho ra đều"*.
#
# ── VÌ SAO KHAI SẴN THAY VÌ ĐỂ AI CASTING MỖI TẬP ────────────────────────────────────────────
# Bản trước gọi Groq casting lại mỗi tập. Nó đúng về mặt "có nhiều vai", nhưng sai về mặt LOẠT:
# tập 4 có `nurse = white scrub dress, brown round hair, glasses`, tập 5 sẽ ra một người khác.
# Người xem theo dõi một KÊNH, không theo dõi một tập — và thứ làm họ nhận ra kênh trước cả tên
# kênh là khuôn mặt quen. Đây đúng cơ chế `VAI` mà `kich_comic.py` đã chạy cho bộ hài.
# Khai sẵn còn rẻ hơn: 0 lượt gọi AI, và tất định nên hai máy dựng ra cùng một dàn vai.
#
# ── BA VAI, KHÔNG PHẢI MỘT, VÀ PHẢI KHÁC NHAU Ở BA TRỤC ─────────────────────────────────────
# Mỗi kênh ba vai và chúng khác nhau ở TUỔI · GIỚI · TRANG PHỤC cùng lúc — ba trục, vì khác một
# trục thì ở cỡ nhỏ vẫn đọc ra cùng một người. Vai đầu là vai chính, xuất hiện nhiều nhất.
#
# ── DẤU MỸ NẰM Ở TRANG PHỤC, KHÔNG NẰM Ở CỜ ─────────────────────────────────────────────────
# Anh: *"nên có nét theo phong cách USA để người xem nhận biết"*. Cách rẻ và không sến là để
# nó ở QUẦN ÁO đời thường Mỹ: mũ lưỡi trai, áo flannel, hoodie, áo sơ mi bỏ ngoài, áo hi-vis,
# giày thể thao, quần jeans, dây đeo thẻ. Không cờ, không tượng Nữ Thần — hai thứ ấy đọc ra là
# hàng du lịch, không đọc ra "kênh của mình".
VAI = {
 "howlong": [
   ("Dale", "38-year-old man, medium build, short sandy hair, olive canvas jacket, grey t-shirt, blue jeans, tan hiking boots, patient and stubborn"),
   ("Rosa", "34-year-old woman, ponytail of dark curly hair, red flannel shirt over a white tee, denim shorts, white sneakers, quick and practical"),
   ("Coach Pete", "61-year-old man, white crew cut, grey university sweatshirt, navy track pants, whistle on a cord, blunt and encouraging"),
     ('Eli', '24-year-old man, long braided ponytail, blonde, navy bomber jacket, green cargo vest, meticulous'),
     ('Milo', '48-year-old man, silver buzz cut, maroon windbreaker, pocket chronometer, impatient')],
 "howbig": [
   ("Marcus", "45-year-old man, tall and broad, shaved head, orange hi-vis vest over a navy work shirt, khaki cargo pants, steel-toe boots, unimpressed"),
   ("Ivy", "29-year-old woman, short black bob, yellow hard hat, denim jacket, olive work trousers, brown boots, curious and precise"),
   ("Dot", "9-year-old girl, two dark braids, purple hoodie, pink leggings, light-up sneakers, wide-eyed"),
     ('Lena', '18-year-old woman, shaved sides with teal mohawk, teal, bright pink safety vest, black work shirt, inventive'),
     ('Gus', '62-year-old man, gray curly hair, amber coveralls, laser measuring rod, methodical')],
 "realcost": [
   ("Ray", "41-year-old man, slightly round, brown side-part hair, white short-sleeve shirt, blue tie loosened, grey slacks, brown loafers, cheerful and careless with money"),
   ("Nina", "39-year-old woman, shoulder-length auburn hair, forest-green blouse, charcoal trousers, low heels, calm and dryly sceptical"),
   ("Uncle Walt", "68-year-old man, white moustache, red ball cap, blue denim jacket, khaki pants, thrifty and opinionated"),
     ('Graham', '52-year-old man, slicked back silver hair, silver, emerald leather apron, cream shirt, calculating'),
     ('Eli', '30-year-old man, black dreadlocks, green sweater, ledger book, frugal')],
 "howmuch": [
   ("Benji", "33-year-old man, wiry, messy black hair, mustard cardigan over a white tee, brown corduroy pants, canvas shoes, easily amazed"),
   ("Claire", "36-year-old woman, blonde hair in a low bun, teal sweater, dark jeans, white trainers, methodical"),
   ("Mr Okoye", "57-year-old man, greying temples, grey vest over a striped shirt, brown slacks, patient teacher manner"),
     ('Mira', '45-year-old woman, short curly red hair, red, purple kimono, black leggings, inquisitive'),
     ('Jax', '24-year-old man, auburn ponytail, purple blazer, abacus, analytical')],
 "whatif": [
   ("Sam", "30-year-old man, average build, curly brown hair, red hoodie, blue jeans, white high-tops, reckless optimist"),
   ("Priya", "31-year-old woman, long straight black hair, mustard t-shirt, olive utility trousers, tan sandals, sharp and amused"),
   ("Gus", "70-year-old man, bald with white sideburns, blue plaid shirt, suspenders, brown work pants, unbothered by chaos"),
     ('Jace', '22-year-old man, high top fade, dark brown, orange jumpsuit, utility belt, daring'),
     ('Rex', '44-year-old man, silver shaved sides, orange trench coat, virtual reality headset, visionary')],
 "survive": [
   ("Kyle", "36-year-old man, lean, stubble, dark green parka, grey thermal shirt, brown cargo pants, worn boots, tense and careful"),
   ("Marta", "40-year-old woman, red hair tied back under a wool beanie, orange puffer jacket, black snow pants, heavy boots, unshakeable"),
   ("Ranger Ellis", "52-year-old man, grey moustache, olive ranger shirt with a badge, campaign hat, khaki trousers, deadpan authority"),
     ('Tara', '28-year-old woman, braided crown, black, yellow insulated vest, gray fleece, resourceful'),
     ('Cole', '60-year-old man, blonde crew cut, khaki survival jacket, multi-tool belt, steadfast')],
 "dayinlife": [
   ("Nurse Tara", "34-year-old woman, dark brown hair in a low bun, teal scrubs, white sneakers, lanyard badge, tired but warm"),
   ("Dr Vance", "48-year-old man, greying black hair, white coat over a light blue shirt, navy trousers, brown shoes, brisk"),
   ("Mr Hollis", "74-year-old man, thin white hair, pale green hospital gown, grey socks, grumbling and grateful"),
     ('Eli', '58-year-old man, short silver hair, navy scrubs with emerald green trim, clipboard holster, compassionate'),
     ('Jace', '22-year-old man, red curly hair, pink scrub coat, white clogs, stethoscope around neck, inquisitive')],
 "wheregoes": [
   ("Trav", "27-year-old man, short blond hair under a backwards cap, grey coveralls, yellow work gloves, black boots, easygoing"),
   ("Bea", "44-year-old woman, silver-streaked dark hair in a bun, navy supervisor polo, khaki trousers, safety glasses, no-nonsense"),
   ("Otis", "19-year-old man, tall and skinny, dark curls, blue warehouse t-shirt, jeans, sneakers, always asking why"),
     ('Mara', '60-year-old woman, braided dark brown hair, high‑visibility orange safety vest over charcoal jumpsuit, steel‑toe boots, meticulous'),
     ('Lena', '35-year-old woman, black shaved head, purple raincoat, dark leggings, hard hat, skeptical')],
 "therules": [
   ("Doug", "47-year-old man, round belly, thinning brown hair, salmon polo shirt, cargo shorts, white socks with sandals, oblivious"),
   ("Karen-Ann", "45-year-old woman, blonde bob, lavender cardigan, white capri pants, sunglasses on her head, clipboard, rule-loving"),
   ("Officer Mel", "38-year-old woman, black hair in a tight bun, tan uniform shirt, dark trousers, utility belt, weary politeness"),
     ('Sam', '60-year-old man, bald with a neat goatee, forest green tie over a crisp white shirt, black suspenders, leather satchel, rule‑abiding'),
     ('Mira', '30-year-old woman, short brown bob, olive drab utility jacket, khaki trousers, clipboard, analytical')],
 "speedof": [
   ("Zeke", "25-year-old man, athletic, buzzcut, red racing jacket, black track pants, running shoes, impatient"),
   ("Dr Lin", "42-year-old woman, straight black hair to the chin, white lab coat over a grey turtleneck, dark trousers, stopwatch, exacting"),
   ("Pop Harlan", "66-year-old man, white beard, brown leather jacket, blue jeans, cowboy boots, tells long stories"),
     ('Rita', '55-year-old woman, long teal ponytail, neon yellow windbreaker, black leggings, digital pulse monitor, precise'),
     ('Toby', '31-year-old man, blonde ponytail, turquoise cycling jersey, black shorts, bike helmet, enthusiastic')],
 "odds": [
   ("Lucky Lou", "52-year-old man, stocky, slicked grey hair, purple bowling shirt, gold chain, black slacks, white shoes, hopeful gambler"),
   ("Fern", "31-year-old woman, red pixie cut, denim jacket over a black tee, green skirt, boots, sharp with numbers"),
   ("Grandma Pearl", "78-year-old woman, white curls, floral cardigan, beige slacks, bingo dauber, mischievous"),
     ('Milo', '65-year-old man, wiry, salt‑and‑pepper shaved head, maroon bomber jacket, charcoal slacks, lucky dice keychain, calculating'),
     ('Silas', '40-year-old man, black braid, teal lab coat, brown shoes, pocket calculator, skeptical')],
 "hiddenfee": [
   ("Victor", "44-year-old man, neat black hair, grey suit without the jacket, white shirt, red tie, black shoes, smooth salesman"),
   ("Alma", "37-year-old woman, dark hair in a ponytail, mustard blazer over a white tee, blue jeans, flat shoes, reads every line"),
   ("Chet", "23-year-old man, freckles, ginger hair, blue polo with a name tag, khaki pants, sneakers, apologetic"),
     ('Nina', '55-year-old woman, sleek auburn bob, teal silk scarf over a charcoal blouse, charcoal pencil skirt, vintage fountain pen, persuasive'),
     ('Gwen', '31-year-old woman, short grey buzz, olive green apron over white shirt, black trousers, magnifying glass, probing')],
 "yearsof": [
   ("Hal", "55-year-old man, greying temples, brown cardigan over a beige shirt, dark trousers, slippers, reflective"),
   ("June", "53-year-old woman, silver-blonde hair to the shoulders, dusty-rose sweater, navy skirt, low boots, warm and direct"),
   ("Young Hal", "19-year-old version of Hal, thick brown hair, white t-shirt, blue jeans, red sneakers, restless"),
     ('Milo', '30-year-old man, shaved sideburns, teal windbreaker over a charcoal tee, cargo shorts, digital watch, inquisitive'),
     ('Mara', '40-year-old woman, curly auburn hair, green sweater, orange trousers, curious')],
 "howloud": [
   ("Rico", "29-year-old man, muscular, black hair in a fade, yellow ear defenders around his neck, grey work shirt, black jeans, boots, shouts everything"),
   ("Dana", "35-year-old woman, brown hair in a braid, orange hi-vis jacket, navy trousers, safety boots, calm in chaos"),
   ("Little Ann", "8-year-old girl, blonde pigtails, pink earmuffs, red jacket, blue jeans, sneakers, covers her ears"),
     ('Jax', '20-year-old man, buzz cut, lime-green safety vest over a black thermal shirt, dark cargo pants, steel-toe boots, monitors vibrations'),
     ('Vik', '44-year-old man, shaved silver hair, purple headphones, brown leather jacket, observant')],
 "whatweighs": [
   ("Big Earl", "50-year-old man, very broad, red beard, grey tank top under open blue overalls, brown boots, gentle giant"),
   ("Suze", "33-year-old woman, athletic, dark braid, black tank top, grey work trousers, weightlifting belt, competitive"),
   ("Chip", "17-year-old boy, skinny, floppy brown hair, green t-shirt, baggy jeans, sneakers, overestimates himself"),
     ('Nora', '41-year-old woman, copper curls, mustard raincoat over a white polo, black leggings, rubber gloves, methodical'),
     ('Cal', '26-year-old man, short black hair, purple hoodie, silver weight scale, precise')],
 "rightnow": [
   ("Ana", "28-year-old woman, long dark wavy hair, blue denim jacket, white tee, black jeans, white sneakers, curious about crowds"),
   ("Devon", "32-year-old man, short black hair, grey hoodie, olive joggers, orange running shoes, always on his phone"),
   ("Mrs Reyes", "60-year-old woman, grey hair in a bun, purple cardigan, floral skirt, comfortable shoes, unhurried"),
     ('Lena', '45-year-old woman, platinum bob, maroon bomber jacket over a striped tee, ripped denim, high-top sneakers, always scanning'),
     ('Tess', '22-year-old woman, straight dark hair, teal windbreaker, yellow sneakers, inquisitive')],
 "howhot": [
   ("Tank", "39-year-old man, shaved head, silver heat-proof jacket open over a black tee, grey trousers, heavy boots, fearless"),
   ("Jo", "34-year-old woman, red hair under a bandana, tan fire-resistant shirt, olive trousers, boots, measured"),
   ("Skip", "26-year-old man, sunburnt, blond curls, white tank top, board shorts, flip-flops, complains about heat"),
     ('Cass', '48-year-old woman, tight braids, cobalt fire-retardant jumpsuit with reflective strips, heat-resistant boots, analytical'),
     ('Gus', '58-year-old man, bald, amber fire‑resistant coat, charcoal gloves, stoic')],
 "smallest": [
   ("Dr Wren", "36-year-old woman, black hair in a short bob, white lab coat over a lilac blouse, navy trousers, safety goggles pushed up, delighted by detail"),
   ("Milo", "31-year-old man, glasses, brown hair, blue lab coat over a checked shirt, grey chinos, white trainers, clumsy"),
   ("Ravi", "12-year-old boy, black hair, orange t-shirt, blue jeans, green sneakers, endless questions"),
   ('Leif', '24-year-old man, neat brown hair, grey safety apron, microscope slide, meticulous'),
 ],
}


_VAI_THEM: dict = {}


def dan_vai_khai(ma: str) -> list:
    """Dàn vai khai sẵn của kênh, dạng [{"vai": tên, "ta": mô tả}]. Rỗng nếu chưa khai.

    ── VÌ SAO CÓ `vai_them.json`  (6/9/2026) ───────────────────────────────────────────────
    Vai mới nối bằng cách SỬA MÃ NGUỒN bảng `VAI` đã làm hỏng tệp hai lần trong một buổi (dấu
    `]` đặt sai chỗ, dấu phẩy treo thiếu) — mỗi lần đều `SyntaxError` lúc import, tức chết ở
    chỗ xa nơi gây ra. Chèn phần tử vào một literal Python bằng phép cắt chuỗi là việc không
    nên làm lần thứ ba.
    Nay vai thêm nằm ở `vai_them.json` và được GỘP lúc chạy. Bảng `VAI` giữ nguyên là dàn vai
    gốc viết tay; tệp JSON là phần mở rộng máy sinh — hai thứ khác nguồn thì để hai chỗ.
    """
    ds = list(VAI.get(ma, []))
    if not _VAI_THEM:
        import json as _j, io as _io, os as _o
        p = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "vai_them.json")
        try:
            _VAI_THEM.update(_j.load(_io.open(p, encoding="utf-8")))
        except Exception:
            _VAI_THEM["_"] = {}
    co = {t for t, _m in ds}
    for v in (_VAI_THEM.get(ma) or []):
        if v.get("ten") and v["ten"] not in co:
            ds.append((v["ten"], v.get("ta") or ""))
            co.add(v["ten"])
    return [{"vai": t, "ta": m} for t, m in ds]


# Khối KHOÁ NHÂN VẬT, viết đúng lối bộ Kling đang dùng: một câu mệnh lệnh viết hoa, rồi danh
# sách, rồi câu cấm thiết kế lại. Chỉ ghép những vai CÓ MẶT trong cảnh — xem `phim.prompt_anh`.
def khoa_vai(ds: list) -> str:
    if not ds:
        return ""
    d = " ".join(f"{v['vai']}: {v['ta']}." for v in ds)
    return (" CHARACTER LOCK — these people must look identical in every shot of the series: "
            + d + " Keep the same faces, body proportions, hair, clothing colours and ages. "
                  "Do not redesign or replace them.")
