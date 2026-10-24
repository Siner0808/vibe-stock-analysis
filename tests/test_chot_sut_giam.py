"""Gác cho cổng CHỐT SỤT GIẢM CỦA SỔ (ĐO 33, BƯỚC 226), module `chot_sut_giam.py` và dụng cụ
`tools/do33_chot_sut_giam.py`.

Khai trước ở `docs/TIEU-CHI-DOC-TRUOC.md`, mục "ĐO 33", ký ở một commit RIÊNG trước mã. Luật:
`CHOT_SUT_GIAM_NGUONG` > 0 thì `consider_entry` không mở lệnh khi sổ đang đóng băng — vốn đã chốt
(lệnh ra TRƯỚC ngày tín hiệu) tụt hơn ngưỡng so với đỉnh thì chặn `CHOT_SUT_GIAM_PHIEN` phiên rồi
đặt lại đỉnh. Mặc định 0 — đường chạy thật không đổi.

Phát đầu dựng lại BẪY "≤ d": lệnh ra ĐÚNG phiên d không được tính vào vốn của phiên d — trong một
phiên walkforward chạy mã theo chữ cái, mỗi mã xử lý lệnh thoát rồi mới xét mở lệnh.
"""
from __future__ import annotations

import ast
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import chot_sut_giam as csg  # noqa: E402
import paper_trading as pt  # noqa: E402
import do33_chot_sut_giam as D  # noqa: E402

PHIEN = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2022-03-01", periods=60)]
N = 20


def _tt(he_so, t, nguong=0.15):
    return csg.may_trang_thai(PHIEN, he_so, PHIEN[t], nguong, N)


# ── phát đầu: bẫy "≤ d" ─────────────────────────────────────────────

def test_BAY_lenh_ra_DUNG_phien_d_chi_tinh_TU_phien_sau():
    he_so = [(PHIEN[5], 0.80)]                         # lỗ 20% cả vốn, ra ở phiên 5
    assert _tt(he_so, 5) is None, "lệnh ra phiên 5 chưa được tính vào vốn của phiên 5"
    sut, bat_dau = _tt(he_so, 6)
    assert bat_dau == PHIEN[6] and sut == pytest.approx(0.20)


def test_CHAN_DUNG_20_phien_roi_MO_BANG():
    he_so = [(PHIEN[5], 0.80)]
    assert all(_tt(he_so, i) is not None for i in range(6, 6 + N))
    assert _tt(he_so, 6 + N) is None, "phiên thứ 21 phải mở băng"
    assert _tt(he_so, 5 + N)[1] == PHIEN[6]


def test_MO_BANG_thi_DAT_LAI_DINH_nen_lo_nho_sau_do_khong_dong_bang_lai():
    he_so = [(PHIEN[5], 0.80), (PHIEN[30], 0.95)]     # sau mở băng (phiên 26) lỗ thêm 5%
    assert _tt(he_so, 31) is None, "đỉnh đặt lại ở 80 nên sụt 5% — không đóng băng"
    assert _tt(he_so, 59) is None


def test_DINH_theo_LAI_roi_sut_so_voi_dinh_MOI():
    he_so = [(PHIEN[2], 1.50), (PHIEN[10], 0.82)]     # 100 → 150 → 123: sụt 18% so với 150
    assert _tt(he_so, 10) is None
    sut, bat_dau = _tt(he_so, 11)
    assert bat_dau == PHIEN[11] and sut == pytest.approx(0.18)


def test_NGUONG_la_SO_SANH_CHAT():
    """Sụt ĐÚNG bằng ngưỡng thì chưa đóng băng (phép so `>` như Azoth). 0,75 biểu diễn đúng."""
    he_so = [(PHIEN[5], 0.75)]
    assert csg.may_trang_thai(PHIEN, he_so, PHIEN[6], 0.25, N) is None
    assert csg.may_trang_thai(PHIEN, he_so, PHIEN[6], 0.2499, N) is not None


