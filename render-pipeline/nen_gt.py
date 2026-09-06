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
import time
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
# Nén còn một nửa (4/9): ba ý giữ nguyên, bỏ chữ thừa. Ngân sách prompt là 1.873 ký tự và
# câu này thuộc nhóm dài nhất — mỗi ký tự ở đây đổi bằng một ký tự của luật khác bị cắt.
# Nén còn một nửa (4/9): ba ý giữ nguyên, bỏ chữ thừa. Ngân sách prompt là 1.873 ký tự,
# và mỗi ký tự tiết kiệm ở đây là một ký tự cho luật khác — cụ thể là bảng màu kênh.
CHUA_CHO = ("top third empty sky or wall, bottom fifth empty ground, "
            "everything important in the middle band")

# ── ẢNH PHẢI TRÀN KHUNG CHỮ NHẬT  (4/9/2026) ───────────────────────────────────────────────
# Anh gửi khung DAY IN LIFE: cả minh hoạ nằm gọn trong MỘT HÌNH TRÒN, bốn góc trắng trơn — mô
# hình dựng nó như một cái huy hiệu dán lên nền trắng, nên khung mất gần một phần ba diện tích
# và bối cảnh bị cắt cụt. Đúng chỗ anh nói "không rõ bối cảnh".
# Không câu nào trong prompt nói về RÌA khung; thứ không viết ra thì mô hình tự chọn (§15.2),
# và kho ảnh minh hoạ đầy icon dạng huy hiệu nên nó hay chọn hình tròn.
# ── BỎ BA VẾ VIẾT NGHỊCH  (4/9/2026) ──────────────────────────────────────────────────────
# `kiem_nen.CAM_NGHICH` ghi rõ, và đã trả giá một lần ở bộ khác: *"FLUX không có negative
# prompt: mọi danh từ trong câu đều là thứ nó sẽ vẽ. `no furniture` vì thế đẻ ra đúng cái đồ
# chắn giữa khung mà nó định cấm."* Bản trên viết `no circular vignette, no round badge,
# no border` — ba danh từ tròn đứng liền nhau, ngay sau câu tả khung. Tức là câu sinh ra để
# CHẶN vignette tròn đang mời mô hình vẽ đúng vignette tròn, và đó chính là khung anh gửi
# kèm lời "vẫn không rõ bối cảnh".
# Vế KHẲNG ĐỊNH đứng ngay trước đã nói trọn điều cần nói. Bỏ ba vế nghịch: đúng hơn về cơ
# chế, và trả lại 46 ký tự cho bảng màu kênh — thứ đang bị cắt ở 32% prompt.
TRAN_KHUNG = "the picture fills the whole rectangular frame edge to edge, "
KHUNG_DOC = ("tall vertical composition, subject centred, nothing important in the outer "
             "quarter left or right, " + TRAN_KHUNG + CHUA_CHO)
KHUNG_NGANG = ("wide horizontal composition, subject centred, " + TRAN_KHUNG + CHUA_CHO)

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


# ── LUẬT SÀN BẢN GỌN CHO BỘ GIẢI THÍCH  (4/9/2026) ─────────────────────────────────────────
# `SAN_NEN` nhập từ `kich_hai` (bộ truyện tranh) dài 295 ký tự. KHÔNG sửa tệp ấy — hai bộ
# không dùng chung engine và sửa chéo là cách chắc chắn làm hỏng bộ kia (§10). Viết bản gọn
# riêng ở đây, giữ đủ BA MỆNH LỆNH bắt buộc của §7 mà `kiem_nen.py` canh:
#   1. wide shot ngang tầm mắt   2. sàn chạy hết bề ngang ở dải dưới   3. giữa khung trống
# ── HAI VẾ CỦA BỘ TRUYỆN TRANH, BỎ ĐI  (4/9/2026) ─────────────────────────────────────────
# Hai câu này chép từ `kich_hai.SAN_NEN` (§7). Ở đó chúng ĐÚNG, vì bộ truyện tranh dán người
# VECTOR lên ảnh AI — nên giữa khung phải trống để còn chỗ dán, và đồ đạc phải dạt ra hai mép
# để không đè lên người. Bộ giải thích đã bỏ hẳn cơ chế ấy: người do chính mô hình vẽ, nằm
# trong ảnh. §12.5 đúng từng chữ — *một câu luật đúng trong ngữ cảnh nó sinh ra, sai ở ngữ
# cảnh mới*.
#
# Hai bằng chứng nó đang gây hại, không chỉ thừa:
#   1. NÓI NGƯỢC VỚI `KHUNG_DOC`. Khung dặn *"subject centred, everything important in the
#      middle band"*; câu này dặn *"centre of the frame is empty walkable floor"*. Hai lệnh
#      trái nhau trong cùng một prompt, và mô hình chọn bên nào là chuyện may rủi — đúng thứ
#      làm chủ thể lúc có lúc không.
#   2. DỒN ĐỒ VÀO DẢI SẮP BỊ CẮT. §12.5 đã đo: cắt vuông xuống 9:16 mất 44% bề ngang, nên
#      *"dồn đồ đạc ra hai mép"* là dặn mô hình đặt bối cảnh vào đúng phần sẽ biến mất — và
#      "không rõ bối cảnh" là lời phê anh nhắc lại nhiều lần nhất.
#
# Giữ lại đúng vế CHỐNG NGƯỜI LƠ LỬNG (sàn liền mạch suốt phần ba dưới) và vế tầm máy. Không
# thêm `nen_gt.py` vào `kiem_nen.TEP`: cổng ấy đòi đủ bốn mệnh lệnh của BỘ TRUYỆN TRANH, tức
# nó sẽ đòi lại đúng hai vế vừa bỏ.
GON_TRONG = ("wide shot at standing eye level, "
             "floor runs unbroken across the bottom third from edge to edge")
GON_NGOAI = ("wide shot at standing eye level, "
             "ground runs unbroken across the bottom third from edge to edge, "
             "outdoors under open sky")


def _luat(ve: str, doc: bool = False) -> str:
    """Luật sàn — và KHÔNG nói lại thứ câu cảnh đã nói.

    Đo trên 109 câu cảnh thật của 18 kênh: **106 câu (97%) đã tự chứa "standing eye level"**,
    vì `giai_thich` ghép sẵn vế ấy vào mô tả cảnh. Nên vế mở đầu của `GON_*` là một bản sao
    đứng cách bản gốc vài trăm ký tự, và nó tiêu 32 ký tự của một ngân sách đang cắt mất bảng
    màu kênh ở 6% prompt.
    Nói hai lần không làm mô hình nghe rõ hơn — nó chỉ đẩy một luật khác ra khỏi câu. §15.12:
    *mỗi ràng buộc chỉ được sống ở đúng một chỗ.*
    """
    ngoai = bool(_NGOAI.search(ve or ""))
    r = GON_NGOAI if ngoai else GON_TRONG
    if "standing eye level" in (ve or ""):
        r = r.split(", ", 1)[1]
    return r


