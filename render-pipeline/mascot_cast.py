#!/usr/bin/env python3
"""DÀN NHÂN VẬT + BỐI CẢNH của 5 kênh hoạt hình (slot 56-60, dựng 25/8/2026).

Đây là bộ mascot đã chốt hồi 22/8 (xem TOON_CONCEPT.md) nhưng phải xếp lại vì cách vẽ cũ làm
nhân vật TRÔI giữa các khung. Nay quay lại bằng cơ chế rig (mascot_rig.py): vẽ một lần, diễn mãi.

BA HẰNG SỐ KHÔNG ĐƯỢC ĐỔI SAU KHI ĐÃ DỰNG RIG
---------------------------------------------
`style`, `mo_ta`, `id` của mỗi nhân vật là KHOÁ NHẬN DIỆN. Sửa một chữ rồi dựng lại rig là ra một
nhân vật khác — khán giả thấy ngay. Muốn đổi tạo hình thì đổi hẳn kênh, đừng sửa tại chỗ.

BỐI CẢNH NHIỀU LỚP (multiplane)
--------------------------------
`nen_lop` liệt kê các lớp sâu theo thứ tự XA -> GẦN. Mỗi lớp là một lệnh vẽ riêng trên nền xanh
khoá, để `MascotStage` trượt chúng ở tốc độ khác nhau — đúng nguyên lý camera đa tầng của phim 2D.
Lớp `sky` KHÔNG tách nền (nó là nền dưới cùng, phủ kín khung).
"""
from __future__ import annotations

# Tư thế nào của nhân vật nào được coi là "đang nói" — MascotStage nhép mồm bằng cặp này.
CAP_NHEP_MOM = ("talk_closed", "talk_open")

CAST: dict[str, list[dict]] = {
    # ── 56 · EAGLEBANDIT — cặp đôi lệch pha biểu tượng Mỹ ────────────────────────────────
    "EAGLEBANDIT": [
        {"id": "BALD", "vai": "A",
         "mo_ta": "a grumpy proud bald eagle standing upright like a person, wearing a "
                  "stars-and-stripes necktie, stern serious face, white head feathers, yellow beak",
         "style": "modern bold flat vector cartoon, thick black outlines, saturated red white and "
                  "blue accents, clean shapes, no gradients"},
        {"id": "BANDIT", "vai": "B",
         "mo_ta": "a scruffy sly raccoon standing upright like a person, wearing red sunglasses, "
                  "holding a red soda cup, smirking, grey fur with black mask marking",
         "style": "modern bold flat vector cartoon, thick black outlines, saturated red white and "
                  "blue accents, clean shapes, no gradients"},
    ],
    # ── 57 · HANKYARD — ngoại ô Mỹ retro 50-60 ───────────────────────────────────────────
    "HANKYARD": [
        {"id": "HANK", "vai": "A",
         "mo_ta": "a burly friendly middle-aged american dad with a thick brown mustache, red plaid "
                  "flannel shirt and a beige trucker cap, warm confident face",
         "style": "retro 1950s american advertising cartoon, mid-century UPA animation look, "
                  "halftone print texture, mustard and avocado retro palette, thick brush outlines"},
        {"id": "DALE", "vai": "B",
         "mo_ta": "a nosy skinny neighbor man with round glasses, thin hair, green polo shirt, "
                  "leaning forward curiously with a knowing grin",
         "style": "retro 1950s american advertising cartoon, mid-century UPA animation look, "
                  "halftone print texture, mustard and avocado retro palette, thick brush outlines"},
    ],
    # ── 58 · PEARLPORCH — bà hàng xóm nhiều chuyện mà tốt bụng ───────────────────────────
    "PEARLPORCH": [
        {"id": "PEARL", "vai": "A",
         "mo_ta": "a friendly nosy middle-aged woman with a high grey hair bun, red cardigan over a "
                  "cream blouse, holding a tall glass of iced tea, warm gossipy expression",
         "style": "modern bold flat cartoon, cream and deep red palette with charcoal outlines, "
                  "soft rounded shapes, clean vector look"},
    ],
    # ── 59 · BISONDESK — giáo sư bò rừng kể sử ngớ ngẩn mà có thật ──────────────────────
    "BISONDESK": [
        {"id": "BISON", "vai": "A",
         "mo_ta": "a scholarly american bison standing upright like a professor, wearing round "
                  "spectacles and a tricorn hat, brown shaggy fur, holding a rolled parchment",
         "style": "vintage woodcut engraving cartoon, sepia parchment tones, fine ink hatching, "
                  "aged paper texture, brown and cream palette"},
    ],
    # ── 60 · OWLOFFICE — cú công sở giải thích hệ thống Mỹ, mặt lạnh ────────────────────
    "OWLOFFICE": [
        {"id": "OWL", "vai": "A",
         "mo_ta": "a deadpan office owl standing upright, wearing a navy necktie, holding a "
                  "clipboard, large unimpressed yellow eyes, brown and cream feathers",
         "style": "minimal clean vector cartoon, pale blue-gray and navy palette with one red "
                  "accent, flat shapes, thin confident outlines, lots of negative space"},
    ],
}

