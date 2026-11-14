"""BƯỚC 275, lát 3 — bootstrap của app chỉ tính lại khi sổ ĐỔI, và kết quả là CÙNG từng chữ số.

1. **Cùng từng byte** với gọi thẳng `paper_metrics.expectancy_significant` (cùng seed, cùng đầu vào),
   ở cả lượt tính lẫn lượt trúng bộ nhớ.
2. **Khoá theo NỘI DUNG**: đổi MỘT lợi nhuận, `iters` hoặc `seed` thì tính lại; đối tượng khác
   nhưng cùng chuỗi lợi nhuận thì trúng. Lệnh chưa đóng không vào khoá (như `_returns`).
3. **Hàm gốc chỉ đọc `_returns(trades)`, `iters`, `seed`** (AST): thêm một đầu vào khác thì bộ nhớ
   thành bộ nhớ SAI mà test 1 không thấy — gác này buộc phải sửa khoá cùng lúc.
4. **Bản trả về là bản sao**: sửa kết quả không làm hỏng bộ nhớ.
5. **Chỉ app nhập**: đường quét, backtest, điều kiện dừng gọi thẳng `paper_metrics`.
"""
import ast
import pathlib

import pytest

import bo_nho_do_app as bn
import paper_metrics as pm
import paper_trading as pt
from paper_trading import ExitReason, Status

GOC = pathlib.Path(__file__).resolve().parent.parent


def _dong(loi_nhuan, dong=True):
    return [pt.Trade(id=i, symbol="X", signal_date="2026-01-01", entry_date="2026-01-02", entry_price=100.0,
                     exit_date="2026-02-02" if dong else None, exit_price=100.0 * (1 + g / 100) if dong else None,
                     exit_reason=ExitReason.MAX_HOLD if dong else None, stop_loss=90.0, take_profit=120.0,
                     size_pct=10.0, entry_score=70, status=Status.CLOSED if dong else Status.OPEN)
            for i, g in enumerate(loi_nhuan)]


MAU = [2.5, -1.2, 0.4, 3.3, -2.8, 1.1, 0.0, -0.7, 4.2, -3.1, 0.9, 1.7]


@pytest.fixture(autouse=True)
def _sach():
    bn.xoa()
    yield
    bn.xoa()


def test_cung_tung_byte_voi_ham_goc_o_lan_tinh_va_lan_trung_bo_nho():
    for seed in (0, 7):
        for iters in (500, 5000):
            goc = pm.expectancy_significant(_dong(MAU), iters, seed)
            lan1 = bn.expectancy_significant_nho(_dong(MAU), iters, seed)
            lan2 = bn.expectancy_significant_nho(_dong(MAU), iters, seed)
            assert repr(lan1) == repr(goc) == repr(lan2), (seed, iters)


def test_mac_dinh_giong_ham_goc_va_so_lan_tinh():
    n0 = bn.SO_LAN_TINH
    a = bn.expectancy_significant_nho(_dong(MAU))
    b = bn.expectancy_significant_nho(_dong(MAU))
    assert repr(a) == repr(pm.expectancy_significant(_dong(MAU))) == repr(b)
    assert bn.SO_LAN_TINH == n0 + 1, "lượt hai phải trúng bộ nhớ"


def test_it_hon_10_lenh_van_di_qua_va_giong_goc():
    assert bn.expectancy_significant_nho(_dong(MAU[:5])) == pm.expectancy_significant(_dong(MAU[:5]))


def test_doi_mot_loi_nhuan_hoac_iters_hoac_seed_thi_tinh_lai():
    bn.expectancy_significant_nho(_dong(MAU), 300, 1)
    n = bn.SO_LAN_TINH
    bn.expectancy_significant_nho(_dong(MAU[:-1] + [MAU[-1] + 0.01]), 300, 1)
    bn.expectancy_significant_nho(_dong(MAU), 301, 1)
    bn.expectancy_significant_nho(_dong(MAU), 300, 2)
    assert bn.SO_LAN_TINH == n + 3
    bn.expectancy_significant_nho(_dong(MAU), 300, 1)            # đối tượng MỚI, cùng nội dung
    assert bn.SO_LAN_TINH == n + 3


