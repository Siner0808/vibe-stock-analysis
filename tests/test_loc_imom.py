"""Gác cho cổng LỌC IMOM NHÓM THẤP (ĐO 31, BƯỚC 223), module `imom.py` và dụng cụ
`tools/do31_loc_imom.py`.

Khai trước ở `docs/TIEU-CHI-DOC-TRUOC.md`, mục "ĐO 31", ký ở một commit RIÊNG trước
mã. Luật: `LOC_IMOM_PHAN_VI` > 0 thì `consider_entry` không mở mã có phân vị IMOM
12 tháng tại ngày tín hiệu ≤ giá trị ấy; IMOM thiếu thì không chặn. Mặc định 0 —
đường chạy thật không đổi.

Phát đầu dựng lại BẪY của bản rút gọn: cửa sổ ước lượng trùng cửa sổ hình thành,
nên trừ hệ số chặn thì trung bình phần dư = 0 theo cấu tạo và IMOM ≡ 0 với mọi mã.
"""
from __future__ import annotations

import ast
import math
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC / "tools"))

import imom  # noqa: E402
import paper_trading as pt  # noqa: E402
import do31_loc_imom as D  # noqa: E402

T = pd.Timestamp("2022-03-01")          # cửa sổ W = [2021-03-01 ; 2022-02-01)


def _thi_truong(n=320, seed=0, troi=0.0):
    rng = np.random.default_rng(seed)
    ngay = pd.bdate_range("2021-01-04", periods=n)
    return pd.Series(rng.normal(troi, 0.01, n), index=ngay)


def _ma(rm, beta=1.5, troi=0.0, seed=1):
    rng = np.random.default_rng(seed)
    return pd.Series(beta * rm.to_numpy() + troi + rng.normal(0, 0.005, len(rm)), index=rm.index)


# ── phát đầu: bẫy hệ số chặn ─────────────────────────────────────────

def test_BAY_he_so_chan_IMOM_khong_bang_0_va_theo_dau_cua_phan_vuot():
    """Mã vượt thị trường đều đặn → IMOM dương rõ; kém đều đặn → âm rõ. Trừ hệ số chặn
    thì cả hai ≈ 0 (bản rút gọn lọc theo nhiễu làm tròn)."""
    rm = _thi_truong()
    assert imom.imom(_ma(rm, troi=+0.002), rm, T) > 0.2
    assert imom.imom(_ma(rm, troi=-0.002), rm, T) < -0.2


def test_DA_TRU_BETA_ma_di_theo_thi_truong_nhung_kem_beta_thi_AM():
    """Thị trường lên mạnh, mã beta 2 kém phần beta 0,1%/phiên: lợi nhuận THÔ dương nhưng
    IMOM phải ÂM. Quên trừ β·r_m thì dấu lật."""
    rm = _thi_truong(troi=0.003)
    ri = _ma(rm, beta=2.0, troi=-0.001)
    assert ri[(ri.index >= T - pd.DateOffset(months=12)) & (ri.index < T - pd.DateOffset(months=1))].mean() > 0
    assert imom.imom(ri, rm, T) < -0.1


def test_BO_thang_gan_nhat_va_BO_phan_cu_hon_12_thang():
    rm = _thi_truong()
    ri = _ma(rm, troi=0.001)
    goc = imom.imom(ri, rm, T)
    for ngay in (T - pd.Timedelta(days=10), T - pd.DateOffset(months=13)):   # ngoài W
        x = ri.copy()
        x.iloc[x.index.get_indexer([ngay], method="nearest")[0]] = 0.5
        assert imom.imom(x, rm, T) == pytest.approx(goc)
    x = ri.copy()
    x.iloc[x.index.get_indexer([T - pd.DateOffset(months=6)], method="nearest")[0]] = 0.5   # trong W
    assert imom.imom(x, rm, T) != pytest.approx(goc)


