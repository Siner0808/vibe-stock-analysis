"""Gác của `tools/do22_doc_ket_qua.py` — dụng cụ đọc ĐO 22 (BƯỚC 143).

Ba phép kiểm cơ học đứng TRƯỚC alpha trong tiêu chí đã ký; một dụng cụ đọc sai
là một tiêu chí không ai thi hành được, nên mỗi phép kiểm được thử ở CẢ HAI
chiều: đưa vào một ca ĐẠT (phải đạt) và một ca HỎNG (phải hỏng).
"""
import sqlite3
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
import do22_doc_ket_qua as d  # noqa: E402


def _lenh(ma, tin_hieu="2026-09-01", vao="2026-09-02", gia=30_100.0, ra=None,
          ly_do="SIGNAL_REVERSED", status="CLOSED", size=5.0):
    return {"symbol": ma, "signal_date": tin_hieu, "entry_date": vao,
            "entry_price": gia, "exit_date": "2026-09-09", "exit_price": ra,
            "exit_reason": ly_do, "status": status, "size_pct": size}


def _so(*lenh):
    return {(r["symbol"], r["signal_date"]): r for r in lenh}


# ─── P4 · giá vào HNX/UPCoM chia hết 100 ─────────────────────────────

def test_P4_dat_khi_sua_100_phan_tram_va_doi_chung_KHONG():
    dc = _so(_lenh("PVS", gia=30_050.0), _lenh("MSR", gia=30_100.0))
    sua = _so(_lenh("PVS", gia=30_100.0), _lenh("MSR", gia=30_100.0))
    kq = d.kiem(dc, sua, "ngay")
    assert kq["p4"] == {"sua": (2, 2), "doi_chung": (1, 2)}


def test_P4_khong_tinh_ma_HOSE():
    kq = d.kiem(_so(_lenh("ACB", gia=22_550.0)), _so(_lenh("ACB", gia=22_550.0)), "ngay")
    assert kq["p4"] == {"sua": (0, 0), "doi_chung": (0, 0)}


# ─── P5 · chế độ theo mã: mọi lệnh HOSE giống hệt ────────────────────

def test_P5_giong_het_thi_khong_co_lenh_khac():
    a = _so(_lenh("ACB", gia=22_550.0, ra=23_000.0), _lenh("PVS", gia=30_050.0))
    b = _so(_lenh("ACB", gia=22_550.0, ra=23_000.0), _lenh("PVS", gia=30_100.0))
    assert d.kiem(a, b, "ma")["p5_khac"] == []


@pytest.mark.parametrize("sua", [
    _so(_lenh("ACB", gia=22_600.0, ra=23_000.0)),              # khác giá vào
    _so(_lenh("ACB", gia=22_550.0, ra=23_050.0)),              # khác giá ra
    _so(_lenh("ACB", gia=22_550.0, ra=23_000.0, status="OPEN")),  # khác trạng thái
    {},                                                        # mất hẳn lệnh
])
def test_P5_bat_moi_kieu_lech_cua_lenh_HOSE(sua):
    doi_chung = _so(_lenh("ACB", gia=22_550.0, ra=23_000.0))
    assert d.kiem(doi_chung, sua, "ma")["p5_khac"] == [("ACB", "2026-09-01")]


def test_P5_bat_ca_lenh_HOSE_chi_co_o_ben_sua():
    kq = d.kiem({}, _so(_lenh("ACB")), "ma")
    assert kq["p5_khac"] == [("ACB", "2026-09-01")]


def test_P5_khong_tinh_che_do_ngay():
    kq = d.kiem(_so(_lenh("ACB", gia=1.0)), _so(_lenh("ACB", gia=2.0)), "ngay")
    assert kq["p5_khac"] == [], "ở chế độ theo ngày trần vốn nối các mã — P5 không áp"


# ─── P6 · giá vào ĐÃ SỬA >= đối chứng ────────────────────────────────

def test_P6_dat_khi_sua_khong_thap_hon():
    dc = _so(_lenh("PVS", gia=30_050.0), _lenh("HUT", gia=9_060.0))
    sua = _so(_lenh("PVS", gia=30_100.0), _lenh("HUT", gia=9_100.0))
    kq = d.kiem(dc, sua, "ngay")
    assert kq["p6_thap"] == [] and kq["n_chung_HNX_UPCOM"] == 2
    assert sorted(c for c, _ in kq["chenh"]) == [40.0, 50.0]


