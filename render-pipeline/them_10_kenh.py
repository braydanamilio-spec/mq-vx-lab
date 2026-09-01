#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ĐĂNG KÝ 10 KÊNH HÀI MỚI — cùng khuôn với 10 kênh đang chạy (1/9/2026)

Anh: *"làm giống 10 funny channel đã thành công đang render, dài 15-20s"*.

Nên KHÔNG phải định dạng 6 giây của gói GROCK (anh đã loại), KHÔNG nhân vật phi nhân (anh đã
loại). Đúng khuôn `KichComic` đang chạy: hai người, va chạm đời thường kiểu Mỹ, 6 panel,
11–19 giây.

Mười chủ đề mới không trùng mười chủ đề cũ (thuê nhà · gym · sân bay · sửa xe · văn phòng ·
ăn kiêng · hỗ trợ kỹ thuật · nuôi con · hàng xóm · vợ chồng).

Tệp này ghi vào ĐỦ BẢNG trong một lượt — bài học từ lần trước: thêm kênh mà quên một bảng thì
nó hỏng ở chỗ không ai ngờ, và hỏng im lặng.
    kich_hai.KENH · kich_comic.{VAI,GIONG_KENH,NET_KENH,BO_CUC_KENH,LOI_VE_KENH,
                                MAU_CHINH,MAU_PHU,NHAC} · noi_chon.json · nen_cf.PHONG_CACH
