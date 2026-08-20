"""Bất biến 7 — dải kết quả phải được trình bày sao cho không ai đọc ra "quán quân".

`NGUYEN-TAC-DO-LUONG.md` mục 7: "Trong dải kết quả, dòng đáng tin nhất là
dòng có NHIỀU LỆNH NHẤT, không phải dòng lãi cao nhất."

Bản cũ của các script tối ưu in đủ 20 dòng rồi thêm một khối
"🏆 VÒNG LẶP TỐI ƯU XUẤT SẮC NHẤT" ở cuối. Người đọc chỉ nhớ khối cuối —
và đó đúng là cách ngưỡng 50,0 ra đời.
"""
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import dai_ket_qua as dk


# Dòng lãi cao nhất CỐ TÌNH có ít lệnh nhất — đúng bẫy mà bất biến 7 nói tới.
MAU = [
    {"threshold": 48.0, "closed": 1304, "pnl": 634.54, "win_rate": 28.2},
    {"threshold": 50.0, "closed": 1126, "pnl": 636.11, "win_rate": 29.1},
    {"threshold": 59.0, "closed": 365, "pnl": 62.32, "win_rate": 30.7},
    {"threshold": 62.0, "closed": 12, "pnl": 999.00, "win_rate": 50.0},
]


def test_sap_theo_so_lenh_khong_theo_lai():
    txt = dk.in_toan_dai(MAU)
    dong = [d for d in txt.splitlines() if "1304" in d or "1126" in d
            or "365" in d or " 12 " in d or "\t12" in d]
    assert dong, "không in ra dòng nào"
    # dòng nhiều lệnh nhất phải đứng trước dòng lãi cao nhất
    vi_tri_nhieu_lenh = txt.index("1304")
    vi_tri_lai_cao = txt.index("999")
    assert vi_tri_nhieu_lenh < vi_tri_lai_cao, (
        "dòng 12 lệnh lãi +999% đứng trước dòng 1304 lệnh — sắp theo lãi")
    print("PASS  dải sắp theo số lệnh giảm dần, không theo lợi nhuận")


def test_khong_dung_ngon_ngu_quan_quan():
    txt = dk.in_toan_dai(MAU).upper()
    # KHÔNG cấm cụm "cao nhất" ở đây: chính câu cảnh báo phải nói
    # "không phải dòng lãi cao nhất". Cấm nó ở đây là cấm lời cảnh báo.
    # Luật chặt hơn dành cho đầu ra của các script tối ưu — xem
    # test_khong_script_nao_in_quan_quan.
    for cam in ("QUÁN QUÂN", "XUẤT SẮC NHẤT", "TỐI ƯU NHẤT", "🏆", "BEST"):
        assert cam.upper() not in txt, f"vẫn còn ngôn ngữ quán quân: {cam!r}"
    print("PASS  không có dấu hiệu quán quân nào trong bảng dải")


def test_in_du_moi_dong():
    txt = dk.in_toan_dai(MAU)
    for r in MAU:
        assert str(r["closed"]) in txt, f"thiếu dòng {r['threshold']}"
    print("PASS  in đủ toàn dải, không lược bớt")


def test_co_canh_bao_bat_bien_7():
    txt = dk.in_toan_dai(MAU)
    assert "bất biến 7" in txt.lower() or "nhiều lệnh nhất" in txt.lower(), (
        "dải kết quả không kèm lời nhắc vì sao KHÔNG được lấy dòng lãi cao nhất")
    print("PASS  có cảnh báo bất biến 7 kèm dải")


def test_danh_dau_dong_dang_tin_nhat():
    txt = dk.in_toan_dai(MAU)
    dong_1304 = [d for d in txt.splitlines() if "1304" in d]
    assert dong_1304 and dk.DAU_DANG_TIN in dong_1304[0], (
        "dòng nhiều lệnh nhất không được đánh dấu")
    print("PASS  dòng nhiều lệnh nhất được đánh dấu là đáng tin nhất")


