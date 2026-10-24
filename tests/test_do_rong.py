"""Gác cho cổng ĐỘ RỘNG THỊ TRƯỜNG và tham số tắt cổng VN-INDEX (ĐO 32, BƯỚC 224),
module `do_rong.py` và dụng cụ `tools/do32_do_rong.py`.

Khai trước ở `docs/TIEU-CHI-DOC-TRUOC.md`, mục "ĐO 32", ký ở một commit RIÊNG trước
mã. Luật: `DO_RONG_NGUONG` > 0 thì `consider_entry` không mở lệnh khi tỉ lệ mã của
cache đóng cửa ≥ MA50 của chính nó tại ngày tín hiệu nhỏ hơn giá trị ấy; độ rộng
thiếu thì không chặn. `CONG_VNI_BAT` False thì bỏ qua hẳn cổng VN-INDEX. Mặc định
(True, 0) — đường chạy thật không đổi.

Phát đầu dựng lại BẪY của bản ngây thơ: `gia >= NaN` là False, nên mã chưa đủ 50 dòng
bị đếm là "dưới MA" và kéo độ rộng xuống.
"""
from __future__ import annotations

import ast
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

import do_rong  # noqa: E402
import paper_trading as pt  # noqa: E402
import do32_do_rong as D  # noqa: E402

NGAY = pd.bdate_range("2022-01-03", periods=80)
T = NGAY[69]                                   # phiên thứ 70: mọi mã đủ 50 dòng đều có MA


def _len(n=80, buoc=1.0, dau=100.0):
    """Giá đi đều `buoc` mỗi phiên trên `n` phiên đầu của NGAY."""
    return pd.Series(dau + buoc * np.arange(n), index=NGAY[:n])


def _co(**chuoi):
    return {ten: do_rong.co_tren_ma(g) for ten, g in chuoi.items()}


# ── phát đầu: bẫy MA còn NaN ─────────────────────────────────────────

def test_BAY_ma_CHUA_DU_50_dong_KHONG_tinh_vao_N():
    """20 mã lên đủ dài + 10 mã mới chỉ có 30 dòng (đang giảm): độ rộng tại T là 20/20.
    Bản ngây thơ đếm 10 mã mới là "dưới MA" → 20/30."""
    g = {f"L{i:02d}": _len() for i in range(20)}
    moi = {f"M{i:02d}": pd.Series(100.0 - np.arange(30), index=NGAY[40:70]) for i in range(10)}
    assert do_rong.do_rong(_co(**g, **moi), T) == 1.0


def test_TREN_la_dong_cua_LON_HON_HOAC_BANG_MA():
    """Giá đứng yên: đóng cửa = MA50 đúng từng chữ số → "trên" (phép so `>=` của cổng VN-INDEX)."""
    g = {f"P{i:02d}": pd.Series(100.0, index=NGAY) for i in range(20)}
    assert do_rong.do_rong(_co(**g), T) == 1.0
    g = {f"X{i:02d}": _len(buoc=-1.0) for i in range(20)}
    assert do_rong.do_rong(_co(**g), T) == 0.0


def test_N_DUOI_20_thi_THIEU():
    g = {f"L{i:02d}": _len() for i in range(do_rong.N_TOI_THIEU - 1)}
    assert do_rong.do_rong(_co(**g), T) is None
    g["THEM"] = _len(buoc=-1.0)
    assert do_rong.do_rong(_co(**g), T) == pytest.approx((do_rong.N_TOI_THIEU - 1) / do_rong.N_TOI_THIEU)


def test_DONG_CUOI_co_ngay_NHO_HON_HOAC_BANG_t_va_KHONG_nhin_tuong_lai():
    """Mã S: phẳng 100, phiên trước T tụt 90 (dưới MA), đúng T bật 110 (trên MA), sau T sập 50.
    Tại T: S "trên" → 20/20. Lấy nhầm dòng TRƯỚC t → 19/20. Đổi giá sau T không đổi gì."""
    g = {f"L{i:02d}": _len() for i in range(19)}
    s = pd.Series(100.0, index=NGAY)
    s.iloc[68], s.iloc[69], s.iloc[70:] = 90.0, 110.0, 50.0
    assert do_rong.do_rong(_co(**g, S=s), T) == 1.0
    cat = s.iloc[:70]
    assert do_rong.do_rong(_co(**g, S=cat), T) == 1.0
    # một ngày sau T mà mã chưa có dòng nào: dùng dòng của T
    assert do_rong.do_rong(_co(**g, S=cat), T + pd.Timedelta(days=1)) == 1.0


