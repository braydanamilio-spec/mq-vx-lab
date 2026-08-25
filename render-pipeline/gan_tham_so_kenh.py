# -*- coding: utf-8 -*-
"""Gắn THAM SỐ RIÊNG cho từng kênh — chống hai kênh cùng nguồn ra cùng một video."""
import io, json
p = "/Users/mrquyenbk/Documents/MM0 YOUTUBE 2026/render-pipeline/kenh_the_he_2.json"
ks = json.load(io.open(p, encoding="utf-8"))

TS = {
 "WHAT IS IN IT":     {"mon": "cereal", "xoay": "mon"},
 "RECALL PLATE":      {"kho": "thuc_pham", "xoay": "nam"},
 "CALORIE SHOCK":     {"mon": "pizza", "xoay": "mon"},
 "ONE STUDY":         {"tu_khoa": "sleep", "xoay": "tu_khoa"},
 "PILL FACTS":        {"kho": "thuoc", "xoay": "nam"},
 "PAYCHECK GAP":      {"chuoi": "luong_gio", "nhan": "Average hourly pay"},
 "RENT REALITY":      {"chuoi": "cpi_nha", "nhan": "Housing cost"},
 "PRICE OF NOW":      {"chuoi": "cpi_thucpham", "nhan": "Food price"},
 "COURT RECORD":      {"tu_khoa": "wrongful death", "xoay": "tu_khoa"},
 "SUED FOR THIS":     {"tu_khoa": "false advertising", "xoay": "tu_khoa"},
 "COLD FILE":         {"tu_khoa": "habeas corpus", "xoay": "tu_khoa"},
 "UNSOLVED LOG":      {"loc": "bi_an", "xoay": "ngay"},
 "MISSING PIECE":     {"loc": "mat_tich", "xoay": "ngay"},
 "DIAMOND NUMBERS":   {"nam": 2025},
 "COURT KINGS":       {"chi_tieu": "PTS", "mua": "2024-25"},
 "PAID VS PLAYED":    {"chi_tieu": "AST", "mua": "2024-25"},
 "AMERICA LOOKED UP": {"loc": "tat_ca", "xoay": "ngay"},
 "FAME CURVE":        {"loc": "nguoi", "xoay": "nguoi"},
 "SHOW NUMBERS":      {"tu_khoa": "detective", "loc": "moi", "xoay": "tu_khoa"},
 "GONE TOO SOON":     {"tu_khoa": "sci-fi", "loc": "da_huy", "xoay": "tu_khoa"},
 "SONG FILE":         {"tu_khoa": "one hit wonder", "xoay": "nghe_si"},
 "ONE HIT":           {"tu_khoa": "one hit wonder", "loc": "mot_hit", "xoay": "nghe_si"},
 "STEAM TRUTH":       {"loc": "dong_nhat"},
 "GAME GRAVEYARD":    {"loc": "chet_yeu"},
 "CAR RECALL":        {"hang": "ford", "dong": "f-150", "nam": 2020, "xoay": "hang"},
 "MPG TRUTH":         {"hang": "Toyota", "nam": 2024, "xoay": "hang"},
 "BREED FILE":        {"xoay": "giong"},
 "WILD NUMBERS":      {"ma": "AG.LND.FRST.ZS", "nhan": "Forest cover", "nam": 2022},
 "COST TO GO":        {"ma": "NY.GDP.PCAP.CD", "nhan": "Richest countries", "nam": 2023},
 "SKY RIGHT NOW":     {"vung": "usa"},
 "FILINGS SAY":       {"tu_khoa": "artificial intelligence"},
 "QUIET LAYOFFS":     {"tu_khoa": "reduction in force"},
 "REAL PLACE":        {"loc": "dia_diem", "xoay": "ngay"},
 "NIGHT SHIFT":       {"loc": "ca_dem", "xoay": "ngay"},
 "MARRIAGE MATH":     {"ma": "SP.DYN.TFRT.IN", "nhan": "Birth rate", "nam": 2022},
 "WHAT THEY SEARCH":  {"loc": "rieng_tu", "xoay": "ngay"},
 "SALARY TRUTH":      {"chuoi": "viec_lam", "nhan": "Jobs in America"},
 "JOB DYING":         {"chuoi": "that_nghiep", "nhan": "Unemployment"},
 "WHERE TO MOVE":     {"chuoi": "cpi_dien_nuoc", "nhan": "Utility cost"},
 "HOUSE MATH":        {"chuoi": "cpi_di_lai", "nhan": "Transport cost"},
 "ARCHIVE REEL":      {"tu_khoa": "america 1950", "xoay": "tu_khoa"},
 "THEN AND NOW":      {"tu_khoa": "city street", "xoay": "tu_khoa"},
 "NEAR EARTH":        {"xoay": "ngay"},
 "SPACE INVOICE":     {"de_tai": "space", "nam": 2024, "xoay": "nam"},
 "ALERT NOW":         {"bang": "TX", "xoay": "bang"},
 "QUAKE LOG":         {"do_lon": 6.5, "xoay": "nam"},
 "PENTAGON LEDGER":   {"de_tai": "ammunition", "nam": 2024, "xoay": "nam"},
 "WEAPON PRICE":      {"de_tai": "missile", "nam": 2024, "xoay": "nam"},
 "YOUR RIGHTS CASE":  {"tu_khoa": "first amendment", "xoay": "tu_khoa"},
 "DEGREE WORTH":      {"chuoi": "cpi_giao_duc", "nhan": "Education cost"},
}
thieu = [k["ten"] for k in ks if k["ten"] not in TS]
assert not thieu, f"chưa gắn tham số: {thieu}"
for k in ks:
    k["tham_so"] = TS[k["ten"]]

# chốt ngay tại đây: hai kênh CÙNG hàm mà CÙNG tham số = ra cùng một video
import collections
d = collections.defaultdict(list)
for k in ks:
    d[(k["ham"], json.dumps(k["tham_so"], sort_keys=True, ensure_ascii=False))].append(k["ten"])
trung = {kk: v for kk, v in d.items() if len(v) > 1}
assert not trung, f"kênh ra trùng nội dung: {list(trung.values())}"
io.open(p, "w", encoding="utf-8").write(json.dumps(ks, ensure_ascii=False, indent=1))
print(f"gắn tham số riêng cho {len(ks)} kênh · 0 cặp trùng nội dung")
