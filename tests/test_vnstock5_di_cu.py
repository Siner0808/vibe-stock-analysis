"""BƯỚC 260 — di cư sang vnstock thế hệ 5: những chỗ KHÔNG được hỏng lặng lẽ.

Mọi phép kiểm chạy OFFLINE: thay `vnstock` bằng module giả, không đăng nhập thật, không đăng
ký thiết bị nào. Thứ chúng canh (đo 06/11 và 10/11/2026, `docs/STATE.md` BƯỚC 260):

  * `time` của vnstock 5 mang múi giờ (`2026-05-04 07:00:00+07:00`) — so với `Timestamp`
    naive thì nổ TypeError, ghi CSV thì mang đuôi `+07:00`.
  * `Quote("VNINDEX")` thế hệ 5 trả điểm chia 1000 và làm tròn 2 chữ số (1737,66 -> 1.74);
    chỉ `Market().index(...)` cho điểm thật.
  * `vnstock.login(khoá)` thay `change_api_key`; không đăng nhập là hạng KHÁCH (10 lượt/phút,
    OHLCV ~1 năm) nên một lần đăng nhập hỏng phải dừng lượt quét, không được nuốt.
  * Lượt quét hằng ngày áp khoá TRƯỚC khi tải (`VNStockCollectorAgent.collect`).
  * `requirements.txt` không còn `vnai`, và `fetch_khoi_ngoai` không còn `vnstock_data`.
"""
import ast
import pathlib
import sys
import types

import pandas as pd
import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import data_quality  # noqa: E402
import vnstock_auth  # noqa: E402


def _khung_tz(n=3, gio=7):
    """Bảng nến ngày dạng thế hệ 5: `time` có múi giờ Asia/Ho_Chi_Minh."""
    ts = pd.date_range("2026-11-03", periods=n, freq="D", tz="Asia/Ho_Chi_Minh") + pd.Timedelta(hours=gio)
    return pd.DataFrame({"time": ts, "open": 50.0, "high": 51.0, "low": 49.0,
                         "close": 50.5, "volume": 1_000_000})


# ─────────────────────────────────────────────────────────────────────
# 1. Cắt múi giờ ở cửa vào
# ─────────────────────────────────────────────────────────────────────

def test_chuan_hoa_thoi_gian_cat_mui_gio_va_GIU_gio_treo_tuong():
    d = data_quality.chuan_hoa_thoi_gian(_khung_tz())
    assert not isinstance(d["time"].dtype, pd.DatetimeTZDtype)
    assert str(d["time"].dtype).startswith("datetime64")
    assert list(d["time"]) == [pd.Timestamp("2026-11-03 07:00"), pd.Timestamp("2026-11-04 07:00"),
                               pd.Timestamp("2026-11-05 07:00")], "phải giữ giờ VN, không đổi sang UTC"
    # So được với Timestamp naive — đúng chỗ thế hệ 5 làm nổ TypeError.
    assert (d["time"] >= pd.Timestamp("2026-11-04")).sum() == 2


def test_chuan_hoa_thoi_gian_khong_dung_vao_cot_da_naive_chuoi_hay_thieu_cot():
    naive = _khung_tz().assign(time=lambda x: x["time"].dt.tz_localize(None))
    chuoi = naive.assign(time=lambda x: x["time"].dt.strftime("%Y-%m-%d"))
    for d in (naive, chuoi):
        ra = data_quality.chuan_hoa_thoi_gian(d)
        assert ra["time"].equals(d["time"])
        assert ra is not d, "phải trả BẢN SAO"
    khong_cot = pd.DataFrame({"x": [1]})
    assert data_quality.chuan_hoa_thoi_gian(khong_cot).equals(khong_cot)
    một = data_quality.chuan_hoa_thoi_gian(_khung_tz())
    assert data_quality.chuan_hoa_thoi_gian(một)["time"].equals(một["time"]), "idempotent"


