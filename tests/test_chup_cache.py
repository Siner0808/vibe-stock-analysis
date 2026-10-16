"""BƯỚC 200 — chụp cache giá vào kho TRƯỚC mỗi lượt ghi (người dùng 16/10/2026, phương án b).

Ca gốc (`docs/STATE.md` BƯỚC 199): lượt làm tươi 12/10/2026 thay cả chuỗi 39 mã mà
không ai sao lưu; số đo ĐO 22 (−1,68%) chỉ tái lập được nhờ một bản sao tình cờ.
Mọi lượt ghi CSV vào cache nay đi qua `backtest.data.ghi_cache`, và lượt ghi đầu của
mỗi tiến trình chụp nguyên cache cũ vào kho trước.

Mọi test ở đây dùng thư mục TẠM cho cả cache lẫn kho. Kho THẬT bị `tests/conftest.py`
(`kho_luu_cache_tat`) tắt cho mọi test. Không mạng, không đồng hồ thật.
"""
from __future__ import annotations

import ast
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import conftest  # noqa: E402
from backtest import data as bt  # noqa: E402
from data_quality import VN_TZ  # noqa: E402

SAU_DONG = datetime(2026, 9, 30, 16, 0, tzinfo=VN_TZ)

#: mtime đặt tay cho cache tạm: ảnh chụp phải mang ngày này (20261014) trong tên.
MTIME_CU = datetime(2026, 10, 14, 10, 0).timestamp()


def _bd(tu: str, n: int) -> list[str]:
    return list(pd.bdate_range(tu, periods=n).strftime("%Y-%m-%d"))


def _df(ngay: list[str], close: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"time": ngay, "open": close, "high": close, "low": close,
                         "close": close, "volume": [1000] * len(ngay)})


@pytest.fixture
def mt(tmp_path, monkeypatch):
    """Cache tạm có hai tệp (mtime 14/10/2026), kho tạm ĐÃ TẠO (kho bật), bộ nhớ giả."""
    cache = tmp_path / "cache"
    cache.mkdir()
    kho = tmp_path / "luu_cache"
    kho.mkdir()
    bo_nho = tmp_path / "sl_pattern_memory.json"
    bo_nho.write_text('{"mau": ["gia"]}', encoding="utf-8")
    ngay = _bd("2026-08-03", 6)
    _df(ngay, [10, 11, 12, 13, 14, 15]).to_csv(cache / "AAA.csv", index=False)
    _df(ngay, [20, 21, 22, 23, 24, 25]).to_csv(cache / "BBB.csv", index=False)
    for f in cache.glob("*.csv"):
        os.utime(f, (MTIME_CU, MTIME_CU))
    monkeypatch.setattr(bt, "CACHE_DIR", cache)
    monkeypatch.setattr(bt, "LUU_CACHE_DIR", kho)
    monkeypatch.setattr(bt, "FILE_BO_NHO_HAU_NGHIEM", bo_nho)
    monkeypatch.setattr(bt, "_DA_CHUP", set())
    return cache, kho, bo_nho


def _anh(kho: Path) -> list[Path]:
    """Ảnh chụp hoàn chỉnh (bỏ thư mục chép dở `.dang_chup…`)."""
    return sorted(d for d in kho.iterdir() if d.is_dir() and not d.name.startswith("."))


def _moi() -> pd.DataFrame:
    return _df(_bd("2026-08-03", 7), [90, 91, 92, 93, 94, 95, 96])


# ───────────────────────── hành vi của ghi_cache ─────────────────────────

def test_kho_bat_thi_chup_dung_cache_CU_truoc_khi_ghi(mt):
    cache, kho, bo_nho = mt
    truoc = bt.bam_cache(cache)
    aaa_cu = (cache / "AAA.csv").read_bytes()

    bt.ghi_cache(_moi(), "AAA")

    anh = _anh(kho)
    assert [d.name for d in anh] == [f"20261014_{truoc['sha256'][:8]}"]
    assert bt.bam_cache(anh[0])["sha256"] == truoc["sha256"]
    assert (anh[0] / "AAA.csv").read_bytes() == aaa_cu          # bản CŨ, không phải bản mới
    assert list(pd.read_csv(cache / "AAA.csv")["close"]) == [90, 91, 92, 93, 94, 95, 96]
    assert (anh[0] / "sl_pattern_memory.json").read_text(encoding="utf-8") == bo_nho.read_text(encoding="utf-8")
    danh_muc = (kho / "DANH_MUC.md").read_text(encoding="utf-8")
    assert f"`{anh[0].name}/`" in danh_muc and "BƯỚC 200" in danh_muc


