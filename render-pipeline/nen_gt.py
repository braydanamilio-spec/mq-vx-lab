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
    r"beach|mountain|snow|lawn|yard|driveway|kerb|curb|sidewalk|space|moon|planet|stars|"
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
GU_CARTOON = (
    "flat 2D cartoon illustration, thick uniform black outlines, large areas of solid flat "
    "colour, no gradients, no texture, crisp vector edges, bright saturated palette, "
    "stick-figure people with plain round white heads, two dot eyes, a simple line mouth and "
    "thin black limbs, modern animated explainer look, not photorealistic, not 3D"
)
# Neo bối cảnh Mỹ — chỉ giữ những vật CHỈ CÓ Ở MỸ và mô hình vẽ được. "Cảm giác Mỹ" thì nó
# không vẽ được; "hòm thư trên cột cắm ở lề" thì vẽ được.
GU_USA = ("set in the United States: clapboard suburban houses with a front porch, a mailbox "
          "on a post at the kerb, wide two-lane roads, American kitchen with an island; "
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


def _prompt(ve: str, tam_trang: str = "", gu: str = "", ma: str = "", doc: bool = False) -> str:
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
    phan = [
        ((gu or GU) + ", " + _sac_thai(ma)).rstrip(", ") + ".",   # 1. phong cách + sắc thái riêng
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
        "a flat cartoon drawing of " + ve + mt + ",",
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
        if len(thu) > 2048:
            break                  # cắt từ đuôi: vế càng sau càng ít quan trọng
        ra = thu
    return ra


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
    if os.path.exists(dest) and os.path.getsize(dest) > 20000:
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
    for lan in range(4):
        seed = (hat0 + lan * 104729) % 4294967295

        def _thu(kk):
            return DS._cf_flux_image(_prompt(ve, tam_trang, gu, ma, doc), dest, kk) and \
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
        _xau = _d is not None and (_d < SAN_PHANG or
                                   (moc is not None and abs(_d - moc) > NGUONG_LECH))
        if _xau:
            if lan < 3:
                os.remove(dest)
                continue          # -> vẽ lại
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
                continue          # -> vẽ lại bằng seed khác
        except Exception as e:
            # NÓI RA khi cổng tắt. Một cổng hỏng mà im lặng còn tệ hơn không có cổng: nó cho
            # cả mẻ đi qua kèm cảm giác đã được kiểm. Chỉ báo MỘT lần mỗi lần chạy — báo mỗi
            # cảnh thì 15 dòng giống nhau lại thành nhiễu, và nhiễu cũng là một kiểu im lặng.
            if not getattr(sinh, "_da_bao", False):
                sinh._da_bao = True
                print(f"     ⚠ CỔNG CHỮ TẮT ({type(e).__name__}: {str(e)[:60]}) — "
                      f"ảnh có chữ bịa sẽ lọt qua")
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
    for _t in ("_can", "_hong", "_het"):
        if hasattr(sinh, _t):
            delattr(sinh, _t)
    n = 0
    moc = None      # mốc chất ảnh của tập — đặt bằng TRUNG VỊ ba ảnh đầu (xem dưới)
    _mau = []       # ba số đo đầu, để lấy trung vị
    _dau = []       # (chỉ số nhịp, prompt) của những ảnh vẽ TRƯỚC khi có mốc
    for i, x in enumerate(nhip):
        ve = x.get("ve") or ""
        if not ve:
            continue
        rel = sinh(ma, idx, i, ve, keys, x.get("tam_trang", ""), gu, doc, moc)
        if rel:
            x["nenAnh"] = rel
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
            if mau_chu and mau_nen:
                try:
                    from to_mau import to_mau as _tm
                    _tm(duong, mau_chu, mau_nen)
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
    # Ghi sổ sức khoẻ khoá TỪ LƯỢT DÙNG THẬT — xem `xoay_key.ghi_trang_thai`.
    # Đặt ở cuối tập, không đặt sau mỗi ảnh: mỗi tập một lượt ghi lô thay vì hàng trăm.
    try:
        import xoay_key as _XK
        _XK.ghi_trang_thai(os.environ.get("OWNER_UID", ""))
    except Exception:
        pass
    return n