def test_THIEU_khi_duoi_200_phien_trong_cua_so():
    rm = _thi_truong()
    ri = _ma(rm)
    dau = T - pd.DateOffset(months=12)
    cuoi = T - pd.DateOffset(months=1)
    trong = ri[(ri.index >= dau) & (ri.index < cuoi)]
    assert len(trong) >= imom.PHIEN_TOI_THIEU
    bot = ri.drop(trong.index[: len(trong) - imom.PHIEN_TOI_THIEU + 1])     # còn 199 phiên
    assert math.isnan(imom.imom(bot, rm, T))
    vua = ri.drop(trong.index[: len(trong) - imom.PHIEN_TOI_THIEU])         # còn đúng 200
    assert not math.isnan(imom.imom(vua, rm, T))


# ── phân vị cắt ngang ────────────────────────────────────────────────

def _bang(so_ma: int):
    rm = _thi_truong()
    # bước 0,1%/phiên: nhiễu của trung bình phần dư qua ~230 phiên ≈ 0,005/√230 ≈ 0,033%,
    # nên thứ hạng theo i là chắc (bước 0,01% nằm TRONG nhiễu — thứ hạng xáo, đo 23/10)
    return {f"M{i:02d}": _ma(rm, troi=0.001 * i, seed=100 + i) for i in range(so_ma)}, rm


def test_PHAN_VI_khong_xep_khi_duoi_20_ma():
    bang, rm = _bang(imom.N_XEP_HANG_TOI_THIEU - 1)
    assert imom.phan_vi(bang, rm, T) is None
    bang, rm = _bang(imom.N_XEP_HANG_TOI_THIEU)
    assert imom.phan_vi(bang, rm, T) is not None


def test_PHAN_VI_la_hang_tang_chia_N_va_ma_kem_nhat_o_day():
    bang, rm = _bang(25)
    pv = imom.phan_vi(bang, rm, T)
    assert len(pv) == 25
    assert pv["M00"] == pytest.approx(1 / 25) and pv["M24"] == pytest.approx(1.0)
    assert sorted(pv.round(6)) == [round(k / 25, 6) for k in range(1, 26)]


def _ghi_cache(thu_muc: Path, so_ma: int = 21) -> None:
    thu_muc.mkdir(parents=True, exist_ok=True)
    rm = _thi_truong()

    def ghi(ten, r):
        gia = 100 * np.cumprod(1 + np.r_[0.0, r.to_numpy()])
        ngay = [rm.index[0] - pd.Timedelta(days=1), *rm.index]
        pd.DataFrame({"time": [d.strftime("%Y-%m-%d") for d in ngay], "open": gia, "high": gia,
                      "low": gia, "close": gia, "volume": 1000}).to_csv(thu_muc / f"{ten}.csv", index=False)
    ghi("VNINDEX", rm)
    for i in range(so_ma):
        ghi(f"M{i:02d}", _ma(rm, troi=0.001 * i, seed=100 + i))


def test_BANG_IMOM_doc_cache_bo_VNINDEX_va_nho_theo_ngay(tmp_path, monkeypatch):
    _ghi_cache(tmp_path / "c")
    b = imom.BangIMOM(tmp_path / "c")
    assert "VNINDEX" not in b.bang_ln and len(b.bang_ln) == 21
    assert b.phan_vi("M00", "2022-03-01") == pytest.approx(1 / 21)
    assert b.phan_vi("KHONG_CO", "2022-03-01") is None
    goi = []
    monkeypatch.setattr(imom, "phan_vi", lambda *a: goi.append(1) or pd.Series(dtype=float))
    b.phan_vi("M01", "2022-03-01")
    assert goi == [], "ngày đã tính phải dùng lại, không tính lại"


def test_PHAN_VI_MAC_DINH_doc_dung_thu_muc_cache_cua_backtest(tmp_path, monkeypatch):
    """Cổng hỏi `imom.phan_vi_mac_dinh` — nó phải đọc ĐÚNG thư mục cache mà backtest đang dùng
    (`backtest.data.CACHE_DIR`, tức `VIBE_CACHE_DIR` nếu đặt), không phải một đường gõ tay."""
    _ghi_cache(tmp_path / "c")
    import backtest.data
    monkeypatch.setattr(backtest.data, "CACHE_DIR", tmp_path / "c")
    truc_tiep = imom.BangIMOM(tmp_path / "c")
    for ma in ("M00", "M07", "M20"):
        assert imom.phan_vi_mac_dinh(ma, "2022-03-01") == truc_tiep.phan_vi(ma, "2022-03-01")
    assert imom.phan_vi_mac_dinh("M00", "2022-03-01") == pytest.approx(1 / 21)
    assert imom.phan_vi_mac_dinh("M00", "2022-03-01 00:00:00") == pytest.approx(1 / 21)


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
    """Sổ ảo trong thư mục tạm; cổng VN-INDEX và ô C5 mở cho lượt test."""
    import market_filter
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda _d: True)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    j = pt.PaperTradingJournal(str(tmp_path / "s.db"))
    yield j
    j.db.close()


