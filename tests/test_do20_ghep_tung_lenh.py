"""Gác của dụng cụ đọc ĐO 20 — `tools/do20_ghep_tung_lenh.py`.

MÁY ĐO cũng phải bị nghi như GÁC (SKILL.md Bước 3, điều 4): một máy ghép
sai thì không đỏ, nó chỉ in ra một con số nghe hợp lý. Nên mỗi ngăn phân
loại được thử bằng một ca biết trước đáp án.
"""
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "tools"))
import do20_ghep_tung_lenh as g  # noqa: E402

COT = g.COT


def _so(duong: Path, dong: list[tuple]) -> Path:
    db = sqlite3.connect(duong)
    db.execute(f"CREATE TABLE trades (id INTEGER PRIMARY KEY, {', '.join(COT)})")
    for d in dong:
        db.execute(f"INSERT INTO trades ({', '.join(COT)}) VALUES "
                   f"({','.join('?' * len(COT))})", d)
    db.commit()
    db.close()
    return duong


def _lenh(ma, tin_hieu, vao="2024-01-03", gia=100.0, status="CLOSED",
          ra="2024-01-10", gia_ra=105.0, ly_do="STOP_LOSS"):
    return (ma, f"{tin_hieu} 00:00:00", vao, gia, ra, gia_ra, ly_do, status, 6.7)


def test_GHEP_phan_dung_bon_ngan(tmp_path):
    a = g.doc_so(_so(tmp_path / "a.db", [
        _lenh("AAA", "2024-01-02"),                       # giống hệt
        _lenh("BBB", "2024-01-02"),                       # khác giá ra
        _lenh("CCC", "2024-01-02"),                       # chỉ đối chứng
    ]))
    b = g.doc_so(_so(tmp_path / "b.db", [
        _lenh("AAA", "2024-01-02"),
        _lenh("BBB", "2024-01-02", gia_ra=99.0),
        _lenh("DDD", "2024-01-02", vao=None, gia=None, status="HUY",
              gia_ra=None, ly_do="sàn từ chối lệnh"),     # chỉ bên sửa
    ]))
    k = g.ghep(a, b)
    assert k["giong_het"] == [("AAA", "2024-01-02")]
    assert k["khac"] == [("BBB", "2024-01-02")]
    assert k["chi_doi_chung"] == [("CCC", "2024-01-02")]
    assert k["chi_sua"] == [("DDD", "2024-01-02")]


def test_GHEP_khoa_theo_NGAY_khong_theo_chuoi_gio(tmp_path):
    """Hai nguồn trả hậu tố giờ khác nhau cho cùng một phiên (audit BƯỚC 121,
    ma_giao_dich-06). Ghép theo chuỗi nguyên thì một lệnh thành HAI."""
    a = g.doc_so(_so(tmp_path / "a.db", [_lenh("AAA", "2024-01-02")]))
    dong = list(_lenh("AAA", "2024-01-02"))
    dong[1] = "2024-01-02 07:00:00"
    b = g.doc_so(_so(tmp_path / "b.db", [tuple(dong)]))
    assert g.ghep(a, b)["giong_het"] == [("AAA", "2024-01-02")]


def test_DOC_SO_no_khi_mot_khoa_xuat_hien_HAI_lan(tmp_path):
    p = _so(tmp_path / "a.db", [_lenh("AAA", "2024-01-02"),
                                _lenh("AAA", "2024-01-02", gia=101.0)])
    with pytest.raises(ValueError, match="hai lần"):
        g.doc_so(p)


def test_LECH_MO_CUA_doc_dung_phien_truoc(tmp_path):
    (tmp_path / "PVS.csv").write_text(
        "time,open,high,low,close,volume\n"
        "2024-01-02,30,31,29,30,100\n"
        "2024-01-03,27,28,27,27.5,100\n", encoding="utf-8")
    assert g.lech_mo_cua(tmp_path, "PVS", "2024-01-03") == pytest.approx(-0.10)
    assert g.lech_mo_cua(tmp_path, "PVS", "2024-01-02") is None   # không có phiên trước
    assert g.lech_mo_cua(tmp_path, "XXX", "2024-01-03") is None


def test_DUNG_CU_thoat_2_khi_THIEU_so(tmp_path):
    r = subprocess.run(
        [sys.executable, str(GOC / "tools" / "do20_ghep_tung_lenh.py"),
         "--doi-chung", str(tmp_path / "khong_co.db"),
         "--sua", str(tmp_path / "cung_khong.db")],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 2, r.stderr
    assert "CHUA KIEM DUOC" in r.stderr
