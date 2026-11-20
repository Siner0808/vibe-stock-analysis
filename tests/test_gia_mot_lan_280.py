"""BƯỚC 280, phần C — biểu đồ ngày (180 ngày) và ô cấu trúc Dow (1.095 ngày) chung MỘT lượt tải giá, số y hệt.

Khoá bốn điều (đột biến ở `docs/STATE.md` BƯỚC 280):

1. **Cắt đúng**: `n` nến cuối của lượt tải rộng bằng ĐÚNG thứ `VNStockCollectorAgent.collect` trả cho cửa sổ hẹp
   (khung, trạng thái, danh sách cảnh báo) — chạy `collect` THẬT trên một nguồn giả phát lại, không dựng lại công thức.
2. **Chỉ cắt khi cùng nguồn**: lượt tải rộng do nguồn KHÁC nguồn đầu chuỗi phục vụ (đo 16/11/2026: cửa sổ 1.583 ngày
   đi VNDirect, các cửa sổ ngắn đi Entrade, giá làm tròn khác) thì KHÔNG cắt, trả đúng đường cũ.
3. **Mọi nhánh không chắc đều về đường cũ**: tải rộng hỏng, trạng thái khác OK, bảng rộng ngắn hơn cửa sổ hẹp,
   kiểm định chặn phần cắt.
4. **App nối đúng**: các chỗ gọi (biểu đồ ngày, ô Dow; từ BƯỚC 288 cả nến tuần/tháng 1.583 ngày) đi qua
   `load_stock_data_cat`; `collect` và `run_daily` không được nhắc tên mới (đường quét không đổi).
   (BƯỚC 280 khoá nến tuần/tháng và VN-INDEX KHÔNG đi qua cat vì nguồn đầu bị bỏ ở cửa sổ ấy; BƯỚC 288 thêm nguồn
   Entrade khử trùng nên đảo phép khoá đó — `tests/test_gop_cua_so_288.py`.)
"""
import ast
import pathlib

import numpy as np
import pandas as pd
import pytest

import data_collectors as dc
import gia_mot_lan as g1l
import nguon_gia_cong_khai as ngk
from data_quality import now_vn

GOC = pathlib.Path(__file__).resolve().parent.parent
# Phiên làm việc liền trước hôm nay: bảng giả kết thúc ở đó thì kiểm định "dữ liệu cũ" không bao giờ chặn
# (cố định một ngày thì bộ test mục dần theo đồng hồ).
END = pd.bdate_range(end=pd.Timestamp(now_vn().date()), periods=2)[0].strftime("%Y-%m-%d")


def _khung_gia(n_ngay=1700, seed=7, den=END) -> pd.DataFrame:
    """Bảng giá giả dài: ngày làm việc tăng dần, high ≥ max(open, close), low ≤ min, giá nghìn đồng."""
    rng = np.random.default_rng(seed)
    ngay = pd.bdate_range(end=den, periods=n_ngay)
    dong = 20 * np.exp(np.cumsum(rng.normal(0, 0.008, n_ngay)))
    mo = np.concatenate([[dong[0]], dong[:-1]]) * (1 + rng.normal(0, 0.002, n_ngay))
    cao = np.maximum(mo, dong) * (1 + rng.uniform(0.001, 0.01, n_ngay))
    thap = np.minimum(mo, dong) * (1 - rng.uniform(0.001, 0.01, n_ngay))
    return pd.DataFrame({
        "time": pd.DatetimeIndex(ngay).astype("datetime64[ns]"),
        "open": mo, "high": cao, "low": thap, "close": dong,
        "volume": rng.integers(300_000, 5_000_000, n_ngay).astype("int64")})