def test_MAC_DINH_TAT_thi_KHONG_cham_imom(monkeypatch):
    """Mặc định 0: đường chạy thật không đổi, và cổng không nạp `imom` hay đọc cache."""
    class _CamCham:
        def __getattr__(self, ten):
            raise AssertionError(f"cổng TẮT mà vẫn chạm imom.{ten}")
    monkeypatch.setitem(sys.modules, "imom", _CamCham())
    monkeypatch.setattr(pt, "LOC_IMOM_PHAN_VI", 0)
    assert pt.phan_vi_imom_bi_loc("HVN", "2022-11-30") is None


@pytest.mark.parametrize("pv, ky_vong", [(0.061, 0.061), (0.20, 0.20), (0.2001, None), (None, None)])
def test_BAT_thi_loc_khi_phan_vi_NHO_HON_HOAC_BANG_nguong(monkeypatch, pv, ky_vong):
    monkeypatch.setattr(pt, "LOC_IMOM_PHAN_VI", 0.20)
    hoi = []
    monkeypatch.setattr(imom, "phan_vi_mac_dinh", lambda ma, ngay: hoi.append((ma, ngay)) or pv)
    assert pt.phan_vi_imom_bi_loc("HVN", "2022-11-30 00:00:00") == ky_vong
    assert hoi == [("HVN", "2022-11-30")], "cổng phải hỏi theo NGÀY (10 ký tự), không theo dấu thời gian"


def test_consider_entry_GHI_ly_do_khi_loc_va_MO_khi_khong(so, monkeypatch):
    monkeypatch.setattr(pt, "LOC_IMOM_PHAN_VI", 0.20)
    nhan = []
    monkeypatch.setattr(imom, "phan_vi_mac_dinh",
                        lambda ma, ngay: nhan.append((ma, ngay)) or {"HVN": 0.061, "FPT": 0.9}[ma])
    assert so.consider_entry("HVN", "2022-11-30", _kq()) is None
    ly_do = so.db.execute("SELECT skip_reason FROM decisions WHERE symbol='HVN' "
                          "ORDER BY seq DESC LIMIT 1").fetchone()[0]
    assert ly_do.startswith(pt.LY_DO_LOC_IMOM) and "0.061" in ly_do
    assert so.consider_entry("FPT", "2022-11-30", _kq()) is not None
    assert nhan == [("HVN", "2022-11-30"), ("FPT", "2022-11-30")]


def test_MAC_DINH_trong_NGUON_la_0():
    """Đọc NGUỒN, không đọc giá trị lúc chạy: test khác có thể đã đặt cờ."""
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    gan = [n.value.value for n in cay.body if isinstance(n, ast.Assign)
           and any(isinstance(t, ast.Name) and t.id == "LOC_IMOM_PHAN_VI" for t in n.targets)]
    assert gan == [0]


def test_cong_dung_SAU_cong_nghi_sau_lo_va_TRUOC_chot_C5():
    """Đọc AST của `consider_entry`, không dò chuỗi (chú thích không được tính)."""
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "consider_entry")

    def dong(la):
        return [n.lineno for n in ast.walk(ham) if la(n)]
    nghi = dong(lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "ngay_ra_lo_gan")
    loc = dong(lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "phan_vi_imom_bi_loc")
    c5 = dong(lambda n: isinstance(n, ast.Assign) and isinstance(n.value, ast.Name)
              and n.value.id == "LY_DO_C5")
    assert len(nghi) == len(loc) == len(c5) == 1
    assert nghi[0] < loc[0] < c5[0]


# ── dụng cụ ĐO 31 ────────────────────────────────────────────────────