# ── Cổng chặn: không script tối ưu nào được in "quán quân" ───────────
# Dấu hiệu đề cử một dòng làm "kết quả". Cấm vô điều kiện: không lời
# cảnh báo tử tế nào cần in một cái cúp.
CAM_TUYET_DOI = ("QUÁN QUÂN", "XUẤT SẮC NHẤT", "TỐI ƯU NHẤT", "🏆",
                 "HIỆU SUẤT TỐT NHẤT", "VÒNG LẶP TỐT NHẤT")

# Cụm này hợp lệ khi nằm trong một câu CẢNH BÁO chống lại nó — ví dụ
# "dòng đáng tin nhất KHÔNG phải dòng lãi cao nhất". Chỉ cấm khi câu đó
# không mang dấu hiệu phủ định nào.
CAM_CO_DIEU_KIEN = ("CAO NHẤT",)
MIEN_TRU = ("KHÔNG", "ĐỪNG", "BẤT BIẾN", "ĐỌC TRƯỚC", "CẢNH BÁO")


def _chuoi_duoc_in(duong_dan):
    """Mọi hằng chuỗi trong file, gồm cả từng mảnh của f-string.

    Chỉ quét CHUỖI, không quét chú thích: một chú thích giải thích vì sao
    lệnh cấm tồn tại thì không phải vi phạm lệnh cấm.
    """
    import ast
    cay = ast.parse(duong_dan.read_text(encoding="utf-8"))

    # Docstring là TÀI LIỆU, không phải đầu ra. Một docstring giải thích
    # vì sao lệnh cấm tồn tại thì không vi phạm lệnh cấm.
    bo_qua = set()
    for n in ast.walk(cay):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)):
            than = getattr(n, "body", None)
            if (than and isinstance(than[0], ast.Expr)
                    and isinstance(than[0].value, ast.Constant)
                    and isinstance(than[0].value.value, str)):
                bo_qua.add(id(than[0].value))

    ra = []
    for n in ast.walk(cay):
        if (isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in bo_qua):
            ra.append((getattr(n, "lineno", 0), n.value))
    return ra


def test_khong_script_nao_in_quan_quan():
    """Bất biến 7 ở mức đầu ra: không dòng in nào được đề cử một dòng.

    Các script tối ưu vốn ĐÃ in đủ cả dải kèm số lệnh. Vấn đề là khối
    "🏆 VÒNG LẶP TỐI ƯU XUẤT SẮC NHẤT" thêm ở cuối — người đọc chỉ nhớ
    khối đó, và đó đúng là cách ngưỡng 50,0 được chọn.
    """
    vi_pham = []
    for f in sorted(list(GOC.glob("optimize_*.py")) + list(GOC.glob("evaluate_*.py"))):
        for dong, chuoi in _chuoi_duoc_in(f):
            hoa = chuoi.upper()
            for cam in CAM_TUYET_DOI:
                if cam in hoa:
                    vi_pham.append(f"{f.name}:{dong} {cam}")
            if any(m in hoa for m in MIEN_TRU):
                continue
            for cam in CAM_CO_DIEU_KIEN:
                if cam in hoa:
                    vi_pham.append(f"{f.name}:{dong} {cam}")
    assert not vi_pham, (
        "script toi uu dang de cu mot dong lam ket qua: "
        + " | ".join(vi_pham)
        + " -- dung tools/dai_ket_qua.in_toan_dai() thay cho khoi quan quan.")
    print("PASS  khong script toi uu nao in ngon ngu quan quan")


if __name__ == "__main__":
    for f in (test_sap_theo_so_lenh_khong_theo_lai, test_khong_dung_ngon_ngu_quan_quan,
              test_in_du_moi_dong, test_co_canh_bao_bat_bien_7,
              test_danh_dau_dong_dang_tin_nhat):
        f()