# Bối cảnh nhiều lớp cho từng kênh. Mỗi mục là một "sân khấu" dùng lại cho nhiều skit — vẽ một
# lần rồi dùng mãi, y như nhân vật. Skit chỉ chọn sân khấu phù hợp, không đẻ nền mới mỗi lần.
SAN_KHAU: dict[str, dict[str, list[dict]]] = {
    "EAGLEBANDIT": {
        "fastfood": [
            {"lop": "sky",  "xa": 0.02, "mo_ta": "flat blue american sky with a few simple clouds, empty, no ground"},
            {"lop": "far",  "xa": 0.10, "mo_ta": "row of distant suburban rooftops and a water tower silhouette"},
            {"lop": "mid",  "xa": 0.35, "mo_ta": "a generic fast food restaurant storefront with a striped awning, no lettering"},
            {"lop": "near", "xa": 0.85, "mo_ta": "a parking lot curb with a trash bin and a lamp post, foreground props"},
        ],
        "dmv": [
            {"lop": "sky",  "xa": 0.02, "mo_ta": "flat pale office ceiling with fluorescent light panels"},
            {"lop": "far",  "xa": 0.10, "mo_ta": "government office back wall with a blank notice board and a wall clock"},
            {"lop": "mid",  "xa": 0.35, "mo_ta": "a service counter with a number display and a queue rope"},
            {"lop": "near", "xa": 0.85, "mo_ta": "a row of plastic waiting chairs seen from behind, foreground"},
        ],
    },
    "HANKYARD": {
        "backyard": [
            {"lop": "sky",  "xa": 0.02, "mo_ta": "warm afternoon suburban sky with soft retro clouds"},
            {"lop": "far",  "xa": 0.10, "mo_ta": "distant treeline and neighboring house roofs"},
            {"lop": "mid",  "xa": 0.35, "mo_ta": "a white picket fence across the frame with a garden hose reel"},
            {"lop": "near", "xa": 0.85, "mo_ta": "a barbecue grill and a folding lawn chair, foreground props"},
        ],
        "garage": [
            {"lop": "sky",  "xa": 0.02, "mo_ta": "plain garage back wall with pegboard, empty"},
            {"lop": "far",  "xa": 0.10, "mo_ta": "shelves with paint cans and cardboard boxes"},
            {"lop": "mid",  "xa": 0.35, "mo_ta": "a workbench with scattered tools and a vise"},
            {"lop": "near", "xa": 0.85, "mo_ta": "an open toolbox and a coiled extension cord, foreground"},
        ],
    },
    "PEARLPORCH": {
        "porch": [
            {"lop": "sky",  "xa": 0.02, "mo_ta": "soft cream evening sky, warm light"},
            {"lop": "far",  "xa": 0.10, "mo_ta": "quiet neighborhood street with distant houses and a mailbox"},
            {"lop": "mid",  "xa": 0.35, "mo_ta": "a front porch railing with hanging flower baskets"},
            {"lop": "near", "xa": 0.85, "mo_ta": "a porch swing edge and a small side table with a pitcher, foreground"},
        ],
    },
    "BISONDESK": {
        "study": [
            {"lop": "sky",  "xa": 0.02, "mo_ta": "aged parchment wall texture, warm sepia, empty"},
            {"lop": "far",  "xa": 0.10, "mo_ta": "tall bookshelf filled with old leather books, engraved style"},
            {"lop": "mid",  "xa": 0.35, "mo_ta": "a heavy wooden desk with an inkwell and a candle"},
            {"lop": "near", "xa": 0.85, "mo_ta": "stacked old books and a rolled map in the foreground"},
        ],
    },
    "OWLOFFICE": {
        "cubicle": [
            {"lop": "sky",  "xa": 0.02, "mo_ta": "plain pale blue-gray office wall, empty, minimal"},
            {"lop": "far",  "xa": 0.10, "mo_ta": "row of empty cubicle dividers receding, minimal vector"},
            {"lop": "mid",  "xa": 0.35, "mo_ta": "a desk with a monitor, a mug and a stack of paper trays"},
            {"lop": "near", "xa": 0.85, "mo_ta": "an office chair back and a potted plant, foreground"},
        ],
    },
}


def cast_cua(kenh: str) -> list[dict]:
    return CAST.get(str(kenh).upper(), [])


def san_khau_cua(kenh: str, ten: str = "") -> list[dict]:
    """Lớp nền của một sân khấu. `ten` rỗng -> lấy sân khấu đầu tiên của kênh."""
    bo = SAN_KHAU.get(str(kenh).upper()) or {}
    if not bo:
        return []
    return bo.get(ten) or list(bo.values())[0]


def ten_san_khau(kenh: str) -> list[str]:
    return list((SAN_KHAU.get(str(kenh).upper()) or {}).keys())