def test_NGAY_khong_co_phien_dung_phien_cuoi_truoc_do():
    he_so = [(PHIEN[5], 0.80)]
    thu_bay = (pd.Timestamp(PHIEN[9]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    assert pd.Timestamp(thu_bay).weekday() == 5 or thu_bay in PHIEN
    tt = csg.may_trang_thai(PHIEN, he_so, thu_bay, 0.15, N)
    assert tt is not None and tt[1] == PHIEN[6]
    assert csg.may_trang_thai(PHIEN, he_so, "2022-03-05", 0.15, N) is None   # thứ Bảy trước phiên 6


class _L:
    def __init__(self, status, exit_date, size_pct, r):
        self.status, self.exit_date, self.size_pct, self._r = status, exit_date, size_pct, r

    def net_return_pct(self):
        return self._r


def test_HE_SO_lenh_cung_cong_thuc_paper_metrics_va_sap_theo_ngay_ra():
    lenh = [_L("CLOSED", "2022-03-10 00:00:00", 20.0, -10.0), _L("CLOSED", "2022-03-02", 50.0, 4.0),
            _L("OPEN", None, 30.0, None), _L("CLOSED", "2022-03-05", 10.0, None), _L("HUY", "2022-03-03", 10.0, 1.0)]
    assert csg.he_so_lenh(lenh) == [("2022-03-02", pytest.approx(1.02)), ("2022-03-10", pytest.approx(0.98))]


def test_KHOI_DONG_BANG_cung_may_trang_thai():
    he_so = [(PHIEN[5], 0.80), (PHIEN[40], 0.70)]
    khoi = csg.khoi_dong_bang(PHIEN, he_so, 0.15, N)
    assert [k[0] for k in khoi] == [PHIEN[6], PHIEN[41]]
    assert khoi[0][1] == PHIEN[6:6 + N] and len(khoi[1][1]) == len(PHIEN) - 41


def test_LICH_PHIEN_doc_VNINDEX_cua_thu_muc(tmp_path):
    pd.DataFrame({"time": ["2022-03-02 00:00:00", "2022-03-01", "2022-03-02"], "close": [1, 2, 3]}
                 ).to_csv(tmp_path / "VNINDEX.csv", index=False)
    assert csg.lich_phien(str(tmp_path)) == ("2022-03-01", "2022-03-02")


# ── cổng trong paper_trading ─────────────────────────────────────────

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
    import market_filter
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda _d: True)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    j = pt.PaperTradingJournal(str(tmp_path / "s.db"))
    yield j
    j.db.close()


def _ly_do(j, ma):
    return j.db.execute("SELECT skip_reason FROM decisions WHERE symbol=? ORDER BY seq DESC LIMIT 1",
                        (ma,)).fetchone()[0]


def test_MAC_DINH_TAT_thi_KHONG_cham_chot_sut_giam(so, monkeypatch):
    class _CamCham:
        def __getattr__(self, ten):
            raise AssertionError(f"cổng TẮT mà vẫn chạm chot_sut_giam.{ten}")
    monkeypatch.setitem(sys.modules, "chot_sut_giam", _CamCham())
    monkeypatch.setattr(pt, "CHOT_SUT_GIAM_NGUONG", 0)
    assert so.dang_dong_bang("2022-11-30") is None


def test_consider_entry_GHI_ly_do_khi_dong_bang_va_MO_khi_khong(so, monkeypatch):
    monkeypatch.setattr(pt, "CHOT_SUT_GIAM_NGUONG", 0.15)
    monkeypatch.setattr(csg, "lich_phien_mac_dinh", lambda: PHIEN)
    goi = []

    def _may(phien, he_so, t, nguong, so_phien):
        goi.append((t, nguong, so_phien))
        return (0.182, "2022-03-01") if t == "2022-03-15" else None
    monkeypatch.setattr(csg, "may_trang_thai", _may)
    assert so.consider_entry("AAA", "2022-03-15", _kq()) is None
    assert _ly_do(so, "AAA").startswith(pt.LY_DO_CHOT_SUT_GIAM) and "2022-03-01" in _ly_do(so, "AAA")
    assert so.consider_entry("ACV", "2022-03-15 00:00:00", _kq()) is None
    assert goi == [("2022-03-15", 0.15, pt.CHOT_SUT_GIAM_PHIEN)], "cùng ngày, cùng sổ: nhớ, không tính lại"
    assert so.consider_entry("FPT", "2022-03-16", _kq()) is not None


def test_SO_THAT_su_dung_net_return_va_size_cua_lenh_da_dong(so, monkeypatch):
    """Đi qua `Trade.net_return_pct()` thật: một lệnh 100% vốn lỗ ~25% đóng ngày 07/03 → phiên sau đóng băng."""
    monkeypatch.setattr(pt, "CHOT_SUT_GIAM_NGUONG", 0.15)
    monkeypatch.setattr(csg, "lich_phien_mac_dinh", lambda: PHIEN)
    so.db.execute("INSERT INTO trades (symbol, exchange, signal_date, entry_date, entry_price, exit_date, "
                  "exit_price, exit_reason, stop_loss, take_profit, size_pct, status) VALUES "
                  "('HPG','HOSE','2022-03-01','2022-03-02',100.0,'2022-03-07',75.0,'SL',90.0,120.0,100.0,'CLOSED')")
    so.db.commit()
    assert so.dang_dong_bang("2022-03-07") is None
    sut, bat_dau = so.dang_dong_bang("2022-03-08")
    assert bat_dau == "2022-03-08" and sut > 0.25


def _gan_trong_nguon(ten):
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    return [n.value.value for n in cay.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == ten for t in n.targets)]


def test_MAC_DINH_trong_NGUON():
    assert _gan_trong_nguon("CHOT_SUT_GIAM_NGUONG") == [0]
    assert _gan_trong_nguon("CHOT_SUT_GIAM_PHIEN") == [20]


def test_cong_SAU_do_rong_TRUOC_chat_luong_va_chot_C5():
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "consider_entry")

    def dong(la):
        return [n.lineno for n in ast.walk(ham) if la(n)]
    dr = dong(lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "do_rong_bi_chan")
    db = dong(lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "dang_dong_bang")
    cl = dong(lambda n: isinstance(n, ast.Name) and n.id == "MUC_CHAT_LUONG_DUNG_DUOC")
    c5 = dong(lambda n: isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) and n.value.id == "LY_DO_C5")
    assert len(dr) == len(db) == len(cl) == len(c5) == 1
    assert dr[0] < db[0] < cl[0] < c5[0]