def test_kho_khong_ton_tai_thi_khong_chup_va_van_ghi(mt, tmp_path, monkeypatch):
    cache, kho, _ = mt
    khong_co = tmp_path / "khong_co_kho"
    monkeypatch.setattr(bt, "LUU_CACHE_DIR", khong_co)
    assert bt.chup_cache_truoc_khi_ghi() is None
    bt.ghi_cache(_moi(), "AAA")
    assert not khong_co.exists()
    assert _anh(kho) == []
    assert len(pd.read_csv(cache / "AAA.csv")) == 7


def test_mot_tien_trinh_chi_chup_MOT_lan_ca_khi_ghi_nhieu_ma(mt):
    """Lượt làm tươi ghi từng mã một: chỉ trạng thái TRƯỚC lượt ghi đầu được chụp."""
    cache, kho, _ = mt
    truoc = bt.bam_cache(cache)["sha256"]
    bt.ghi_cache(_moi(), "AAA")
    bt.ghi_cache(_moi(), "BBB")
    bt.ghi_cache(_moi(), "CCC")
    anh = _anh(kho)
    assert len(anh) == 1
    assert bt.bam_cache(anh[0])["sha256"] == truoc


def test_phien_ban_da_co_trong_kho_thi_khong_chup_trung(mt):
    cache, kho, _ = mt
    b = bt.bam_cache(cache)["sha256"]
    co_san = kho / f"20200101_{b[:8]}"
    co_san.mkdir()
    assert bt.chup_cache_truoc_khi_ghi() == co_san
    bt.ghi_cache(_moi(), "AAA")
    assert _anh(kho) == [co_san]


def test_cache_nam_TRONG_kho_thi_tu_choi_ghi(mt, monkeypatch):
    """Kho chỉ đọc: trỏ VIBE_CACHE_DIR vào một ảnh chụp rồi làm tươi là phá ảnh chụp."""
    cache, kho, _ = mt
    anh = kho / "20261014_abcdef12"
    anh.mkdir()
    (anh / "AAA.csv").write_bytes((cache / "AAA.csv").read_bytes())
    cu = (anh / "AAA.csv").read_bytes()
    monkeypatch.setattr(bt, "CACHE_DIR", anh)
    with pytest.raises(ValueError, match="kho chỉ đọc"):
        bt.ghi_cache(_moi(), "AAA")
    assert (anh / "AAA.csv").read_bytes() == cu


def test_ban_chep_lech_bam_thi_no_va_KHONG_ghi(mt, monkeypatch):
    cache, kho, _ = mt
    cu = (cache / "AAA.csv").read_bytes()
    that = bt.shutil.copy2

    def chep_hong(nguon, dich):
        that(nguon, dich)
        if str(dich).endswith(".csv"):
            Path(dich).write_bytes(b"hong")

    monkeypatch.setattr(bt.shutil, "copy2", chep_hong)
    with pytest.raises(RuntimeError, match="lệch băm"):
        bt.ghi_cache(_moi(), "AAA")
    assert (cache / "AAA.csv").read_bytes() == cu
    assert _anh(kho) == []
    assert any(d.name.startswith(".dang_chup") for d in kho.iterdir())   # để nguyên cho người xem


def test_cache_rong_thi_khong_chup(mt, tmp_path, monkeypatch):
    _, kho, _ = mt
    rong = tmp_path / "cache_rong"
    rong.mkdir()
    monkeypatch.setattr(bt, "CACHE_DIR", rong)
    assert bt.chup_cache_truoc_khi_ghi() is None
    bt.ghi_cache(_moi(), "AAA")
    assert _anh(kho) == []


def test_bam_cache_TRUNG_phep_bam_M0_cua_cac_DO(mt):
    """Băm trong kho phải tra ra được bằng băm M0 đã ghi ở STATE (`bam_thu_muc`)."""
    import do25_ke_hoach_vao_lenh as d25
    cache, _, _ = mt
    assert bt.bam_cache(cache)["sha256"] == d25.bam_thu_muc(cache)["sha256"]
    assert bt.bam_cache(cache)["so_file"] == d25.bam_thu_muc(cache)["so_file"] == 2


# ───────────────────────── đường ghi thật ─────────────────────────