def _phat_lai(monkeypatch, khung: pd.DataFrame, ten_nguon: str = "entrade"):
    """Thay `lay_ohlcv` bằng bản PHÁT LẠI: cắt `khung` vào [tu, den], rồi `kiem_so_phien` và `kiem_them` y như thật."""
    dem = {"n": 0}

    def lay(ma, tu, den, *, toi_thieu=None, kiem_them=None, **kw):
        dem["n"] += 1
        d_tu, d_den = ngk._ngay(tu, "tu"), ngk._ngay(den, "den")
        df = khung.loc[(khung["time"] >= pd.Timestamp(d_tu)) & (khung["time"] <= pd.Timestamp(d_den))
                       ].reset_index(drop=True)
        try:
            ngk.kiem_so_phien(df, ngk.toi_thieu_mac_dinh(d_tu, d_den) if toi_thieu is None else toi_thieu)
            if kiem_them is not None and kiem_them(df):
                raise ngk.NguonGiaLoi("kiem_them")
        except ngk.NguonGiaLoi as e:
            raise ngk.NguonGiaHetNguon(ma, [("phat_lai", str(e))])
        return ngk.KetQuaGia(df=df, nguon=ten_nguon, da_thu=[])
    monkeypatch.setattr(ngk, "lay_ohlcv", lay)
    return dem


def _tai(ticker, start, end, exch="HOSE"):
    """Bản sao logic `app.load_stock_data` (không đệm)."""
    res = dc.VNStockCollectorAgent().collect(ticker, start, end, exchange=exch)
    q = res.get("quality")
    return res.get("df"), res.get("status", "OK"), [i.message for i in q.warnings] if q is not None else []


def _tai_nguon(ticker, start, end, exch="HOSE"):
    res = dc.VNStockCollectorAgent().collect(ticker, start, end, exchange=exch)
    q = res.get("quality")
    return (res.get("df"), res.get("status", "OK"), [i.message for i in q.warnings] if q is not None else [],
            res.get("source", ""))


def _ngay(n):
    return (pd.Timestamp(END) - pd.Timedelta(days=n)).strftime("%Y-%m-%d")


# ── 1. cắt đúng ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("san", ["HOSE", "HNX", "UPCOM"])
def test_cat_bang_collect_that_cho_cua_so_180_tu_cua_so_1095(monkeypatch, san):
    _phat_lai(monkeypatch, _khung_gia(), "entrade")
    cu = _tai("ABC", _ngay(180), END, san)
    rong = _tai("ABC", _ngay(1095), END, san)
    cat = g1l.cat_tu_khung_rong(rong[0], _ngay(180), END, symbol="ABC", exchange=san)
    pd.testing.assert_frame_equal(cu[0], cat[0], check_exact=True)
    assert cat[1] == cu[1] == "OK" and cat[2] == cu[2]


def test_cat_cua_so_bang_chinh_no_ra_nguyen_bang(monkeypatch):
    _phat_lai(monkeypatch, _khung_gia(), "entrade")
    rong = _tai("ABC", _ngay(1095), END)
    cat = g1l.cat_tu_khung_rong(rong[0], _ngay(1095), END, symbol="ABC", exchange="HOSE")
    pd.testing.assert_frame_equal(rong[0], cat[0], check_exact=True)


def test_so_nen_cua_so_dung_ham_cua_duong_tai_khong_go_lai_cong_thuc():
    cay = ast.parse((GOC / "gia_mot_lan.py").read_text(encoding="utf-8"))
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "so_nen_cua_so")
    goi = {getattr(n.func, "attr", getattr(n.func, "id", "")) for n in ast.walk(ham) if isinstance(n, ast.Call)}
    assert "cua_so_vci_cu" in goi and "bdate_range" not in goi


