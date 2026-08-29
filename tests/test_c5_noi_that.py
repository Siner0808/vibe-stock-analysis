"""Trạng thái ô C5 in ra báo cáo phải SUY RA từ cờ, không viết cứng.

VÌ SAO CÓ FILE NÀY
──────────────────
Từ 24/08/2026 tới 29/08/2026 cổng C5 MỞ, nhưng mọi báo cáo phiên vẫn in
"⛔ DỪNG mở vị thế mới (ô C5)" — chuỗi đó viết cứng trong template. Lượt
quét 28/08/2026 21:13 mở 4 lệnh (NAF, STB, TCB, HUT) và báo cáo của
chính lượt đó vẫn nói đang dừng mở vị thế mới.

Không ai gian lận. Cờ đổi ở `paper_trading.py`, câu chữ nằm ở
`run_daily.py`, và không có gì buộc hai chỗ đi cùng nhau. Đây là file
buộc chúng đi cùng nhau.

Ba tầng khoá:
  1. hàm `trang_thai_c5` trả đúng hai nhánh;
  2. template KHÔNG chứa chuỗi trạng thái viết cứng nào;
  3. template CÓ nội suy hai biến do hàm đó sinh ra.

Tầng 2 và 3 dùng AST chứ không dùng `in src`: một dòng chú thích nhắc
tới "DỪNG mở vị thế mới" sẽ làm phép kiểm bằng chuỗi kêu oan, và một
phép kiểm hay kêu oan thì sớm muộn bị nới ra cho hết kêu.
"""
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import run_daily as rd  # noqa: E402

GOC = Path(__file__).resolve().parent.parent


def _cay(ten_file: str) -> ast.Module:
    return ast.parse((GOC / ten_file).read_text(encoding="utf-8"))


def _ham(cay: ast.Module, ten: str) -> ast.FunctionDef:
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"không tìm thấy hàm {ten}")


def test_cong_MO_thi_bao_cao_noi_MO():
    dong, khoi = rd.trang_thai_c5(True, 62.0)
    assert "MỞ" in dong and "DỪNG" not in dong, dong
    assert "62.0" in dong, dong
    assert "MỞ" in khoi, khoi
    print(f"PASS  cờ bật -> {dong}")


def test_cong_DONG_thi_bao_cao_noi_DONG():
    dong, khoi = rd.trang_thai_c5(False, 62.0)
    assert "ĐÓNG" in dong and "DỪNG" in dong, dong
    assert "alpha" in khoi, khoi
    print(f"PASS  cờ tắt -> {dong}")


def test_hai_nhanh_KHONG_duoc_giong_nhau():
    """Một hàm trả cùng một câu cho cả hai nhánh thì bằng viết cứng."""
    assert rd.trang_thai_c5(True, 62.0) != rd.trang_thai_c5(False, 62.0)
    print("PASS  hai nhánh khác nhau")


def test_template_KHONG_viet_cung_trang_thai_C5():
    """Không hằng chuỗi nào trong `execute_daily_scan` tự khẳng định C5."""
    ham = _ham(_cay("run_daily.py"), "execute_daily_scan")
    xau = []
    for n in ast.walk(ham):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            xau.append(n.value)
        elif isinstance(n, ast.JoinedStr):
            xau += [p.value for p in n.values
                    if isinstance(p, ast.Constant) and isinstance(p.value, str)]

    CAM = ("DỪNG mở vị thế mới", "ngưỡng mua đang ĐỂ", "Ô C5 đang MỞ")
    pham = [(c, s[:70]) for s in xau for c in CAM if c.lower() in s.lower()]
    assert not pham, f"trạng thái C5 viết cứng trong template: {pham}"
    print(f"PASS  {len(xau)} hằng chuỗi, không cái nào tự khẳng định C5")


def test_template_CO_noi_suy_hai_bien_trang_thai():
    """Không viết cứng thì cũng phải thật sự DÙNG kết quả của hàm."""
    ham = _ham(_cay("run_daily.py"), "execute_daily_scan")
    ten = set()
    for n in ast.walk(ham):
        if isinstance(n, ast.JoinedStr):
            for p in n.values:
                if isinstance(p, ast.FormattedValue):
                    ten |= {x.id for x in ast.walk(p.value)
                            if isinstance(x, ast.Name)}
    for can in ("_trang_thai_c5", "_giai_thich_c5"):
        assert can in ten, f"template không nội suy {can} (có: {sorted(ten)})"
    print("PASS  template nội suy cả hai biến trạng thái")


def test_ham_duoc_goi_bang_thuoc_tinh_module():
    """`from paper_trading import CHO_PHEP...` sẽ đóng băng giá trị lúc nạp.

    Backtest và test bật cờ này LÚC CHẠY. Đọc bản sao lấy lúc import thì
    báo cáo của một lượt backtest sẽ nói ngược với thứ nó vừa làm.
    """
    ham = _ham(_cay("run_daily.py"), "execute_daily_scan")
    goi = [n for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id == "trang_thai_c5"]
    assert len(goi) == 1, f"gọi trang_thai_c5 {len(goi)} lần, phải đúng 1"
    doi_so = goi[0].args[0]
    assert isinstance(doi_so, ast.Attribute), ast.dump(doi_so)
    assert doi_so.attr == "CHO_PHEP_MO_LENH_MOI", doi_so.attr
    print("PASS  đọc cờ qua thuộc tính module, không qua bản sao lúc nạp")


def test_cong_C5_dang_DONG_trong_ma_nguon():
    """Đọc từ NGUỒN, không đọc giá trị lúc chạy.

    Vài file test gán `paper_trading.CHO_PHEP_MO_LENH_MOI = True` ở mức
    module — rò sang mọi test chạy sau. Đọc giá trị lúc chạy ở đây sẽ cho
    một phép kiểm phụ thuộc thứ tự chạy, tức là vô nghĩa.

    Mở lại cổng thì phải sửa cả dòng này. Đó là chủ đích: mở cổng là một
    hành vi có cân nhắc, không phải một ký tự đổi lặng lẽ.
    """
    gan = [n for n in ast.walk(_cay("paper_trading.py"))
           if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == "CHO_PHEP_MO_LENH_MOI"
                   for t in n.targets)]
    assert len(gan) == 1, f"gán CHO_PHEP_MO_LENH_MOI {len(gan)} lần"
    assert isinstance(gan[0].value, ast.Constant), ast.dump(gan[0].value)
    assert gan[0].value.value is False, (
        "Cổng C5 đang MỞ trong mã nguồn. Chỉ mở khi: điều kiện dừng đo "
        "bằng alpha, CÓ nơi thi hành, và đã đo lệch điểm giữa hai gói "
        "vnstock. Xem docs/STATE.md — GỐC RỄ CỦA CỔNG C5.")
    print("PASS  ô C5 đóng trong mã nguồn")


if __name__ == "__main__":
    for ten, ham in sorted(globals().items()):
        if ten.startswith("test_"):
            ham()