def test_lenh_chua_dong_khong_vao_khoa_nhu_ham_goc():
    n = bn.SO_LAN_TINH
    bn.expectancy_significant_nho(_dong(MAU), 300, 1)
    bn.expectancy_significant_nho(_dong(MAU) + _dong([9.0, 9.0], dong=False), 300, 1)
    assert bn.SO_LAN_TINH == n + 1


def test_ban_tra_ve_la_ban_sao():
    a = bn.expectancy_significant_nho(_dong(MAU), 300, 1)            # lượt TÍNH
    luc_dau = repr(a)
    a["ci"] = ("hỏng", "hỏng")
    a["expectancy"] = 123
    b = bn.expectancy_significant_nho(_dong(MAU), 300, 1)            # lượt TRÚNG bộ nhớ
    assert repr(b) == luc_dau
    b["ci"] = ("hỏng", "hỏng")
    b["verdict"] = "hỏng"
    c = bn.expectancy_significant_nho(_dong(MAU), 300, 1)            # trúng lần nữa: bản trúng trước đó là bản SAO
    assert repr(c) == luc_dau


def test_bo_nho_co_tran():
    for i in range(bn.TOI_DA_MUC + 3):
        bn.expectancy_significant_nho(_dong(MAU), 50, i)
    assert len(bn._BO_NHO) == bn.TOI_DA_MUC


def test_AST_ham_goc_chi_doc_returns_iters_seed():
    """Khoá bộ nhớ = (`_returns(trades)`, iters, seed). Hàm gốc mà đọc thêm gì từ `trades` hay
    từ thứ khác thì bộ nhớ sai âm thầm."""
    cay = ast.parse((GOC / "paper_metrics.py").read_text(encoding="utf-8"))
    f = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "expectancy_significant")
    assert [a.arg for a in f.args.args] == ["trades", "iters", "seed"]
    dung_trades = [n for n in ast.walk(f) if isinstance(n, ast.Name) and n.id == "trades"
                   and isinstance(n.ctx, ast.Load)]
    assert len(dung_trades) == 1                                  # đúng một chỗ: `_returns(trades)`
    cha = {id(c): p for p in ast.walk(f) for c in ast.iter_child_nodes(p)}
    p = cha[id(dung_trades[0])]
    assert isinstance(p, ast.Call) and ast.unparse(p) == "_returns(trades)"
    # ngoài tham số, chỉ có tên cấp module an toàn (random, statistics, _returns); không đọc biến toàn cục khác
    cho_phep = {"trades", "iters", "seed", "rets", "rng", "means", "sample", "lo", "hi", "sig", "_", "len",
                "random", "statistics", "int", "range", "_returns", "f"}
    ten = {n.id for st in f.body for n in ast.walk(st) if isinstance(n, ast.Name)}
    assert ten <= cho_phep, ten - cho_phep


def test_AST_khoa_bo_nho_dung_ba_thanh_phan_va_goi_ham_goc():
    cay = ast.parse((GOC / "bo_nho_do_app.py").read_text(encoding="utf-8"))
    f = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "expectancy_significant_nho")
    gan = [n for n in ast.walk(f) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "khoa"]
    assert len(gan) == 1 and ast.unparse(gan[0].value) == "(tuple(paper_metrics._returns(trades)), iters, seed)"
    goi = [ast.unparse(n.func) for n in ast.walk(f) if isinstance(n, ast.Call)]
    assert "paper_metrics.expectancy_significant" in goi


def test_chi_app_nhap_bo_nho_do_app():
    cac = []
    for p in sorted(GOC.glob("*.py")) + sorted((GOC / "backtest").glob("*.py")) + sorted((GOC / "tools").glob("*.py")):
        cay = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.ImportFrom) and n.module == "bo_nho_do_app":
                cac.append(p.name)
            if isinstance(n, ast.Import) and any(a.name == "bo_nho_do_app" for a in n.names):
                cac.append(p.name)
    assert cac == ["app.py"], cac


def test_app_goi_ban_co_nho_o_khoi_hieu_qua():
    cay = ast.parse((GOC / "app.py").read_text(encoding="utf-8"))
    goi = [n for n in ast.walk(cay) if isinstance(n, ast.Call) and ast.unparse(n.func) == "expectancy_significant_nho"]
    assert len(goi) == 1 and ast.unparse(goi[0]) == "expectancy_significant_nho(list(_so_lenh.lenh_dong))"
    assert not [n for n in ast.walk(cay) if isinstance(n, ast.Call) and ast.unparse(n.func) == "expectancy_significant"]