def test_canh_bao_cua_phan_cat_lay_tu_kiem_dinh_chay_lai_tren_phan_cat(monkeypatch):
    """Hai nến có giá mở nằm NGOÀI khoảng cao-thấp (cảnh báo, không chặn): một trong 180 ngày cuối, một cũ hơn.
    Khung 1.095 ngày đếm 2 phiên, khung 180 ngày đếm 1; phần cắt phải đếm 1 như đường cũ (kiểm định chạy lại
    trên phần cắt, không chép cảnh báo của khung rộng)."""
    k = _khung_gia()
    for i in (len(k) - 20, len(k) - 500):
        k.loc[i, "open"] = k.loc[i, "high"] * 1.5
    _phat_lai(monkeypatch, k, "entrade")
    cu = _tai("ABC", _ngay(180), END)
    rong = _tai("ABC", _ngay(1095), END)
    cat = g1l.cat_tu_khung_rong(rong[0], _ngay(180), END, symbol="ABC", exchange="HOSE")
    assert cu[2] == cat[2] and len(cu[2]) == 1 and "1 phiên" in cu[2][0]
    assert rong[2] != cat[2] and "2 phiên" in rong[2][0]


@pytest.mark.parametrize("san", ["HOSE", "HNX", "UPCOM"])
def test_canh_bao_theo_san_cua_ma_khong_theo_san_co_dinh(monkeypatch, san):
    """Một phiên tăng 12% (ngưỡng cảnh báo nhảy giá: 1,5 × biên của sàn → HOSE cảnh báo, HNX và UPCoM không):
    phần cắt phải kiểm định theo sàn của MÃ như đường cũ."""
    k = _khung_gia()
    i = len(k) - 30
    k.loc[i:, ["open", "high", "low", "close"]] = k.loc[i:, ["open", "high", "low", "close"]].to_numpy() * 1.12
    _phat_lai(monkeypatch, k, "entrade")
    cu = _tai("ABC", _ngay(180), END, san)
    cat = g1l.cat_tu_khung_rong(_tai("ABC", _ngay(1095), END, san)[0], _ngay(180), END, symbol="ABC", exchange=san)
    assert cu[2] == cat[2]
    assert bool(cu[2]) == (san == "HOSE")


# ── 2. chỉ cắt khi cùng nguồn ───────────────────────────────────────────────
def _tai_mot_lan(monkeypatch, ten_nguon_rong, khung=None, ngay_rong=1095):
    """Chạy `tai_mot_lan` với nguồn giả; trả (kết quả, số lượt đi qua `tai_nguon`, số lượt đi qua `tai`)."""
    _phat_lai(monkeypatch, khung if khung is not None else _khung_gia(), "entrade")
    dem = {"nguon": 0, "cu": 0}

    def tai_nguon(*a):
        dem["nguon"] += 1
        df, tt, w, _ = _tai_nguon(*a)
        return df, tt, w, ten_nguon_rong

    def tai(*a):
        dem["cu"] += 1
        return _tai(*a)
    kq = g1l.tai_mot_lan(tai_nguon, tai, "ABC", _ngay(180), END, "HOSE", ngay_rong)
    return kq, dem


def test_nguon_dau_chuoi_thi_cat_khong_goi_duong_cu(monkeypatch):
    kq, dem = _tai_mot_lan(monkeypatch, "entrade")
    assert dem == {"nguon": 1, "cu": 0}
    pd.testing.assert_frame_equal(kq[0], _tai("ABC", _ngay(180), END)[0], check_exact=True)


def test_nguon_khac_nguon_dau_thi_KHONG_cat_ma_tra_duong_cu(monkeypatch):
    kq, dem = _tai_mot_lan(monkeypatch, "vndirect")
    assert dem == {"nguon": 1, "cu": 1}
    pd.testing.assert_frame_equal(kq[0], _tai("ABC", _ngay(180), END)[0], check_exact=True)