def _ghi(thu_muc: Path, ten: str, gia: pd.Series) -> None:
    pd.DataFrame({"time": [d.strftime("%Y-%m-%d") for d in gia.index], "open": gia, "high": gia,
                  "low": gia, "close": gia, "volume": 1000}).to_csv(thu_muc / f"{ten}.csv", index=False)


def _ghi_cache(thu_muc: Path, so_len: int = 15, so_xuong: int = 5) -> None:
    thu_muc.mkdir(parents=True, exist_ok=True)
    _ghi(thu_muc, "VNINDEX", _len(buoc=-1.0))       # VN-Index xuống — KHÔNG được tính
    for i in range(so_len):
        _ghi(thu_muc, f"L{i:02d}", _len())
    for i in range(so_xuong):
        _ghi(thu_muc, f"X{i:02d}", _len(buoc=-1.0))


def test_BANG_doc_cache_BO_VNINDEX_va_nho_theo_ngay(tmp_path, monkeypatch):
    _ghi_cache(tmp_path / "c")
    b = do_rong.BangDoRong(tmp_path / "c")
    assert "VNINDEX" not in b.bang_co and len(b.bang_co) == 20
    assert b.do_rong(T.strftime("%Y-%m-%d")) == pytest.approx(15 / 20)
    goi = []
    monkeypatch.setattr(do_rong, "do_rong", lambda *a: goi.append(1) or 0.0)
    b.do_rong(T.strftime("%Y-%m-%d"))
    assert goi == [], "ngày đã tính phải dùng lại, không tính lại"


def test_MAC_DINH_doc_dung_thu_muc_cache_cua_backtest(tmp_path, monkeypatch):
    """Cổng hỏi `do_rong.do_rong_mac_dinh` — nó phải đọc ĐÚNG thư mục cache backtest đang dùng
    (`backtest.data.CACHE_DIR`, tức `VIBE_CACHE_DIR` nếu đặt), không phải một đường gõ tay."""
    _ghi_cache(tmp_path / "c", so_len=12, so_xuong=8)
    import backtest.data
    monkeypatch.setattr(backtest.data, "CACHE_DIR", tmp_path / "c")
    ngay = T.strftime("%Y-%m-%d")
    assert do_rong.do_rong_mac_dinh(ngay) == pytest.approx(12 / 20)
    assert do_rong.do_rong_mac_dinh(ngay + " 00:00:00") == pytest.approx(12 / 20)


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
    """Sổ ảo trong thư mục tạm; cổng VN-INDEX cho qua, ô C5 mở cho lượt test."""
    import market_filter
    monkeypatch.setattr(market_filter, "is_vni_bullish", lambda _d: True)
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    j = pt.PaperTradingJournal(str(tmp_path / "s.db"))
    yield j
    j.db.close()


def _ly_do(j, ma):
    return j.db.execute("SELECT skip_reason FROM decisions WHERE symbol=? ORDER BY seq DESC LIMIT 1",
                        (ma,)).fetchone()[0]


def test_MAC_DINH_TAT_thi_KHONG_cham_do_rong(monkeypatch):
    """Mặc định 0: đường chạy thật không đổi, và cổng không nạp `do_rong` hay đọc cache."""
    class _CamCham:
        def __getattr__(self, ten):
            raise AssertionError(f"cổng TẮT mà vẫn chạm do_rong.{ten}")
    monkeypatch.setitem(sys.modules, "do_rong", _CamCham())
    monkeypatch.setattr(pt, "DO_RONG_NGUONG", 0)
    assert pt.do_rong_bi_chan("2022-11-30") is None


@pytest.mark.parametrize("dr, ky_vong", [(0.446, 0.446), (0.4999, 0.4999), (0.0, 0.0),
                                         (0.50, None), (None, None)])
