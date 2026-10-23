"""Gác cho cổng NGHỈ SAU LỆNH LỖ (ĐO 30, BƯỚC 221) và dụng cụ `tools/do30_nghi_sau_lo.py`.

Khai trước ở `docs/TIEU-CHI-DOC-TRUOC.md`, mục "ĐO 30", ký ở một commit RIÊNG
trước mã. Luật: `NGHI_SAU_LO_NGAY` > 0 thì `consider_entry` không mở lại CÙNG
mã khi ngày tín hiệu rơi trong [ngày ra ; ngày ra + N ngày lịch] của một lệnh
CLOSED có giá ra < giá vào. Mặc định 0 — đường chạy thật không đổi.

Phát đầu dựng lại ca thật đã khai: DPM ra bằng STOP_LOSS (lỗ) ngày 07/04/2022
và có tín hiệu mới CÙNG ngày (sổ OOS lượt B của ĐO 29, lệnh id 18).
"""
from __future__ import annotations

import ast
import re
import sqlite3
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import paper_trading as pt  # noqa: E402
import do30_nghi_sau_lo as D  # noqa: E402


def _kq(diem: int = 95) -> dict:
    return {"final_score": diem, "recommendation": "MUA 📈",
            "data_quality": "OK", "score_breakdown": {},
            "key_reasons": [], "safety": {"safe_position_size": 10.0},
            "analyses": {"risk": {"recommendations": {
                "entry_price": 100.0, "stop_loss_price": 90.0,
                "take_profit_price": 120.0,
                "suggested_position_size_pct": 10.0}}}}


@pytest.fixture
def so(tmp_path, monkeypatch):
    """Sổ ảo trong thư mục tạm; cổng VN-INDEX và ô C5 mở cho lượt test."""
    import market_filter
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda _d: True)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    j = pt.PaperTradingJournal(str(tmp_path / "s.db"))
    yield j
    j.db.close()


def _dong(j, ma: str, ngay_ra: str, gia_vao: float, gia_ra: float,
          trang_thai: str = pt.Status.CLOSED) -> None:
    j.db.execute(
        "INSERT INTO trades (symbol, exchange, signal_date, entry_date, entry_price,"
        " exit_date, exit_price, exit_reason, status) VALUES (?,?,?,?,?,?,?,?,?)",
        (ma, "HOSE", "2022-03-01", "2022-03-02", gia_vao, ngay_ra, gia_ra,
         "STOP_LOSS", trang_thai))
    j.db.commit()


def _ly_do(j, ma: str) -> str:
    return j.db.execute("SELECT skip_reason FROM decisions WHERE symbol=? ORDER BY seq DESC LIMIT 1",
                        (ma,)).fetchone()[0]


# ── phát đầu: ca thật đã khai ────────────────────────────────────────

def test_CA_THAT_DPM_ra_lo_va_co_tin_hieu_CUNG_NGAY_thi_bi_chan(so, monkeypatch):
    monkeypatch.setattr(pt, "NGHI_SAU_LO_NGAY", 7)
    _dong(so, "DPM", "2022-04-07", 100.0, 92.0)
    assert so.consider_entry("DPM", "2022-04-07", _kq(), buy_threshold=50.0) is None
    ly_do = _ly_do(so, "DPM")
    assert ly_do.startswith(pt.LY_DO_NGHI_SAU_LO) and "2022-04-07" in ly_do


# ── biên cửa sổ, và thứ KHÔNG được chặn ──────────────────────────────

@pytest.mark.parametrize("ngay_tin_hieu, bi_chan", [
    ("2022-04-14", True),    # đúng 7 ngày lịch: còn trong cửa sổ
    ("2022-04-15", False),   # 8 ngày: hết nghỉ
    ("2022-04-06", False),   # lệnh lỗ ra SAU ngày tín hiệu: không phải "sau lệnh lỗ"
])
def test_BIEN_cua_so_7_ngay_lich(so, monkeypatch, ngay_tin_hieu, bi_chan):
    monkeypatch.setattr(pt, "NGHI_SAU_LO_NGAY", 7)
    _dong(so, "GIL", "2022-04-07", 100.0, 92.0)
    mo = so.consider_entry("GIL", ngay_tin_hieu, _kq(), buy_threshold=50.0)
    assert (mo is None) is bi_chan