def test_trang_thai_khac_OK_thi_KHONG_cat_du_co_bang_va_dung_nguon(monkeypatch):
    """`SYNTHETIC` đi kèm một bảng giá ngẫu nhiên hợp lệ về hình dạng: cắt nó là bịa giá cho biểu đồ."""
    _phat_lai(monkeypatch, _khung_gia(), "entrade")
    dem = {"cu": 0}

    def tai_nguon(*a):
        return _khung_gia(n_ngay=900), "SYNTHETIC", [], "entrade"

    def tai(*a):
        dem["cu"] += 1
        return "DUONG_CU", "SYNTHETIC", []
    assert g1l.tai_mot_lan(tai_nguon, tai, "ABC", _ngay(180), END, "HOSE", 1095)[0] == "DUONG_CU"
    assert dem["cu"] == 1


def test_diem_dau_cua_so_rong_la_end_tru_ngay_rong(monkeypatch):
    thay = {}
    _phat_lai(monkeypatch, _khung_gia(), "entrade")

    def tai_nguon(tk, s, e, x):
        thay["start_rong"] = s
        return _tai_nguon(tk, s, e, x)
    g1l.tai_mot_lan(tai_nguon, _tai, "ABC", _ngay(180), END, "HOSE", 1095)
    assert thay["start_rong"] == _ngay(1095)


def test_nguon_dau_chuoi_la_ten_that_cua_chuoi():
    assert g1l.nguon_dau_chuoi("acb") == ngk.chuoi_nguon("ACB")[0].ten == "entrade"
    assert g1l.nguon_dau_chuoi("VNINDEX") == ngk.chuoi_nguon("VNINDEX")[0].ten == "vndirect"


# ── 3. mọi nhánh không chắc về đường cũ ─────────────────────────────────────
def test_bang_rong_ngan_hon_cua_so_hep_thi_ve_duong_cu(monkeypatch):
    k = _khung_gia(n_ngay=60)                         # mã niêm yết muộn: chỉ 60 phiên
    _phat_lai(monkeypatch, k, "entrade")
    rong = _tai("ABC", _ngay(1095), END)[0]
    assert len(rong) < g1l.so_nen_cua_so(_ngay(180), END)
    assert g1l.cat_tu_khung_rong(rong, _ngay(180), END, symbol="ABC", exchange="HOSE") is None


@pytest.mark.parametrize("rong", [None, pd.DataFrame()])
def test_bang_rong_rong_hay_none_thi_none(rong):
    assert g1l.cat_tu_khung_rong(rong, _ngay(180), END, symbol="ABC", exchange="HOSE") is None


def test_tai_rong_hong_thi_ve_duong_cu(monkeypatch):
    _phat_lai(monkeypatch, _khung_gia(), "entrade")
    dem = {"cu": 0}

    def tai_nguon(*a):
        return None, "FAILED", [], ""

    def tai(*a):
        dem["cu"] += 1
        return "DUONG_CU", "OK", []
    assert g1l.tai_mot_lan(tai_nguon, tai, "ABC", _ngay(180), END, "HOSE", 1095) == ("DUONG_CU", "OK", [])
    assert dem["cu"] == 1


def test_kiem_dinh_chan_phan_cat_thi_ve_duong_cu(monkeypatch):
    import data_quality as dq

    class Chan:
        blocked = True
        warnings = []
    monkeypatch.setattr(dq, "validate_ohlcv", lambda *a, **k: Chan())
    assert g1l.cat_tu_khung_rong(_khung_gia(), _ngay(180), END, symbol="ABC", exchange="HOSE") is None


def test_cua_so_rong_hon_start_thi_lay_start_lam_diem_dau(monkeypatch):
    """`ngay_rong` NHỎ hơn cửa sổ hẹp: điểm đầu là `start` (không bao giờ hẹp hơn thứ được xin)."""
    thay = {}
    _phat_lai(monkeypatch, _khung_gia(), "entrade")

    def tai_nguon(tk, s, e, x):
        thay["start_rong"] = s
        return _tai_nguon(tk, s, e, x)
    g1l.tai_mot_lan(tai_nguon, _tai, "ABC", _ngay(180), END, "HOSE", 10)
    assert thay["start_rong"] == _ngay(180)