# ══ KẸP PHONG CÁCH — KHỐI ĐỨNG NGAY SAU CHỦ THỂ, CHƯA BAO GIỜ BỊ CẮT ═══════════════════════
# Mười một mệnh lệnh, viết chặt. Ngân sách prompt là 1.873 ký tự và tổng các phần từng lên
# 2.175 — mỗi ký tự thừa ở đây đẩy một luật khác ra khỏi câu, và thứ bị đẩy ra là BẢNG MÀU
# KÊNH (mất ở 203/252 prompt).
#
# Câu về ĐẦU viết theo lối ĐỒNG NHẤT ("each head IS a plain white oval"), không theo lối
# thêm vào: bản cũ "stick-figure people with plain round white heads" đứng cạnh một chủ thể
# đã tả kỹ thì mô hình đọc ra HAI vật và vẽ một hình bầu dục trắng dán đè lên mặt đã vẽ —
# đúng khung anh gửi.
KEP_GU = (
    "flat 2D cartoon illustration, confident bold black ink outlines, "
    "each head is a simple round shape with warm pale skin tone, two dot eyes, "
    "one short mouth line, no nose, minimal shading; hair always drawn, also from "
    "behind, never a bare head; "
    "objects are simple shapes filled with warm rich colour, same bold outlines; "
    "no photo texture, no lens blur, not 3D; "
    "modern animated explainer style, gentle soft shading for volume; "
    "background always LIGHT and warm, never dark or desaturated; "
    "the setting is exactly the place named above, drawn with its own props, "
    "never a blank backdrop; an everyday American setting")


# ── GIỮ PHẦN `KEP_GU` CHƯA NÓI, BỎ PHẦN LẶP  (4/9/2026) ───────────────────────────────────
# Khối này từng dài 1.065 ký tự và phần lớn lặp lại `KEP_GU` (nét mực đậm · không ảnh chụp ·
# không lấy nét nông · không 3D · không chữ). Trần prompt là 2.048 và phép ghép cắt từ đuôi,
# nên một khối lặp dài chính là thứ đẩy các luật ngắn ra khỏi câu.
#
# Giữ lại ĐÚNG BỐN điều `KEP_GU` không nói, và mỗi điều đều là một lỗi đã trả giá:
#   1. neo thể loại  — "phim giải thích hoạt hoạ", để nó không trôi sang tranh minh hoạ sách
#   2. NỀN PHẢI SÁNG — câu chữa lỗi "ảnh ra tối" (§16.2), mất nó là ảnh tối trở lại
#   3. có khối, có bóng mềm nhẹ — thiếu thì hình phẳng lì như clipart
#   4. BỐI CẢNH ĐÚNG NƠI được tả và vẽ đủ đạo cụ — đây chính là "không rõ bối cảnh"
GU_CARTOON = (
    "in the style of a modern animated explainer video, "
    "the background is always LIGHT, warm and airy — never dark, never night-dark, "
    "never a moody or desaturated palette, "
    "flat cheerful colours with gentle soft shading for volume, "
    "the setting is exactly the place named above, drawn out with its own props, "
    "never a blank backdrop"
)
# Neo bối cảnh Mỹ — chỉ giữ những vật CHỈ CÓ Ở MỸ và mô hình vẽ được. "Cảm giác Mỹ" thì nó
# không vẽ được; "hòm thư trên cột cắm ở lề" thì vẽ được.
GU_USA = ("an everyday American setting — US road signs, US buildings, US clothing, "
          "nothing European or Asian")
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

# ── STYLE NGẮN CHO Ô `style=` CỦA `_generate_image_ai`  (5/9/2026) ─────────────────────────
# `_generate_image_ai`/`_cf_flux_image` nhét CHÍNH `style` vào wrap: `f"A {style} of: {prompt}"`
# — và `gu`/`GU_CARTOON` (324 ký tự) đã NÓI LẠI gần như nguyên văn thứ `KEP_GU` (embedded
# trong THÂN prompt) đã nói: cả hai đều có "modern animated explainer style", "background
# always light", "the setting is exactly the place named above, drawn with its own props,
# never a blank backdrop". Comment ở dòng 193 nói đã tách "đúng bốn điều KEP_GU không nói",
# nhưng đọc lại nội dung thật thì `GU_CARTOON` đang lặp gần trọn — hai khối trôi dần về
# giống nhau qua nhiều lần sửa mà không ai gộp lại.
#
# Kết quả đo được: truyền `style=gu` (324 ký tự) làm `tran_boc_toi_da` tính ra mức dự phòng
# tới 610–769 ký tự (thay vì ~490 khi thử bằng một chuỗi style ngắn) — ngân sách còn lại cho
# phần THÂN prompt (scene + KEP_GU + khoá nhân vật + SACH + khung) hụt tới mức KEP_GU và
# `_khoa` bị cắt ở 40%/30% tổ hợp — hỏng NẶNG hơn cả thứ 324 ký tự kia định bảo vệ.
#
# `_generate_image_ai`'s ô `style=` chỉ cần một NEO NGẮN để câu "A {style} of:" đọc thông,
# không cần nhắc lại toàn bộ luật — luật đã nằm trong THÂN prompt rồi. Dùng CHÍNH constant
# này ở CẢ HAI nơi (`_prompt()`'s `tran_boc_toi_da` VÀ `sinh()`'s `style=`) — khác constant ở
# hai nơi là tái diễn đúng lỗi 2048 vừa vá (đo một chuỗi, gửi một chuỗi khác).
STYLE_NGAN = "flat 2D cartoon illustration"

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
    # ── KÊNH XOAY NGHỀ THÌ KHOÁ PHẢI LÀ NÉT VẼ, KHÔNG PHẢI DANH TÍNH  (4/9/2026) ──────
    # `sinh_dayinlife` xoay hẳn nghề theo tập: lính La Mã · thợ bánh · lái tàu điện ngầm ·
    # kiểm soát không lưu · y tá ca đêm… Khoá cũ tả MỘT người cụ thể ("đàn ông cuối hai
    # mươi, tóc đen ngắn, áo chẽn vải thô") nên nó **đánh nhau với chính câu cảnh**: tập y tá
    # ra prompt vừa "a night-shift nurse" vừa "a man in a linen tunic".
    # Thứ cần giữ nguyên qua các khung là NÉT VẼ và KHUÔN MẶT, không phải danh tính — danh
    # tính đã nằm sẵn ở câu cảnh và đổi theo tập là đúng ý đồ của kênh.
    # Chỉ nói phần khoá THÊM VÀO. Tạo hình mặt đã do `MOI_MAT` lo — nhắc lại là tiêu ký tự
    # của trần prompt để mua về đúng thứ đã có.
    "dayinlife": "the same person, same face and same hair in every shot of this episode",
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
# ── ĐỪNG LIỆT KÊ NGHỀ — NHẬN RA QUY LUẬT SINH RA CHÚNG  (4/9/2026) ─────────────────────────
# Bản cũ là một danh sách chép tay: `soldier · baker · keeper · watchman` — đúng ba nghề mà ai
# đó đã vấp phải rồi thêm vào. Thử lại trên mười nghề thật của kênh DAY IN LIFE:
#
#     soldier ✔   watchman ✔   baker ✔
#     nurse ✘   farmer ✘   driver ✘   teacher ✘   miner ✘   fisherman ✘   pilot ✘
#
# Bảy trên mười trượt, và mỗi lần trượt là **không khoá nhân vật** — nên bốn khung của cùng
# một tập ra bốn người khác nhau (tóc đen búi · vàng · cam · trắng). Đó chính là thứ anh nhìn
# thấy: "không toát lên được ý truyền đạt", vì người xem không nhận ra đang theo dõi AI cả.
#
# §13.9 đã trả giá cho đúng chuyện này ở bộ Kling: *danh sách ngoại lệ là danh sách VÔ HẠN* —
# thêm `nurse` hôm nay thì mai vấp `welder`, `librarian`, `paramedic`.
#
# Quy luật sinh ra chúng: tiếng Anh đặt tên người làm nghề bằng một nhúm HẬU TỐ đóng
# (-er/-or/-ist/-ian/-man/-woman/-ess) cộng một ít từ gốc Latin không theo hậu tố (nurse,
# chef, clerk, guard, cook, maid, pilot, judge). Nhúm sau ngắn và ĐÓNG THẬT — nó không đẻ
# thêm như danh sách nghề.
_CO_NGUOI = re.compile(
    r"\b(figure|person|people|man|men|woman|women|child|children|adult|crowd|silhouette|"
    r"someone|hand|hands|"
    r"\w{3,}(?:er|or|ist|ian|man|men|woman|women|ess)|"
    r"nurse|chef|clerk|guard|cook|maid|pilot|judge|\w*medic|crew|staff)\b", re.I)