def test_BAT_thi_chan_khi_do_rong_NHO_HON_nguong(monkeypatch, dr, ky_vong):
    monkeypatch.setattr(pt, "DO_RONG_NGUONG", 0.50)
    hoi = []
    monkeypatch.setattr(do_rong, "do_rong_mac_dinh", lambda ngay: hoi.append(ngay) or dr)
    assert pt.do_rong_bi_chan("2022-11-30 00:00:00") == ky_vong
    assert hoi == ["2022-11-30"], "cổng phải hỏi theo NGÀY (10 ký tự), không theo dấu thời gian"


def test_consider_entry_GHI_ly_do_khi_chan_va_MO_khi_khong(so, monkeypatch):
    monkeypatch.setattr(pt, "DO_RONG_NGUONG", 0.50)
    bang = {"2022-11-30": 0.446, "2022-12-01": 0.0, "2022-12-02": 0.61}
    monkeypatch.setattr(do_rong, "do_rong_mac_dinh", lambda ngay: bang[ngay])
    assert so.consider_entry("AAA", "2022-11-30", _kq()) is None
    assert _ly_do(so, "AAA").startswith(pt.LY_DO_DO_RONG) and "0.446" in _ly_do(so, "AAA")
    assert so.consider_entry("ACV", "2022-12-01", _kq()) is None, "độ rộng 0,0 vẫn phải CHẶN"
    assert _ly_do(so, "ACV").startswith(pt.LY_DO_DO_RONG)
    assert so.consider_entry("FPT", "2022-12-02", _kq()) is not None


def test_CONG_VNI_TAT_thi_KHONG_hoi_is_vni_bullish_va_BAT_thi_van_chan(tmp_path, monkeypatch):
    import market_filter
    monkeypatch.setattr(pt, "CHO_PHEP_MO_LENH_MOI", True)
    j = pt.PaperTradingJournal(str(tmp_path / "s.db"))
    try:
        def _cam(_d):
            raise AssertionError("cổng VN-INDEX TẮT mà vẫn bị hỏi")
        monkeypatch.setattr(market_filter, "is_vni_bullish", _cam)
        monkeypatch.setattr(pt, "CONG_VNI_BAT", False)
        assert j.consider_entry("FPT", "2022-11-30", _kq()) is not None
        monkeypatch.setattr(market_filter, "is_vni_bullish", lambda _d: False)
        monkeypatch.setattr(pt, "CONG_VNI_BAT", True)
        assert j.consider_entry("HPG", "2022-11-30", _kq()) is None
        assert _ly_do(j, "HPG") == pt.LY_DO_VNI
    finally:
        j.db.close()


def test_LY_DO_VNI_GIU_NGUYEN_chuoi_cu():
    """Sổ thật và bản tin đọc lý do theo đúng chuỗi này; đổi thành hằng không được đổi chữ."""
    assert pt.LY_DO_VNI == "VN-INDEX nằm dưới MA50 (Downtrend/Điều chỉnh - Giữ 100% tiền mặt)"


def _gan_trong_nguon(ten):
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    return [n.value.value for n in cay.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == ten for t in n.targets)]


def test_MAC_DINH_trong_NGUON_giu_duong_hien_tai():
    """Đọc NGUỒN, không đọc giá trị lúc chạy: test khác có thể đã đặt cờ."""
    assert _gan_trong_nguon("CONG_VNI_BAT") == [True]
    assert _gan_trong_nguon("DO_RONG_NGUONG") == [0]


