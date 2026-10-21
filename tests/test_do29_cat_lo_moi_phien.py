"""BƯỚC 212 — dụng cụ ĐO 29 (`tools/do29_cat_lo_moi_phien.py`): đối chứng (iii), (iv).

Bản ký: `docs/TIEU-CHI-DOC-TRUOC.md`, `## ĐO 29` (commit `c4d01ed`, trước dụng cụ).
Thế giới giả, đáp án tính tay — FPT 12 phiên từ 01/09/2026, mốc sạch xa trong tương
lai nên cả 12 phiên là OOS; `min_history` 4, `stride` 2, `do_tre_khop` 1:

  lưới chấm   : chỉ số 4, 6, 8, 10   (05/09 → ngày 4 là 07/09 ...)
  chỉ-khớp    : chỉ số 5, 7, 9, 11

  Lệnh 1 FPT tín hiệu 04/09: A ra chỉ số 6 (phiên chấm) bằng STOP_LOSS;
                             B ra chỉ số 5 (phiên chỉ-khớp) bằng STOP_LOSS.
  Lệnh GIL tín hiệu 14/12/2022 (ca đã ký): B ra 21/12/2022 bằng STOP_LOSS ở 13.500.
"""
from __future__ import annotations

import ast
import inspect
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import do29_cat_lo_moi_phien as do29  # noqa: E402
import walkforward  # noqa: E402

NGAY = list(pd.bdate_range("2026-09-01", periods=12).strftime("%Y-%m-%d"))
THAM_SO = {"stride": 2, "min_history": 4, "do_tre_khop": 1}
COT = ("id", "symbol", "signal_date", "entry_date", "entry_price", "exit_date",
       "exit_price", "exit_reason", "status", "size_pct")


def _lenh(i, ma, tin_hieu, vao, gia_vao, ra, gia_ra, ly_do="STOP_LOSS"):
    return (i, ma, tin_hieu, vao, gia_vao, ra, gia_ra, ly_do, "CLOSED", 10.0)


def _so(duong: Path, dong: list[tuple]) -> Path:
    db = sqlite3.connect(duong)
    db.execute(f"CREATE TABLE trades ({', '.join(COT)})")
    db.executemany(f"INSERT INTO trades VALUES ({', '.join('?' * len(COT))})", dong)
    db.commit()
    db.close()
    return duong


GIL_TOT = _lenh(9, "GIL", "2022-12-14", "2022-12-15", 19_000.0, "2022-12-21", 13_500.0)