def test_PHAN_VI_cua_dung_cu_KHOP_muc_DO_31_da_ky():
    """Suy ra, đừng gõ: giá trị lượt B phải đúng số đã ghim trong bản khai."""
    van = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
    muc = van[van.index("## ĐO 31"):]
    m = re.search(r"Lượt B đặt \*\*(\d+),(\d+)\*\*", muc)
    assert m and float(f"{m.group(1)}.{m.group(2)}") == D.PHAN_VI_LUOT_B == D.LUOT["B"]
    assert D.LUOT["A"] == 0


def test_phep_dem_iv_CUNG_DINH_NGHIA_voi_cong():
    pv = {"AAA": 0.134, "HVN": 0.061, "SHS": 0.20, "VCG": 0.2001, "FPT": None}
    lenh = [{"id": i, "symbol": m, "signal_date": "2022-11-30", "status": tt}
            for i, (m, tt) in enumerate([("AAA", "CLOSED"), ("HVN", "CLOSED"), ("SHS", "CLOSED"),
                                         ("VCG", "CLOSED"), ("FPT", "CLOSED"), ("HVN", "HUY")], 1)]
    assert [x["id"] for x in D.lenh_bi_loc(lenh, lambda m, d: pv[m], 0.20)] == [1, 2, 3]


def test_dung_cu_GIAO_cho_do1_chu_khong_chep_duong_chay():
    cay = ast.parse((GOC / "tools" / "do31_loc_imom.py").read_text(encoding="utf-8"))
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "chay_mot_luot" in goi
    gan_co = [n for n in ast.walk(cay) if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Attribute) and t.attr == "LOC_IMOM_PHAN_VI"
                      for t in n.targets)]
    assert len(gan_co) == 1
    assert D.LUOT_DO1 == 2


def test_luot_B_THAT_SU_chay_voi_co_0_20_va_dung_luot_2_cua_do1(monkeypatch):
    import do1_chi_phi_thuc_thi as do1
    monkeypatch.setattr(pt, "LOC_IMOM_PHAN_VI", pt.LOC_IMOM_PHAN_VI)  # trả lại sau test
    thay_the = []
    monkeypatch.setattr(do1, "chay_mot_luot",
                        lambda n, *a, **k: thay_the.append((n, pt.LOC_IMOM_PHAN_VI)) or 0)
    assert D.chay_luot("B") == 0
    assert D.chay_luot("A") == 0
    assert thay_the == [(2, 0.20), (2, 0)]


def test_dung_cu_dem_chay_THAT_tren_so_tam_va_cache_tam(tmp_path, monkeypatch, capsys):
    _ghi_cache(tmp_path / "c")
    import backtest.data
    monkeypatch.setattr(backtest.data, "CACHE_DIR", tmp_path / "c")
    db = tmp_path / "wf_oos.db"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE trades (id INTEGER, symbol TEXT, signal_date TEXT, status TEXT)")
    c.executemany("INSERT INTO trades VALUES (?,?,?,?)", [
        (1, "M00", "2022-03-01", "CLOSED"), (2, "M20", "2022-03-01", "CLOSED"),
        (3, "M01", "2022-03-01", "HUY")])
    c.commit()
    c.close()
    assert D.main(["--dem", str(db)]) == 0
    ra = capsys.readouterr().out
    assert "lệnh CLOSED: 2" in ra and "tại ngày tín hiệu: 1" in ra and "M00" in ra


def test_CA_THAT_HVN_30_11_2022_tren_cache_goc_da_khai():
    """Ca thật đã khai (đối chứng iii): HVN phân vị 0,061 trong N = 82. Chỉ ở máy có bản
    chép cache gốc (`scratch/vibe_cache_goc_20260911`, cạnh repo)."""
    cache = GOC.parent / "vibe_cache_goc_20260911"
    if not (cache / "VNINDEX.csv").exists():
        pytest.skip("máy này không có bản chép cache gốc acf6dca1 cạnh repo")
    b = imom.BangIMOM(cache)
    assert round(b.phan_vi("HVN", "2022-11-30"), 3) == 0.061
    assert len(imom.phan_vi(b.bang_ln, b.r_tt, pd.Timestamp("2022-11-30"))) == 82