def test_lenh_THANG_lenh_HOA_ma_KHAC_va_lenh_HUY_khong_chan(so, monkeypatch):
    monkeypatch.setattr(pt, "NGHI_SAU_LO_NGAY", 7)
    _dong(so, "AAA", "2022-04-07", 100.0, 105.0)                 # thắng
    _dong(so, "BBB", "2022-04-07", 100.0, 100.0)                 # hoà: không "lỗ"
    _dong(so, "CCC", "2022-04-07", 100.0, 92.0)                  # lỗ, nhưng mã KHÁC DDD
    _dong(so, "EEE", "2022-04-07", 100.0, 92.0, trang_thai=pt.Status.HUY)  # chưa từng là giao dịch
    for ma in ("AAA", "BBB", "DDD", "EEE"):
        assert so.consider_entry(ma, "2022-04-08", _kq(), buy_threshold=50.0) is not None, ma


def test_lay_lenh_lo_GAN_NHAT_khong_phai_bat_ky(so, monkeypatch):
    """Lệnh lỗ cũ ngoài cửa sổ không chặn; lệnh lỗ gần trong cửa sổ thì chặn."""
    monkeypatch.setattr(pt, "NGHI_SAU_LO_NGAY", 7)
    _dong(so, "HUT", "2022-01-03", 100.0, 90.0)
    _dong(so, "HUT", "2022-04-05", 100.0, 95.0)
    assert so.ngay_ra_lo_gan("HUT", "2022-04-07") == "2022-04-05"
    assert so.ngay_ra_lo_gan("HUT", "2022-01-20") is None


def test_MAC_DINH_TAT_thi_khong_chan_va_KHONG_doc_so(so, monkeypatch):
    """Mặc định 0: đường chạy thật không đổi, và cổng không chạm sổ."""
    monkeypatch.setattr(pt, "NGHI_SAU_LO_NGAY", 0)
    _dong(so, "DPM", "2022-04-07", 100.0, 92.0)
    so.db.close()                                   # chạm sổ là nổ
    assert so.ngay_ra_lo_gan("DPM", "2022-04-07") is None
    so.db = sqlite3.connect(":memory:")             # để fixture đóng được


def test_MAC_DINH_trong_NGUON_la_0():
    """Đọc NGUỒN, không đọc giá trị lúc chạy: test khác có thể đã đặt cờ."""
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    gan = [n.value.value for n in cay.body if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == "NGHI_SAU_LO_NGAY" for t in n.targets)]
    assert gan == [0]


def _dong_ma(ham: ast.FunctionDef, la) -> list[int]:
    return [n.lineno for n in ast.walk(ham) if la(n)]


def test_cong_dung_SAU_cong_dang_giu_va_TRUOC_chot_C5():
    """Lý do ghi sổ phải cho biết lệnh LẼ RA đã mở — cùng luật đặt chốt C5 cuối.
    Đọc AST của `consider_entry`, không dò chuỗi (chú thích không được tính)."""
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "consider_entry")

    def gan_skip(ten):
        return lambda n: (isinstance(n, ast.Assign) and isinstance(n.value, ast.Name)
                          and n.value.id == ten
                          and any(isinstance(t, ast.Name) and t.id == "skip" for t in n.targets))
    giu = _dong_ma(ham, gan_skip("LY_DO_DANG_GIU"))
    nghi = _dong_ma(ham, lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "ngay_ra_lo_gan")
    c5 = _dong_ma(ham, gan_skip("LY_DO_C5"))
    assert len(giu) == len(nghi) == len(c5) == 1
    assert giu[0] < nghi[0] < c5[0]


# ── dụng cụ ĐO 30 ────────────────────────────────────────────────────

def test_NGAY_NGHI_cua_dung_cu_KHOP_muc_DO_30_da_ky():
    """Suy ra, đừng gõ: số ngày của lượt B phải đúng số đã ghim trong bản khai."""
    van = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
    muc = van[van.index("## ĐO 30"):]
    m = re.search(r"Lượt B đặt \*\*(\d+)\*\*", muc)
    assert m and int(m.group(1)) == D.NGAY_NGHI_LUOT_B == D.LUOT["B"]
    assert D.LUOT["A"] == 0


