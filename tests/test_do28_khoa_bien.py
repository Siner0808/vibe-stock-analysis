"""BƯỚC 209 — dụng cụ ĐO 28 (`tools/do28_khoa_bien.py`): đối chứng (iii) và số đếm.

Bản ký: `docs/TIEU-CHI-DOC-TRUOC.md`, `## ĐO 28` (commit `059e456`, trước dụng cụ).
Thế giới giả, đáp án tính tay — FPT (HOSE, biên 7%), sáu phiên:

  d0 01/09 đóng 30,00 · d1 02/09 MỘT GIÁ 32,07 (+6,9% ⇒ KỊCH TRẦN)
  d2 03/09 hai giá · d3 04/09 MỘT GIÁ 29,86 (−6,9% so 32,07 ⇒ KỊCH SÀN)
  d4 05/09 MỘT GIÁ 27,80 (−6,9% ⇒ KỊCH SÀN) · d5 08/09 hai giá

  Lệnh 1 (tín hiệu 20/08): A ra d3 (STOP_LOSS) ⇒ thuộc (iii).
  Lệnh 2 (tín hiệu 01/09): A VÀO d1 ⇒ thuộc (iii).
  Lệnh 3 (tín hiệu 25/08): vào/ra phiên thường ⇒ ngoài (iii).
  B tốt: lệnh 1 ra d5 sau chuỗi d3–d4 (2 phiên kịch sàn); lệnh 2 `HUY` lý do kịch trần.
  B xấu: lệnh 1 y hệt A ⇒ (iii) TRƯỢT, mã thoát 1.
"""
from __future__ import annotations

import ast
import sqlite3
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
sys.path.insert(0, str(GOC))

import do28_khoa_bien as do28  # noqa: E402
import paper_trading as pt  # noqa: E402

NEN = [  # time, open, high, low, close
    ("2026-09-01", 30.0, 30.2, 29.8, 30.0),
    ("2026-09-02", 32.07, 32.07, 32.07, 32.07),
    ("2026-09-03", 32.0, 32.3, 31.8, 32.07),
    ("2026-09-04", 29.86, 29.86, 29.86, 29.86),
    ("2026-09-05", 27.80, 27.80, 27.80, 27.80),
    ("2026-09-08", 27.0, 28.0, 26.5, 27.5),
]
COT = ("id", "symbol", "signal_date", "entry_date", "entry_price", "exit_date",
       "exit_price", "exit_reason", "status", "size_pct")
LENH_A = [
    (1, "FPT", "2026-08-20", "2026-08-21", 30000.0, "2026-09-04", 29860.0, "STOP_LOSS", "CLOSED", 5.0),
    (2, "FPT", "2026-09-01", "2026-09-02", 32070.0, "2026-09-08", 27000.0, "STOP_LOSS", "CLOSED", 5.0),
    (3, "FPT", "2026-08-25", "2026-08-26", 30000.0, "2026-09-03", 32000.0, "MAX_HOLD", "CLOSED", 5.0),
]


def _so(duong: Path, dong) -> Path:
    db = sqlite3.connect(duong)
    db.execute(f"CREATE TABLE trades ({', '.join(COT)})")
    db.executemany(f"INSERT INTO trades VALUES ({','.join('?' * len(COT))})", dong)
    db.commit()
    db.close()
    return duong


@pytest.fixture
def the_gioi(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "FPT.csv").write_text(
        "time,open,high,low,close,volume\n"
        + "".join(f"{t},{o},{h},{l},{c},100000\n" for t, o, h, l, c in NEN),
        encoding="utf-8")
    a = _so(tmp_path / "a.db", LENH_A)
    b_tot = _so(tmp_path / "b_tot.db", [
        (1, "FPT", "2026-08-20", "2026-08-21", 30000.0, "2026-09-08", 27000.0, "STOP_LOSS", "CLOSED", 5.0),
        (2, "FPT", "2026-09-01", None, None, "2026-09-02", None, pt.LY_DO_KICH_TRAN, "HUY", 5.0),
        LENH_A[2]])
    b_xau = _so(tmp_path / "b_xau.db", [LENH_A[0], LENH_A[1], LENH_A[2]])
    return cache, a, b_tot, b_xau


def test_NAP_KHOA_tinh_tay_dung_ba_phien(the_gioi):
    cache, *_ = the_gioi
    ngay, khoa = do28.nap_khoa(cache, "FPT")
    assert ngay == [t for t, *_ in NEN]
    assert khoa == {"2026-09-02": do28.KICH_TRAN, "2026-09-04": do28.KICH_SAN,
                    "2026-09-05": do28.KICH_SAN}


def test_B_TOT_thi_iii_DAT_va_dem_dung(the_gioi, capsys):
    cache, a, b_tot, _ = the_gioi
    assert do28.main(["--a", str(a), "--b", str(b_tot), "--cache", str(cache)]) == 0
    ra = capsys.readouterr().out
    assert "(iii) lệnh A vào ở KỊCH TRẦN hoặc ra ở KỊCH SÀN: 2" in ra
    assert "(iii) ĐẠT: 2/2" in ra
    assert "B — HUY vì kịch trần: 1" in ra
    assert "chuỗi dài nhất 2 phiên" in ra


def test_B_XAU_ma_sua_KHONG_chay_thi_iii_TRUOT(the_gioi, capsys):
    cache, a, _, b_xau = the_gioi
    assert do28.main(["--a", str(a), "--b", str(b_xau), "--cache", str(cache)]) == 1
    assert "(iii) TRƯỢT: 0/2" in capsys.readouterr().out


def test_QUAN_THE_RONG_la_CHUA_KIEM_DUOC_khong_phai_DAT(the_gioi, tmp_path):
    cache, *_ = the_gioi
    chi_thuong = _so(tmp_path / "chi_thuong.db", [LENH_A[2]])
    assert do28.main(["--a", str(chi_thuong), "--b", str(chi_thuong),
                      "--cache", str(cache)]) == 2


def test_THIEU_TEP_la_CHUA_KIEM_DUOC(the_gioi, tmp_path):
    cache, a, *_ = the_gioi
    assert do28.main(["--a", str(a), "--b", str(tmp_path / "khong_co.db"),
                      "--cache", str(cache)]) == 2


def test_DUNG_CU_dung_khoa_bien_CUA_MO_HINH_khong_tu_dinh_nghia_lai():
    """Một định nghĩa khoá biên: dụng cụ gọi `vong_doi_lenh.khoa_bien`, không mang
    hệ số 0,9 hay biên độ gõ tay của riêng nó."""
    cay = ast.parse((GOC / "tools" / "do28_khoa_bien.py").read_text(encoding="utf-8"))
    goi = {n.func.id for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "khoa_bien" in goi
    so_thuc = {n.value for n in ast.walk(cay)
               if isinstance(n, ast.Constant) and isinstance(n.value, float)}
    assert not so_thuc & {0.9, 0.07, 0.1, 0.15}, so_thuc