def test_chuan_hoa_thoi_gian_khong_sua_bang_goc():
    goc = _khung_tz()
    data_quality.chuan_hoa_thoi_gian(goc)
    assert isinstance(goc["time"].dtype, pd.DatetimeTZDtype)


def test_normalize_ohlcv_di_qua_cua_cat_mui_gio():
    d = data_quality.normalize_ohlcv(_khung_tz())
    assert not isinstance(d["time"].dtype, pd.DatetimeTZDtype)
    assert len(d) == 3 and d["time"].iloc[0] == pd.Timestamp("2026-11-03 07:00")


# ─────────────────────────────────────────────────────────────────────
# 2. backtest.data.fetch_one: cổ phiếu qua Quote, CHỈ SỐ qua Market().index
# ─────────────────────────────────────────────────────────────────────

class _Ghi:
    def __init__(self):
        self.quote = []
        self.index = []
        self.limit = None


@pytest.fixture
def vnstock_gia(monkeypatch):
    import backtest.data as bd

    ghi = _Ghi()
    vn = types.ModuleType("vnstock")

    class Quote:
        def __init__(self, symbol, source):
            self.symbol, self.source = symbol, source

        def history(self, start=None, end=None):
            ghi.quote.append((self.symbol, self.source))
            return _khung_tz()

    class _Chi_so:
        def __init__(self, ma):
            self.ma = ma

        def ohlcv(self, start=None, end=None, limit=None):
            ghi.index.append(self.ma)
            ghi.limit = limit
            return _khung_tz().assign(close=1737.66)

    class Market:
        def index(self, ma):
            return _Chi_so(ma)

    vn.Quote, vn.Market = Quote, Market
    monkeypatch.setitem(sys.modules, "vnstock", vn)
    monkeypatch.setattr(vnstock_auth, "ensure_api_key", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(bd.time, "sleep", lambda *_: None)
    return bd, ghi, vn


def test_fetch_one_co_phieu_qua_Quote_va_cat_mui_gio(vnstock_gia):
    bd, ghi, _ = vnstock_gia
    df = bd.fetch_one("FPT", "2026-11-01", "2026-11-10", nguon="vci")
    assert ghi.quote == [("FPT", "vci")] and ghi.index == []
    assert not isinstance(df["time"].dtype, pd.DatetimeTZDtype)


def test_fetch_one_chi_so_qua_Market_index_KHONG_qua_Quote(vnstock_gia):
    bd, ghi, _ = vnstock_gia
    df = bd.fetch_one("VNINDEX", "2026-11-01", "2026-11-10")
    assert ghi.index == ["VNINDEX"] and ghi.quote == [], (
        "Quote('VNINDEX') thế hệ 5 trả 1.74 thay vì 1737,66")
    assert float(df["close"].iloc[-1]) == 1737.66
    assert not isinstance(df["time"].dtype, pd.DatetimeTZDtype)
    # `ohlcv()` của chỉ số cắt lặng lẽ còn 1000 dòng nếu không truyền `limit` (đo 10/11/2026).
    assert ghi.limit is not None and ghi.limit >= 5000, ghi.limit


def test_fetch_one_chi_so_hong_thi_None_KHONG_roi_xuong_Quote(vnstock_gia):
    bd, ghi, vn = vnstock_gia

    class Market:
        def index(self, ma):
            raise RuntimeError("mạng hỏng")

    vn.Market = Market
    assert bd.fetch_one("VNINDEX", "2026-11-01", "2026-11-10") is None
    assert ghi.quote == [], "rơi xuống Quote là nhận chuỗi chỉ số SAI THANG"


def test_MA_CHI_SO_co_VNINDEX():
    import backtest.data as bd
    assert "VNINDEX" in bd.MA_CHI_SO


# ─────────────────────────────────────────────────────────────────────
# 3. Nến nội phiên
# ─────────────────────────────────────────────────────────────────────

def test_intraday_tai_cat_mui_gio_truoc_khi_loc_va_ghi_cache(monkeypatch):
    import intraday_data

    gio = pd.date_range("2026-11-09 09:00", periods=4, freq="30min", tz="Asia/Ho_Chi_Minh")
    tho = pd.DataFrame({"time": gio, "open": 50.0, "high": 51.0, "low": 49.0,
                        "close": 50.5, "volume": 1000})
    mod = types.ModuleType("vnstock.api.quote")

    class Quote:
        def __init__(self, symbol, source):
            pass

        def history(self, start=None, end=None, interval=None):
            return tho

    mod.Quote = Quote
    monkeypatch.setitem(sys.modules, "vnstock.api.quote", mod)
    monkeypatch.setattr(vnstock_auth, "ensure_api_key", lambda *a, **k: {"ok": True})
    d = intraday_data.tai("FPT", "2026-11-09", "2026-11-09", "30m", dung_cache=False)
    assert not isinstance(d["time"].dtype, pd.DatetimeTZDtype)
    assert d["time"].iloc[0] == pd.Timestamp("2026-11-09 09:00")
    assert (d["time"] <= pd.Timestamp("2026-11-09") + pd.Timedelta(days=1)).all()


# ─────────────────────────────────────────────────────────────────────
# 4. Đăng nhập: vnstock.login, không nuốt lỗi
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def dang_nhap(monkeypatch):
    """Cách ly: không `st.secrets` thật, không `vnstock` thật, trạng thái sạch."""
    monkeypatch.setattr(vnstock_auth, "_STATE", {"done": False, "ok": False, "source": "",
                                                 "error": "", "tier": ""})
    st = types.ModuleType("streamlit")
    st.secrets = types.SimpleNamespace(get=lambda *a, **k: None)
    monkeypatch.setitem(sys.modules, "streamlit", st)
    monkeypatch.delenv("VNSTOCK_API_KEY", raising=False)
    vn = types.ModuleType("vnstock")
    monkeypatch.setitem(sys.modules, "vnstock", vn)
    return vn, monkeypatch


KHOA = "vnstock_KHOA_GIA_CHI_DE_TEST_0123456789"


def test_dang_nhap_goi_vnstock_login_voi_khoa_va_ghi_hang(dang_nhap):
    vn, mp = dang_nhap
    nhan = []
    vn.login = lambda k: (nhan.append(k), {"authenticated": True, "tier": "silver"})[1]
    mp.setenv("VNSTOCK_API_KEY", KHOA)
    s = vnstock_auth.ensure_api_key()
    assert nhan == [KHOA]
    assert s["ok"] is True and s["tier"] == "silver" and s["source"] == "biến môi trường"
    assert KHOA not in str(s) and KHOA not in vnstock_auth.status_message()
    assert "silver" in vnstock_auth.status_message()


def test_dang_nhap_nem_loi_thi_ok_False_va_loi_nam_trong_state_khong_lo_khoa(dang_nhap):
    vn, mp = dang_nhap

    def _no(k):
        raise RuntimeError(f"AuthError: khoá {k} bị từ chối")
    vn.login = _no
    mp.setenv("VNSTOCK_API_KEY", KHOA)
    s = vnstock_auth.ensure_api_key()
    assert s["ok"] is False and "RuntimeError" in s["error"]
    assert KHOA not in s["error"] and "<khoá>" in s["error"]
    assert "Không nạp được" in vnstock_auth.status_message()
    assert KHOA not in vnstock_auth.status_message()


def test_login_tra_ve_chua_xac_thuc_thi_KHONG_ok(dang_nhap):
    """Máy chủ trả lời nhưng `authenticated` không True = vẫn là hạng khách."""
    vn, mp = dang_nhap
    vn.login = lambda k: {"authenticated": False, "tier": "guest"}
    mp.setenv("VNSTOCK_API_KEY", KHOA)
    s = vnstock_auth.ensure_api_key()
    assert s["ok"] is False and "không xác nhận khoá" in s["error"]


def test_bat_buoc_dang_nhap_nem_khi_hong_va_tra_trang_thai_khi_tot(dang_nhap):
    vn, mp = dang_nhap
    mp.setenv("VNSTOCK_API_KEY", KHOA)
    vn.login = lambda k: {"authenticated": False, "tier": "guest"}
    with pytest.raises(vnstock_auth.DangNhapLoi) as e:
        vnstock_auth.bat_buoc_dang_nhap()
    assert "hạng khách" in str(e.value) and KHOA not in str(e.value)

    mp.setattr(vnstock_auth, "_STATE", {"done": False, "ok": False, "source": "",
                                        "error": "", "tier": ""})
    vn.login = lambda k: {"authenticated": True, "tier": "silver"}
    assert vnstock_auth.bat_buoc_dang_nhap()["ok"] is True


def test_khong_co_khoa_va_chua_dang_nhap_thi_bat_buoc_NEM(dang_nhap):
    vn, _ = dang_nhap
    vn.status = lambda: {"authenticated": False, "tier": "guest"}
    with pytest.raises(vnstock_auth.DangNhapLoi) as e:
        vnstock_auth.bat_buoc_dang_nhap()
    assert "chưa cấu hình" in str(e.value)


def test_khong_co_khoa_nhung_may_da_dang_nhap_san_thi_ok(dang_nhap):
    vn, _ = dang_nhap
    vn.status = lambda: {"authenticated": True, "tier": "silver"}
    s = vnstock_auth.ensure_api_key()
    assert s["ok"] is True and s["source"] == "đăng nhập sẵn có của vnstock"


def test_ensure_api_key_chi_dang_nhap_MOT_lan(dang_nhap):
    vn, mp = dang_nhap
    dem = []
    vn.login = lambda k: (dem.append(1), {"authenticated": True, "tier": "silver"})[1]
    mp.setenv("VNSTOCK_API_KEY", KHOA)
    vnstock_auth.ensure_api_key()
    vnstock_auth.ensure_api_key()
    vnstock_auth.ensure_api_key(force=True)
    assert len(dem) == 2, "lần 2 phải dùng lại, chỉ force=True mới đăng nhập lại"


# ─────────────────────────────────────────────────────────────────────
# 5. Gác bằng AST: đường quét áp khoá và dừng khi hỏng
# ─────────────────────────────────────────────────────────────────────

def _cay(ten):
    return ast.parse((GOC / ten).read_text(encoding="utf-8"))


def _ham(cay, ten, lop=None):
    for n in ast.walk(cay):
        if lop and isinstance(n, ast.ClassDef) and n.name == lop:
            for m in n.body:
                if isinstance(m, ast.FunctionDef) and m.name == ten:
                    return m
        if not lop and isinstance(n, ast.FunctionDef) and n.name == ten:
            return n
    raise AssertionError(f"không thấy {ten}")


def _goi(nut):
    return {c.func.id if isinstance(c.func, ast.Name) else c.func.attr
            for c in ast.walk(nut) if isinstance(c, ast.Call)
            and isinstance(c.func, (ast.Name, ast.Attribute))}


def test_collect_ap_khoa_TRUOC_khi_tai():
    ham = _ham(_cay("data_collectors.py"), "collect", "VNStockCollectorAgent")
    dong_khoa = [c.lineno for c in ast.walk(ham) if isinstance(c, ast.Call)
                 and getattr(c.func, "id", "") == "ensure_api_key"]
    dong_tai = [c.lineno for c in ast.walk(ham) if isinstance(c, ast.Call)
                and getattr(c.func, "attr", "") == "history"]
    assert dong_khoa and dong_tai and min(dong_khoa) < min(dong_tai), (dong_khoa, dong_tai)


def test_collect_cat_mui_gio_qua_normalize_ohlcv():
    assert "normalize_ohlcv" in _goi(_ham(_cay("data_collectors.py"), "collect",
                                          "VNStockCollectorAgent"))


def _khoi_main(cay):
    for n in cay.body:
        if isinstance(n, ast.If) and isinstance(n.test, ast.Compare) \
                and getattr(n.test.left, "id", "") == "__name__":
            return n
    raise AssertionError("run_daily không có khối __main__")


def test_run_daily_main_dung_phien_khi_dang_nhap_hong_TRUOC_khi_quet():
    khoi = _khoi_main(_cay("run_daily.py"))
    cuoc = [(c.lineno, getattr(c.func, "attr", getattr(c.func, "id", "")))
            for c in ast.walk(khoi) if isinstance(c, ast.Call)]
    ten = [t for _, t in cuoc]
    assert "bat_buoc_dang_nhap" in ten and "execute_daily_scan" in ten
    dong_dn = min(d for d, t in cuoc if t == "bat_buoc_dang_nhap")
    dong_quet = min(d for d, t in cuoc if t == "execute_daily_scan")
    assert dong_dn < dong_quet
    # Bắt DangNhapLoi và thoát mã 1: cảnh báo không đi bằng mã thoát thì job không đỏ.
    xu_ly = [h for h in ast.walk(khoi) if isinstance(h, ast.ExceptHandler)
             and "DangNhapLoi" in ast.dump(h.type)]
    assert xu_ly, "không bắt DangNhapLoi"
    exits = [c for c in ast.walk(xu_ly[0]) if isinstance(c, ast.Call)
             and getattr(c.func, "attr", "") == "exit"
             and c.args and getattr(c.args[0], "value", None) == 1]
    assert exits, "phải sys.exit(1) để job đỏ và chuông canh"


def test_fetch_khoi_ngoai_dung_vnstock_Market_khong_con_vnstock_data():
    cay = _cay("fetch_khoi_ngoai.py")
    ten = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ten |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            ten.add(n.module.split(".")[0])
    assert "vnstock_data" not in ten and "vnstock" in ten
    assert "bat_buoc_dang_nhap" in _goi(_ham(cay, "main"))
    # Bảng khối ngoại thế hệ 5 mang múi giờ: phải cắt trước khi ghi CSV.
    assert "chuan_hoa_thoi_gian" in _goi(_ham(cay, "keo_mot_ma"))


def test_fetch_fundamentals_doc_hang_tu_vnstock_usage_khong_con_vnai():
    cay = _cay("fetch_fundamentals.py")
    ten = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            ten |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            ten.add(n.module.split(".")[0])
    assert "vnai" not in ten
    assert "usage" in _goi(_ham(cay, "hang_hien_tai"))


def test_requirements_khong_con_vnai_va_khong_ezchart_va_ghim_ban_5():
    dong = [d.split("#")[0].strip() for d in
            (GOC / "requirements.txt").read_text(encoding="utf-8").splitlines()]
    dong = [d for d in dong if d]
    ten = [d.split("==")[0].lower() for d in dong if not d.startswith("-")]
    assert "vnai" not in ten and "vnstock_ezchart" not in ten and "vnstock-ezchart" not in ten
    assert "vnstock==5.2.1" in dong
    assert "--extra-index-url https://vnstocks.com/api/packages" in dong


def test_khong_file_nao_o_goc_nhap_vnai_hay_goi_change_api_key():
    for f in sorted(GOC.glob("*.py")):
        cay = ast.parse(f.read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.Import):
                assert all(a.name.split(".")[0] != "vnai" for a in n.names), f.name
            elif isinstance(n, ast.ImportFrom):
                assert (n.module or "").split(".")[0] != "vnai", f.name
            elif isinstance(n, ast.Attribute):
                assert n.attr != "change_api_key", f"{f.name}:{n.lineno}"
