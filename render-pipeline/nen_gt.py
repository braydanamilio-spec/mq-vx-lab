#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VẼ CẢNH BẰNG CLOUDFLARE cho phim giải thích — mỗi nhịp một ảnh.  (1/9/2026)

Anh: *"sao ko dùng cf vẽ chính xác cảnh đẹp ra luôn, ko cần động phần nhân vật đâu, chỉ cần vẽ
đúng bối cảnh biểu cảm, bối cảnh khớp đẹp là ok."*

Anh đúng, và em đã đi sai một vòng. Em cố vẽ nhân vật bằng vector rồi dán lên nền vẽ tay — mà
nhân vật vector CHÍNH LÀ chỗ xấu: tóc bù thành cái chổi, thân thành hình chữ nhật nâu, và cảnh
nhóm thì năm người giống hệt nhau tay chồng lên nhau.

CÓ 97 KHOÁ CF. Vẽ nguyên cảnh bằng FLUX vừa đẹp hơn hẳn vừa không tốn công em, và quan trọng
hơn: nó VẼ ĐÚNG THỨ CÂU ĐANG NÓI. Vector chỉ vẽ được mười một căn phòng em đã lập trình sẵn.

── VÌ SAO LẦN NÀY KHÁC LẦN TRƯỚC ───────────────────────────────────────────────────────────
CLAUDE.md ghi: *"bốn lỗi của bản hài cũ đều chảy ra từ dán người vector lên ảnh AI."* Đúng —
nhưng đó là lỗi của việc DÁN NGƯỜI VECTOR LÊN, không phải lỗi của ảnh AI. Ở đây không dán gì
cả: FLUX vẽ cả người lẫn cảnh trong cùng một ảnh, nên không có chuyện ánh sáng lệch, bóng sai
hướng, hay người lơ lửng. Bốn lỗi ấy không có chỗ để phát sinh.

Đổi lại mất tính nhất quán nhân vật giữa các khung. Với kênh HÀI có dàn vai cố định thì đó là
lỗi chết người (gói 15s viết hoa `MASTER CHARACTER LOCK` vì thế). Với kênh GIẢI THÍCH thì không
có vai nào cả — chỉ có "một người", "một người đi bộ". Nên cái giá ấy bằng không.