"""
import io
import json
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))

# de, tên, handle, kiểuA, kiểuB, màu nền dự phòng
# VAI: (kiểu, giới, tuổi, cao, vai VN, vai EN)
# Chiều cao theo quan hệ thật: người có quyền/lớn tuổi thường cao hơn trong khung, trẻ thấp hơn.
KENH_MOI = [
    dict(de="dmv", ten="DMV LINE", handle="@dmvlineusa", mau="#E7E2D4",
         a=("luat_tre", "nam", "tre", 0.97, "người xin bằng", "the applicant"),
         b=("bank", "nu", "trung", 0.93, "nhân viên DMV", "the clerk"),
         net=dict(net=6, cham=15, bo=16, tile=0.46), bc=dict(duoi=False, bo=8, no="UGH!"),
         ve="goc_canh", m1="#3C6E9F", m2="#D9803C", nhac="music/broke_pad.mp3",
         noi=["the DMV counter", "the waiting area", "the photo booth", "the eye test station",
              "the number ticket machine", "the parking lot outside", "the form table",
              "the payment window", "the road test desk", "the DMV entrance"],
         pc="drab government office, beige and pale green, flat fluorescent light, worn counters"),
    dict(de="erbill", ten="ER BILLING", handle="@erbillingusa", mau="#EAF0F2",
         a=("khoa_hoc", "nu", "trung", 0.93, "bệnh nhân", "the patient"),
         b=("cong_to", "nam", "trung", 1.02, "nhân viên thu ngân", "the billing rep"),
         net=dict(net=8, cham=6, bo=22, tile=0.49), bc=dict(duoi=True, bo=14, no="OOPS!"),
         ve="mat_to", m1="#2E8B84", m2="#D4553F", nhac="music/km_ossuary_air.mp3",
         noi=["the billing window", "the hospital waiting room", "the discharge desk",
              "the insurance office", "the pharmacy counter", "the hallway by triage",
              "the payment kiosk", "the records office", "the front reception", "the exit corridor"],
         pc="clinical hospital interior, cool white and mint, even bright light, clean surfaces"),
    dict(de="hoa", ten="HOA RULES", handle="@hoarulesusa", mau="#EFE9DC",
         a=("hang_xom", "nam", "trung", 1.04, "chủ nhà", "the homeowner"),
         b=("cong_to", "nu", "trung", 0.94, "trưởng ban khu phố", "the HOA chair"),
         net=dict(net=10, cham=12, bo=4, tile=0.45), bc=dict(duoi=False, bo=0, no="WHAT?!"),
         ve="net_manh", m1="#7A4FA3", m2="#5FA355", nhac="music/km_impact_andante.mp3",
         noi=["the front lawn", "the driveway", "the mailbox row", "the community pool",
              "the clubhouse meeting room", "the sidewalk out front", "the fence line",
              "the garage door", "the front porch", "the neighborhood entrance"],
         pc="tidy American suburb exterior, pale siding and green lawn, bright midday light"),
    dict(de="ret", ten="RETURN POLICY", handle="@returnpolicyusa", mau="#F2E7DB",
         a=("sao_dem", "nu", "tre", 0.93, "khách trả hàng", "the shopper"),
         b=("tham_phan", "nam", "gia", 1.01, "quản lý cửa hàng", "the store manager"),
         net=dict(net=5, cham=16, bo=26, tile=0.50), bc=dict(duoi=True, bo=20, no="NOPE."),
         ve="mat_to", m1="#C7522A", m2="#3B7A57", nhac="music/km_ossuary_rest.mp3",
         noi=["the returns counter", "the customer service desk", "the checkout lane",
              "the aisle by electronics", "the store entrance", "the stockroom door",
              "the fitting room area", "the manager's office", "the receipt printer", "the exit doors"],
         pc="big-box retail interior, grey shelving and warm signage light, wide aisles"),
    dict(de="wed", ten="WEDDING PLAN", handle="@weddingplanusa", mau="#F6E9EE",
         a=("bank", "nu", "trung", 0.94, "cô dâu", "the bride"),
         b=("hang_xom", "nam", "trung", 1.05, "nhà cung cấp", "the vendor"),
         net=dict(net=7, cham=6, bo=36, tile=0.47), bc=dict(duoi=False, bo=26, no="HUH?"),
         ve="mat_to", m1="#C2557E", m2="#4A7FA8", nhac="music/km_long_note_four.mp3",
         noi=["the venue hall", "the tasting table", "the florist counter", "the dress fitting room",
              "the cake display", "the outdoor ceremony lawn", "the planning office",
              "the reception setup", "the chapel entrance", "the vendor booth"],
         pc="soft romantic venue interior, blush and cream, warm string lights, airy space"),
    dict(de="mov", ten="MOVING DAY", handle="@movingdayusa", mau="#EDE4D2",
         a=("cong_to", "nam", "trung", 1.03, "khách", "the customer"),
         b=("luat_tre", "nam", "tre", 0.98, "thợ chuyển nhà", "the mover"),
         net=dict(net=9, cham=15, bo=18, tile=0.44), bc=dict(duoi=True, bo=4, no="THUD!"),
         ve="goc_canh", m1="#B5622B", m2="#2F6FA8", nhac="music/carefree_tram.mp3",
         noi=["the empty living room", "the moving truck ramp", "the front doorway",
              "the stairwell landing", "the packed garage", "the curb outside",
              "the hallway full of boxes", "the empty bedroom", "the kitchen with boxes",
              "the elevator lobby"],
         pc="half-empty American home mid-move, bare walls, cardboard boxes at the edges, daylight"),
    dict(de="vet", ten="VET VISIT", handle="@vetvisitusa", mau="#E6F0E8",
         a=("khoa_hoc", "nu", "trung", 0.92, "chủ thú cưng", "the pet owner"),
         b=("tham_phan", "nam", "gia", 1.02, "bác sĩ thú y", "the vet"),
         net=dict(net=6, cham=12, bo=24, tile=0.50), bc=dict(duoi=False, bo=18, no="GASP!"),
         ve="mat_to", m1="#3E8F5E", m2="#D9A441", nhac="music/forecast_tram.mp3",
         noi=["the exam room", "the vet waiting area", "the reception desk", "the scale corner",
              "the treatment table", "the pet food shelf", "the kennel hallway",
              "the payment counter", "the clinic entrance", "the grooming station"],
         pc="friendly veterinary clinic, soft green and light wood, warm even light"),
    dict(de="cab", ten="CABLE BILL", handle="@cablebillusa", mau="#E4E8F0",
         a=("hang_xom", "nam", "trung", 1.03, "thuê bao", "the subscriber"),
         b=("sao_dem", "nu", "tre", 0.92, "nhân viên giữ khách", "the retention agent"),
         net=dict(net=11, cham=9, bo=16, tile=0.46), bc=dict(duoi=False, bo=10, no="CLICK!"),
         ve="net_manh", m1="#2F6FA8", m2="#E0803C", nhac="music/km_ascending_tram.mp3",
         noi=["the living room with the TV", "the cable box shelf", "the home office desk",
              "the call center row", "the router corner", "the retention desk",
              "the apartment living room", "the service counter", "the wall of screens",
              "the front hallway"],
         pc="ordinary American living room and call-center desk, cool grey-blue, screen glow"),
    dict(de="sch", ten="SCHOOL RUN", handle="@schoolrunusa", mau="#F0EBDA",
         a=("bank", "nu", "trung", 0.94, "phụ huynh", "the parent"),
         b=("cong_to", "nu", "trung", 0.95, "giáo viên", "the teacher"),
         net=dict(net=4, cham=8, bo=30, tile=0.48), bc=dict(duoi=True, bo=24, no="BELL!"),
         ve="mat_to", m1="#D9803C", m2="#3B7A57", nhac="music/inspired_tram.mp3",
         noi=["the classroom door", "the school hallway", "the pickup line curb",
              "the front office", "the gymnasium", "the cafeteria", "the playground fence",
              "the parent teacher table", "the school entrance", "the bus loading zone"],
         pc="American elementary school interior, warm cream walls, bulletin boards, daylight"),
    dict(de="chk", ten="SELF CHECKOUT", handle="@selfcheckoutusa", mau="#E9EDE6",
         a=("luat_tre", "nam", "tre", 0.96, "khách", "the shopper"),
         b=("khoa_hoc", "nu", "trung", 0.93, "nhân viên siêu thị", "the store attendant"),
         net=dict(net=8, cham=16, bo=6, tile=0.51), bc=dict(duoi=False, bo=0, no="BEEP-BEEP!"),
         ve="goc_canh", m1="#4C8C4A", m2="#C4453A", nhac="music/km_undaunted_tram.mp3",
         noi=["the self checkout station", "the grocery aisle", "the produce section",
              "the bagging area", "the store entrance", "the customer service point",
              "the freezer aisle", "the cart corral", "the receipt printer", "the exit lane"],
         pc="American grocery store interior, bright white light, colourful shelves at the edges"),
]


def _chen(tep: str, ten_bang: str, dong_moi: str) -> bool:
    """Chèn một dòng vào cuối bảng dict, ngay TRƯỚC dấu `}` khớp cặp.

    Bản đầu dùng regex `^TEN\s*[:=][^=]*=?\s*\{` rồi tìm `"\n}"`. Hai lỗi:
      · `[^=]*` THAM LAM nên nuốt qua cả bảng tới dấu `=` kế tiếp ở đâu đó phía dưới;
      · hai bảng `MAU_CHINH`/`MAU_PHU` đóng ngoặc NGAY SAU giá trị cuối (`…"#E0367A"}`), không
        có `}` ở cột 0 — nên tìm `"\n}"` là hụt.
    Nay đếm cặp ngoặc, không đoán định dạng.
    """
    p = os.path.join(GOC, tep)
    s = io.open(p, encoding="utf-8").read()
    m = re.search(rf"^{ten_bang}\s*=\s*\{{", s, re.M)
    if not m:
        print(f"   ⚠️ không thấy bảng {ten_bang} trong {tep}")
        return False
    sau, i = 1, m.end()
    while i < len(s) and sau:
        if s[i] == "{":
            sau += 1
        elif s[i] == "}":
            sau -= 1
        i += 1
    dong = i - 1                                    # vị trí dấu } đóng
    khoa = dong_moi.strip().split(":")[0]
    if khoa in s[m.end():dong]:
        return False
    # chèn trước dấu đóng, giữ nguyên thụt lề của dòng chứa nó
    truoc = s[:dong].rstrip()
    if not truoc.endswith(","):
        truoc += ","
    s = truoc + "\n" + dong_moi.rstrip() + "\n" + s[dong:]
    io.open(p, "w", encoding="utf-8").write(s)
    return True


def main() -> int:
    from kich_hai import SAN_NEN
    n = 0

    # ── 1. bảng KENH trong kich_hai.py ──────────────────────────────────────────────────
    p = os.path.join(GOC, "kich_hai.py")
    s = io.open(p, encoding="utf-8").read()
    them = []
    for k in KENH_MOI:
        if f'"de": "{k["de"]}"' in s:
            continue
        nen = [f"{noi}, {SAN_NEN}" for noi in k["noi"][:4]]
        them.append("    " + json.dumps(
            {"ten": k["ten"], "handle": k["handle"], "a": k["a"][0], "b": k["b"][0],
             "mau": k["mau"], "de": k["de"], "nen": nen}, ensure_ascii=False) + ",")
    if them:
        m = re.search(r"^KENH\s*=\s*\[", s, re.M)
        j = s.index("\n]", m.end())
        s = s[:j] + "\n" + "\n".join(them) + s[j:]
        io.open(p, "w", encoding="utf-8").write(s)
        n += len(them)
        print(f"  ✓ kich_hai.KENH  +{len(them)} kênh")

    # ── 2. các bảng trong kich_comic.py ─────────────────────────────────────────────────
    for k in KENH_MOI:
        de = k["de"]
        _chen("kich_comic.py", "VAI",
              f'    "{de}": ({json.dumps(k["a"], ensure_ascii=False)},\n'
              f'             {json.dumps(k["b"], ensure_ascii=False)}),'.replace("[", "(").replace("]", ")"))
        _chen("kich_comic.py", "NET_KENH",
              f'    "{de}": dict(net={k["net"]["net"]}, cham={k["net"]["cham"]}, '
              f'bo={k["net"]["bo"]}, tile={k["net"]["tile"]}),')
        _chen("kich_comic.py", "BO_CUC_KENH",
              f'    "{de}": dict(duoi={k["bc"]["duoi"]}, bo={k["bc"]["bo"]}, no="{k["bc"]["no"]}"),')
        _chen("kich_comic.py", "LOI_VE_KENH", f'    "{de}": "{k["ve"]}",')
        _chen("kich_comic.py", "MAU_CHINH", f'    "{de}": "{k["m1"]}",')
        _chen("kich_comic.py", "MAU_PHU", f'    "{de}": "{k["m2"]}",')
        _chen("kich_comic.py", "NHAC", f'    "{de}": "{k["nhac"]}",')
    print("  ✓ kich_comic: VAI · NET_KENH · BO_CUC_KENH · LOI_VE_KENH · MAU_CHINH · MAU_PHU · NHAC")

    # ── 3. nơi chốn ─────────────────────────────────────────────────────────────────────
    p = os.path.join(GOC, "noi_chon.json")
    d = json.load(io.open(p, encoding="utf-8"))
    for k in KENH_MOI:
        d.setdefault(k["de"], k["noi"])
    io.open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
    print(f"  ✓ noi_chon.json  ({len(KENH_MOI)} kênh × 10 nơi)")

    # ── 4. phong cách nền ───────────────────────────────────────────────────────────────
    for k in KENH_MOI:
        _chen("nen_cf.py", "PHONG_CACH", f'    "{k["de"]}": "{k["pc"]}",')
    print("  ✓ nen_cf.PHONG_CACH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
