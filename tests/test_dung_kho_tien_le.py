"""Dụng cụ dựng kho tiền lệ ý 5 (`tools/dung_kho_tien_le.py`, BƯỚC 215).

Sổ giả bốn lệnh và VNINDEX giả 60 phiên, đáp án tính tay:
  VN-Index đóng 1000 suốt 55 phiên rồi 1100 từ phiên 56 ⇒ MA50 phiên 60 = (45·1000 + 5·1100)/50
  = 1010 ⇒ % trên MA50 = (1100 − 1010)/1010·100 = 8,9109; phiên 55 (18/03): 0.
  Lệnh 1 FPT điểm 70 tín hiệu phiên 60, vào 30.000 ra 33.000 ⇒ net_return_pct đúng hàm sổ.
  Lệnh 2 HPG điểm 61 (dưới ngưỡng mua) ⇒ loại. Lệnh 3 VNM chưa đóng ⇒ loại.
  Lệnh 4 SSI điểm 62 tín hiệu phiên 55 (VN-Index 0%), VÀO phiên 56 (đã 1100) ⇒ phải ra 0%:
  độ cao VN-Index lấy theo ngày TÍN HIỆU, như cổng mở lệnh đã nhìn.
  Sổ giả là sqlite TRẦN chỉ có bảng `trades` (như sổ đời cũ): mở thẳng bằng `PaperTradingJournal`
  sẽ tạo thêm bảng trong sổ nguồn — dụng cụ phải làm trên bản chép.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import dung_kho_tien_le as dk  # noqa: E402
from paper_trading import Trade  # noqa: E402

NGAY = list(pd.bdate_range("2026-01-01", periods=60).strftime("%Y-%m-%d"))


@pytest.fixture
def the_gioi(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    dong = [1000.0] * 55 + [1100.0] * 5
    pd.DataFrame({"time": NGAY, "open": dong, "high": dong, "low": dong, "close": dong,
                  "volume": 1e6}).to_csv(cache / "VNINDEX.csv", index=False)
    so_p = tmp_path / "wf_oos.db"
    db = sqlite3.connect(so_p)
    db.execute("CREATE TABLE trades (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, "
               "exchange TEXT, signal_date TEXT, entry_date TEXT, entry_price REAL, exit_date TEXT, "
               "exit_price REAL, exit_reason TEXT, stop_loss REAL, take_profit REAL, size_pct REAL, "
               "entry_score INT, entry_recommendation TEXT, components TEXT, reasons TEXT, "
               "status TEXT, created_at REAL)")
    cot = ("symbol, signal_date, entry_date, entry_price, exit_date, exit_price, exit_reason, "
           "entry_score, status, size_pct")
    for r in [("FPT", NGAY[59], "2026-03-26", 30000.0, "2026-04-02", 33000.0, "SIGNAL_REVERSED", 70, "CLOSED", 10.0),
              ("HPG", NGAY[59], "2026-03-26", 30000.0, "2026-04-02", 31000.0, "STOP_LOSS", 61, "CLOSED", 10.0),
              ("VNM", NGAY[59], "2026-03-26", 30000.0, None, None, None, 66, "OPEN", 10.0),
              ("SSI", NGAY[54], NGAY[55], 20000.0, "2026-03-23", 19000.0, "STOP_LOSS", 62, "CLOSED", 10.0)]:
        db.execute(f"INSERT INTO trades ({cot}) VALUES (?,?,?,?,?,?,?,?,?,?)", r)
    db.commit()
    db.close()
    return so_p, cache, tmp_path


def _chay(the_gioi):
    so_p, cache, tmp = the_gioi
    ra = tmp / "kho.json"
    ma = dk.main(["--so", str(so_p), "--cache", str(cache), "--ra", str(ra), "--do", "ĐO 99",
                  "--commit", "abc1234", "--nguong-is", "45"])
    return ma, ra


def test_KHO_tinh_tay_loc_dung_va_dung_HAM_cua_so(the_gioi):
    ma, ra = _chay(the_gioi)
    assert ma == 0
    du = json.loads(ra.read_text(encoding="utf-8"))
    lenh = {d["ma"]: d for d in du["lenh"]}
    assert set(lenh) == {"FPT", "SSI"}
    fpt = Trade(id=1, symbol="FPT", signal_date=NGAY[59], entry_date="2026-03-26",
                entry_price=30000.0, exit_date="2026-04-02", exit_price=33000.0,
                exit_reason="SIGNAL_REVERSED", stop_loss=0, take_profit=0, size_pct=10.0,
                entry_score=70, status="CLOSED")
    assert lenh["FPT"]["loi_nhuan_rong_pct"] == pytest.approx(round(fpt.net_return_pct(), 4))
    assert lenh["FPT"]["vni_pct_tren_ma50"] == pytest.approx(8.9109, abs=1e-4)
    assert lenh["SSI"]["vni_pct_tren_ma50"] == pytest.approx(0.0, abs=1e-9)
    assert [d["ma"] for d in du["lenh"]] == ["SSI", "FPT"]          # xếp theo ngày ra
    assert du["so_lenh_so"] == 4 and du["nguon"]["do"] == "ĐO 99"


def test_SO_NGUON_khong_bi_cham(the_gioi):
    so_p = the_gioi[0]
    truoc = so_p.read_bytes()
    _chay(the_gioi)
    assert so_p.read_bytes() == truoc


def test_TAI_LAP_tung_byte(the_gioi):
    _, ra = _chay(the_gioi)
    mot = ra.read_bytes()
    _, ra2 = _chay(the_gioi)
    assert ra2.read_bytes() == mot


def test_THIEU_VNINDEX_thi_DUNG_khong_keo_mang(the_gioi):
    so_p, cache, tmp = the_gioi
    (cache / "VNINDEX.csv").unlink()
    assert dk.main(["--so", str(so_p), "--cache", str(cache), "--ra", str(tmp / "x.json"),
                    "--do", "ĐO 99", "--commit", "abc", "--nguong-is", "45"]) == 2
    assert not (tmp / "x.json").exists()


def test_CACHE_DIR_tra_ve_nhu_cu_sau_khi_nap(the_gioi):
    import backtest.data as bd
    cu = bd.CACHE_DIR
    _chay(the_gioi)
    assert bd.CACHE_DIR == cu