def _chu_ngu(ve: str) -> str:
    """Cụm CHỦ NGỮ của câu cảnh — phần trước giới từ/dấu phẩy đầu tiên.

    Vì sao cần: luật hậu tố `-er/-or/…` bắt được mọi nghề, nhưng nó cũng bắt **water · paper ·
    counter · tower** khi chúng nằm ở giữa câu. Thử ngược ra ngay: *"a single glass of water on
    a table"* bị nhận là cảnh có người — và gắn khoá nhân vật vào một cảnh đồ vật thì mô hình
    nhét thêm một người không ai cần, đúng cái hại mà chú thích gốc đã cảnh báo.

    `_ve()` luôn đặt CHỦ THỂ lên đầu, nên chỉ cần soi cụm đầu là đủ và hết bắt oan:
        "a night-shift nurse alone, rising stiffly"  -> "a night-shift nurse alone"   ✔ người
        "a single glass of water on a table"         -> "a single glass"              ✔ đồ vật
        "a school bus alone, centred"                -> "a school bus alone"          ✔ đồ vật
    """
    dau = re.split(r",| of | on | in | with | at | and | beside | next to ", ve or "", 1)[0]
    return dau.strip()


# ── ĐỒ VẬT TÌNH CỜ KẾT THÚC BẰNG HẬU TỐ NGƯỜI LÀM  (4/9/2026) ──────────────────────────────
# Luật hậu tố bắt được mọi nghề, và bắt luôn `tower · water · counter` khi chúng là CHỦ NGỮ:
# thử ngược ra *"a tall paper tower on a counter"* bị nhận là cảnh có người.
#
# Không viết tay danh sách đồ vật — nó vô hạn y như danh sách nghề. Nhưng tập đồ vật mà DỰ ÁN
# NÀY nói tới thì hữu hạn và đã khai sẵn: đó là các thứ trong bảng dữ liệu (`QUANG_DUONG`,
# `CO_LON`, `KHOI_LUONG`…) cộng tên biểu tượng trong engine. Lấy từ đó thì tập loại trừ tự lớn
# theo dữ liệu, không phải theo trí nhớ người sửa.
def _do_vat() -> set:
    ra = {"tower", "water", "counter", "paper", "container", "computer", "monitor", "elevator",
          "escalator", "refrigerator", "radiator", "generator", "calculator"}
    try:
        import giai_thich as _G
        for ten in ("QUANG_DUONG", "CO_LON", "KHOI_LUONG", "AM_THANH", "NHIET_DO",
                    "CUC_NHO", "PHI_AN", "XAC_SUAT"):
            for hang in getattr(_G, ten, []) or []:
                if isinstance(hang, (list, tuple)) and hang and isinstance(hang[0], str):
                    ra |= {w.lower() for w in re.findall(r"[A-Za-z]{3,}", hang[0])}
    except Exception:
        pass
    return ra


_DO_VAT = None


def _la_nguoi(ve: str) -> bool:
    """Cảnh này có CHỦ THỂ LÀ NGƯỜI không — soi chủ ngữ, trừ đi đồ vật dự án biết tên."""
    global _DO_VAT
    if _DO_VAT is None:
        _DO_VAT = _do_vat()
    cn = _chu_ngu(ve)
    for m in _CO_NGUOI.finditer(cn):
        if m.group(0).lower() not in _DO_VAT:
            return True
    return False


def _khoa(ma: str, ve: str) -> str:
    k = KHOA_VAI.get(ma, "")
    # Soi CHỦ NGỮ, không soi cả câu — xem `_chu_ngu`.
    if not k or not _la_nguoi(ve):
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


# ══ SỔ ĐẾM ẢNH CỦA CẢ LUỒNG — Ở TỆP, KHÔNG Ở BIẾN  (4/9/2026) ══════════════════════════════
# Trần `TRAN_ANH_LUONG` đếm bằng `sinh._da_ve`, một thuộc tính HÀM. Chú thích của nó ghi
# *"120 ảnh/luồng/lượt × 18 luồng × 4 lượt/ngày = 8.640 ảnh = 52% sức hồ"* — con số đúng cho
# một giả định sai: rằng một luồng là một tiến trình.
#
# `render_giai_thich_18.yml` có vòng `while` chạy TỪNG TẬP bằng một lệnh `python` riêng, nên
# bộ đếm chết theo tiến trình và trần thật là *"120 ảnh mỗi TẬP"*. Đo trên lượt 33819928469
# (18 luồng, 4,5 giờ, bấm tay lúc 23:59 UTC): **8.059 ảnh CF** thay vì 2.160 — vượt 3,7 lần,
# và nó vét sạch hạn mức của NGÀY HÔM SAU vì CF hồi lúc 00:00 UTC, đúng lúc lượt ấy đang chạy.
# Hậu quả anh nhìn thấy: 9.175/17.234 nhịp không có ảnh, và cả ngày hôm sau không vẽ được gì.
#
# §15.23 đã ghi đúng câu này rồi — *"dấu mốc để ở tệp `/tmp` chứ không phải biến module, vì
# mỗi tập có thể là một tiến trình riêng"* — và chỗ này không áp dụng. Cùng họ lỗi, khác tệp.
#
# Tệp đặt theo GITHUB_RUN_ID nên lượt sau bắt đầu lại từ 0; mỗi luồng là một runner riêng nên
# `/tmp` vốn đã tách sẵn giữa các luồng, không cần thêm khoá.
# `or` chứ không phải tham số thứ hai: biến môi trường ĐẶT MÀ RỖNG sẽ phá mặc định của
# `.get(K, "mđ")` — sổ rơi vào thư mục "" và mọi lượt ghi im lặng hỏng, tức trần ảnh biến mất
# đúng lúc nó cần nhất. `selftest.t_khong_tron_so` canh dạng này.
_ANH_TEP = os.path.join(os.environ.get("TMPDIR") or "/tmp",
                        "mm0_anh_luong_%s.txt" % (os.environ.get("GITHUB_RUN_ID") or "cucbo"))


