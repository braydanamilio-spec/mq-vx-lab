#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KHUNG CÂU HỎI — một kênh là MỘT LỜI HỨA chứa VÀI CHỤC khuôn nhỏ.  (7/9/2026)

── VÌ SAO KHÔNG PHẢI MỘT KÊNH MỘT KHUÔN ───────────────────────────────────────────────────
Bản thiết kế đầu của em gán mỗi kênh đúng một kiểu câu hỏi ("STILL MISSING" chỉ hỏi về thứ
mất tích). Anh bác: *"có thể cho vài chục nhóm nhỏ vào 1 channel cho đa dạng mở rộng"*.

Anh đúng, và luật YouTube đứng về phía anh. §13.18 đã đọc kỹ nguyên văn: luật KHÔNG cấm kênh
này giống kênh kia — nghìn kênh na ná nhau vẫn sống. Thứ nó cấm là **các video trong CÙNG
một kênh giống hệt nhau**, và thiếu bàn tay biên tập. Vài chục khuôn trong một kênh chính là
thứ luật ấy gọi là *meaningful variation*.

── NHƯNG LỜI HỨA PHẢI GIỮ ─────────────────────────────────────────────────────────────────
Một kênh đăng thứ gì cũng được thì không ai đăng ký. Nên kênh không định nghĩa bằng KHUÔN,
mà bằng LỜI HỨA: "thứ từng là tương lai rồi biến mất". Trong lời hứa ấy, hàng chục cách hỏi
đều hợp lệ, và người xem vẫn biết mình sẽ được xem gì.

Ba tầng, và mỗi tầng nhân lên tầng dưới:

    18 lời hứa  ×  ~24 khuôn hỏi mỗi lời hứa  ×  hồ chủ thể vô hạn

Khuôn viết TAY vì nó là NỘI DUNG chứ không phải cú pháp — ghép tự động từ tên trường sẽ ra
câu đúng ngữ pháp mà rỗng nghĩa, đúng bài học của `THEM_NHIP` trong `giai_thich`.
"""

# `{x}` = chủ thể. Mỗi khuôn là một CÁCH HỎI khác nhau về cùng một lời hứa, nên hai tập cùng
# chủ thể mà khác khuôn vẫn ra hai video khác hẳn nhau.
KHUNG = {
    "vanished": {
        "hua": "Thứ từng là tương lai, giờ không ai nhắc nữa",
        "khuon": [
            "Why {x} stopped being the future",
            "{x} was everywhere. Then it wasn't.",
            "What actually killed {x}",
            "The year {x} peaked, and nobody noticed",
            "{x} still exists. Almost nobody uses it.",
            "They promised {x} would change everything",
            "How much money died with {x}",
            "The last place on earth still running {x}",
            "{x} did not fail. It was replaced.",
            "Who owns {x} now",
            "The patent that outlived {x}",
            "What {x} looked like at its peak",
            "The one thing {x} got right",
            "Why nobody rebuilt {x}",
            "{x} came back. You missed it.",
            "The engineers who warned about {x}",
            "What replaced {x}, and what it cost",
            "{x} in the year it was born",
            "The museum where {x} ended up",
            "How close {x} came to working",
            "The country that kept {x}",
            "What {x} would cost today",
            "{x} and the decision that ended it",
            "Everyone forgot {x}. The data did not.",
        ],
    },
    "unsolved": {
        "hua": "Công nghệ đầy đủ mà vẫn không ai trả lời được",
        "khuon": [
            "GPS, radar, satellites — and {x} is still missing",
            "What the last signal from {x} said",
            "{x}: everything they found, and everything they did not",
            "The search for {x}, by the numbers",
            "How much has been spent looking for {x}",
            "Why {x} was never found",
            "The theory about {x} that will not die",
            "What {x} proves about our instruments",
            "{x}: the timeline nobody agrees on",
            "The witness accounts of {x} that conflict",
            "How long {x} has been open",
            "{x} and the evidence that went missing",
            "The one clue in {x} everyone skips",
            "What would have to be true for {x}",
            "{x}: what was ruled out, and why",
            "The people still looking for {x}",
            "{x} would be solved today. Here is why it isn't.",
            "The cost of never knowing about {x}",
            "{x} and the rule it broke",
            "What {x} changed about how we search",
            "The official report on {x}, in plain words",
            "{x}: three explanations, none complete",
            "Where {x} was last certain",
            "Why {x} still gets funded",
        ],
    },
}