def _l(i, ma, tin_hieu, ra, vao, gia_ra, tt="CLOSED"):
    return {"id": i, "symbol": ma, "signal_date": tin_hieu, "exit_date": ra,
            "entry_price": vao, "exit_price": gia_ra, "status": tt}


def test_phep_dem_iv_CUNG_DINH_NGHIA_voi_cong():
    lenh = [
        _l(1, "DPM", "2022-03-01", "2022-04-07", 100, 92),     # lỗ, ra 07/04
        _l(2, "DPM", "2022-04-07", "2022-05-01", 100, 110),    # tín hiệu cùng ngày → chặn
        _l(3, "DPM", "2022-05-03", "2022-06-01", 100, 90),     # lỗ 07/04 đã quá 7 ngày
        _l(4, "DPM", "2022-06-08", None, 100, None, "OPEN"),   # 7 ngày sau lỗ 01/06 → chặn
        _l(5, "GIL", "2022-04-15", "2022-05-01", 100, 99),     # mã khác
        _l(6, "GIL", "2022-05-09", "2022-06-01", 100, 99),     # 8 ngày sau lỗ 01/05 → không
        _l(7, "HUT", "2022-03-01", "2022-04-07", 100, 92, "HUY"),
        _l(8, "HUT", "2022-04-08", "2022-05-01", 100, 99),     # "lỗ" trước đó là lệnh HUỶ → không
        _l(9, "VNM", "2022-03-01", "2022-04-07", 100, 100),    # HOÀ: không phải lỗ
        _l(10, "VNM", "2022-04-08", "2022-05-01", 100, 101),   # → không chặn
    ]
    assert [x["id"] for x in D.tin_hieu_bi_chan(lenh, 7)] == [2, 4]


def test_dung_cu_GIAO_cho_do1_chu_khong_chep_duong_chay():
    """Lượt A/B phải là lượt 2 của do1 — cùng một đường chạy, chỉ khác cờ."""
    cay = ast.parse((GOC / "tools" / "do30_nghi_sau_lo.py").read_text(encoding="utf-8"))
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "chay_mot_luot" in goi
    gan_co = [n for n in ast.walk(cay) if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Attribute) and t.attr == "NGHI_SAU_LO_NGAY"
                      for t in n.targets)]
    assert len(gan_co) == 1
    assert D.LUOT_DO1 == 2


def test_luot_B_THAT_SU_chay_voi_co_7_va_dung_luot_2_cua_do1(monkeypatch):
    """Gác AST ở trên chỉ thấy CÓ một phép gán cờ; gán sai giá trị vẫn lọt.
    Ở đây thay `chay_mot_luot` bằng hàm giả và đọc cờ ĐÚNG lúc lượt chạy."""
    import do1_chi_phi_thuc_thi as do1
    monkeypatch.setattr(pt, "NGHI_SAU_LO_NGAY", pt.NGHI_SAU_LO_NGAY)  # trả lại sau test
    thay_the = []
    monkeypatch.setattr(do1, "chay_mot_luot",
                        lambda n, *a, **k: thay_the.append((n, pt.NGHI_SAU_LO_NGAY)) or 0)
    assert D.chay_luot("B") == 0
    assert D.chay_luot("A") == 0
    assert thay_the == [(2, 7), (2, 0)]


def test_dung_cu_chay_THAT_tren_so_tam(tmp_path):
    db = tmp_path / "wf_oos.db"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE trades (id INTEGER, symbol TEXT, signal_date TEXT, exit_date TEXT,"
              " entry_price REAL, exit_price REAL, status TEXT)")
    c.executemany("INSERT INTO trades VALUES (?,?,?,?,?,?,?)", [
        (1, "DPM", "2022-03-01", "2022-04-07", 100, 92, "CLOSED"),
        (2, "DPM", "2022-04-07", "2022-05-01", 100, 110, "CLOSED")])
    c.commit()
    c.close()
    assert [x["id"] for x in D.tin_hieu_bi_chan(D.doc_so(str(db)), 7)] == [2]
    assert D.main(["--dem", str(db)]) == 0