def test_P6_bat_gia_vao_sua_THAP_hon():
    kq = d.kiem(_so(_lenh("PVS", gia=30_100.0)), _so(_lenh("PVS", gia=30_050.0)), "ngay")
    assert kq["p6_thap"] == [("PVS", "2026-09-01")]


def test_P6_chi_so_lenh_CUNG_NGAY_VAO_khong_so_khac_ngay():
    dc = _so(_lenh("PVS", vao="2026-09-02", gia=30_100.0))
    sua = _so(_lenh("PVS", vao="2026-09-03", gia=29_000.0))     # khác ngày: không so
    kq = d.kiem(dc, sua, "ngay")
    assert kq["p6_thap"] == [] and kq["n_chung_HNX_UPCOM"] == 0


def test_chenh_gia_vao_chia_theo_dai_gia():
    dc = _so(_lenh("PVS", gia=30_000.0), _lenh("HUT", gia=9_000.0))
    sua = _so(_lenh("PVS", gia=30_100.0), _lenh("HUT", gia=9_100.0))
    theo = dict((k, v) for v, k in d.kiem(dc, sua, "ngay")["chenh"])
    assert theo == {"10-50k": 100.0, "<10k": 100.0}


# ─── đường dòng lệnh ─────────────────────────────────────────────────

def _ghi_db(duong: Path, lenh: list[dict]) -> Path:
    db = sqlite3.connect(duong)
    db.execute("CREATE TABLE trades (id INTEGER PRIMARY KEY, symbol, signal_date, "
               "entry_date, entry_price, exit_date, exit_price, exit_reason, status, size_pct)")
    for r in lenh:
        db.execute("INSERT INTO trades (symbol, signal_date, entry_date, entry_price, "
                   "exit_date, exit_price, exit_reason, status, size_pct) VALUES (?,?,?,?,?,?,?,?,?)",
                   tuple(r[k] for k in d.g20.COT))
    db.commit()
    db.close()
    return duong


def test_main_thoat_0_khi_dat_va_1_khi_hong(tmp_path, capsys):
    dc = _ghi_db(tmp_path / "dc.db", [_lenh("PVS", gia=30_050.0), _lenh("ACB", gia=22_550.0)])
    tot = _ghi_db(tmp_path / "tot.db", [_lenh("PVS", gia=30_100.0), _lenh("ACB", gia=22_550.0)])
    xau = _ghi_db(tmp_path / "xau.db", [_lenh("PVS", gia=30_050.0), _lenh("ACB", gia=22_550.0)])
    assert d.main(["--doi-chung", str(dc), "--sua", str(tot), "--che-do", "ma"]) == 0
    assert "ĐẠT" in capsys.readouterr().out
    assert d.main(["--doi-chung", str(dc), "--sua", str(xau), "--che-do", "ma"]) == 1, (
        "sửa mà giá vào PVS vẫn 30.050đ (không chia hết 100) phải HỎNG P4")


def test_main_thoat_2_khi_thieu_file(tmp_path, capsys):
    assert d.main(["--doi-chung", str(tmp_path / "khong.db"),
                   "--sua", str(tmp_path / "khong2.db"), "--che-do", "ma"]) == 2
    assert "CHƯA KIỂM ĐƯỢC" in capsys.readouterr().out


def test_main_P4_HONG_khi_doi_chung_cung_dat_100_phan_tram(tmp_path, capsys):
    """Đối chứng dương: nếu cả luồng đối chứng cũng chia hết 100 thì phép kiểm
    không phân biệt được gì — phải HỎNG chứ không được báo ĐẠT."""
    dc = _ghi_db(tmp_path / "dc.db", [_lenh("PVS", gia=30_100.0)])
    sua = _ghi_db(tmp_path / "sua.db", [_lenh("PVS", gia=30_100.0)])
    assert d.main(["--doi-chung", str(dc), "--sua", str(sua), "--che-do", "ngay"]) == 1
    assert "HỎNG" in capsys.readouterr().out


def test_main_P4_HONG_khi_luong_sua_khong_co_lenh_HNX_UPCoM(tmp_path, capsys):
    """0/0 không phải 100%: không có lệnh nào để kiểm thì không được báo ĐẠT."""
    dc = _ghi_db(tmp_path / "dc.db", [_lenh("ACB", gia=22_550.0)])
    sua = _ghi_db(tmp_path / "sua.db", [_lenh("ACB", gia=22_550.0)])
    assert d.main(["--doi-chung", str(dc), "--sua", str(sua), "--che-do", "ngay"]) == 1
    assert "HỎNG" in capsys.readouterr().out
