"""BƯỚC 272 — gác của DỤNG CỤ ĐO 35 (`tools/do35_chinh_thang_gia.py`) trên sổ và khung giá DỰNG TAY.

Máy đo cũng phải bị nghi ngờ như gác (Quy tắc của skill, lỗi 61): dụng cụ phát lại là thứ in ra con số phán
kết cục, nên nó có test riêng — trên dữ liệu tổng hợp, KHÔNG đọc sổ hay nến thật. Ca dựng: lệnh vào 30000 (thang
cũ), nguồn ĐÃ điều chỉnh ÷1,5 từ nến đầu tiên (đúng hình dạng của lượt đo, nguồn "hôm nay").
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys

import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import do35_chinh_thang_gia as d35  # noqa: E402
from nhat_ky_vi_sao import COT_NHAT_KY  # noqa: E402
from paper_trading import PaperTradingJournal  # noqa: E402


def _dung_so(duong: pathlib.Path) -> dict:
    j = PaperTradingJournal(str(duong))
    j.db.execute(
        "INSERT INTO trades (id, symbol, signal_date, entry_date, entry_price, exit_date, exit_price,"
        " exit_reason, stop_loss, take_profit, size_pct, status)"
        " VALUES (1,'XYZ','2026-10-01','2026-10-01',30000,'2026-10-08',21000,'STOP_LOSS',28500,36000,5,'CLOSED')")
    j.db.execute(
        "INSERT INTO trades (id, symbol, signal_date, entry_date, entry_price, exit_date, exit_price,"
        " exit_reason, stop_loss, take_profit, size_pct, status)"
        " VALUES (2,'ABC','2026-09-01','2026-09-01',10000,'2026-09-05',9500,'STOP_LOSS',9600,12000,5,'CLOSED')")
    d = {c: None for c in COT_NHAT_KY}
    d.update(trade_id=1, symbol="XYZ", entry_date="2026-10-01", entry_price=30000.0, stop_loss_ban_dau=28500.0,
             rui_ro_pct=5.0, diem_agent="{}", ly_do="[]", boi_canh=json.dumps({"atr_pct": 2.0}))
    j.db.execute(f"INSERT INTO nhat_ky ({','.join(COT_NHAT_KY)}) VALUES ({','.join('?' * len(COT_NHAT_KY))})",
                 [d[c] for c in COT_NHAT_KY])
    for ngay in ("2026-10-02", "2026-10-05", "2026-10-06"):
        j.record_decision("XYZ", ngay, {"final_score": 70, "recommendation": "GIU"}, False, "x")
    j.record_decision("ABC", "2026-09-02", {"final_score": 60}, False, "x")
    j.db.commit()
    j.db.close()
    return {"id": 1, "symbol": "XYZ", "entry_date": "2026-10-01", "entry_price": 30000.0, "stop_loss": 28500.0,
            "nhat_ky": {"stop_loss_ban_dau": 28500.0}}


def _kho() -> dict:
    nen = [("2026-10-01", 20.0, 20.2, 19.8, 20.0), ("2026-10-02", 20.2, 20.6, 20.0, 20.4),
           ("2026-10-05", 20.4, 20.8, 20.2, 20.6), ("2026-10-06", 20.6, 21.0, 20.4, 20.8)]
    df = pd.DataFrame({"time": pd.to_datetime([n[0] for n in nen]), "open": [n[1] for n in nen],
                       "high": [n[2] for n in nen], "low": [n[3] for n in nen], "close": [n[4] for n in nen],
                       "volume": [1_000_000.0] * len(nen)})
    df["ngay"] = df["time"].dt.strftime("%Y-%m-%d")
    return {"XYZ": {"df": df, "nguon": "test", "tu": "2026-09-26", "bam": d35.bam_khung(df)}}


def _diem():
    return {"2026-10-02": 70, "2026-10-05": 70, "2026-10-06": 70}


def test_co_so_tai_lap_cat_lo_GIA_nguon_da_dieu_chinh_so_cu(tmp_path):
    so = tmp_path / "so.db"
    t = _dung_so(so)
    r = d35.phat_lai(so, t, _kho(), _diem(), sua=False)
    # nến 02/10 thấp 20000 ≤ cắt lỗ 28500 (thang cũ): cắt lỗ GIẢ ở nến đầu tiên; giá ra ≤ mở 20200
    assert r["row"]["exit_reason"] == "STOP_LOSS" and r["row"]["exit_date"][:10] == "2026-10-02"
    assert r["row"]["exit_price"] <= 20200.0 and r["dem_chinh"] == 0 and r["su_kien"] == []


def test_ban_sua_chinh_o_nen_dau_khong_con_cat_lo_va_khong_dong_dong_nao_khac(tmp_path):
    so = tmp_path / "so.db"
    t = _dung_so(so)
    r = d35.phat_lai(so, t, _kho(), _diem(), sua=True)
    assert r["dem_chinh"] == 1 and r["row"]["status"] == "OPEN"
    assert r["row"]["entry_price"] == pytest.approx(20000.0, rel=1e-9)
    assert r["row"]["stop_loss"] >= 19000.0 - 1e-6          # 28500 ÷ 1,5 = 19000; trailing chỉ nâng lên
    assert r["ban_giu_nguyen_ngoai_lenh"] is True
    nk = r["nhat_ky_sau"]
    assert nk["entry_price"] == pytest.approx(20000.0, rel=1e-9)
    assert nk["stop_loss_ban_dau"] == pytest.approx(19000.0, rel=1e-9)
    assert json.loads(nk["boi_canh"])["atr_pct"] == 2.0


def test_ban_sua_theo_toi_cuoi_du_lieu_dong_gia_dung_so_sach_va_gan_nhan(tmp_path):
    so = tmp_path / "so.db"
    t = _dung_so(so)
    r = d35.phat_lai(so, t, _kho(), _diem(), sua=True, dong_cuoi=True)
    assert r["ra_gia"] is True
    assert r["row"]["exit_reason"] == "HET_DU_LIEU" and r["row"]["exit_price"] == pytest.approx(20800.0)
    ret = r["row"]["exit_price"] / r["row"]["entry_price"] - 1
    assert ret == pytest.approx(0.04, rel=1e-9)             # 20800 / 20000 − 1


def test_nhan_f_0_98_chia_cho_f_nho_hon_nen_gia_vao_cao_hon(tmp_path):
    so = tmp_path / "so.db"
    t = _dung_so(so)
    r = d35.phat_lai(so, t, _kho(), _diem(), sua=True, nhan_f=0.98)
    assert r["row"]["entry_price"] == pytest.approx(30000.0 / (1.5 * 0.98), rel=1e-9)


def test_phat_lai_chi_doc_so_goc_bang_ro_va_khong_doi_tep(tmp_path):
    so = tmp_path / "so.db"
    t = _dung_so(so)
    truoc = d35.bam_tep(so)
    d35.phat_lai(so, t, _kho(), _diem(), sua=True)
    d35.phat_lai(so, t, _kho(), _diem(), sua=False)
    assert d35.bam_tep(so) == truoc
    with pytest.raises(sqlite3.OperationalError):
        d35.mo_so(so).execute("UPDATE trades SET size_pct=1")


def test_phat_lai_bo_qua_ngay_khong_co_dong_quyet_dinh(tmp_path):
    so = tmp_path / "so.db"
    t = _dung_so(so)
    r = d35.phat_lai(so, t, _kho(), {"2026-10-06": 70}, sua=True)     # chỉ nến 06/10 từng được xử lý
    assert [b["ngay"] for b in r["buoc"]] == ["2026-10-06"]


def test_so_o_so_ngay_10_ky_tu_va_cac_o_con_lai_tung_chu_so():
    a = {"exit_date": "2026-10-09 00:00:00", "exit_price": 21600.0, "exit_reason": "STOP_LOSS", "status": "CLOSED"}
    b = {"exit_date": "2026-10-09", "exit_price": 21600.000000000004, "exit_reason": "STOP_LOSS", "status": "CLOSED"}
    assert d35.so_o(a, b) == ["exit_price: 21600.0 ≠ 21600.000000000004"]
    assert d35.so_o(a, dict(a)) == []


def test_p95_hang_gan_nhat_va_mo_so_tu_choi_ghi():
    assert d35.p95([1.0, 2.0, 3.0, 4.0, 5.0]) == 5.0
    assert d35.CA_DUONG[122]["cua_so_den"] == "2026-10-09" and d35.CA_DUONG[128]["cua_so_den"] == "2026-10-29"