def test_cong_do_rong_SAU_cong_VNI_TRUOC_cong_chat_luong_va_chot_C5():
    """Đọc AST của `consider_entry`, không dò chuỗi (chú thích không được tính)."""
    cay = ast.parse((GOC / "paper_trading.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef) and n.name == "consider_entry")

    def dong(la):
        return [n.lineno for n in ast.walk(ham) if la(n)]
    vni = dong(lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "is_vni_bullish")
    dr = dong(lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id == "do_rong_bi_chan")
    cl = dong(lambda n: isinstance(n, ast.Name) and n.id == "MUC_CHAT_LUONG_DUNG_DUOC")
    c5 = dong(lambda n: isinstance(n, ast.Assign) and isinstance(n.value, ast.Name)
              and n.value.id == "LY_DO_C5")
    assert len(vni) == len(dr) == len(cl) == len(c5) == 1
    assert vni[0] < dr[0] < cl[0] < c5[0]


# ── dụng cụ ĐO 32 ────────────────────────────────────────────────────

def test_NGUONG_cua_dung_cu_KHOP_muc_DO_32_da_ky():
    """Suy ra, đừng gõ: giá trị lượt B phải đúng số đã ghim trong bản khai."""
    van = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
    muc = van[van.index("## ĐO 32"):]
    m = re.search(r"\*\*B\*\* = \(False, \*\*(\d+),(\d+)\*\*\)", muc)
    assert m and float(f"{m.group(1)}.{m.group(2)}") == D.NGUONG_LUOT_B == D.LUOT["B"][1]
    assert "**A** = (True, 0)" in muc and "**C** = (False, 0)" in muc
    assert D.LUOT["A"] == (True, 0) and D.LUOT["C"] == (False, 0) and D.LUOT["B"][0] is False


def test_HANG_SO_cua_module_KHOP_muc_DO_32_da_ky():
    """Test trên tự suy số mã từ `N_TOI_THIEU` — nên giá trị phải được ghim vào bản khai ở đây."""
    van = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
    muc = van[van.index("## ĐO 32"):]
    muc = muc[:muc.index("### Dữ liệu và lượt chạy")]
    assert int(re.search(r"Cần N\(t\) ≥ (\d+)", muc).group(1)) == do_rong.N_TOI_THIEU
    assert int(re.search(r"có ≥ (\d+) dòng với ngày ≤ t", muc).group(1)) == do_rong.MA_PHIEN
    assert f"MA{do_rong.MA_PHIEN} = trung bình {do_rong.MA_PHIEN} giá đóng cửa" in muc


def test_phep_dem_iv_CUNG_DINH_NGHIA_voi_cong():
    dr = {"2022-11-30": 0.446, "2022-12-01": 0.0, "2022-12-02": 0.50, "2022-12-05": None}
    lenh = [{"id": i, "symbol": "AAA", "signal_date": d, "status": tt}
            for i, (d, tt) in enumerate([("2022-11-30", "CLOSED"), ("2022-12-01", "CLOSED"),
                                         ("2022-12-02", "CLOSED"), ("2022-12-05", "CLOSED"),
                                         ("2022-11-30", "HUY")], 1)]
    assert [x["id"] for x in D.lenh_bi_chan(lenh, dr.get, 0.50)] == [1, 2]


def test_dung_cu_GIAO_cho_do1_chu_khong_chep_duong_chay():
    cay = ast.parse((GOC / "tools" / "do32_do_rong.py").read_text(encoding="utf-8"))
    goi = {n.func.attr for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "chay_mot_luot" in goi
    gan = [t.attr for n in ast.walk(cay) if isinstance(n, ast.Assign)
           for tt in n.targets for t in (tt.elts if isinstance(tt, ast.Tuple) else [tt])
           if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
           and t.value.id == "paper_trading"]
    assert sorted(gan) == ["CONG_VNI_BAT", "DO_RONG_NGUONG"]
    assert D.LUOT_DO1 == 2


def test_ba_luot_THAT_SU_chay_voi_dung_co_va_dung_luot_2_cua_do1(monkeypatch):
    import do1_chi_phi_thuc_thi as do1
    monkeypatch.setattr(pt, "CONG_VNI_BAT", pt.CONG_VNI_BAT)       # trả lại sau test
    monkeypatch.setattr(pt, "DO_RONG_NGUONG", pt.DO_RONG_NGUONG)
    ghi = []
    monkeypatch.setattr(do1, "chay_mot_luot",
                        lambda n, *a, **k: ghi.append((n, pt.CONG_VNI_BAT, pt.DO_RONG_NGUONG)) or 0)
    assert [D.chay_luot(x) for x in ("B", "C", "A")] == [0, 0, 0]
    assert ghi == [(2, False, 0.50), (2, False, 0), (2, True, 0)]


def test_chan_doan_A62_GHIM_dai_nguong_va_dung_co_cua_luot_A(monkeypatch):
    """ĐO 32b: A62 = cờ của lượt A + `walkforward.DAI_NGUONG` = [62] trong tiến trình. Lượt A, B, C
    KHÔNG được chạm dải ngưỡng."""
    import do1_chi_phi_thuc_thi as do1
    import walkforward
    monkeypatch.setattr(pt, "CONG_VNI_BAT", pt.CONG_VNI_BAT)       # trả lại sau test
    monkeypatch.setattr(pt, "DO_RONG_NGUONG", pt.DO_RONG_NGUONG)
    # dải ĐÁNH DẤU, không đọc lại dải đang có: một lượt chạy trước trong cùng tiến trình có thể đã
    # ghi đè nó, và đọc lại thì phép so tự khớp với chính chỗ hỏng (đột biến sống sót 24/10).
    goc = [45.0, 99.0]
    monkeypatch.setattr(walkforward, "DAI_NGUONG", goc)
    ghi = []
    monkeypatch.setattr(do1, "chay_mot_luot", lambda n, *a, **k: ghi.append(
        (n, pt.CONG_VNI_BAT, pt.DO_RONG_NGUONG, list(walkforward.DAI_NGUONG))) or 0)
    assert D.chay_luot("A") == 0 and D.chay_luot("B") == 0
    assert D.chay_luot("A62") == 0
    assert ghi == [(2, True, 0, goc), (2, False, 0.50, goc), (2, True, 0, [62.0])]


def test_NGUONG_GHIM_cua_dung_cu_KHOP_muc_DO_32b_da_ky():
    van = (GOC / "docs" / "TIEU-CHI-DOC-TRUOC.md").read_text(encoding="utf-8")
    muc = van[van.index("## ĐO 32b"):]
    m = re.search(r"chỉ còn MỘT giá trị \*\*(\d+)\*\*", muc)
    assert m and float(m.group(1)) == D.NGUONG_GHIM_A62 == D.CHAN_DOAN["A62"][1]
    assert D.CHAN_DOAN["A62"][0] == D.LUOT["A"]


def test_dung_cu_dem_chay_THAT_tren_so_tam_va_cache_tam(tmp_path, monkeypatch, capsys):
    _ghi_cache(tmp_path / "c", so_len=8, so_xuong=12)          # độ rộng 0,40 < 0,50 tại T
    import backtest.data
    monkeypatch.setattr(backtest.data, "CACHE_DIR", tmp_path / "c")
    ngay = T.strftime("%Y-%m-%d")
    db = tmp_path / "wf_oos.db"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE trades (id INTEGER, symbol TEXT, signal_date TEXT, status TEXT)")
    c.executemany("INSERT INTO trades VALUES (?,?,?,?)", [
        (1, "L00", ngay, "CLOSED"), (2, "L01", NGAY[10].strftime("%Y-%m-%d"), "CLOSED"),
        (3, "L02", ngay, "HUY")])
    c.execute("CREATE TABLE decisions (seq INTEGER, signal_date TEXT, skip_reason TEXT)")
    c.executemany("INSERT INTO decisions VALUES (?,?,?)", [
        (1, ngay, pt.LY_DO_VNI), (2, ngay, f"{pt.LY_DO_DO_RONG}: 0.400 < 0.5"),
        (3, NGAY[10].strftime("%Y-%m-%d"), f"{pt.LY_DO_DO_RONG}: lạc chỗ"), (4, ngay, "")])
    c.commit()
    c.close()
    assert D.main(["--dem", str(db)]) == 0
    ra = capsys.readouterr().out
    assert "lệnh CLOSED: 2 · thiếu độ rộng: 1" in ra and "tại ngày tín hiệu: 1" in ra and "L00" in ra
    assert "lý do VN-INDEX: 1 · lý do độ rộng: 2" in ra and "hoặc thiếu: 1)" in ra


def test_CA_THAT_30_11_2022_va_08_09_2022_tren_cache_goc_da_khai():
    """Ca thật đã khai (đối chứng iii và số đếm 24/10): độ rộng 30/11/2022 = 37/83 (0,446),
    08/09/2022 = 41/83 (0,494). Chỉ ở máy có bản chép cache gốc cạnh repo."""
    cache = GOC.parent / "vibe_cache_goc_20260911"
    if not (cache / "VNINDEX.csv").exists():
        pytest.skip("máy này không có bản chép cache gốc acf6dca1 cạnh repo")
    b = do_rong.BangDoRong(cache)
    assert b.do_rong("2022-11-30") == pytest.approx(37 / 83)
    assert b.do_rong("2022-09-08") == pytest.approx(41 / 83)