# ── dụng cụ ĐO 33 ────────────────────────────────────────────────────

def test_HANG_SO_KHOP_muc_DO_33_da_ky():
    van = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
    muc = van[van.index("## ĐO 33"):]
    m = re.search(r"\*\*B\*\* = \*\*(\d+),(\d+)\*\*", muc)
    assert m and float(f"{m.group(1)}.{m.group(2)}") == D.NGUONG_LUOT_B == D.LUOT["B"]
    assert D.LUOT["A"] == 0
    n = re.search(r"chặn đúng (\d+) phiên", muc)
    assert n and int(n.group(1)) == pt.CHOT_SUT_GIAM_PHIEN


def test_DOI_CHIEU_dem_dung_ngoai_khoi_va_lenh_trong_khoi():
    khoi = [(PHIEN[6], PHIEN[6:9])]
    ly = pt.LY_DO_CHOT_SUT_GIAM
    qd = [{"signal_date": PHIEN[6], "skip_reason": f"{ly}: sụt 20.0% từ {PHIEN[6]}"},
          {"signal_date": PHIEN[12], "skip_reason": f"{ly}: lạc chỗ"},
          {"signal_date": PHIEN[7], "skip_reason": "khác"}, {"signal_date": PHIEN[8], "skip_reason": None}]
    lenh = [{"signal_date": PHIEN[7], "status": "CLOSED"}, {"signal_date": PHIEN[7], "status": "HUY"},
            {"signal_date": PHIEN[20], "status": "CLOSED"}]
    assert D.doi_chieu(khoi, qd, lenh, ly) == {"so_khoi": 1, "so_phien_chan": 3, "qd_ly_do": 2,
                                               "qd_ngoai_khoi": 1, "lenh_trong_khoi": 1}


def test_dung_cu_GIAO_cho_do1_va_dat_co_MOT_lan():
    cay = ast.parse((GOC / "tools" / "do33_chot_sut_giam.py").read_text(encoding="utf-8"))
    goi = {n.func.attr for n in ast.walk(cay) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "chay_mot_luot" in goi
    gan = [t.attr for n in ast.walk(cay) if isinstance(n, ast.Assign) for t in n.targets
           if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "paper_trading"]
    assert gan == ["CHOT_SUT_GIAM_NGUONG"]
    assert D.LUOT_DO1 == 2


def test_hai_luot_THAT_SU_chay_voi_dung_co(monkeypatch):
    import do1_chi_phi_thuc_thi as do1
    monkeypatch.setattr(pt, "CHOT_SUT_GIAM_NGUONG", pt.CHOT_SUT_GIAM_NGUONG)
    ghi = []
    monkeypatch.setattr(do1, "chay_mot_luot", lambda n, *a, **k: ghi.append((n, pt.CHOT_SUT_GIAM_NGUONG)) or 0)
    assert D.chay_luot("B") == 0 and D.chay_luot("A") == 0
    assert ghi == [(2, 0.15), (2, 0)]


def test_dung_cu_dem_chay_THAT_tren_so_tam_va_cache_tam(tmp_path, monkeypatch, capsys):
    (tmp_path / "c").mkdir()
    pd.DataFrame({"time": PHIEN, "close": 1.0}).to_csv(tmp_path / "c" / "VNINDEX.csv", index=False)
    import backtest.data
    monkeypatch.setattr(backtest.data, "CACHE_DIR", tmp_path / "c")
    db = tmp_path / "wf_oos.db"
    j = pt.PaperTradingJournal(str(db))
    j.db.execute("INSERT INTO trades (symbol, exchange, signal_date, entry_date, entry_price, exit_date, "
                 "exit_price, exit_reason, stop_loss, take_profit, size_pct, status) VALUES "
                 f"('HPG','HOSE','{PHIEN[1]}','{PHIEN[2]}',100.0,'{PHIEN[5]}',75.0,'SL',90.0,120.0,100.0,'CLOSED'),"
                 f"('FPT','HOSE','{PHIEN[8]}','{PHIEN[9]}',100.0,'{PHIEN[12]}',101.0,'TP',90.0,120.0,10.0,'CLOSED')")
    j.db.execute("INSERT INTO decisions (signal_date, skip_reason) VALUES (?, ?)",
                 (PHIEN[7], f"{pt.LY_DO_CHOT_SUT_GIAM}: sụt 25.5% từ {PHIEN[6]}"))
    j.db.commit()
    j.db.close()
    assert D.main(["--dem", str(db)]) == 0
    ra = capsys.readouterr().out
    assert "lệnh CLOSED: 2" in ra and "phiên trong lịch: 60" in ra
    assert f"bắt đầu {PHIEN[6]} · 20 phiên" in ra
    assert "quyết định lý do chốt sụt giảm: 1 · nằm ngoài khối: 0" in ra
    assert "lệnh CLOSED có ngày tín hiệu trong khối: 1" in ra