# Bộ đếm CŨ thì phải quên đi — nếu không, cái trần thành cái KHOÁ VĨNH VIỄN.  (5/9/2026)
#
# Trên Actions, tên tệp mang `GITHUB_RUN_ID` nên mỗi lượt một tệp riêng và nó tự hết hạn.
# Ở máy anh KHÔNG có biến ấy, nên mọi lượt chạy đời đời dùng chung một tệp `cucbo` — nó bò
# lên 120 rồi ở đó mãi, và từ giây phút ấy `sinh()` trả rỗng cho MỌI lượt render, IM LẶNG.
#
# Đo được cái giá: cả buổi chiều em báo cáo "0% nhịp có ảnh AI" và đi dựng lại toàn bộ lớp
# vector vì tưởng hồ CF cạn — trong khi hồ đang ở 80% và thứ chặn là chính bộ đếm này.
# Đúng §12.8 ở dạng tệ nhất: hỏng, không báo gì, và còn dẫn người đọc đi sai hướng cả ngày.
#
# Một cái trần bảo vệ NGÂN SÁCH CỦA MỘT LƯỢT CHẠY thì nó phải hết hiệu lực khi lượt ấy kết
# thúc. Không có mã lượt để mà biết, thì dùng THỜI GIAN: quá hai giờ coi như lượt khác.
_ANH_HAN = 7200


def _da_ve() -> int:
    """Số ảnh CF luồng này đã vẽ — đọc từ tệp, nên sống qua mọi tiến trình của luồng."""
    try:
        if (not os.environ.get("GITHUB_RUN_ID")
                and time.time() - os.path.getmtime(_ANH_TEP) > _ANH_HAN):
            return 0                      # tệp của một lượt đã xong từ lâu
        with open(_ANH_TEP) as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0


def _ghi_da_ve(n: int) -> None:
    # Hỏng thì BỎ QUA, không ném: trần ảnh là việc tiết kiệm, không phải việc thiết yếu —
    # để nó làm chết một lượt dựng là đổi sai chiều.
    try:
        with open(_ANH_TEP, "w") as f:
            f.write(str(n))
    except Exception:
        pass

# ── SIẾT DẦN KHI CỔNG ĐÁNH TRƯỢT  (khôi phục 4/9/2026) ───────────────────────────────────
# Bảng này được VIẾT hôm 3/9 và bị một lượt cắt hụt xoá mất phần khai báo, trong khi `_prompt`
# vẫn gọi nó ở dòng 691. Nghĩa là mọi lần cổng chất vẽ đánh trượt đều `NameError` — tức đúng
# cái vòng vẽ lại mà bảng này sinh ra để phục vụ đã chết câm kể từ lúc ấy. Không có lỗi nào
# báo ra ngoài, vì `goi_xoay` bọc lời gọi trong `except Exception` và chỉ đếm nó là "một khoá
# hỏng", nên nhìn từ log thì y hệt mạng chập chờn. Cùng họ 12.8: hỏng mà vẫn báo xanh.
#
# BA BẬC, và mỗi bậc nói MẠNH HƠN về đúng thứ hai cổng đang đo:
#   `do_phang` — ảnh ngả sang ảnh chụp (đổ bóng mềm, chiều sâu quang học)
#   `do_sang`  — ảnh quá tối (mô hình tự chọn nền tối khi không được dặn)
# Hai cổng chữa bằng MỘT việc nên chúng đi chung một bảng, không tách hai vòng.
#
# HAI ĐIỀU KHÔNG ĐƯỢC LÀM, cả hai đã trả giá:
#   1. **Không đẩy nền về TRẮNG.** Bản đầu viết *"on a blank white page"*; FLUX làm đúng và ra
#      một trang trắng, rồi `kiem_chelap` bắt 8 nhịp có nền sáng TB 237 trên trần 150 — phụ đề
#      trắng đè nền trắng, chữ tàng hình. Siết chất vẽ và giữ nền CÓ MÀU là hai việc; câu siết
#      phải làm việc thứ nhất mà không phá việc thứ hai. `selftest.t_prompt_canh_dung_truoc`
#      canh đúng điều này.
#   2. **Không nói "no shading" trơn.** Ảnh tham chiếu anh gửi CÓ đổ bóng mềm; cấm gradient là
#      ép mô hình vẽ clipart phẳng (§16.2). Thứ cần cấm là chiều sâu QUANG HỌC — bóng đổ dài,
#      tiêu cự, ánh sáng ngược — không phải mọi chuyển sắc.
SIET = (
    "flat 2D illustration, not a photograph",
    "bold flat vector illustration on a mid-tone coloured ground, "
    "clean even lighting, no photographic depth of field",
    "poster-flat 2D artwork, solid colour shapes with clean ink outlines, "
    "a clearly coloured mid-tone background, bright even light, "
    "absolutely not a photograph and not a 3D render",
)


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


