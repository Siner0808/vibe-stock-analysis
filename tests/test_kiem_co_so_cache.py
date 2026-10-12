"""BƯỚC 180 — `tools/kiem_co_so_cache.py`: dụng cụ soát cache CHỈ ĐỌC.

Số tính tay trên chuỗi giả. Không mạng, không đụng `backtest/cache` của repo.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

from data_quality import VN_TZ  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "kiem_co_so_cache", GOC / "tools" / "kiem_co_so_cache.py")
kc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kc)


def _df(ngay, close):
    return pd.DataFrame({"time": ngay, "open": close, "high": close,
                         "low": close, "close": close,
                         "volume": [1000] * len(ngay)})


def _ghi(thu_muc: Path, ma: str, ngay, close) -> None:
    _df(ngay, close).to_csv(thu_muc / f"{ma}.csv", index=False)


NGAY = ["2026-08-05", "2026-08-06", "2026-08-07", "2026-08-10", "2026-08-11"]


# ───────────────────────── tim_buoc — hàm thuần ─────────────────────────

def test_bac_tru_18_phan_tram_cua_HOSE_bi_bao_dung_ngay():
    """100 → 100 → 82,13: 82,13 / 100 − 1 = −17,87% (đúng số SSI ngày
    2026-08-10 mà leader đo). Biên HOSE 7% + 0,5 điểm = 7,5% < 17,87%."""
    d = _df(NGAY, [100.0, 100.0, 100.0, 82.13, 82.0])
    kq = kc.tim_buoc(d, "HOSE")
    assert len(kq) == 1
    ngay, truoc, pct = kq[0]
    assert (ngay, truoc) == ("2026-08-10", "2026-08-07")
    assert pct == pytest.approx(-17.87, abs=1e-9)


def test_bac_9_9_phan_tram_la_bien_binh_thuong_cua_HNX_nhung_vuot_HOSE():
    """+9,9%: HNX biên 10% (+0,5 = 10,5%) → không báo; HOSE 7,5% → báo."""
    d = _df(NGAY, [100.0, 100.0, 100.0, 109.9, 109.9])
    assert kc.tim_buoc(d, "HNX") == []
    assert len(kc.tim_buoc(d, "HOSE")) == 1


def test_upcom_bien_15_phan_tram():
    d = _df(NGAY, [100.0, 114.0, 114.0, 114.0, 114.0])
    assert kc.tim_buoc(d, "UPCOM") == []              # +14% < 15,5%
    d = _df(NGAY, [100.0, 116.0, 116.0, 116.0, 116.0])
    assert len(kc.tim_buoc(d, "UPCOM")) == 1          # +16% > 15,5%


def test_ranh_gioi_hose_hai_phia():
    """7,4% không báo, 7,6% báo (ngưỡng 7,5%)."""
    assert kc.tim_buoc(_df(NGAY[:2], [100.0, 107.4]), "HOSE") == []
    assert len(kc.tim_buoc(_df(NGAY[:2], [100.0, 107.6]), "HOSE")) == 1


def test_gia_vo_nghia_bi_bo_khoi_chuoi():
    d = _df(NGAY, [100.0, float("nan"), 0.0, 100.0, 100.0])
    assert kc.tim_buoc(d, "HOSE") == []


def test_vung_so_voi_moc_du_lieu_sach():
    moc = {"ACB": "2021-10-14"}
    assert kc.vung("ACB", "2021-01-05", moc) == "ngoài mẫu"
    assert kc.vung("ACB", "2021-10-14", moc) == "trong mẫu"
    assert kc.vung("ACB", "2026-08-10", moc) == "trong mẫu"
    assert kc.vung("XYZ", "2026-08-10", moc) == "không có mốc"


def test_quet_ma_ngoai_bang_khong_lui_ve_HOSE():
    """IDC (HNX, KHÔNG có trong BANG_SAN) bước +9,9% — nếu lùi về HOSE sẽ báo
    nhầm. Phải ra CHƯA KIỂM ĐƯỢC, 0 bước. SSI (HOSE) cùng bước thì báo."""
    from san_giao_dich import tra_san
    assert tra_san("IDC") is None and tra_san("SSI") == "HOSE"
    chuoi = _df(NGAY, [100.0, 100.0, 100.0, 109.9, 109.9])
    buoc, chua = kc.quet({"IDC": chuoi, "SSI": chuoi}, {})
    assert [b[0] for b in buoc] == ["SSI"]
    assert [c[0] for c in chua] == ["IDC"]
    assert "HOSE" in chua[0][1] and "không lùi" in chua[0][1]


# ───────────────────────────── dòng lệnh ─────────────────────────────

def test_cli_co_buoc_vuot_bien_thoat_1_va_in_dung_ngay(tmp_path, capsys):
    _ghi(tmp_path, "SSI", NGAY, [100.0, 100.0, 100.0, 82.13, 82.0])
    ma = kc.main(["--cache", str(tmp_path)])
    ra = capsys.readouterr().out
    assert ma == 1
    assert "SSI" in ra and "2026-08-10" in ra and "-17.87%" in ra
    assert "trước 2026-08-07" in ra
    assert "1 bước vượt biên ở 1 mã" in ra


def test_cli_sach_thoat_0(tmp_path, capsys):
    _ghi(tmp_path, "SSI", NGAY, [100.0, 101.0, 102.0, 101.0, 100.0])
    assert kc.main(["--cache", str(tmp_path)]) == 0
    assert "0 bước vượt biên" in capsys.readouterr().out


def test_cli_hnx_9_9_khong_bao_va_ma_ngoai_bang_chua_kiem_duoc(tmp_path, capsys):
    """MBS (HNX, trong bảng) +9,9% → sạch; IDC −18% → CHƯA KIỂM ĐƯỢC chứ
    KHÔNG báo vượt biên; mã thoát vẫn 0."""
    _ghi(tmp_path, "MBS", NGAY, [100.0, 100.0, 100.0, 109.9, 109.9])
    _ghi(tmp_path, "IDC", NGAY, [100.0, 100.0, 100.0, 82.0, 82.0])
    ma = kc.main(["--cache", str(tmp_path)])
    ra = capsys.readouterr().out
    assert ma == 0
    assert "VƯỢT BIÊN" not in ra
    assert "CHƯA KIỂM ĐƯỢC IDC" in ra and "1 mã CHƯA KIỂM ĐƯỢC" in ra


def test_cli_in_vung_theo_moc_that(tmp_path, capsys):
    """ACB có mốc 2021-10-14 trong `docs/moc_du_lieu_sach.json`: bậc ngày
    2021-01-06 là NGOÀI MẪU, bậc 2026-08-10 là TRONG MẪU."""
    _ghi(tmp_path, "ACB",
         ["2021-01-04", "2021-01-05", "2021-01-06", "2026-08-07", "2026-08-10"],
         [100.0, 100.0, 80.0, 80.0, 60.0])
    kc.main(["--cache", str(tmp_path)])
    ra = capsys.readouterr().out
    assert "2021-01-06" in ra and "[ngoài mẫu]" in ra
    assert "2026-08-10" in ra and "[trong mẫu]" in ra


def test_cli_khong_doc_duoc_cache_thoat_2(tmp_path, capsys):
    assert kc.main(["--cache", str(tmp_path / "khong_co")]) == 2
    (tmp_path / "rong").mkdir()
    assert kc.main(["--cache", str(tmp_path / "rong")]) == 2
    (tmp_path / "hong").mkdir()
    (tmp_path / "hong" / "SSI.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    assert kc.main(["--cache", str(tmp_path / "hong")]) == 2
    assert "thiếu cột" in capsys.readouterr().out


def test_cli_khong_ghi_gi_vao_thu_muc_cache(tmp_path):
    _ghi(tmp_path, "SSI", NGAY, [100.0, 100.0, 100.0, 82.13, 82.0])
    truoc = {p.name: p.read_bytes() for p in tmp_path.glob("*")}
    kc.main(["--cache", str(tmp_path)])
    sau = {p.name: p.read_bytes() for p in tmp_path.glob("*")}
    assert truoc == sau


# ───────────────────── --doi-chieu-nguon (nguồn giả) ─────────────────────

def test_doi_chieu_dung_ham_so_co_so_voi_nguon_gia(tmp_path):
    """HDB: mới = cũ × 0,77 → LECH_CO_SO; ACB: mới = cũ → CUNG_CO_SO; mã không
    kéo được → None. Cache KHÔNG bị ghi."""
    ngay = list(pd.bdate_range("2026-08-03", periods=9).strftime("%Y-%m-%d"))
    gia = [100.0, 102.0, 104.0, 106.0, 108.0, 110.0, 112.0, 114.0]
    cache = {"HDB": _df(ngay[:8], gia), "ACB": _df(ngay[:8], gia),
             "VCB": _df(ngay[:8], gia)}

    def nguon(ma, start, end):
        if ma == "HDB":
            return _df(ngay, [round(g * 0.77, 4) for g in gia] + [88.0])
        if ma == "ACB":
            return _df(ngay, gia + [115.0])
        return None

    ghi_nho = {k: v.copy() for k, v in cache.items()}
    kq = kc.doi_chieu(cache, nguon, datetime(2026, 9, 30, 16, 0, tzinfo=VN_TZ))
    assert kq["HDB"].nhan == "LECH_CO_SO"
    assert kq["HDB"].ty_le_min == pytest.approx(0.77, abs=1e-9)
    assert kq["ACB"].nhan == "CUNG_CO_SO"
    assert kq["VCB"] is None
    for k in cache:
        pd.testing.assert_frame_equal(cache[k], ghi_nho[k])


def test_doi_chieu_cua_so_keo_lui_tu_nen_cuoi():
    """Nến cuối 2026-08-12, `so_ngay` 120 → start = 2026-04-14."""
    ngay = list(pd.bdate_range("2026-08-03", periods=8).strftime("%Y-%m-%d"))
    hoi = []
    kc.doi_chieu({"X": _df(ngay, [1.0] * 8)},
                 lambda m, s, e: hoi.append((m, s, e)),
                 datetime(2026, 9, 30, 16, 0, tzinfo=VN_TZ), 120)
    # Tính tay: 08-12 lùi về 07-12 là 31 ngày, 06-12 là 30, 05-12 là 31,
    # 04-12 là 30 → 122 ngày; 120 ngày thì dừng sau 04-12 hai ngày = 04-14.
    assert hoi == [("X", "2026-04-14", "2026-09-30")]


# ───────────────────────── gác AST: chỉ đọc ─────────────────────────

def test_dung_cu_khong_goi_ham_ghi():
    cay = ast.parse((GOC / "tools" / "kiem_co_so_cache.py")
                    .read_text(encoding="utf-8"))
    cam = {"to_csv", "write_text", "write_bytes", "write", "writelines",
           "mkdir", "unlink", "rename", "replace", "remove", "rmtree",
           "touch", "to_json", "to_parquet", "dump", "open"}
    thay = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            ten = getattr(n.func, "attr", getattr(n.func, "id", ""))
            if ten in cam:
                thay.append((ten, n.lineno))
    assert not thay, f"dụng cụ CHỈ ĐỌC mà gọi hàm ghi: {thay}"


def test_dung_cu_tra_san_bang_ham_cua_bang_va_khong_dung_san_cua():
    """`san_cua` lùi về HOSE cho mã ngoài bảng — cấm. Phải là `tra_san`."""
    cay = ast.parse((GOC / "tools" / "kiem_co_so_cache.py")
                    .read_text(encoding="utf-8"))
    goi = {getattr(n.func, "id", getattr(n.func, "attr", ""))
           for n in ast.walk(cay) if isinstance(n, ast.Call)}
    assert "tra_san" in goi and "san_cua" not in goi
    nhap = {a.name for n in ast.walk(cay) if isinstance(n, ast.ImportFrom)
            for a in n.names}
    assert "san_cua" not in nhap


def test_dung_cu_dung_dung_so_co_so_cua_extend_history():
    """Một nguồn sự thật: `--doi-chieu-nguon` nhập `so_co_so` từ
    `backtest.data`, không dựng phép so riêng."""
    cay = ast.parse((GOC / "tools" / "kiem_co_so_cache.py")
                    .read_text(encoding="utf-8"))
    nhap = [(n.module, a.name) for n in ast.walk(cay)
            if isinstance(n, ast.ImportFrom) for a in n.names]
    assert ("backtest.data", "so_co_so") in nhap
    assert ("backtest.data", "fetch_one") in nhap