── KHOÁ PHONG CÁCH ─────────────────────────────────────────────────────────────────────────
Mọi ảnh của cả mười kênh dùng chung một câu khoá phong cách. Không phải để đẹp — để 250 khung
của một tập trông như MỘT bộ phim chứ không như 250 ảnh nhặt về.
"""
import io
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
THU = os.path.join(os.path.dirname(GOC), "engine-remotion", "public", "gt_nen")

from kich_hai import SAN_NEN                                   # noqa: E402

# ── LUẬT BỐ CỤC PHẢI ĐỔI THEO TRONG NHÀ / NGOÀI TRỜI ────────────────────────────────────────
# 1/9 — soi khung bắt được: nhịp "No sleep" nói về người đi bộ ban đêm giữa sa mạc, mà ảnh ra
# là một PHÒNG KHÁCH có tủ kệ; nhịp "Days go by" thì có chậu cây với cái ghế đặt giữa cồn cát.
#
# Gốc rễ nằm ở chính câu `SAN_NEN` mà tôi vừa viết lại sáng nay: *"all FURNITURE and objects
# pushed far to the left and right edges"*. Câu ấy soạn cho cảnh TRONG NHÀ. Đem nguyên si sang
# cảnh ngoài trời thì FLUX làm đúng điều được bảo — nó kê đồ nội thất vào sa mạc.
#
# Đây là họ lỗi *"mượn giá trị cho việc nó không sinh ra để làm"* đã ghi ở CLAUDE.md. `SAN_NEN`
# sinh ra cho bộ truyện tranh, nơi mọi cảnh đều trong nhà. Dùng lại là đúng; dùng lại mà không
# hỏi "câu này còn đúng ở ngữ cảnh mới không" là sai.
# ══ CẮT VUÔNG XUỐNG KHUNG PHIM — LUẬT BỐ CỤC PHẢI BIẾT ĐIỀU ĐÓ (1/9/2026) ═══════════════════
# Đã thử và bị từ chối: `@cf/black-forest-labs/flux-1-schnell` KHÔNG nhận `width`/`height`
# (HTTP 400). Ảnh luôn là 1024×1024 vuông. Thử đổi sang `sdxl-lightning` (model này CÓ nhận
# khung 768×1344) thì nó trả về một tấm ĐEN THUI — bộ lọc an toàn của SDXL trên CF.
# Nên: giữ FLUX, và giải bài toán tỉ lệ ở chỗ đúng của nó là LUẬT BỐ CỤC.
#
# Số học của phép cắt:
#   vuông -> 9:16  giữ lại 56% BỀ NGANG   (mất 44%, cắt đều hai bên)
#   vuông -> 16:9  giữ lại 56% CHIỀU CAO  (mất 44%, cắt đều trên dưới)
#
# Và đây mới là chỗ chết người: luật cũ dặn *"dồn đồ đạc ra hai mép"* — tức dặn mô hình đặt đồ
# vào ĐÚNG dải sắp bị cắt bỏ. Prompt đúng, ảnh đúng, khung phim cắt sạch. Cùng họ lỗi với vụ
# `SAN_NEN` kê tủ vào sa mạc: một câu luật đúng trong ngữ cảnh nó sinh ra, sai ở ngữ cảnh mới.
# ══ CHỪA CHỖ CHO CHỮ — ĐO TỪ CHÍNH ENGINE, KHÔNG ƯỚC LƯỢNG ═════════════════════════════════
# Anh: *"nhớ căn ép ảnh khi generate, chừa vùng trống để có chỗ để chart hay text hay số liệu,
# để không bị che khuất — như phần trước em làm ấy."*
#
# Anh nhắc đúng: tôi đã có luật ép sàn ("sàn chiếm trọn phần ba dưới, đồ đạc dồn hai mép, giữa
# để trống") và nó hiệu quả — nhưng tôi chỉ áp cho SÀN, quên áp cho VÙNG CHỮ. Hậu quả đã thấy:
# chữ "KILOMETRES" nằm lọt sau người, số "30" đè lên mặt.
#
# Đo lại chính engine xem lớp chữ thật sự nằm ở đâu (tính theo chiều cao khung đầy đủ):
#     dải nền số liệu  0,07      số liệu        0,21
#     trục             0,42      đáy cột chart  0,64
#     dải chữ dưới     0,72      chú thích      0,75      phụ đề  0,92
# => VÙNG PHẢI TRỐNG: 0,05–0,32 ở trên, và 0,68–1,00 ở dưới. Chủ thể sống ở dải giữa.
#
# Viết bằng ngôn ngữ TRANH VẼ, không phải ngôn ngữ ảnh chụp — nói "khoảng trời phẳng", "mặt sàn
# phẳng", chứ không nói "khoảng âm" hay "vùng an toàn" (mô hình không hiểu hai chữ ấy).
CHUA_CHO = ("the top third is empty plain sky or flat wall with nothing drawn in it, the "
            "bottom fifth is empty flat ground with nothing in it, everything important sits "
            "in the middle band")

KHUNG_DOC = ("tall vertical composition, subject centred, nothing important in the outer "
             "quarter left or right, " + CHUA_CHO)
KHUNG_NGANG = ("wide horizontal composition, subject centred, " + CHUA_CHO)

SAN_NGOAI = ("wide shot, camera at standing eye level, "
             "the ground fills the entire bottom third of the frame as one continuous "
             "unbroken surface running from the left edge to the right edge, "
             "rocks plants and scenery pushed far to the left and right edges, "
             "the centre of the frame is open empty ground, no interior, no walls, no ceiling")

_NGOAI = re.compile(
    r"\b(desert|tundra|plain|field|sky|outdoor|street|road|highway|forest|valley|coast|"
    r"beach|mountain|snow|lawn|yard|driveway|curb|curb|sidewalk|space|moon|planet|stars|"
    r"horizon|open ground|savanna|wilderness|dunes)\b", re.I)


SAN_DOC = ("camera at standing eye level, the ground runs across the lower part of the frame "
           "as one continuous unbroken surface, the subject standing on it near the centre, "
           "scenery arranged above and below the subject rather than out to the sides")
SAN_DOC_NGOAI = SAN_DOC + ", open outdoor scene, no interior, no walls, no ceiling"


def _luat(ve: str, doc: bool = False) -> str:
    """Chọn luật bố cục theo CẢNH và theo HƯỚNG KHUNG.

    Hai trục, không phải một:
      · trong nhà / ngoài trời — quyết định có được nhắc chữ `furniture` hay không;
      · dọc / ngang — quyết định thứ quan trọng được đứng ở đâu để sống sót qua phép cắt.
    Bản dọc KHÔNG được dồn đồ ra hai mép (mép bị cắt), nên chuyển sang xếp chồng theo chiều cao.
    """
    ngoai = bool(_NGOAI.search(ve or ""))
    if doc:
        return SAN_DOC_NGOAI if ngoai else SAN_DOC
    return SAN_NGOAI if ngoai else SAN_NEN

# Khoá phong cách — dựng theo đúng thứ đo được ở hai video tham chiếu (mục 6-7 của
# PHAN_TICH_GIAI_THICH.md): nét đen dày đều, màu phẳng tươi, người que đầu tròn trắng, và nền
# CÓ CHIỀU SÂU ba lớp (trời -> núi xa -> tiền cảnh) chứ không phải tường phẳng.
# Anh: *"người que xấu thì có thể vẽ người thật hay dạng khác, sao cho phù hợp USA đẹp và hợp
# niche."* Nên phong cách là MỘT KHOÁ RIÊNG CHO TỪNG KÊNH, không ép một kiểu cho cả mười.
# Người que hợp kênh khoa học vui; kênh tài chính thì hình phẳng kiểu tạp chí đọc "đáng tin"
# hơn hẳn; kênh lịch sử thì tranh vẽ tay ấm màu. Chọn sai phong cách là kênh mất uy trước khi
# nói được câu nào — và uy tín là thứ quyết định RPM ở mấy niche này.
# ══ MỘT PHONG CÁCH DUY NHẤT: CARTOON PHẲNG ══════════════════════════════════════════════════
# Anh gửi hai khung tham chiếu và nói: *"vẽ kiểu thật xấu thì e vẽ kiểu cartoon xem sao."*
#
# Đúng, và nó khớp chính xác với số đo của tôi: ảnh mang chất ảnh chụp đo độ phẳng 0,13–0,20 và
# trông tệ; ảnh phẳng đo 0,85–0,91 và trông đẹp. Hai khung anh gửi (người que trên ghế sofa xanh
# lá · người que ở cửa nhà vàng) thuộc đúng nhóm sau.
#
# BỎ HẲN NĂM PHONG CÁCH. Bản trước tôi gán mỗi niche một phong cách — nghe hợp lý, nhưng thực
# tế là hai trong năm phong cách ấy (`tranh`, `kich`) YÊU CẦU chất ảnh thật, tức tôi tự tay đặt
# hàng đúng thứ trông tệ. Mười kênh phân biệt nhau bằng BẢNG MÀU (đã có, xem `MAU_KENH`), không
# cần phân biệt bằng chất vẽ.
#
# VÀ BỎ NGÔN NGỮ MÔ TẢ ẢNH CHỤP. Đây là chỗ tôi đã nhận ra mà chưa sửa: prompt sáu tầng có
# "background:", "foreground:", "warm light from the left, long soft shadows" — đó là cách người
# ta tả một BỨC ẢNH. Mô hình đọc xong thì vẽ ra một bức ảnh. Muốn cartoon thì phải nói bằng ngôn
# ngữ của tranh vẽ: mảng màu phẳng, nét viền đen dày, không chuyển sắc, không kết cấu bề mặt.
# ── PHONG CÁCH VẼ — VIẾT LẠI THEO SÁU ẢNH THAM CHIẾU ANH GỬI  (3/9/2026) ────────────────────
# Anh: *"template nền màu tối xấu, ảnh generate sinh ra cũng tối xấu… loại ảnh CF tạo đẹp mà em
# chưa tận dụng được, đang viết prompt chưa chuẩn."*
#
# Đối chiếu prompt cũ với ảnh anh gửi thì thấy **hai câu đang chống lại chính thứ anh muốn**:
#
#   "no gradients, no texture"  →  ảnh anh gửi CÓ đổ bóng mềm (ghế sofa, quầng đèn bàn), trời
#                                  chuyển màu, lông thú có nét. Cấm gradient là ép mô hình vẽ
#                                  clipart phẳng — đúng thứ trông rẻ tiền khi đứng cạnh cảnh thật.
#   "bright saturated palette"  →  nói về ĐỘ RỰC của màu, KHÔNG nói nền phải SÁNG. Mô hình vì thế
#                                  tự do chọn nền tối, và nó chọn tối thật.
#
# Và prompt cũ **không có câu nào về bối cảnh**, nên ra khung rỗng. Sáu ảnh tham chiếu thì ngược
# lại: kín chi tiết — cửa sổ có mây, đồng hồ tường, chậu cây, sạp chợ, lạc đà, đống rơm.
#
# Ba mệnh lệnh mới, mỗi câu chữa đúng một lỗi đo được:
#   1. NỀN LUÔN SÁNG VÀ ẤM — nói thẳng, kèm ví dụ màu, và cấm nền tối bằng tên.
#   2. CÓ ĐỔ BÓNG MỀM — nhưng vẫn cấm chất ẢNH CHỤP (§12.6: tả theo lối ảnh chụp thì ra ảnh chụp).
#   3. BỐI CẢNH VẼ ĐẦY — liệt kê loại đồ vật, vì "chi tiết" là chữ trừu tượng còn "đồng hồ tường,
#      chậu cây, cửa sổ" thì mô hình vẽ được (§13.2: cổng đo một TỪ thì lệnh dặn phải liệt kê từ).
# ── KẸP PHONG CÁCH NGẮN, ĐẶT NGAY SAU CÂU CẢNH  (3/9/2026) ─────────────────────────────────
# Dời câu cảnh lên đầu prompt thì ảnh khớp lời hẳn — nhưng khối phong cách 844 ký tự lùi xuống
# cuối và mất trọng số: một nhịp của SURVIVE ra chất ẢNH CHỤP (độ phẳng 0,17 so mốc 0,65 của cả
# tập), vẽ lại ba lần vẫn thế.
#
# Hai yêu cầu đánh nhau: cảnh phải đứng đầu để ảnh đúng nội dung, phong cách phải đứng gần đầu
# để ảnh đúng chất. Giải bằng cách TÁCH: sáu chữ cốt lõi kẹp ngay sau cảnh (vẫn ở vùng trọng số
# cao), khối chi tiết để sau. Không phải thêm chữ — là xếp lại thứ tự cùng một lượng chữ.
# ── CÂU SIẾT CHẤT VẼ, DÙNG KHI CỔNG ĐÁNH TRƯỢT  (3/9/2026) ─────────────────────────────────
# Cổng `do_phang` bắt được ảnh ngả chất ảnh chụp và cho vẽ lại tới ba lần — nhưng `_thu` gọi
# `_prompt(...)` Y HỆT mỗi lần, và FLUX schnell KHÔNG nhận `seed` (§12.1, đã trả giá bằng HTTP
# 400 trên mọi lệnh vẽ). Nên "vẽ lại bằng seed khác" chưa bao giờ tồn tại: cùng prompt ra cùng
# ảnh, ba lượt vẽ lại là ba lượt tiêu neuron cho đúng một kết quả.
#
# Đo được ở SURVIVE: hai nhịp CHỈ CÓ VẬT ("raw wild roots and berries" · "unfamiliar wild plants
# and exposed roots") ra ảnh chụp thật với độ phẳng 0,48 và 0,18 trong khi cả tập ở 0,71–0,83.
# Vẽ lại ba lần: **0,18 cả ba lần**. Không phải may rủi — chính prompt kéo nó đi (§12.6).
#
# Nên mỗi lần trượt thì SIẾT prompt theo hướng cổng đang đo. Đặt ở ĐẦU prompt vì đó là vùng
# trọng số cao nhất, và nói bằng khẳng định dương chứ không phải câu cấm — FLUX không có
# negative prompt, mọi danh từ viết ra đều là thứ SẼ xuất hiện.
# ── CÂU SIẾT KHÔNG ĐƯỢC ĐẨY VỀ PHÍA TRẮNG  (3/9/2026, cùng ngày) ───────────────────────────
# Bản đầu của bảng này viết "on white paper" và "on a blank white page". FLUX làm đúng: ra một
# TRANG TRẮNG. Cổng `kiem_chelap` bắt ngay ở bản dài HOW LOUD — 8 nhịp có nền **sáng TB 237,
# 99% điểm sáng** (trần 150 và 35%), tức chữ trắng đè lên nền trắng và tàng hình.
#
# Siết chất vẽ và giữ nền có màu là HAI việc, và câu siết phải làm việc thứ nhất mà không phá
# việc thứ hai. Nay mọi mức đều khẳng định NỀN CÓ MÀU — cùng họ lỗi với dải mờ màu đen: chữa
# một trục thì đừng phá trục bên cạnh.
# Mỗi mức siết nay khẳng định CẢ HAI: chất vẽ phẳng VÀ nền sáng. Bản cũ chỉ nói về chất
# vẽ, nên một ảnh bị đánh trượt vì quá tối được vẽ lại bằng một câu không hề nhắc tới độ
# sáng — tức vẽ lại mà không đổi thứ đang hỏng (§16.4: một vòng thử lại phải đổi ĐẦU VÀO).
SIET = (
    "children's picture-book illustration, felt-tip pen line work, flat filled colours, "
    "bright daylight scene on a light background",
    "simple flat vector clip art, solid colour fills, no shading at all, "
    "the background is one solid LIGHT mid-tone colour, bright overall",
    "bold poster-style flat illustration, three flat colours only, "
    "the background is a single light saturated colour filling the whole frame, "
    "high key, nothing dark",
)

KEP_GU = ("flat 2D cartoon illustration, thick black ink outlines, "
          "stick-figure people with plain round white heads, "
          # ── VẬT cũng cần neo, không chỉ NGƯỜI  (3/9/2026) ─────────────────────────────
          # Sau khi kẹp phong cách, hai nhịp CÓ NGƯỜI ra đúng chất (độ phẳng 0,79 và 0,74)
          # còn hai nhịp CHỈ CÓ VẬT vẫn ngả ảnh chụp (0,51 và 0,18): "raw wild roots and
          # berries" · "unfamiliar wild plants and exposed roots".
          # Vì câu kẹp chỉ tả tạo hình NGƯỜI — cảnh không người thì nó không neo được gì, và
          # chủ thể tự nó gợi ảnh chụp thực vật (§12.6). Thêm một vế cho vật.
          "every object drawn as simple flat shapes with the same thick outlines, "
          "no photographic texture, no realistic lighting, no depth of field")

GU_CARTOON = (
    "hand-drawn 2D cartoon illustration in the style of a modern animated explainer video, "
    "thick confident black ink outlines of even weight, "
    "stick-figure people with plain round white heads, two dot eyes, simple line mouth, "
    "expressive eyebrows and thin black limbs, "
    # ── nền phải SÁNG: đây là câu chữa lỗi "ảnh ra tối" ──────────────────────────────────
    "the background is always LIGHT, warm and airy — pale sky blue, soft daylight, warm sand, "
    "cream or light wood interior; never a dark background, never black, never night-dark, "
    "never a moody or desaturated palette, "
    # ── cho phép đổ bóng mềm, nhưng vẫn cấm chất ảnh chụp ────────────────────────────────
    "flat cheerful colours with gentle soft shading and simple soft cast shadows to give volume, "
    "no photographic texture, no lens blur, no realistic lighting, "
    # ── BỎ DANH SÁCH ĐỒ VẬT  (3/9/2026) ──────────────────────────────────────────────────
    # Sáng nay em viết câu này để chữa lỗi "khung trống, nền tối", và liệt kê thẳng đồ vật:
    # *"windows with sky, a wall clock, a potted plant, lamps, furniture, market stalls, trees
    # — the frame is never mostly empty"*.
    #
    # Chiều soi ảnh mới sinh của kênh SURVIVE (Kỷ Băng Hà): prompt cảnh viết đúng *"a lone
    # modern person in a frozen tundra under heavy grey sky, bare and endless"* — và **cả bốn
    # ảnh ra một căn phòng hiện đại sáng sủa có đồng hồ treo tường và chậu cây**. FLUX làm đúng
    # thứ được bảo: câu phong cách LIỆT KÊ đồ vật, còn câu cảnh chỉ MÔ TẢ, nên đồ vật thắng.
    #
    # Đây đúng §12.5 và đúng cái bẫy `SAN_NEN` kê tủ kệ vào sa mạc — em viết lại luật ấy trong
    # CLAUDE.md rồi vi phạm nó trong cùng một ngày, ở cùng một dạng.
    #
    # Hai câu cấm cũng đánh nhau với chính nội dung: *"the frame is never mostly empty"* mâu
    # thuẫn trực tiếp với "một người nhỏ bé giữa vùng băng trống trải" — mà đó CHÍNH LÀ bố cục
    # câu ấy cần.
    #
    # Nay chỉ nói YÊU CẦU (vẽ đầy, có bối cảnh nhận ra được) và nói rõ bối cảnh do CÂU CẢNH
    # quyết định. Không tên đồ vật nào — mọi danh từ viết ra đều có thể xuất hiện trong khung
    # (§15.2, bộ thiên nhiên đã trả giá cho đúng điều này).
    "the setting is exactly the place named in the scene description and nothing else, "
    "drawn completely with its own props and depth, not a blank backdrop, "
    "clean and cheerful, not photorealistic, not 3D, no text anywhere"
)
# Neo bối cảnh Mỹ — chỉ giữ những vật CHỈ CÓ Ở MỸ và mô hình vẽ được. "Cảm giác Mỹ" thì nó
# không vẽ được; "hòm thư trên cột cắm ở lề" thì vẽ được.
GU_USA = ("set in the United States: clapboard suburban houses with a front porch, a mailbox "
          "on a post at the curb, wide two-lane roads, American kitchen with an island; "
          "people in t-shirt or hoodie, jeans and sneakers")
GU_KENH = {k: GU_CARTOON for k in
           ("que", "phang", "tranh", "kich", "iso")}
# Cả 18 kênh dùng CHUNG phong cách cartoon phẳng; phân biệt bằng bảng màu, giọng đọc và sắc
# thái nét (xem `GU_RIENG`). Cho mỗi kênh một phong cách VẼ khác đã thử và hỏng: đo được 30/74
# ảnh lệch nhau, và lệch phong cách là lỗi người xem thấy trong nửa giây.
KENH_GU = {m: "que" for m in
           ("howlong", "howbig", "realcost", "howmuch", "whatif",
            "survive", "dayinlife", "wheregoes", "therules", "speedof",
            "odds", "hiddenfee", "yearsof", "howloud", "whatweighs",
            "rightnow", "howhot", "smallest")}
GU = GU_CARTOON

# ══ KHOÁ NHÂN VẬT ═══════════════════════════════════════════════════════════════════════════
# Anh: *"nhớ khoá nhân vật để cho đồng bộ cả channel cho nó đỡ lộn xộn, xây dựng bộ nhân vật để
# dùng chung để AI vẽ ra có nét theo niche."*
#
# NÓI THẲNG GIỚI HẠN TRƯỚC. FLUX qua Cloudflare chỉ nhận CHỮ — không có ảnh tham chiếu, không
# có LoRA, không có IP-Adapter. Nên khoá bằng mô tả không bao giờ đạt 100%; thực tế được khoảng
# bảy tám phần mười. Ai hứa hơn thế là chưa thử.
#
# Nhưng có một cách làm phần bảy tám ấy thành đủ dùng: **làm nhân vật ĐƠN GIẢN và cho nó MỘT
# DẤU HIỆU RẤT MẠNH.** Mô hình khuếch tán tái tạo hình khối đơn giản và màu đặc rất đáng tin;
# nó tái tạo khuôn mặt tinh tế rất tệ. Nên "người que đầu tròn trắng, áo cam gạch" giữ được
# xuyên suốt, còn "người đàn ông 41 tuổi mũi thẳng mắt sâu" thì mỗi khung một người.
# Đây cũng đúng là cách hai video tham chiếu làm: nhân vật của họ gần như không có mặt.
#
# BA QUY TẮC VIẾT MỘT KHOÁ:
#   1. một SILHOUETTE gọi tên được (người que · bóng đặc · người mặc áo phản quang)
#   2. một MÀU ĐẶC duy nhất, gọi bằng tên màu cụ thể chứ không phải "sáng màu"
#   3. một PHỤ KIỆN hoặc nét tóc gọn, và KHÔNG tả gì thêm về khuôn mặt
# Tả thêm là hại: mỗi chi tiết mặt thêm vào là một chỗ để mô hình đi chệch.
#
# Khoá đặt Ở ĐẦU prompt. Mô hình khuếch tán đọc phần đầu nặng ký hơn hẳn — cùng lý do câu cấm
# chữ phải đặt đầu (luật 7bk).
KHOA_VAI = {
    "howlong":  "a simple stick figure with a round white head, thick black outline, thin black "
                "limbs, wearing a plain rust-orange t-shirt and grey shorts, two dot eyes and no "
                "other facial detail",
    "whatif":   "a simple stick figure with a round white head, thick black outline, thin black "
                "limbs, wearing a plain cobalt-blue t-shirt, two dot eyes and no other facial detail",
    "speedof":  "a simple stick figure with a round white head, thick black outline, thin black "
                "limbs, wearing a plain mustard-yellow t-shirt, two dot eyes and no other facial detail",
    "howbig":   "a single solid deep-teal human silhouette with soft rounded edges and no face",
    "howmuch":  "a single solid indigo human silhouette with soft rounded edges and no face",
    "realcost": "a flat-vector man in his thirties, plain forest-green crew-neck sweater, charcoal "
                "trousers, short black hair, two simple dot eyes and no other facial detail",
    "therules": "a flat-vector man in his forties, plain light-blue polo shirt, khaki shorts, "
                "short sandy hair, two simple dot eyes and no other facial detail",
    "wheregoes": "a minimal isometric worker in an orange hi-vis vest and white hard hat, no face",
    "survive":  "a lean man in his early thirties, short dark hair, a heavy brown fur wrap over "
                "one shoulder, weathered skin, plain simple features",
    "dayinlife": "a man in his late twenties, short dark hair, thick eyebrows, a plain worn "
                 "linen tunic, plain simple features",
    # 8 kênh bổ sung — mỗi khoá là MỘT silhouette + MỘT màu đặc + MỘT phụ kiện, không tả mặt.
    # Đây là ba quy tắc đã rút ra: mô hình tái tạo hình khối đơn giản rất đáng tin, tái tạo
    # khuôn mặt tinh tế rất tệ.
    "odds":       "a simple stick figure with a round white head, thin black limbs, a plain "
                  "violet t-shirt, two dot eyes and no other facial detail",
    "hiddenfee":  "a flat-vector person in a plain forest-green apron, short dark hair, "
                  "two simple dot eyes and no other facial detail",
    "yearsof":    "a flat-vector person in a plain rust-brown jumper, short grey-streaked "
                  "hair, two simple dot eyes and no other facial detail",
    "howloud":    "a simple stick figure with a round white head, thin black limbs, a plain "
                  "crimson t-shirt, two dot eyes and no other facial detail",
    "whatweighs": "a stocky flat-vector person in a plain olive work shirt, short dark hair, "
                  "two simple dot eyes and no other facial detail",
    "rightnow":   "a single solid teal human silhouette with soft rounded edges and no face",
    "howhot":     "a simple stick figure with a round white head, thin black limbs, a plain "
                  "burnt-orange t-shirt, two dot eyes and no other facial detail",
    "smallest":   "a single solid slate-blue human outline drawn as a thin single line, no fill "
                  "and no face",
}

# Cảnh nào CÓ NGƯỜI thì mới gắn khoá. Cảnh vẽ đồ vật, biểu đồ, phong cảnh trống thì gắn vào chỉ
# tổ khiến mô hình nhét thêm một người không ai cần.
_CO_NGUOI = re.compile(
    r"\b(figure|person|people|man|woman|child|adult|crowd|silhouette|worker|sprinter|"
    r"soldier|baker|keeper|watchman|someone|hand|hands)\b", re.I)


def _khoa(ma: str, ve: str) -> str:
    k = KHOA_VAI.get(ma, "")
    if not k or not _CO_NGUOI.search(ve or ""):
        return ""
    return f"the same recurring character in every shot: {k}. "


# Câu cấm chữ — đặt Ở ĐẦU và viết THUẬN. Xem luật 7bk: FLUX không có negative prompt, nên câu
# cấm viết nghịch (`no text`) biến thành lệnh vẽ. Mô tả bề mặt SẠCH thay vì cấm chữ.
SACH = "every surface blank and unmarked, wordless scene"


# ══ DẢI ĐỘ PHẲNG CHO TỪNG PHONG CÁCH ════════════════════════════════════════════════════════
# Đo trên 74 ảnh đã sinh: thước "độ phẳng" tách sạch từ 0,13 (ảnh chụp / dựng 3D) tới 0,91
# (vector phẳng). Và đây là bằng chứng của bệnh: TRONG CÙNG MỘT TẬP `realcost`, ảnh nhịp 0 đo
# 0,136 (người 3D như ảnh chụp) còn ảnh nhịp 7 đo 0,889 (lịch vector phẳng). Cùng kênh, cùng
# tập, hai thế giới khác nhau.
#
# Đó chính là thứ làm video đọc ra "nghiệp dư", và nó KHÔNG phải chuyện màu — thử chỉnh màu
# tách tông tới cường độ 0,32 vẫn gần như không thấy khác biệt. Lệch phong cách thì chỉnh màu
# không cứu được.
#
# Câu khoá phong cách viết bằng chữ là chưa đủ vì FLUX trôi. Nên thêm CỔNG ĐO: ảnh nào rơi
# ngoài dải của phong cách kênh thì vẽ lại bằng lần thử khác.
# ── CỔNG ĐO SỰ NHẤT QUÁN, KHÔNG ĐO "ĐÚNG PHONG CÁCH" ───────────────────────────────────────
# Bản đầu của cổng này đặt một dải cố định cho từng phong cách rồi loại ảnh nằm ngoài. Thử thật
# trên kênh `therules` (đang sai 5/5):
#     phong cách ở cuối prompt  -> độ phẳng 0,162
#     phong cách ở đầu prompt   -> độ phẳng 0,445     (cải thiện mạnh)
#     dải cố định đòi           -> 0,58–0,97          (vẫn trượt)
#
# Đưa phong cách lên đầu giúp rất nhiều nhưng không đủ, và lý do là MÂU THUẪN DO CHÍNH TÔI TẠO
# RA: prompt sáu tầng chi tiết ("foreground: grass close to camera", "warm light from the
# right") là NGÔN NGỮ MÔ TẢ ẢNH CHỤP. Càng tả kỹ chiều sâu và ánh sáng thì mô hình càng vẽ ra
# ảnh thật. Ép nó về vector phẳng là đi ngược chính những câu mình vừa viết.
#
# Nên đổi mục tiêu cho đúng: thứ làm video đọc ra nghiệp dư KHÔNG phải "sai phong cách" mà là
# "mười lăm ảnh thuộc mười lăm thế giới". Người xem không biết kênh này *đáng lẽ* phải vector
# phẳng; họ chỉ thấy ảnh này khác ảnh kia.
#
# Nên cổng nay TỰ CHUẨN HOÁ: ảnh ĐẦU TIÊN vẽ được của một tập đặt ra mốc, mọi ảnh sau phải nằm
# trong ±NGUONG quanh mốc ấy. Không có con số phép thuật nào, không đánh nhau với mô hình, và
# nó ép đúng thứ cần ép.
# SÀN ĐỘ PHẲNG. Đo trên 74 ảnh cũ: ảnh cartoon phẳng đẹp nằm ở 0,66–0,91; ảnh mang chất ảnh
# chụp nằm ở 0,13–0,45. Đặt sàn 0,62 — dưới mức ấy là đã bắt đầu ngả sang ảnh thật.
# Đây là SÀN CỨNG chứ không còn là "nhất quán quanh ảnh đầu": bản trước tự chuẩn hoá theo ảnh
# đầu tiên, nghĩa là nếu ảnh đầu lỡ ra chất ảnh chụp thì cả tập bị khoá vào chất ấy. Nhất quán
# quanh một mốc SAI thì vẫn sai — chỉ là sai đều.
# 1/9, SỬA LẦN HAI — THƯỚC ĐO ĐO SAI THỨ TÔI TƯỞNG.
# Đặt sàn 0,62 rồi chạy thử: 6/11 ảnh "trượt". NHÌN vào sáu ảnh ấy thì cả sáu đều là cartoon
# phẳng đúng chất, cùng một nhân vật — tấm điểm thấp nhất (0,30) là cảnh đám đông ban đêm có
# nhiều hình nhỏ và trời chuyển sắc.
# Tức thước này lẫn lộn "PHONG CÁCH phẳng" với "BỐ CỤC đơn giản". Tôi calibrate nó trên hai đầu
# cực (ảnh chụp 0,13 vs vector phẳng 0,91) rồi tưởng nó đọc được cả khoảng giữa. Nó không.
# Suýt nữa tôi báo "ép cartoon thất bại" trong khi ép cartoon đã thành công — đúng luật
# CLAUDE.md: *khi con số và con mắt bất đồng thì đo pixel*, và pixel nói con số sai.
# Nay sàn hạ về 0,26: dưới mức ấy mới thật sự là ảnh chụp (dải đo được của ảnh chụp là 0,13-0,20).
# Cổng chỉ còn làm một việc: chặn ảnh chụp lọt vào, không phán xét bố cục.
SAN_PHANG = 0.26
# NGƯỠNG LỆCH ±0,35 QUANH MỐC — và ghi lại vì sao KHÔNG siết chặt hơn.  (1/9/2026)
#
# Tôi đã siết xuống ±0,20 để hai cổng khớp nhau về toán học (±X quanh mốc cho biên độ 2X, mà
# `kiem_hinh` đòi biên độ ≤ 0,40). Lập luận ấy đúng, nhưng NHÌN ẢNH THẬT thì kết luận đảo lại.
#
# Soi bốn ảnh của tập `smallest` (độ phẳng 0.36 · 0.65 · 0.73 · 0.80): **cả bốn cùng một thế
# giới** — cùng nét mực dày, cùng người que đầu tròn, cùng bảng màu. Ảnh 0,36 khác mỗi chỗ có
# ĐỔ BÓNG MỀM trên chủ thể. `do_phang` đo độ phẳng, nên nó chấm thấp cho ảnh có bóng, không
# phải cho ảnh lạc phong cách. Vẽ lại ba lần đều ra 0,36 — không phải may rủi.
#
# Đây là lần THỨ HAI thước này đánh lừa (§12.3 là lần đầu, khi nó gắn cờ 6/11 ảnh cartoon đúng
# chất). Siết ±0,20 chỉ tạo ra ba lượt vẽ lại tốn hạn mức cho mỗi tập, đổi lấy không gì cả.
#
# Việc thước NÀY làm được là bắt ảnh THẬT SỰ ngả ảnh chụp — và đó là `SAN_PHANG` (sàn tuyệt
# đối), không phải phép so tương đối. Giữ ±0,35 để chặn lệch lớn, đừng siết hơn.
NGUONG_LECH = 0.35


def do_mau(tep: str, o: int = 4) -> list:
    """Bảng màu của một ảnh — histogram RGB thô, chuẩn hoá. Dùng để đo "cùng một thế giới".

    ── VÌ SAO THÊM PHÉP ĐO NÀY  (3/9/2026) ─────────────────────────────────────────────────
    Cổng nhất quán đang dùng `do_phang`, và nó báo *"chất vẽ lệch 0,61 trong một tập"* ở gần như
    mọi tập. Ghép hai ảnh bị chấm lệch nhất của cùng một tập rồi NHÌN: chúng cùng một thế giới —
    nét mực dày, phẳng, bảng màu đen/trắng/đỏ. Chênh 0,38 vs 0,56 đến từ **mật độ chi tiết**
    (chiếc máy bay có hàng chục tia toả), không từ phong cách.

    Đây đúng luật 12.3 đã trả giá một lần: *thước lẫn lộn PHONG CÁCH PHẲNG với BỐ CỤC ĐƠN GIẢN*.
    Tôi đọc lại luật ấy hôm nay và vẫn suýt đi siết ngưỡng.

    Thứ người xem thật sự cảm được khi nói "hai ảnh này không cùng một bộ" là **bảng màu**, không
    phải mật độ nét. Hai ảnh cùng kênh dùng chung đen/trắng/đỏ thì trông cùng bộ, dù một tấm
    nhiều chi tiết hơn tấm kia gấp mười lần.

    Cùng họ với bài học 13.5 ở bộ Kling: *đo CHUỖI khi thứ cần đo là NỘI DUNG* — ở đây là đo
    MẬT ĐỘ khi thứ cần đo là MÀU.

    ── VÀ ĐÂY LÀ CHỖ PHẢI ĐỌC TRƯỚC KHI DÙNG NÓ LÀM CỔNG: **ĐỪNG.**  ────────────────────────
    Hai ảnh đầu tiên tôi thử cho kết quả rất đẹp — cùng tập **0,18**, khác kênh **0,81**, tách
    gấp bốn lần rưỡi. Tôi suýt ship ngay.

    Đo trên TOÀN BỘ 14 kênh (74 cặp cùng kênh · 91 cặp khác kênh):

        cùng kênh : trung vị 0,46 · max 0,97
        khác kênh : trung vị 0,49 · min 0,04
        khoảng trống giữa hai nhóm: **−0,93** — chồng lấn hoàn toàn

    Cặp 0,18/0,81 chỉ là một cặp may. Đúng bẫy 12.3: *calibrate ở hai đầu cực chỉ chứng minh
    thước tách được hai đầu; cổng sống ở khoảng giữa.*

    Nên hàm này giữ lại để CHẨN ĐOÁN (so hai ảnh cụ thể khi đang soi tay), **không dùng làm
    cổng**. Ghi ra đây theo luật 13.22 — *"chưa đo được" là một kết luận hợp lệ, và nó ngăn
    phiên sau đi làm lại đúng cái cổng đã bị bác.*
    """
    try:
        from PIL import Image
    except Exception:
        return []
    try:
        im = Image.open(tep).convert("RGB").resize((64, 64))
    except Exception:
        return []
    n = 256 // o
    h = [0] * (o * o * o)
    for r, g, b in im.getdata():
        h[(r // n) * o * o + (g // n) * o + (b // n)] += 1
    t = sum(h) or 1
    return [x / t for x in h]


def lech_mau(a: list, b: list) -> float:
    """Khoảng cách hai bảng màu, 0 = giống hệt, 1 = không chung màu nào."""
    if not a or not b or len(a) != len(b):
        return 0.0
    return 1.0 - sum(min(x, y) for x, y in zip(a, b))


def sang_day(tep: str) -> int:
    """Độ sáng trung bình của DẢI ĐÁY ảnh — chỗ phụ đề sẽ đè lên. 0-255, -1 nếu đọc hỏng.

    ── VÌ SAO CẦN  (3/9/2026) ─────────────────────────────────────────────────────────────
    Cổng `kiem_hinh` chấm bản dài 84/100 vì *"tương phản phụ đề 2.6:1 < 4,5:1"*. Đo pixel: dải
    phụ đề của những nhịp CÓ ẢNH sáng tới 181–187, tức chữ trắng chỉ đạt **1,9–2,0:1**.

    Anh đã bảo bỏ tấm che đen, nên không đắp lại một lớp phủ. Thứ đúng là **đổi màu chữ theo
    nền** — nền sáng thì dùng mực đậm. Nhưng engine không đo được ảnh lúc dựng, còn ở đây thì
    ảnh đang mở sẵn trong tay. Đo một lần, ghi vào nhịp, engine chỉ đọc.

    Cùng nguyên tắc với `bo_the`/`kieu_so`: nơi BIẾT thì quyết, rồi truyền kết quả (§15.3).
    """
    try:
        from PIL import Image
        im = Image.open(tep).convert("L")
        W, H = im.size
        dai = im.crop((int(W * 0.15), int(H * 0.86), int(W * 0.85), int(H * 0.97)))
        px = list(dai.getdata())
        return int(sum(px) / max(1, len(px)))
    except Exception:
        return -1


# ── SÀN ĐỘ SÁNG TOÀN ẢNH  (4/9/2026) ──────────────────────────────────────────────────────
# Anh xem và nói *"nó hơi tối và xấu thiếu chuyên nghiệp"*. Đo bảy ảnh CF của MỘT tập:
#
#     49 · 35 · 141 · 175 · 173 · 178 · 27      (trên thang 255)
#
# Ba ảnh ở 11–20% độ sáng — gần đen — nằm cạnh bốn ảnh 55–70%. Nên vấn đề không chỉ là
# "tối": nó là **BIÊN ĐỘ**. Một tập nhảy từ 11% sang 70% rồi về 11% đọc ra chắp vá, và đó
# đúng là thứ người xem gọi là "thiếu chuyên nghiệp".
#
# Vì sao mô hình vẽ tối: câu phong cách nói `bright saturated palette` — đó là độ RỰC của
# màu, không phải độ SÁNG của nền. Mô hình được tự do chọn nền tối, và với nhịp có chữ
# "4 AM" hay "before light" thì nó chọn đêm. §16.2 đã ghi đúng cái bẫy này một lần rồi:
# prompt cấm/nói đúng thứ mình muốn, chứ không nói thứ mình tưởng.
#
# Sàn 90/255 (35%) chọn theo phân bố đo được: nó chặt hơn hẳn ba ảnh hỏng (27–50) và
# thoáng hơn hẳn bốn ảnh đạt (141–178), tức nằm giữa hai cụm chứ không cắt vào cụm nào.
SAN_SANG = int(os.environ.get("SAN_SANG_ANH", "90") or 90)


def do_sang(tep: str) -> int:
    """Độ sáng trung bình 0–255 của cả ảnh. -1 nếu không đọc được."""
    try:
        from PIL import Image
        im = Image.open(tep).convert("L").resize((48, 48))
        return int(sum(im.getdata()) / 2304)
    except Exception:
        return -1


def do_phang(tep: str):
    """Độ 'phẳng' của ảnh: 0 = ảnh chụp thật, 1 = hình vẽ phẳng. None nếu không đo được.

    Hai phép đo nhân trọng số:
      · ĐỘ PHỦ CỦA 8 MÀU CHÍNH — hình vẽ phẳng có ít màu, mỗi màu phủ mảng lớn; ảnh thật thì
        màu tãi ra hàng nghìn sắc độ vì chuyển sáng liên tục.
      · ĐỘ MỊN CỤC BỘ — hình vẽ phẳng gần như không đổi trong một mảng, chỉ đổi ở đường viền;
        ảnh thật đổi khắp nơi vì có kết cấu bề mặt.
    Đã đối chiếu bằng mắt trên hai đầu dải: khớp."""
    try:
        from PIL import Image
        import collections
    except Exception:
        return None
    try:
        im = Image.open(tep).convert("RGB").resize((256, 256))
        q = im.quantize(colors=48, method=Image.MEDIANCUT).convert("RGB")
        dem = collections.Counter(q.getdata())
        phu8 = sum(n for _c, n in dem.most_common(8)) / (256 * 256)
        g = im.convert("L"); px = g.load()
        doi = n = 0
        for y in range(0, 256, 2):
            for x in range(0, 254, 2):
                doi += abs(px[x, y] - px[x + 2, y]); n += 1
        min_diem = max(0.0, 1.0 - (doi / n) / 14.0)
        return round(phu8 * 0.55 + min_diem * 0.45, 3)
    except Exception:
        return None


def _sac_thai(ma: str) -> str:
    """Sắc thái vẽ riêng của kênh — vẫn trong khuôn 'cartoon phẳng', chỉ khác nét.

    Không cho mỗi kênh một PHONG CÁCH khác (đã thử và hỏng: trộn ảnh thật với cartoon làm
    30/74 ảnh lệch nhau). Cho mỗi kênh một SẮC THÁI trong cùng một phong cách: viền dày hay
    mảnh, có viền hay không, nét máy hay nét tay, bảng màu rộng hay hạn chế ba màu.
    Bốn thứ ấy đủ để mười kênh không nhìn ra cùng một xưởng, mà không kéo cái nào về ảnh thật."""
    try:
        from giai_thich import GU_RIENG
        return GU_RIENG.get(ma, ("", "", ""))[2]
    except Exception:
        return ""


def _prompt(ve: str, tam_trang: str = "", gu: str = "", ma: str = "", doc: bool = False,
            siet: int = 0) -> str:
    """Ghép prompt cho MỘT nhịp.

    Thứ tự có chủ đích: chủ thể trước, rồi luật bố cục, rồi phong cách, rồi bề mặt sạch.
    Mô hình khuếch tán đọc phần đầu nặng ký hơn — nên thứ quan trọng nhất (cảnh đang nói tới)
    phải đứng đầu, không đứng cuối."""
    mt = {
        "kho":  ", cold grey overcast light, desaturated palette",
        "ngay": ", warm golden daylight, bright cheerful palette",
        "dem":  ", night scene, deep blue palette, warm firelight",
        "lanh": ", cool blue winter light, pale palette",
    }.get(tam_trang, "")
    # Gợi ý bố cục theo hướng khung. Không chỉ là chuyện kích thước tệp: khung dọc và khung
    # ngang cần BỐ CỤC KHÁC NHAU. "Wide shot" trên khung dọc cho ra chủ thể bé tí giữa hai dải
    # trống; khung dọc phải xếp chồng theo chiều cao.
    khung = KHUNG_DOC if doc else KHUNG_NGANG
    # TRẦN 2048 KÝ TỰ — đo được, không đọc tài liệu: gửi thử 2500 ký tự thì CF trả
    #     HTTP 400  Length of '/prompt' must be <= 2048
    # Tôi đã nhồi prompt lên ~2800 ký tự theo yêu cầu "viết dài và chi tiết hơn", và MỌI lệnh
    # vẽ trả 400 — cả đường sinh ảnh chết câm, không ảnh nào ra. Lần thứ hai trong ngày một
    # tham số API chưa thử làm sập cả pipeline (lần trước là `seed`).
    # Nay ghép theo THỨ TỰ ƯU TIÊN và cắt từ đuôi khi vượt trần, thay vì để API từ chối cả câu:
    # thà thiếu vế phụ còn hơn không có ảnh nào.
    # PHONG CÁCH ĐẶT Ở ĐẦU. Mô hình khuếch tán đọc phần đầu nặng ký hơn hẳn — đã học điều này
    # hai lần trong hôm nay (câu cấm chữ, và câu ép sàn). Để phong cách ở cuối câu là để nó bị
    # át bởi phần mô tả cảnh, và đó là lý do cùng một kênh ra ảnh lúc vector phẳng lúc ảnh chụp.
    # ── CẢNH ĐỨNG TRƯỚC, PHONG CÁCH ĐỨNG SAU  (3/9/2026) ─────────────────────────────────
    # Chú thích của chính hàm này viết: *"chủ thể trước, rồi luật bố cục, rồi phong cách. Mô
    # hình khuếch tán đọc phần đầu nặng ký hơn — nên thứ quan trọng nhất (cảnh đang nói tới)
    # phải đứng đầu, không đứng cuối."*
    #
    # **Mã làm NGƯỢC LẠI**: `phan[0]` là phong cách (844 ký tự), câu cảnh nằm ở vị trí thứ ba.
    # Chú thích mô tả ý định, mã thực hiện điều khác — và không ai thấy vì cả hai đều đọc hợp lý.
    #
    # Hậu quả đo được: kênh SURVIVE (Kỷ Băng Hà) có prompt cảnh đúng *"a lone modern person in
    # a frozen tundra, bare and endless"* mà **cả bốn ảnh ra một căn phòng hiện đại**. Câu phong
    # cách dài gấp bốn lần câu cảnh và đứng trước nó, nên nó thắng.
    #
    # Nay đúng như chú thích: cảnh trước, khoá nhân vật, rồi phong cách. Neo phong cách vẫn dán
    # ngay trước chủ thể ("a flat cartoon drawing of …") nên chủ thể gợi-ảnh-chụp vẫn bị ghìm —
    # đó là hai việc khác nhau và cả hai đều cần.
    phan = [
        # ── SIẾT DẦN THEO LẦN THỬ  (3/9/2026) ────────────────────────────────────────────
        # `siet` là số lần cổng chất vẽ đã đánh trượt ảnh này. Xem chú thích ở `sinh()`: vẽ lại
        # bằng CÙNG một prompt là vô nghĩa vì FLUX schnell không nhận `seed`. Mỗi lần trượt thì
        # đổi chính prompt, và đổi theo hướng cổng đang đo — nói mạnh hơn về CHẤT VẼ.
        # `siet - 1`: lần trượt THỨ NHẤT dùng câu siết thứ nhất. Viết `min(siet, …)` là hụt
        # một bậc — câu nhẹ nhất không bao giờ được dùng, và ảnh nhảy thẳng sang mức siết mạnh.
        (SIET[min(siet - 1, len(SIET) - 1)] + ", ") if siet else "",
        "a flat cartoon drawing of " + ve + mt + ",",             # 1. CHÍNH CẢNH — đứng đầu
        KEP_GU + ",",              # 1b. kẹp phong cách ngắn — xem `KEP_GU`
        _khoa(ma, ve).rstrip(),    # 2. khoá nhân vật (rỗng nếu cảnh không có người)
        ((gu or GU) + ", " + _sac_thai(ma)).rstrip(", ") + ".",   # 3. phong cách + sắc thái riêng
        # 3. chính cảnh của nhịp này — CÓ NEO PHONG CÁCH DÁN NGAY TRƯỚC CHỦ THỂ.
        #
        # Đặt phong cách ở đầu câu (mục 1) là chưa đủ với những chủ thể tự nó gợi ẢNH CHỤP:
        # `smallest` tả "a virus magnified far beyond life size" — đó là ngôn ngữ ảnh hiển vi,
        # và mô hình vẽ ra đúng một ảnh hiển vi. Đo được: nhịp ấy có độ phẳng 0,37 trong khi cả
        # tập ở 0,64–0,81, và VẼ LẠI cũng ra 0,37 — tức không phải may rủi, mà là chính prompt
        # kéo nó đi.
        #
        # FLUX không có negative prompt (§12.1), nên không thể dặn "đừng vẽ ảnh chụp" — mọi danh
        # từ viết ra đều là thứ SẼ xuất hiện. Cách còn lại là khẳng định dương, và dán ngay cạnh
        # chủ thể chứ không để cách xa mười lăm chữ ở đầu câu.
        khung + ",",               # 4. chừa chỗ cho chữ
        _luat(ve, doc) + ",",      # 5. luật sàn
        GU_USA + ",",              # 6. neo bối cảnh Mỹ
        SACH,                      # 7. bề mặt sạch
    ]
    ra = ""
    for x in phan:
        if not x:
            continue
        thu = (ra + " " + x).strip()
        # ── TRỪ LỚP BỌC MÀ `_cf_flux_image` THÊM VÀO  (3/9/2026) ────────────────────────
        # Trần 2048 là của chuỗi **gửi đi**, không phải của chuỗi hàm này ghép ra. `_cf_flux_image`
        # còn bọc thêm `"Absolutely no text… A <style> of: {prompt}. Textless image."` — **159 ký
        # tự**. Nên chốt ở 2048 là chốt sai chuỗi: prompt 1989 ký tự lọt cổng rồi bị CF trả
        # `HTTP 400 Length of '/prompt' must be <= 2048`, đúng lúc vừa viết lại phong cách.
        #
        # Cùng bài học 13.7: *cổng phải nhận CHÍNH thứ sắp giao đi và ghép bằng CHÍNH phép ghép
        # mà bên kia sẽ chạy* — không mô hình hoá lại. Ở đây tôi chốt trên bản nháp, còn bên kia
        # gửi bản đã bọc.
        if len(thu) > 2048 - 175:      # 159 lớp bọc + 16 đệm cho `style` dài hơn
            break                  # cắt từ đuôi: vế càng sau càng ít quan trọng
        ra = thu
    return ra


# ══ SỔ CẠNH ẢNH — MỘT TỆP JSON NHỎ ĐI KÈM MỖI ẢNH  (4/9/2026) ═══════════════════════════════
# Hai lỗi khác nhau cùng cần đúng một thứ, nên chúng dùng chung một sổ:
#
#   1. CACHE LẤY NHẦM CẢNH. Tên tệp không mang nội dung cảnh, nên "đã có tệp" bị đọc thành
#      "đã có ĐÚNG cảnh này". Sổ giữ vân tay câu cảnh -> so được.
#   2. CHỈNH MÀU CHỒNG LỚP. `to_mau` ghi đè tại chỗ và được gọi mỗi lượt dựng, kể cả khi ảnh
#      lấy từ cache. Mỗi lượt hạ bão hoà 14% và kéo tông về màu kênh, nên hiệu ứng CỘNG DỒN.
#      Đo trên một ảnh thật, lặp đúng hàm ấy: bão hoà 163 -> 154 -> 144 -> 120 (5 lượt) ->
#      82 (12 lượt) -> 55 (20 lượt). Và đo trên 290 ảnh đang có, xếp theo kênh:
#         odds 14 · howbig 15 · howmuch 16   (kênh dựng đi dựng lại nhiều nhất)
#         dayinlife 72 · rightnow 72 · howhot 139   (kênh mới dựng một hai lượt)
#      Chênh gần MƯỜI LẦN giữa hai đầu — đó không phải "bảng màu kênh", đó là số lượt dựng.
#      Bộ ảnh xám bợt mà anh nhìn thấy chính là cái này.
#      Sổ ghi "ảnh này đã chỉnh màu rồi" -> chỉnh đúng MỘT lần trong đời mỗi ảnh.
#
# Vì sao là tệp riêng chứ không nhét vào EXIF: `to_mau` lưu lại bằng PIL và không giữ EXIF,
# nên một cờ đặt trong ảnh sẽ bị chính bước cần đánh dấu xoá đi.
def _so(dest: str) -> str:
    return dest + ".so.json"


def _doc_so(dest: str) -> dict:
    try:
        import json
        with open(_so(dest), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _ghi_so(dest: str, **kw) -> None:
    """Ghi/cập nhật sổ. Hỏng thì im — mất sổ chỉ làm ảnh bị vẽ lại, không làm hỏng tập."""
    try:
        import json
        d = _doc_so(dest)
        d.update(kw)
        with open(_so(dest), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    except Exception:
        pass


def _van_tay(ve: str) -> str:
    import hashlib
    return hashlib.sha1((ve or "").strip().encode("utf-8")).hexdigest()[:16]


def _so_khop(dest: str, ve: str) -> bool:
    """Ảnh đang có CÓ ĐÚNG là ảnh của câu cảnh này không."""
    return bool(ve) and _doc_so(dest).get("ve") == _van_tay(ve)


def can_to_mau(dest: str) -> bool:
    """Ảnh này đã được chỉnh màu chưa. Chưa thì mới được chỉnh — chỉnh hai lần là hỏng."""
    return not _doc_so(dest).get("toMau")


def danh_dau_to_mau(dest: str) -> None:
    _ghi_so(dest, toMau=True)


def _ten(ma: str, idx: int, i: int) -> str:
    return f"{ma}_{idx:04d}_{i:02d}.jpg"


def sinh(ma: str, idx: int, i: int, ve: str, keys, tam_trang: str = "", gu: str = "",
         doc: bool = True, moc: float = None) -> str:
    """Vẽ một cảnh. Trả đường dẫn tương đối trong `public/`, hoặc "" nếu không vẽ được.

    KHÔNG ném lỗi khi hỏng: tầng dưới (`NenQue` vẽ bằng code) luôn đỡ được, nên một ảnh hỏng
    chỉ làm cảnh ấy xấu hơn chứ không làm hỏng cả tập. Đây là bài học từ bốn tầng nền của bộ
    truyện tranh — thứ gì gọi mạng thì phải có tầng không gọi mạng đứng dưới."""
    os.makedirs(THU, exist_ok=True)
    # Tên tệp mang HƯỚNG KHUNG: bản dọc và bản ngang là hai ảnh khác nhau, không dùng chung
    # được. Trộn chung một tên là lần sau dựng bản kia lấy nhầm ảnh của bản này.
    hw = "d" if doc else "n"
    dest = os.path.join(THU, _ten(ma, idx, i).replace(".jpg", f"_{hw}.jpg"))
    rel = f"gt_nen/{_ten(ma, idx, i).replace('.jpg', f'_{hw}.jpg')}"
    # ── CACHE PHẢI KHOÁ THEO CHÍNH CÂU CẢNH  (4/9/2026) ────────────────────────────────
    # Khoá cũ là `(kênh, số tập, chỉ số nhịp, hướng khung)` — KHÔNG có nội dung cảnh trong đó.
    # Nhưng nhịp thứ `i` của tập 0 hôm nay và nhịp thứ `i` của tập 0 hôm qua là HAI CẢNH KHÁC
    # NHAU: kịch bản đổi mỗi lượt (`doi_loi`, `ap_gu`, bộ lịch). Nên mỗi lượt dựng lại, mọi
    # nhịp đều "trúng cache" và nhận về ảnh của một cảnh khác hẳn.
    #
    # Đo được, và đây là lỗi HÌNH nặng nhất của cả bộ: kênh HOW BIG đặt hàng
    #   nhịp 3  "a school bus and a blue whale side by side at true relative scale"
    #   nhịp 4  "a school bus alone, centred, clean side profile"
    #   nhịp 6  "a blue whale alone, filling most of the frame"
    # và **cả sáu ảnh** trả về đúng một thứ: mấy người que đứng trong phòng có đồng hồ treo
    # tường. Sáu tệp cùng mang mtime một giây — dấu vân tay của "không gọi mạng lần nào".
    #
    # Không đổi tên tệp (đổi tên là bỏ trắng 290 ảnh đang có và đẻ ra một bãi tệp mồ côi).
    # Đặt một SỔ cạnh ảnh: vân tay của câu cảnh đã vẽ ra nó. Khớp thì dùng lại thật; lệch
    # hoặc chưa có sổ thì vẽ lại. Ảnh cũ không có sổ sẽ được vẽ lại một lần — đúng điều cần,
    # vì chúng vừa lạc cảnh vừa đã bị chỉnh màu chồng nhiều lượt (xem `_da_to_mau`).
    if os.path.exists(dest) and os.path.getsize(dest) > 20000 and _so_khop(dest, ve):
        return rel
    if not ve:
        return ""
    # ── HỒ CẠN RỒI THÌ ĐỪNG GÕ CỬA TỪNG KHOÁ CHẾT NỮA  (2/9/2026) ───────────────────────────
    # Đo hôm nay: **30/30 khoá CF lấy mẫu đều trả `429 … used up your daily free allocation of
    # 10,000 neurons`** — cả hồ 97 tài khoản đã cạn. Đó chính là lý do bản dài chỉ vẽ được 6/42
    # cảnh, và là lý do cổng chấm cho 78/100.
    #
    # Nhưng cái đắt hơn nằm ở chỗ khác: `CanThat` chỉ thoát MỘT cảnh. Cảnh sau lại gọi
    # `goi_xoay`, lại xoay hết 97 khoá chết, mỗi khoá một vòng mạng — nhân với 36 cảnh còn lại
    # là hàng nghìn lượt gọi vô ích, và nhìn từ ngoài y hệt "mạng chậm". Đây đúng cái bẫy đã ghi
    # ở CLAUDE.md 12.1: một lỗi làm mọi lệnh vẽ hỏng, mà chết CHẬM nên đọc ra như sự cố mạng.
    #
    # Cạn hồ là trạng thái của CẢ TIẾN TRÌNH, không phải của một cảnh. Biết rồi thì đi thẳng
    # xuống tầng nền vẽ bằng code — tầng ấy không gọi mạng nên không bao giờ hỏng.
    if getattr(sinh, "_can", 0):
        sinh._can += 1
        sinh._can_tap = getattr(sinh, "_can_tap", 0) + 1
        return ""
    # ── TRẦN ẢNH AI MỖI LUỒNG MỖI LƯỢT  (3/9/2026) ─────────────────────────────────────────
    # Anh: *"nhiều key thế sao cạn vậy, tìm nguyên nhân."* Đo xong thì thủ phạm là **số vòng
    # lặp**, không phải số key và cũng không phải vòng thử lại:
    #
    #     sức hồ        : 97 tài khoản × 10.000 neuron ÷ 58 = 16.724 ảnh/ngày
    #     tỉ lệ vẽ lại  : 19 lượt trên ~812 nhịp = **2,3%** (hệ số 1,02× — không đáng kể)
    #     nhu cầu thật  : 18 luồng × 14 vòng × 58 nhịp × 1,02 = **14.900 ảnh = 89% sức hồ**
    #
    # Trước khi có vòng lặp liên tục thì nhu cầu là 828 ảnh = **4%**. Vòng lặp làm sản lượng
    # nhảy 36 → 872 video, và nhu cầu ảnh nhảy 4% → 89%. Sản lượng và ảnh AI đánh nhau trực tiếp.
    #
    # Chặn ở đâu cũng phải trả giá, nên chọn chỗ trả giá RẺ NHẤT: giới hạn **số ảnh mỗi luồng**,
    # không giảm số video. Tập đầu của luồng có ảnh AI đầy đủ; tập sau dùng lớp vẽ bằng code —
    # vẫn ra video, vẫn giao được, chỉ khác chất. Đó là đánh đổi có kiểm soát, thay vì để hồ cạn
    # giữa chừng rồi MỌI tập sau đó mất ảnh một cách ngẫu nhiên.
    #
    # 120 ảnh/luồng/lượt × 18 luồng × 4 lượt/ngày = 8.640 ảnh = 52% sức hồ, còn biên cho việc khác.
    _tran = int(os.environ.get("TRAN_ANH_LUONG", "120") or 120)
    if _tran > 0 and getattr(sinh, "_da_ve", 0) >= _tran:
        if getattr(sinh, "_da_ve", 0) == _tran:
            sinh._da_ve += 1        # +1 để câu này chỉ in một lần
            print(f"     🎚 đã vẽ {_tran} ảnh AI trong lượt này — các cảnh sau dùng lớp vẽ bằng "
                  f"code để giữ hạn mức cho những luồng còn lại (đặt TRAN_ANH_LUONG để đổi)")
        return ""

    import datastory_ci as DS
    from xoay_key import goi_xoay, CanThat

    # (Đã bỏ seed: endpoint FLUX của CF trả HTTP 400 khi có `seed`. `hat0` chỉ còn dùng để
    #  xoay khoá cho đều, không còn hứa hẹn tái lập ảnh.)
    hat0 = (sum(ord(c) for c in ma) * 7919 + idx * 131 + i) % 4294967295

    # ── LOẠI VÌ CÓ CHỮ THÌ VẼ LẠI, ĐỪNG BỎ ──────────────────────────────────────────────
    # Mẻ trước kênh `realcost` chỉ được 4/7 cảnh. Không phải API hỏng — cổng `_co_chu` bắt
    # được chữ do FLUX bịa ra và XOÁ ảnh, rồi hàm này trả rỗng, nên ba nhịp rơi xuống nền vẽ
    # bằng code. Cổng làm đúng việc của nó; chỗ sai là tôi coi "bị loại" đồng nghĩa với "chịu
    # thua".
    # FLUX bịa chữ hay không phụ thuộc rất nhiều vào seed. Đổi seed rồi vẽ lại là gần như chắc
    # chắn thoát — và rẻ, vì ảnh chỉ tốn 58 neuron. Ba lần vẫn dính thì mới chịu.
    # BỐN LẦN THỬ, nhận ở lần thứ tư. `range(3)` + `lan < 3` là hụt một: điều kiện luôn đúng
    # nên ảnh lệch bị xoá ở CẢ lần cuối, và nhịp ấy mất hẳn cảnh — tệ hơn một ảnh hơi khác chất.
    # `_siet` đếm số lần cổng CHẤT VẼ đánh trượt — khác với `lan` (đếm mọi loại thất bại, kể
    # cả mạng hỏng). Chỉ siết prompt khi trượt vì chất vẽ; mạng hỏng thì prompt không có tội.
    _siet = 0
    for lan in range(4):
        def _thu(kk, _s=_siet):
            return DS._cf_flux_image(_prompt(ve, tam_trang, gu, ma, doc, siet=_s), dest, kk) and \
                os.path.getsize(dest) > 20000

        try:
            ok, _tk = goi_xoay(keys, _thu, hat=hat0 + lan)
        except CanThat:
            # ── CẠN HẠN MỨC PHẢI NÓI RA, VÀ NÓI MỘT LẦN  (2/9/2026) ─────────────────────
            # Đo trên lượt 33631376874: bản dài vẽ được **6/42 cảnh**, tức 36 cảnh rơi về nền
            # vẽ bằng code — mà log chỉ có 8 dòng lỗi. 36 ảnh biến mất KHÔNG để lại một dòng
            # nào, vì cả ba nhánh thoát của hàm này đều `return ""` trong im lặng.
            #
            # Hậu quả không phải "thiếu log": chất lượng tập tụt hẳn (chấm 78/100 và 84/100
            # trên sàn 90) mà không ai biết vì sao, nên người đọc đi tìm lỗi ở khâu dựng —
            # trong khi lỗi nằm ở khâu vẽ, và nằm ở một chỗ không nói gì.
            sinh._can = getattr(sinh, "_can", 0) + 1
            if sinh._can == 1:
                print(f"     🪫 nhịp {i}: CF cạn hạn mức — từ đây các cảnh còn lại dùng nền "
                      f"vẽ bằng code (sẽ đếm tổng ở cuối tập)")
            return ""
        if not ok:
            sinh._hong = getattr(sinh, "_hong", 0) + 1
            continue

        # CỔNG NHẤT QUÁN — ảnh phải cùng thế giới với ảnh đầu tiên của tập.
        # Đây là cổng đắt nhất trong bộ: nó ngăn một tập có mười lăm ảnh thuộc mười lăm thế
        # giới. Lệch phong cách là lỗi người xem thấy trong nửa giây, mà mọi thước đo cũ đều mù.
        _d = do_phang(dest)
        # Cổng độ sáng đi CÙNG cổng chất vẽ, không thành một vòng riêng: hai cổng cùng
        # chữa bằng một việc (vẽ lại với prompt siết hơn), nên tách ra chỉ tốn thêm lượt.
        _s = do_sang(dest)
        _toi = 0 <= _s < SAN_SANG
        _xau = _toi or (_d is not None and (_d < SAN_PHANG or
                                            (moc is not None and abs(_d - moc) > NGUONG_LECH)))
        if _xau:
            if lan < 3:
                os.remove(dest)
                _siet += 1        # -> vẽ lại VỚI PROMPT SIẾT HƠN, xem `SIET`
                continue
            # Lần cuối thì NHẬN — nền vẽ bằng code còn lệch xa hơn một ảnh hơi khác chất.
            # Nhưng phải NÓI RA. Bản trước nhận trong im lặng, nên một tập có ảnh lạc phong cách
            # trông y hệt một tập sạch, và chỉ lộ ra ở cổng chấm sau khi đã dựng xong cả video.
            # Cổng biết mà không nói thì cũng như không có cổng.
            print(f"     ⚠ nhịp {i}: chất vẽ {_d:.2f} lệch khỏi mốc {moc if moc is None else round(moc,2)}"
                  f" sau 3 lần vẽ lại — nhận để không mất cảnh")

        # CỔNG CHỮ — thứ video tham chiếu KHÔNG có, và đó là lý do một khung của họ hiện nguyên
        # dòng `SPLIT FRAME` (lời dặn cho máy vẽ) giữa màn hình. Chữ do mô hình vẽ ra luôn sai
        # chính tả và trông ngay ra là máy làm.
        try:
            from kich_hai import _co_chu
            if _co_chu(dest) is True:
                os.remove(dest)
                continue          # -> vẽ lại (prompt đổi nếu đã trượt chất vẽ)
        except Exception as e:
            # NÓI RA khi cổng tắt. Một cổng hỏng mà im lặng còn tệ hơn không có cổng: nó cho
            # cả mẻ đi qua kèm cảm giác đã được kiểm. Chỉ báo MỘT lần mỗi lần chạy — báo mỗi
            # cảnh thì 15 dòng giống nhau lại thành nhiễu, và nhiễu cũng là một kiểu im lặng.
            if not getattr(sinh, "_da_bao", False):
                sinh._da_bao = True
                print(f"     ⚠ CỔNG CHỮ TẮT ({type(e).__name__}: {str(e)[:60]}) — "
                      f"ảnh có chữ bịa sẽ lọt qua")
        sinh._da_ve = getattr(sinh, "_da_ve", 0) + 1
        # Ghi sổ NGAY SAU khi mọi cổng đã nhận, không ghi lúc tải xong: sổ nói "ảnh này là ảnh
        # ĐÃ DUYỆT của câu cảnh này". Ghi sớm là hứa hộ cho một ảnh có thể còn bị xoá ở dòng dưới.
        # `toMau=False` tường minh: ảnh vừa vẽ chưa qua chỉnh màu, và `sinh_tap` đọc đúng cờ này.
        _ghi_so(dest, ve=_van_tay(ve), toMau=False)
        return rel
    # BỐN LƯỢT ĐỀU HỎNG — cũng phải nói. Đây là nhánh im lặng thứ hai: nhịp này mất cảnh mà
    # không có dấu vết nào, nên nhìn từ log nó y hệt một nhịp chưa từng được yêu cầu vẽ.
    sinh._het = getattr(sinh, "_het", 0) + 1
    print(f"     ✗ nhịp {i}: 4 lượt vẽ đều hỏng — dùng nền vẽ bằng code")
    return ""


def sinh_tap(ma: str, idx: int, nhip: list, keys, doc: bool = True,
             mau_chu: str = "", mau_nen: str = "") -> int:
    """Vẽ mọi cảnh của một tập. Trả số ảnh vẽ được.

    Chạy TUẦN TỰ chứ không song song: `goi_xoay` xoay khoá theo trạng thái chung, chạy song
    song thì nhiều luồng cùng đâm vào một khoá đã 429 và cả mẻ hỏng theo. Chậm hơn nhưng đúng.
    """
    gu = GU_KENH.get(KENH_GU.get(ma, "que"), GU)
    # Đặt lại bộ đếm lý do MỖI TẬP — không đặt lại thì con số cộng dồn qua cả short lẫn long
    # và bản tổng kết nói về một tập khác với tập đang chạy.
    # ── `_can` KHÔNG được reset theo tập  (4/9/2026) ────────────────────────────────────
    # `_hong`/`_het` là bộ đếm BÁO CÁO của một tập — reset đúng. `_can` thì khác hẳn: nó là
    # cờ "hồ CF đã cạn hạn mức ngày", tức trạng thái của CẢ TIẾN TRÌNH. Hạn mức free của CF
    # hồi lúc 00:00 giờ Thái Bình Dương, nên trong một lượt chạy nó không bao giờ tự đầy lại.
    #
    # Xoá cờ ấy mỗi tập làm vô hiệu hoá đúng cơ chế mà chú thích ở dòng 645 dựng lên để
    # chống: mỗi tập mới lại xoay trọn 97 khoá chết, mỗi khoá một vòng mạng cộng
    # `time.sleep(0.25)`, và khoá 429 còn thêm 1,2 giây. Với 45 tập một luồng thì đó là
    # hàng nghìn lượt gọi vô ích — và nhìn từ ngoài y hệt "mạng chậm", đúng cái bẫy §12.1.
    #
    # Gộp một cờ TRẠNG THÁI với một bộ đếm BÁO CÁO vào cùng một tên là họ lỗi §14.8 (hai
    # ngân sách khác bản chất chung một bộ đếm). Tách ra: `_can` giữ nguyên qua các tập,
    # `_can_tap` mới là con số của tập này.
    for _t in ("_hong", "_het", "_can_tap"):
        if hasattr(sinh, _t):
            delattr(sinh, _t)
    n = 0
    moc = None      # mốc chất ảnh của tập — đặt bằng TRUNG VỊ ba ảnh đầu (xem dưới)
    _mau = []       # ba số đo đầu, để lấy trung vị
    _dau = []       # (chỉ số nhịp, prompt) của những ảnh vẽ TRƯỚC khi có mốc
    for i, x in enumerate(nhip):
        ve = x.get("ve") or ""
        # `canh_ve` = nhịp này vẽ nơi chốn bằng code, ĐỪNG gọi CF (xem `giai_thich.NOI_KENH`).
        # `_rai_canh_ve` đã bỏ `ve` của những nhịp ấy, nên điều kiện dưới đủ; giữ phép kiểm
        # tường minh này làm hàng rào thứ hai vì đây là CỬA DUY NHẤT đi tới lệnh gọi CF —
        # một chỗ sót ở đây là tiền thật, và nó sẽ không báo gì.
        if not ve or x.get("canh_ve"):
            continue
        rel = sinh(ma, idx, i, ve, keys, x.get("tam_trang", ""), gu, doc, moc)
        if rel:
            x["nenAnh"] = rel
            # Đo ngay lúc ảnh còn trong tay — xem `sang_day`. Engine đọc để chọn màu phụ đề.
            _sd = sang_day(os.path.join(THU, os.path.basename(rel)))
            if _sd >= 0:
                x["sangDay"] = _sd
            n += 1
            duong = os.path.join(THU, os.path.basename(rel))
            # MỐC = TRUNG VỊ BA ẢNH ĐẦU, không phải ảnh đầu tiên.
            # CLAUDE.md §12.4 đã ghi cái bẫy này: *cổng tự chuẩn hoá theo mẫu đầu tiên thì nhất quán
            # quanh một mốc SAI vẫn sai* — nếu ảnh đầu lỡ lạc chất thì cả tập bị khoá vào chất lạc ấy,
            # và cổng báo xanh vì mọi ảnh đều "nhất quán". Trung vị ba mẫu thì một mẫu lạc không kéo
            # được mốc đi. Vẫn có sàn tuyệt đối `SAN_PHANG` chặn trước, đúng thứ tự luật ấy đòi.
            if moc is None:
                _dau.append((i, ve))
                d = do_phang(duong)
                if d is not None:
                    _mau.append(d)
                    if len(_mau) >= 3:
                        moc = sorted(_mau)[len(_mau) // 2]
                        print(f"     mốc chất ảnh của tập: {moc:.2f} "
                              f"(trung vị {[round(x, 2) for x in _mau]}, ±{NGUONG_LECH})")
            # CHỈNH MÀU sau khi cổng đã nhận — để cổng đo đúng thứ mô hình trả về, không đo
            # thứ mình vừa sửa. Hiệu quả nhẹ (đã đo: gần như không thấy trên ảnh tối), nhưng
            # rẻ (36 ms) và cộng dồn với vignette + grain thì đủ để cả tập có chung một chất.
            # ── VÀ CHỈ CHỈNH MỘT LẦN TRONG ĐỜI MỖI ẢNH  (4/9/2026) ────────────────────────
            # `to_mau` ghi đè TẠI CHỖ. Ảnh lấy từ cache vẫn đi qua đây, nên mỗi lượt dựng lại
            # là thêm một lớp hạ bão hoà 14% + một lớp kéo tông. Xem số đo ở khối `_so`:
            # 20 lượt đưa bão hoà 163 xuống 55. Cờ trong sổ cắt hẳn việc cộng dồn.
            if mau_chu and mau_nen and can_to_mau(duong):
                try:
                    from to_mau import to_mau as _tm
                    if _tm(duong, mau_chu, mau_nen):
                        danh_dau_to_mau(duong)
                except Exception:
                    pass
    # ── SOI LẠI BA ẢNH ĐẦU  (1/9/2026) ──────────────────────────────────────────────────────
    # Lỗ hổng cấu trúc, không phải chuyện ngưỡng: ba ảnh đầu được vẽ TRƯỚC khi có mốc, nên
    # KHÔNG ảnh nào trong ba ảnh ấy bị cổng nhất quán kiểm. Đo trên tập `smallest`: chất vẽ
    # [0.37, 0.65, 0.74, 0.81] — ảnh lạc chính là ảnh ĐẦU TIÊN, thứ duy nhất không ai soi.
    # Cổng chỉ canh được từ ảnh thứ tư trở đi thì nó bỏ trống đúng chỗ dễ lạc nhất.
    # Có mốc rồi thì quay lại soi chúng, và vẽ lại ảnh nào ngoài ngưỡng.
    if moc is not None and _dau:
        for i, ve in _dau:
            p = nhip[i].get("nenAnh")
            if not p:
                continue
            d = do_phang(os.path.join(THU, os.path.basename(p)))
            if d is None or abs(d - moc) <= NGUONG_LECH:
                continue
            print(f"     ↻ nhịp {i}: chất vẽ {d:.2f} lệch khỏi mốc {moc:.2f} — vẽ lại")
            rel2 = sinh(ma, idx, i, ve, keys, nhip[i].get("tam_trang", ""), gu, doc, moc)
            if rel2:
                nhip[i]["nenAnh"] = rel2
                _sd2 = sang_day(os.path.join(THU, os.path.basename(rel2)))
                if _sd2 >= 0:
                    nhip[i]["sangDay"] = _sd2
    # Ghi sổ sức khoẻ khoá TỪ LƯỢT DÙNG THẬT — xem `xoay_key.ghi_trang_thai`.
    # Đặt ở cuối tập, không đặt sau mỗi ảnh: mỗi tập một lượt ghi lô thay vì hàng trăm.
    try:
        import xoay_key as _XK
        _XK.ghi_trang_thai(os.environ.get("OWNER_UID", ""))
    except Exception:
        pass
    return n