# ══ BẢNG MÀU KÊNH PHẢI ĐI VÀO PROMPT  (4/9/2026) ═══════════════════════════════════════════
# Anh: *"phối màu bố cục hình ảnh xấu."* Soi một tập DAY IN LIFE: bốn khung ảnh AI ra **xanh
# lạnh bệnh viện**, hai khung vẽ bằng code ra **be ấm** — hai thế giới trong mười hai giây.
#
# Gốc: mỗi kênh CÓ SẴN bảng bốn màu (`MAU_KENH`), lớp vẽ code dùng nó, còn prompt ảnh thì
# **chưa bao giờ nói ra nó**. Câu duy nhất về màu là "nền phải sáng và ấm" — một lời khuyên,
# không phải một bảng màu. Nên mỗi ảnh tự chọn, và hai lớp không có lý do gì trùng nhau.
#
# §12.10 đã đo và ghi: *lệch phong cách giữa các ảnh là đòn bẩy lớn nhất, và chỉnh màu
# KHÔNG cứu được nó*. Đúng — chỉnh màu sau khi vẽ chỉ kéo được vài phần trăm. Thứ ăn thua là
# nói bảng màu TRƯỚC khi vẽ.
#
# Mô hình không đọc mã hex, nên đổi sang TÊN MÀU: sắc độ + độ sáng + độ bão hoà -> một cụm
# tiếng Anh ("warm sand", "deep rust orange", "slate blue").
def _ten_mau(hex_: str) -> str:
    """Mã hex -> một cụm màu tiếng Anh. Mô hình không đọc hex.

    Chia theo CẢ BA chiều, không chỉ sắc độ: bản đầu chỉ chia theo hue nên `#F0E7D6` (kem),
    `#8A6134` (nâu) và `#D9622B` (cam gạch) cùng ra "rust orange" — ba kênh khác nhau nhận
    một câu màu giống hệt, tức mất đúng thứ bảng màu sinh ra để giữ: bản sắc kênh.
    Nâu CHÍNH LÀ cam tối và ít bão hoà, nên phải đọc độ sáng mới tách được."""
    h = (hex_ or "").lstrip("#")
    if len(h) != 6:
        return ""
    r, g, b = (int(h[k:k + 2], 16) / 255 for k in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    l, d = (mx + mn) / 2, mx - mn
    sat = 0 if d == 0 else d / (1 - abs(2 * l - 1) + 1e-6)
    if d < 0.05 or sat < 0.10:
        return ("soft white" if l > 0.88 else "warm off-white" if l > 0.74 else
                "light warm grey" if l > 0.55 else "mid grey" if l > 0.32 else "charcoal")
    hu = (((g - b) / d) % 6 if mx == r else (b - r) / d + 2 if mx == g else (r - g) / d + 4) * 60
    if hu < 16 or hu >= 345:
        ten = "brick red" if l < 0.45 else "coral red"
    elif hu < 34:
        ten = "chocolate brown" if l < 0.40 else "burnt orange" if l < 0.62 else "peach"
    elif hu < 48:
        ten = "warm brown" if l < 0.42 else "tan" if l < 0.68 else "warm cream"
    elif hu < 62:
        ten = "olive brown" if l < 0.45 else "golden amber" if l < 0.70 else "pale straw"
    elif hu < 90:
        ten = "moss green" if l < 0.50 else "sage green"
    elif hu < 165:
        ten = "forest green" if l < 0.45 else "muted green"
    elif hu < 200:
        ten = "deep teal" if l < 0.45 else "soft teal"
    elif hu < 245:
        ten = "steel blue" if l < 0.52 else "pale sky blue"
    elif hu < 290:
        ten = "indigo" if l < 0.50 else "lavender"
    else:
        ten = "plum" if l < 0.50 else "dusty pink"
    return ten


def _bang_mau(ma: str) -> str:
    """Câu khoá bảng màu của kênh — ba màu, gọi bằng tên."""
    try:
        from giai_thich import MAU_KENH
        m = MAU_KENH.get(ma) or {}
    except Exception:
        return ""
    nen, chinh, phu = (_ten_mau(m.get(k, "")) for k in ("nen", "mau", "phu"))
    if not (nen and chinh):
        return ""
    return (f"limited palette: {nen} background, {chinh} as the main colour"
            + (f", {phu} as the only accent" if phu else "") + ", no other hues")


def _sac_thai(ma: str) -> str:
    """Sắc thái vẽ riêng của kênh — vẫn trong khuôn 'cartoon phẳng', chỉ khác nét.

    Không cho mỗi kênh một PHONG CÁCH khác (đã thử và hỏng: trộn ảnh thật với cartoon làm
    30/74 ảnh lệch nhau). Cho mỗi kênh một SẮC THÁI trong cùng một phong cách: viền dày hay
    mảnh, có viền hay không, nét máy hay nét tay, bảng màu rộng hay hạn chế ba màu.
    Bốn thứ ấy đủ để mười kênh không nhìn ra cùng một xưởng, mà không kéo cái nào về ảnh thật.

    ── BỎ VẾ NÓI VỀ BẢNG MÀU  (4/9/2026) ──────────────────────────────────────────────────
    `GU_RIENG` viết trước khi có `_bang_mau`, nên bốn kênh mang sẵn một vế bảng màu MƠ HỒ:
    *"restrained three-color palette"* · *"high-contrast palette"* · *"muted earthy palette"*
    · *"warm limited palette"*. Nay chúng đứng ngay SAU câu nêu đích danh ba màu của kênh, và
    hai câu ấy nói ngược nhau — `speedof` vừa được dặn "steel blue nền trắng dịu" vừa được
    dặn "bảng màu tương phản cao".
    Cắt ở ĐÂY chứ không sửa `GU_RIENG`: bảng ấy là nguồn dùng chung (giọng · nhạc · sắc thái)
    và cửa sổ khác đang làm trên cùng tệp. Nơi mâu thuẫn phát sinh là chỗ ghép prompt, nên nơi
    chữa cũng là chỗ ấy.
    Lợi thêm: `_bang_mau` và vế này là hai vế CUỐI của prompt, tức hai vế bị chốt chặn cắt
    trước nhất — bỏ chữ thừa ở đây là trả chỗ cho chính bảng màu.
    """
    try:
        from giai_thich import GU_RIENG
        v = GU_RIENG.get(ma, ("", "", ""))[2]
    except Exception:
        return ""
    giu = [c.strip() for c in v.split(",")
           if c.strip() and "palette" not in c.lower()]
    return ", ".join(giu)


# Vế nào bị chốt chặn độ dài cắt bỏ — xem chú thích trong `_prompt`. Danh sách toàn cục vì
# `_prompt` được gọi từ nhiều chỗ và cái cần biết là "cả tập này đã mất vế nào", không phải
# "lượt gọi thứ mấy đã mất".
_DA_CAT: list = []


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
    # ── SIẾT DẦN THEO LẦN THỬ  (3/9/2026) ────────────────────────────────────────────────
    # `siet` là số lần cổng chất vẽ đã đánh trượt ảnh này. Xem chú thích ở `sinh()`: vẽ lại
    # bằng CÙNG một prompt là vô nghĩa vì FLUX schnell không nhận `seed`. Mỗi lần trượt thì
    # đổi chính prompt, và đổi theo hướng cổng đang đo — nói mạnh hơn về CHẤT VẼ.
    # `siet - 1`: lần trượt THỨ NHẤT dùng câu siết thứ nhất. Viết `min(siet, …)` là hụt một
    # bậc — câu nhẹ nhất không bao giờ được dùng, và ảnh nhảy thẳng sang mức siết mạnh.
    _siet_txt = (SIET[min(siet - 1, len(SIET) - 1)] + ", ") if siet else ""
    # ── MỘT CHẤT LIỆU CHO CẢ BỘ PHIM  (5/9, bỏ giấy kraft 6/9/2026) ─────────────────────
    # Bản 5/9 ép thêm ", ink on kraft paper," để khớp nền giấy có vân của lớp vector — nhưng
    # KEP_GU (dán ngay sau, xem `_bat_buoc`) đã tự quyết định màu nền theo luật riêng của nó
    # ("background always LIGHT and warm"), nên hai lớp tranh nhau: một câu đòi giấy kraft cụ
    # thể, một câu đòi "nền sáng ấm" chung chung. Anh: *"ko cần nền paper nữa đâu sao đẹp là
    # được"* — bỏ hẳn ràng buộc vật liệu nền, để KEP_GU với FLUX tự chọn màu nền đẹp nhất cho
    # từng cảnh (đã đo: xanh navy đêm, be/kem ban ngày — đều đẹp, không cần ép giấy kraft).
    #
    # ── 5/9/2026 — CÂU CẢNH KHÔNG ĐƯỢC MẤT TOÀN BỘ  ─────────────────────────────────────
    # Câu này từng đứng trong danh sách vừa ghép vừa cắt như mọi câu khác — và khi nó là
    # câu ĐẦU TIÊN không vừa, `ra` vẫn đang RỖNG, nên cả câu biến mất, không phải cắt bớt.
    # Soi khung thật của bản pilot đầu tiên: 36% tổ hợp rơi đúng vào ca này — nghĩa là 36%
    # ảnh được gửi đi với một prompt CHỈ CÓ LUẬT PHONG CÁCH, KHÔNG MỘT CHỮ NÀO TẢ CẢNH. Mô
    # hình khi đó vẽ đúng những gì nó được bảo: một hình bất kỳ hợp phong cách, không liên
    # quan gì tới nội dung nhịp. Đây là lỗi NẶNG HƠN việc mất phong cách (KEP_GU) — ít nhất
    # ảnh sai phong cách còn đúng NỘI DUNG; ảnh này đúng phong cách nhưng sai/không có nội
    # dung, tức vẫn là "ảnh không liên quan" dù trông có vẻ đúng bộ.
    #
    # Chữa bằng CẮT BỚT chứ không XOÁ SẠCH: nếu không đủ chỗ, bỏ `mt` (mô tả sáng/thời tiết —
    # phụ) trước, rồi cắt `ve` ở BIÊN TỪ (không cắt giữa chữ) cho vừa — luôn giữ lại ít nhất
    # một phần câu tả cảnh, dù ngắn, còn hơn không có gì.
    _canh_day = _siet_txt + "a black ink line drawing of " + ve + mt + ","
    _canh_khong_mt = _siet_txt + "a black ink line drawing of " + ve + ","

    def _canh_vua(budget: int) -> str:
        if len(_canh_day) <= budget:
            return _canh_day
        if len(_canh_khong_mt) <= budget:
            return _canh_khong_mt
        # Vẫn không vừa dù đã bỏ `mt` — cắt `ve` ở biên từ. Đuôi cố định (đủ để CF vẫn hiểu
        # đây là một cảnh) chiếm chỗ trước, phần còn lại dành cho `ve`.
        duoi = ","
        dau = _siet_txt + "a black ink line drawing of "
        con = budget - len(dau) - len(duoi)
        if con <= 10:      # không còn đủ chỗ để nói được gì có nghĩa — vẫn trả một mẩu
            return (dau + ve[:max(10, con)] + duoi)[:budget]
        ve_cat = ve[:con].rsplit(" ", 1)[0] if " " in ve[:con] else ve[:con]
        return dau + ve_cat + duoi

    phan = [
        # `KEP_GU` KHÔNG còn ở đây — xem lý do trong khối `_bat_buoc` bên dưới.
        _khoa(ma, ve).rstrip(),    # 2. khoá nhân vật (rỗng nếu cảnh không có người)
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
        # ── THỨ TỰ = ĐỘ QUAN TRỌNG, VÌ PHÉP CẮT ĂN TỪ ĐUÔI  (4/9/2026) ────────────────
        # Vòng ghép dưới đây cắt từ đuôi khi chạm trần 2.048. Nên thứ tự phải xếp theo ĐỘ
        # QUAN TRỌNG — và bản cũ vi phạm chính nguyên tắc của nó: khối phong cách dài 1.065
        # ký tự đứng TRƯỚC bốn luật ngắn mà quan trọng hơn.
        #
        # Đo được sau khi thêm vài chục ký tự vào câu tả mặt: prompt bị cắt mất `GU_USA` và
        # `SACH`. `SACH` là câu cấm chữ — thứ chặn đúng lỗi ảnh vẽ ra tấm vé ghi "LICKET"
        # (§12.7: chữ mô hình bịa là dấu hiệu nghiệp dư người xem đọc ra trong nửa giây).
        # Một câu 47 ký tự bị hi sinh cho một khối 1.065 ký tự mà `KEP_GU` đã kẹp phần lớn.
        #
        # Nay: mọi luật NGẮN đứng trước, khối phong cách dài đứng cuối — nếu phải cắt thì cắt
        # đúng thứ đã có bản rút gọn ở `KEP_GU`.
        # `SACH`/`khung`/`_luat`/`_bang_mau`/`_sac_thai` KHÔNG nằm trong danh sách này nữa —
        # cả năm đều tự nhận là "không được mất" ngay trong chú thích của chính chúng, nên
        # cả năm đều thuộc nhóm bắt buộc — xem lý do ngay dưới.
        # ── MỘT LUẬT LUÔN BỊ CẮT LÀ MỘT LUẬT KHÔNG TỒN TẠI  (4/9/2026) ────────────────
        # Neo bối cảnh Mỹ từng là mục cuối. Đo trên 168 prompt của 18 kênh: **153 cái bị
        # cắt mất nó** — tức nó gần như chưa bao giờ được gửi đi, trong khi vẫn chiếm chỗ
        # trong danh sách và làm người đọc tưởng nó đang có tác dụng.
        # Nay ba chữ "an everyday American setting" nằm trong `KEP_GU` — khối đứng ngay sau
        # chủ thể và chưa bao giờ bị cắt. Rẻ hơn 80 ký tự và thật sự tới nơi.
    ]
    # ── TRỪ LỚP BỌC MÀ `_generate_image_ai` THÊM VÀO  (3/9, vá lại 5/9/2026) ─────────────
    # Trần 2048 là của chuỗi **gửi đi**, không phải của chuỗi hàm này ghép ra.
    #
    # Bản 3/9 trừ cứng 175 (159 ký tự bọc CF/Gemini + 16 đệm) — đúng cho lúc `sinh()` còn
    # gọi THẲNG `_cf_flux_image`. Từ khi nó đổi sang gọi `_generate_image_ai` (hồ CF+Gemini
    # gộp — xem `sinh()`), hàm ấy còn tự nối THÊM hai lớp TRƯỚC lớp bọc kia: `_bo_mat_chu`
    # (tối đa ~159 ký tự, khi prompt gọi tên thứ có mặt chữ) rồi `_salt_prompt` (~172 ký tự,
    # LUÔN LUÔN). Mức trừ cũ chỉ đủ cho MỘT trong BA lớp — đo thật một lượt dựng kênh
    # `howlong`: **15/15 nhịp gửi CF đều trả `400 Length of '/prompt' must be <= 2048`**.
    #
    # Gọi thẳng `datastory_ci.tran_boc_toi_da(gu)` thay vì chép một hằng số khác: đúng bài
    # học 13.7 (*cổng phải nhận CHÍNH thứ sắp giao đi và ghép bằng CHÍNH phép ghép mà bên
    # kia sẽ chạy*) — ba lớp bọc kia đổi câu chữ thì trần ở đây tự cập nhật theo, không cần
    # nhớ ra mà sửa một hằng số thứ hai.
    try:
        import datastory_ci as _DSb
    except Exception:
        _DSb = None

    # ── KEP_GU + SACH + KHUNG + LUẬT SÀN + BẢNG MÀU + SẮC THÁI: KHÔNG ĐƯỢC CẮT  (5/9/2026) ──
    # Sáu câu NGẮN nhưng QUAN TRỌNG NHẤT. Ba vòng đo liên tiếp mới lộ hết:
    #   vòng 1 — chỉ kéo `_luat`/`_bang_mau`/`_sac_thai` ra: `khung` hứng chỗ hụt, cắt 54%.
    #   vòng 2 — kéo thêm `SACH`+`khung` ra: `KEP_GU` hứng chỗ hụt, cắt 36% (177/496).
    #   vòng 3 — SOI KHUNG THẬT của bản pilot đầu tiên mới thấy hậu quả: ba cảnh CF vẽ ra
    #   MỘT PHONG CÁCH KHÁC HẲN — minh hoạ tả thực có bóng đổ, có trăng sao, không còn là
    #   "flat 2D cartoon, đầu hình oval trắng, không bóng đổ" — đúng kiểu lỗi "trộn hai
    #   phong cách trong một video" đã bị phàn nàn ở phiên trước. Số đo (36% cắt) đọc trên
    #   giấy nghe không nghiêm trọng; nhìn ẢNH THẬT mới thấy nó hỏng NẶNG — đúng bài học
    #   §16.1: điểm số/tỉ lệ phần trăm không nói được "đẹp hay xấu", phải soi khung mới biết.
    #
    # Cả sáu câu đều tự nhận "không được mất" ngay trong chú thích của chính chúng ở các
    # bản sửa trước — nên cả sáu đều thuộc nhóm này.
    #
    # Kéo ra khỏi danh sách vừa ghép vừa cắt, trừ thẳng chỗ của chúng khỏi ngân sách phần
    # CÒN LẠI (giờ chỉ còn: câu tả cảnh + khoá nhân vật — đúng phần NỘI DUNG BIẾN ĐỘNG theo
    # từng nhịp, khác với sáu câu LUẬT/PHONG CÁCH cố định ở trên), rồi nối vào ở CUỐI sau
    # khi phần còn lại đã tự cắt xong — cách duy nhất bảo đảm "không hạn ngạch nào cả" bằng
    # TOÁN, không bằng may rủi thứ tự (đúng lỗi §14.13: *"một luật luôn bị cắt là một luật
    # không tồn tại"* — `_sac_thai` từng đứng cuối danh sách cuttable và bị cắt 496/496 tổ
    # hợp, tức chưa từng thật sự được gửi đi).
    _luat_txt = _luat(ve, doc)
    _bm_txt = _bang_mau(ma)
    _st_txt = _sac_thai(ma)
    _bat_buoc = (", ".join(x for x in (KEP_GU, SACH, khung, _luat_txt, _bm_txt, _st_txt) if x) + ","
                 if any((KEP_GU, SACH, khung, _luat_txt, _bm_txt, _st_txt)) else "")
    _du_bat_buoc = (1 + len(_bat_buoc)) if _bat_buoc else 0    # +1 cho dấu cách sẽ nối

    def _ghep(tran_boc: int) -> str:
        budget_tong = 2048 - tran_boc - _du_bat_buoc
        canh = _canh_vua(max(0, budget_tong))
        if canh != _canh_day:
            # Câu cảnh phải RÚT NGẮN — khai ra để `sinh()`/selftest biết (cùng cờ với các
            # vế khác, dù đây là CẮT chứ không phải BỎ HẲN).
            _DA_CAT.append(("[cảnh bị rút ngắn] " + _canh_day)[:48])
        # ── 6/9/2026 — KEP_GU DÁN NGAY SAU CHỦ THỂ, KHÔNG PHẢI CUỐI CÂU  ────────────────
        # Đưa KEP_GU vào `_bat_buoc` (5/9) bảo đảm nó KHÔNG BAO GIỜ bị cắt — nhưng đẩy nó
        # xuống CUỐI câu, đúng chỗ mô hình khuếch tán đọc NHẸ NHẤT (chính comment ở đầu
        # `_prompt()` đã nói: *"Mô hình khuếch tán đọc phần đầu nặng ký hơn"*). Soi khung
        # thật: ảnh CF vẫn ra minh hoạ bút mực tả thực — đầu người có tóc/mặt chi tiết,
        # không phải "oval trắng, hai chấm mắt" như KEP_GU đặt hàng. Khoá cứng NỘI DUNG
        # không cứu được khi VỊ TRÍ làm nó bị át bởi 300+ ký tự tả cảnh đứng trước.
        # Nối `_bat_buoc` (KEP_GU+SACH+khung+luật) ngay sau câu cảnh — trước cả `_khoa` —
        # để nó về đúng vị trí đã có ý định ban đầu ("neo phong cách dán ngay trước chủ
        # thể... rồi khoá nhân vật, rồi phong cách" — nay: chủ thể, PHONG CÁCH, khoá).
        ra = f"{canh} {_bat_buoc}".strip() if _bat_buoc else canh
        for x in phan:
            if not x:
                continue
            thu = (ra + " " + x).strip()
            if len(thu) > 2048 - tran_boc:
                # ── CẮT THÌ PHẢI KHAI RA  (4/9/2026) ────────────────────────────────────
                # Bản trước `break` trong im lặng, và §14.13 đã trả giá đúng cho hình dạng
                # này: *khi một hàm vừa ĐO vừa TỰ SỬA thì cổng đặt sau nó luôn xanh*. Ở đây
                # tệ hơn một bậc — không có cổng nào cả, nên một mệnh đề của prompt biến
                # mất khỏi bản gửi đi mà không ai duyệt việc bỏ mệnh đề nào.
                # Nay ghi lại vế bị bỏ; `sinh()` in ra một lần mỗi tập, selftest đọc cờ này.
                _DA_CAT.append(x[:48])
                break              # cắt từ đuôi: vế càng sau càng ít quan trọng
            ra = thu
        return ra

    # ── HAI VÒNG: THỬ MỨC SIẾT NHẸ TRƯỚC, CHỈ SIẾT NẶNG KHI THẬT SỰ CẦN  (5/9/2026) ─────
    # `_bo_mat_chu` (bên `datastory_ci`) chỉ nối thêm 159 ký tự khi prompt gọi tên một thứ
    # CÓ MẶT CHỮ (biển hiệu, giấy tờ, xe cộ…) — không phải MỌI prompt. Nhưng `nen_gt` phải
    # QUYẾT trước khi biết chuỗi cuối cùng trông ra sao, nên vòng đầu cắt theo giả định
    # NHẸ (không tính 159 ký tự ấy), rồi tự kiểm bằng chính `datastory_ci.co_mat_chu()` —
    # nếu bản vừa ghép ra THẬT SỰ kích nó, cắt lại lần hai với mức dự phòng ĐẦY ĐỦ. Không
    # làm thế thì mọi prompt đều bị cắt bớt cho một lớp bọc mà phần lớn chúng chẳng dùng
    # tới (đo được: siết cứng theo trường hợp xấu nhất đẩy tỉ lệ mất `KEP_GU`/`_khoa` lên
    # tới 40% — hỏng nặng hơn cả cái đang được phòng).
    if _DSb is not None:
        _boc_nhe = _DSb.tran_boc_toi_da(STYLE_NGAN, co_the_co_mat_chu=False)
        ket = _ghep(_boc_nhe)
        if _DSb.co_mat_chu(ket):
            _DA_CAT.clear()
            ket = _ghep(_DSb.tran_boc_toi_da(STYLE_NGAN, co_the_co_mat_chu=True))
        return ket
    # Không import được `datastory_ci` — quay về mức dự phòng ĐẦY ĐỦ cho an toàn (đo thật
    # với `STYLE_NGAN`: 473 ký tự).
    return _ghep(473)


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


def sinh(ma: str, idx: int, i: int, ve: str, tam_trang: str = "", gu: str = "",
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
    #
    # ── 5/9/2026 — BỎ CỜ NHỚ RIÊNG, DÙNG THẲNG `_ai_candidates`  ────────────────────────
    # Cờ cũ chỉ nhớ "CF đã cạn" (đặt bởi `CanThat`, chỉ CF mới ném). Từ khi `sinh()` gọi
    # `DS._generate_image_ai` (hồ CF + Gemini gộp, xem dưới), hồ nào cạn cũng phải chặn —
    # và `datastory_ci._ai_candidates` đã tự nhớ khoá nào đang nghỉ (`_ve_chet`, có hạn),
    # tra trong bộ nhớ nên không tốn mạng. Giữ thêm một cờ sticky ở đây là NHỚ HAI LẦN
    # cùng một việc, và cờ sticky còn tệ hơn: khoá 429 hết nghỉ giữa tập vẫn bị khoá cứng.
    import datastory_ci as _DSc
    if not _DSc._ai_candidates(""):
        sinh._can = getattr(sinh, "_can", 0) + 1
        sinh._can_tap = getattr(sinh, "_can_tap", 0) + 1
        if sinh._can == 1:
            print(f"     🪫 nhịp {i}: cả hồ CF+Gemini đều cạn/đang nghỉ — từ đây các cảnh "
                  f"còn lại dùng nền vẽ bằng code (sẽ đếm tổng ở cuối tập)")
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
    _dv = _da_ve()                 # ĐỌC TỆP, không đọc biến — xem `_ANH_TEP`
    if _tran > 0 and _dv >= _tran:
        # ── IN MỘT LẦN MỖI TIẾN TRÌNH, KHÔNG MỘT LẦN MỖI TỆP ĐẾM  (5/9/2026) ────────────
        # Bản cũ in khi `_dv == _tran` rồi ghi +1 để khỏi in lại — tức câu này in đúng MỘT
        # lần trong cả đời tệp đếm, và mọi tiến trình sau đó câm tuyệt đối. Cộng với chuyện
        # tệp không bao giờ hết hạn ở máy anh, kết quả là: hàng chục lượt render liên tiếp
        # không có một ảnh AI nào và KHÔNG NÓI GÌ.
        # Một lượt dựng phải luôn khai được vì sao nó không có ảnh — đó là khác biệt giữa
        # "cạn hạn mức" (đi thêm khoá) và "chạm trần tự đặt" (đổi một biến môi trường).
        if not getattr(sinh, "_da_bao_tran", False):
            sinh._da_bao_tran = True
            print(f"     🎚 đã vẽ {_dv} ảnh AI trong lượt này (trần {_tran}) — các cảnh sau "
                  f"dùng lớp vẽ bằng code. Đặt TRAN_ANH_LUONG để đổi, hoặc xoá "
                  f"{_ANH_TEP} nếu đây là lượt mới.")
        return ""

    import datastory_ci as DS

    # (Đã bỏ seed: endpoint FLUX của CF trả HTTP 400 khi có `seed`. Khoá không còn xoay ở
    #  đây nữa — `_generate_image_ai` tự xoay theo hồ đã nạp ở `set_ai_pool` bên `sinh_tap`.)

    # ── 5/9/2026 — HỒ GỘP CF + GEMINI, KHÔNG CÒN RIÊNG CF  ──────────────────────────────
    # Anh: *"ảnh kết hợp cả cf + gemini nha"*. Cơ chế NÀY ĐÃ CÓ SẴN trong `datastory_ci.py`
    # (`set_ai_pool` + `_ai_candidates` + `_generate_image_ai`) và đang chạy thật ở nhiều
    # chỗ khác (`kich_hai.py`, `kich_v2.py`) — CF đứng trước (rẻ, ~172 ảnh/khoá/ngày), cạn
    # mới chạm Gemini (rộng hơn, ~500 ảnh/khoá/ngày, quota TÁCH RIÊNG khỏi khâu viết chữ,
    # và bộ này viết kịch bản 100% bằng code nên không tranh hạn mức với ai). Bộ giải thích
    # trước nay tự dựng một đường CHỈ-CF riêng (`goi_xoay`+`_cf_flux_image`) — đúng luật
    # 13.1/17.1: *"cơ chế đã có sẵn — hỏi cái gì CHẠY nó trước khi viết cái mới"*, nên nối
    # vào đường chung thay vì giữ hai đường song song (họ lỗi số 6, vá một nhánh để nguyên
    # nhánh kia). `set_ai_pool(keys, channel=ma)` được gọi Ở ĐẦU `sinh_tap()` — ở đây chỉ
    # cần gọi `_generate_image_ai(..., None, ...)` để nó DÙNG hồ đã nạp.

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
        if lan and not DS._ai_candidates(""):
            # Cạn NGAY TRONG lúc thử lại một cảnh (hồ vừa hết ở lượt trước) — nói một lần,
            # đừng gọi `_generate_image_ai` thêm để nó tự in một dòng cảnh báo trùng ý.
            sinh._can = getattr(sinh, "_can", 0) + 1
            if sinh._can == 1:
                print(f"     🪫 nhịp {i}: cả hồ CF+Gemini đều cạn/đang nghỉ — từ đây các cảnh "
                      f"còn lại dùng nền vẽ bằng code (sẽ đếm tổng ở cuối tập)")
            return ""
        ok = DS._generate_image_ai(_prompt(ve, tam_trang, gu, ma, doc, siet=_siet), dest,
                                    None, style=STYLE_NGAN) and os.path.getsize(dest) > 20000
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
        _ghi_da_ve(_da_ve() + 1)
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

    Chạy TUẦN TỰ chứ không song song: hồ khoá xoay theo trạng thái chung (`datastory_ci._AI_POOL`),
    chạy song song thì nhiều luồng cùng đâm vào một khoá đã 429 và cả mẻ hỏng theo. Chậm hơn nhưng đúng.
    """
    # NẠP HỒ CF+GEMINI MỘT LẦN MỖI TẬP (5/9/2026) — cửa DUY NHẤT `sinh()` đi qua để lấy khoá
    # là `datastory_ci._ai_candidates`/`_generate_image_ai`, và cả hai đọc từ `_AI_POOL` do
    # `set_ai_pool` nạp. Không gọi ở đây thì hồ rỗng, `_ai_candidates` luôn trả `[]`, và MỌI
    # cảnh của bộ giải thích rơi về nền vẽ code — đúng kiểu hỏng câm quen thuộc của bộ này.
    # Xoay theo TÊN KÊNH (giống 16 chỗ gọi khác) để 18 luồng song song không cùng bốc một khoá.
    try:
        import datastory_ci as _DSp
        _DSp.set_ai_pool(keys, ma)
    except Exception as _e:
        print(f"   ⚠ nạp hồ ảnh AI hỏng ({type(_e).__name__}: {str(_e)[:60]}) — "
              f"cảnh sẽ dùng nền vẽ bằng code")
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
        rel = sinh(ma, idx, i, ve, x.get("tam_trang", ""), gu, doc, moc)
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
            rel2 = sinh(ma, idx, i, ve, nhip[i].get("tam_trang", ""), gu, doc, moc)
            if rel2:
                nhip[i]["nenAnh"] = rel2
                _sd2 = sang_day(os.path.join(THU, os.path.basename(rel2)))
                if _sd2 >= 0:
                    nhip[i]["sangDay"] = _sd2
    # ── 5/9/2026 — BỎ LƯỢT XẢ `_QUAN_SAT`, ĐÃ TRỞ THÀNH LỆNH RỖNG ──────────────────────
    # Sổ này gom quan sát của `goi_xoay` (chỉ CF) rồi xả LÔ vào cuối tập. Từ khi `sinh()`
    # đổi sang `DS._generate_image_ai` (xem trên), khâu vẽ ảnh không còn gọi `goi_xoay` —
    # nó ghi trạng thái NGAY LÚC DÙNG, TỪNG KHOÁ MỘT, qua `datastory_ci.bao_key` ->
    # `firestore_bridge.mark_key_alive` (đúng hàm khắc `dead_since`/`dead_kind`, phân biệt
    # rõ "cạn hạn mức" với "chết hẳn" — điều mà lượt xả lô cũ KHÔNG làm, vì nó ghi thẳng
    # bằng `db.batch().set()` mà không đụng tới `dead_since`). Gọi `ghi_trang_thai` ở đây
    # giờ luôn gặp `_QUAN_SAT` rỗng và `return 0` câm lặng — giữ lại là giữ một lệnh chết.
    return n