@pytest.fixture
def the_gioi(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    pd.DataFrame({"time": NGAY, "open": 30.0, "high": 30.5, "low": 29.5, "close": 30.0,
                  "volume": 1e6}).to_csv(cache / "FPT.csv", index=False)
    monkeypatch.setattr(walkforward, "nap_moc_sach", lambda *a, **k: {"FPT": "2099-01-01"})
    monkeypatch.setattr(do29, "tham_so_luot", lambda: dict(THAM_SO))
    a = _so(tmp_path / "a.db", [
        _lenh(1, "FPT", NGAY[3], NGAY[4], 30_000.0, NGAY[6], 27_000.0),
        _lenh(9, "GIL", "2022-12-14", "2022-12-15", 19_000.0, "2022-12-22", 16_200.0)])
    return cache, a, tmp_path


def _chay(the_gioi, dong_b):
    cache, a, tmp = the_gioi
    b = _so(tmp / "b.db", dong_b)
    return do29.main(["--a", str(a), "--b", str(b), "--cache", str(cache)])


def test_LICH_CHI_KHOP_tinh_tay_qua_diem_ghe(the_gioi):
    cache, _, _ = the_gioi
    ngay, ck = do29.nap_lich(cache, ["FPT"], THAM_SO)
    assert ngay["FPT"] == NGAY
    assert ck["FPT"] == {NGAY[5], NGAY[7], NGAY[9], NGAY[11]}


def test_B_TOT_thi_iii_iv_DAT_va_dem_dung(the_gioi, capsys):
    kq = _chay(the_gioi, [_lenh(1, "FPT", NGAY[3], NGAY[4], 30_000.0, NGAY[5], 28_000.0),
                          GIL_TOT])
    ra = capsys.readouterr().out
    assert kq == 0, ra
    assert "(iv) cắt lỗ ở phiên chỉ-khớp: A 0 · B 1 → ĐẠT" in ra
    assert "B ra sớm hơn A (số phiên OOS): {1: 1}" in ra


def test_B_KHONG_co_cat_lo_o_phien_chi_khop_thi_iv_TRUOT(the_gioi, capsys):
    """Mã sửa không chạy trên đường walk-forward: B y hệt A."""
    kq = _chay(the_gioi, [_lenh(1, "FPT", NGAY[3], NGAY[4], 30_000.0, NGAY[6], 27_000.0),
                          GIL_TOT])
    assert kq == 1 and "TRƯỢT (cần A = 0" in capsys.readouterr().out


def test_A_co_cat_lo_o_phien_chi_khop_thi_iv_TRUOT(the_gioi, capsys):
    cache, _, tmp = the_gioi
    a = _so(tmp / "a2.db", [_lenh(1, "FPT", NGAY[3], NGAY[4], 30_000.0, NGAY[7], 27_000.0)])
    b = _so(tmp / "b2.db", [_lenh(1, "FPT", NGAY[3], NGAY[4], 30_000.0, NGAY[5], 28_000.0),
                            GIL_TOT])
    assert do29.main(["--a", str(a), "--b", str(b), "--cache", str(cache)]) == 1


def test_CAT_LO_o_phien_CHAM_khong_tinh_la_chi_khop(the_gioi):
    """Chỉ cắt lỗ ở phiên CHỈ-KHỚP vào (iv); lý do khác ở phiên chỉ-khớp cũng không."""
    so = {("FPT", "x"): {"symbol": "FPT", "status": "CLOSED", "exit_reason": "STOP_LOSS",
                         "exit_date": NGAY[6]},
          ("FPT", "y"): {"symbol": "FPT", "status": "CLOSED", "exit_reason": "MAX_HOLD",
                         "exit_date": NGAY[5]},
          ("FPT", "z"): {"symbol": "FPT", "status": "CLOSED", "exit_reason": "STOP_LOSS",
                         "exit_date": NGAY[9]}}
    ck = {"FPT": {NGAY[5], NGAY[7], NGAY[9], NGAY[11]}}
    assert do29.cat_lo_chi_khop(so, ck) == [("FPT", "z")]


@pytest.mark.parametrize("gil, mo_ta", [
    (_lenh(9, "GIL", "2022-12-14", "2022-12-15", 19_000.0, "2022-12-22", 13_500.0), "ra trễ"),
    (_lenh(9, "GIL", "2022-12-14", "2022-12-15", 19_000.0, "2022-12-21", 13_600.0), "giá cao"),
    (_lenh(9, "GIL", "2022-12-14", "2022-12-15", 19_000.0, "2022-12-21", 13_500.0, "MAX_HOLD"),
     "sai lý do"),
])
def test_CA_GIL_sai_thi_iii_TRUOT(the_gioi, gil, mo_ta):
    kq = _chay(the_gioi, [_lenh(1, "FPT", NGAY[3], NGAY[4], 30_000.0, NGAY[5], 28_000.0), gil])
    assert kq == 1, mo_ta


def test_THIEU_GIL_o_B_thi_iii_TRUOT(the_gioi):
    assert _chay(the_gioi, [_lenh(1, "FPT", NGAY[3], NGAY[4], 30_000.0, NGAY[5], 28_000.0)]) == 1


def test_DOI_NGAY_RA_tinh_tay(the_gioi):
    cache, _, _ = the_gioi
    ngay, _ = do29.nap_lich(cache, ["FPT"], THAM_SO)
    a = {("FPT", "t"): {"symbol": "FPT", "status": "CLOSED", "entry_date": NGAY[4],
                        "entry_price": 30_000.0, "exit_date": NGAY[8], "exit_price": 27_000.0}}
    b = {("FPT", "t"): {"symbol": "FPT", "status": "CLOSED", "entry_date": NGAY[4],
                        "entry_price": 30_000.0, "exit_date": NGAY[5], "exit_price": 28_500.0}}
    (x,) = do29.doi_ngay_ra(a, b, ngay)
    assert x["delta"] == pytest.approx(28_500 / 30_000 - 27_000 / 30_000)
    assert x["som_hon"] == 3


def test_THIEU_TEP_va_LICH_RONG_la_CHUA_KIEM_DUOC(the_gioi, tmp_path):
    cache, a, _ = the_gioi
    assert do29.main(["--a", str(a), "--b", str(tmp_path / "khong.db"),
                      "--cache", str(cache)]) == 2
    rong = tmp_path / "rong"
    rong.mkdir()
    b = _so(tmp_path / "b3.db", [GIL_TOT])
    assert do29.main(["--a", str(a), "--b", str(b), "--cache", str(rong)]) == 2


def test_THAM_SO_LUOT_suy_tu_mac_dinh_cua_walkforward_chay():
    """Không gõ tay 2/60/1: lấy đúng mặc định `walkforward.chay` (lượt do1 không truyền)."""
    ps = inspect.signature(walkforward.chay).parameters
    assert do29.tham_so_luot() == {k: ps[k].default
                                  for k in ("stride", "min_history", "do_tre_khop")}


def test_LICH_dung_HAM_CUA_MAY_DO_khong_tu_dung_lai():
    cay = ast.parse((GOC / "tools" / "do29_cat_lo_moi_phien.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "lich_mot_ma")
    goi = {(n.func.value.id, n.func.attr) for n in ast.walk(ham)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and isinstance(n.func.value, ast.Name)}
    assert {("walkforward", "diem_ghe"), ("walkforward", "chia_vung")} <= goi