# ── 4. app nối đúng ─────────────────────────────────────────────────────────
def _app():
    return ast.parse((GOC / "app.py").read_text(encoding="utf-8"))


def _goi_trong(cay, ten_ham):
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten_ham)
    return {getattr(n.func, "attr", getattr(n.func, "id", "")) for n in ast.walk(ham) if isinstance(n, ast.Call)}


def test_AST_nen_tuan_thang_va_vnindex_DI_qua_cat_tu_BUOC_288():
    """BƯỚC 288 ĐẢO phép khoá của BƯỚC 280: `_nen_ba_khung` (cửa sổ 1.583 ngày) tải qua `load_stock_data_cat` nên cổ
    phiếu chung MỘT lượt tải với biểu đồ ngày và ô Dow; không còn lời gọi `load_stock_data` trực tiếp ở đó."""
    goi = _goi_trong(_app(), "_nen_ba_khung")
    assert "load_stock_data_cat" in goi and "load_stock_data" not in goi


def test_AST_bieu_do_ngay_o_Dow_va_nen_tuan_thang_di_qua_cat():
    cay = _app()
    dung = [n for n in ast.walk(cay) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
            and getattr(n.value.func, "id", "") == "load_stock_data_cat"]
    muc_tieu = {ast.unparse(n.targets[0]).strip("()") for n in dung}
    assert muc_tieu == {"df, _price_status, _quality_warnings", "_ct_df, _ct_tt, _ct_canh_bao",
                        "d, trang_thai, _"}


def test_AST_load_stock_data_cat_chi_goi_tai_mot_lan_voi_hai_ham_tai():
    cay = _app()
    ham = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "load_stock_data_cat")
    goi = [n for n in ast.walk(ham) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "tai_mot_lan"]
    assert len(goi) == 1
    ten = [ast.unparse(a) for a in goi[0].args[:2]]
    assert ten == ["load_stock_data_nguon", "load_stock_data"]
    assert [ast.unparse(d) for d in ham.decorator_list] == ["st.cache_data(ttl=300)"]
    # cửa sổ rộng = ba cửa sổ ĐƯỢC gộp (BƯỚC 288 thêm cửa sổ nến tuần/tháng: người dùng chọn phương án C)
    nguon = ast.unparse(ham)
    assert "_NGAY_LICH_DOW" in nguon and "NGAY_LICH_CHO_KHUNG_THANG" in nguon and "days_back" in nguon


def test_NGAY_LICH_DOW_cua_app_la_chinh_so_ngay_cua_o_Dow():
    import cau_truc_gia as ctg
    cay = _app()
    nhap = [n for n in ast.walk(cay) if isinstance(n, ast.ImportFrom) and n.module == "cau_truc_gia"]
    assert [(a.name, a.asname) for n in nhap for a in n.names] == [("NGAY_LICH_CUA_SO", "_NGAY_LICH_DOW")]
    assert ctg.NGAY_LICH_CUA_SO > 180            # cửa sổ Dow rộng hơn cửa sổ biểu đồ ngày (mặc định `days_back`)


def test_duong_quet_va_collect_khong_nhac_ten_moi():
    cam = {"gia_mot_lan", "tai_mot_lan", "cat_tu_khung_rong", "load_stock_data_cat", "load_stock_data_nguon"}
    for p in [GOC / f for f in ("run_daily.py", "paper_runner.py", "san_dau.py", "paper_trading.py",
                                "data_collectors.py", "nguon_gia_cong_khai.py", "keo_bang_gia.py",
                                "master_agent.py")] + sorted((GOC / "backtest").glob("*.py")):
        if not p.exists():
            continue
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            ten = (n.attr if isinstance(n, ast.Attribute) else n.id if isinstance(n, ast.Name)
                   else n.name if isinstance(n, ast.alias) else None)
            assert ten not in cam, f"{p.name}:{getattr(n, 'lineno', '?')} nhắc {ten}"