def test_extend_history_thay_ca_chuoi_chup_ban_cu_truoc(mt, monkeypatch):
    """Đúng ca 12/10: thay CẢ chuỗi bằng một cơ sở giá khác — bản cũ phải nằm trong kho."""
    cache, kho, _ = mt
    aaa_cu = (cache / "AAA.csv").read_bytes()
    moi = _df(_bd("2026-08-03", 7), [7.7, 8.47, 9.24, 10.01, 10.78, 11.55, 12.32])
    monkeypatch.setattr(bt, "fetch_one", lambda s, a, b, **k: moi)
    doi = bt.extend_history(["AAA"], "2026-08-01", "2026-09-30",
                            thay_ca_chuoi=True, bay_gio=SAU_DONG)
    assert "AAA" in doi
    anh = _anh(kho)
    assert len(anh) == 1 and (anh[0] / "AAA.csv").read_bytes() == aaa_cu
    assert list(pd.read_csv(cache / "AAA.csv")["close"])[0] == pytest.approx(7.7)


def test_download_force_chup_ban_cu_truoc(mt, monkeypatch):
    cache, kho, _ = mt
    aaa_cu = (cache / "AAA.csv").read_bytes()
    monkeypatch.setattr(bt, "fetch_one", lambda s, a, b, **k: _moi())
    bt.download(["AAA"], "2026-08-01", "2026-09-30", force=True, bay_gio=SAU_DONG)
    anh = _anh(kho)
    assert len(anh) == 1 and (anh[0] / "AAA.csv").read_bytes() == aaa_cu
    assert len(pd.read_csv(cache / "AAA.csv")) == 7


# ───────────────────────── gác hình dạng (AST) ─────────────────────────

def _cac_to_csv(duong: Path) -> list[tuple[int, str | None]]:
    """(dòng, tên hàm bao quanh gần nhất) của mọi lời gọi `.to_csv(`."""
    cay = ast.parse(duong.read_text(encoding="utf-8"))
    ra = []

    def di(nut, ham):
        for con in ast.iter_child_nodes(nut):
            ten = con.name if isinstance(con, (ast.FunctionDef, ast.AsyncFunctionDef)) else ham
            if (isinstance(con, ast.Call) and isinstance(con.func, ast.Attribute)
                    and con.func.attr == "to_csv"):
                ra.append((con.lineno, ham))
            di(con, ten)

    di(cay, None)
    return ra


def test_AST_moi_to_csv_vao_cache_chi_nam_trong_ghi_cache():
    du_lieu = _cac_to_csv(GOC / "backtest" / "data.py")
    assert du_lieu and all(ham == "ghi_cache" for _, ham in du_lieu), du_lieu
    assert _cac_to_csv(GOC / "market_filter.py") == []


def test_AST_ghi_cache_chup_TRUOC_roi_moi_ghi():
    cay = ast.parse((GOC / "backtest" / "data.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "ghi_cache")
    goi = [(n.lineno, n.func.id if isinstance(n.func, ast.Name) else n.func.attr)
           for n in ast.walk(ham) if isinstance(n, ast.Call)
           and isinstance(n.func, (ast.Name, ast.Attribute))]
    dong = {ten: so for so, ten in goi}
    assert dong["chup_cache_truoc_khi_ghi"] < dong["to_csv"], goi


def test_AST_ba_duong_ghi_deu_goi_ghi_cache():
    """download · extend_history · market_filter (VNINDEX) — đủ ba chỗ từng ghi thẳng."""
    def goi_trong(duong: Path, ham_ten: str | None) -> bool:
        cay = ast.parse(duong.read_text(encoding="utf-8"))
        goc = cay if ham_ten is None else next(
            n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ham_ten)
        return any(isinstance(n, ast.Call) and (
            (isinstance(n.func, ast.Name) and n.func.id == "ghi_cache")
            or (isinstance(n.func, ast.Attribute) and n.func.attr == "ghi_cache"))
            for n in ast.walk(goc))
    assert goi_trong(GOC / "backtest" / "data.py", "download")
    assert goi_trong(GOC / "backtest" / "data.py", "extend_history")
    assert goi_trong(GOC / "market_filter.py", None)


def test_kho_THAT_tat_trong_moi_test():
    """Gác của conftest: không fixture `mt` thì kho trỏ đường KHÔNG tồn tại."""
    assert bt.LUU_CACHE_DIR == conftest._KHO_TAT
    assert not bt.LUU_CACHE_DIR.exists()
