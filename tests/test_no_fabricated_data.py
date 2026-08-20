"""Chặn dữ liệu bịa quay lại.

Bối cảnh: bản cũ của financial_collector.py sinh P/E, EPS, Beta, vốn hóa từ
hash(symbol) và báo cáo tài chính 5 năm từ np.random — rồi hiển thị công khai
như số liệu của doanh nghiệp niêm yết có thật.

Ba tầng bảo vệ ở đây:
  1. Tất định  — cùng đầu vào phải cho cùng đầu ra, qua nhiều tiến trình.
  2. Fail-closed — không lấy được nguồn thật thì available=False, không có số.
  3. Tĩnh      — cấm np.random / hash() trong module dữ liệu.

Chạy offline:  python3 tests/test_no_fabricated_data.py
"""
import ast
import os
import subprocess
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

import financial_collector as fc
from financial_collector import FinancialDataCollector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_MODULES = ["financial_collector.py", "data_collectors.py"]


def _no_network():
    """Ép mọi lời gọi vnstock thất bại, mô phỏng mất kết nối."""
    fake = types.ModuleType("vnstock")

    def _boom(*a, **kw):
        raise ConnectionError("mô phỏng mất mạng")

    fake.Finance = _boom
    fake.Trading = _boom
    fake.Company = _boom
    fake.Quote = _boom
    return fake


# Chặn mạng trong tiến trình con: test phải nhanh và tất định, không phụ
# thuộc việc máy chạy test có ra được internet hay không.
_STUB_NET = """
import sys, types
_f = types.ModuleType("vnstock")
def _boom(*a, **kw): raise ConnectionError("test: chặn mạng")
_f.Finance = _f.Trading = _f.Company = _f.Quote = _boom
sys.modules["vnstock"] = _f
"""


def _isolated(fn_body: str) -> str:
    """Chạy đoạn mã trong tiến trình riêng (hash seed khác nhau), không mạng.

    Ném lỗi nếu tiến trình con thất bại. Không có bước này, 5 lần chạy cùng
    ném một traceback giống nhau sẽ bị coi là "kết quả tất định" — test báo
    PASS trong khi thực chất chẳng đo được gì.
    """
    src = f"import sys; sys.path.insert(0, {ROOT!r})\n{_STUB_NET}\n{fn_body}"
    out = subprocess.run([sys.executable, "-c", src],
                         capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise RuntimeError(
            f"tiến trình con lỗi (mã {out.returncode}): {out.stderr.strip()[-300:]}")
    return out.stdout.strip()


# ─────────────────────────────────────────────────────────────────────
# 1. TẤT ĐỊNH — đây là test bắt được lỗi cũ
# ─────────────────────────────────────────────────────────────────────
def test_chi_so_khong_doi_giua_cac_tien_trinh():
    """Cùng mã FPT, chạy ở 5 tiến trình khác nhau => kết quả phải GIỐNG HỆT.

    Bản cũ fail test này: hash() chuỗi được ngẫu nhiên hoá theo tiến trình,
    nên P/E chạy từ 14.5 đến 26.5 và vốn hóa từ 11.900 đến 82.450 tỷ.
    """
    code = (
        "from financial_collector import FinancialDataCollector as F\n"
        "o = F().get_company_overview('FPT')\n"
        "print(o['pe'], o['eps'], o['beta'], o['market_cap_billions'],"
        " o['shares_outstanding'], o['available'])"
    )
    results = {_isolated(code) for _ in range(5)}
    assert len(results) == 1, (
        f"Số liệu ĐỔI giữa các lần chạy — dấu hiệu sinh từ hash/random: {results}")
    print(f"PASS  tất định qua 5 tiến trình -> {results.pop()}")


def test_bctc_khong_doi_giua_cac_tien_trinh():
    code = (
        "from financial_collector import FinancialDataCollector as F\n"
        "d = F().get_financial_statements('FPT')\n"
        "print(d['available'], d['years'], d['revenue'])"
    )
    results = {_isolated(code) for _ in range(4)}
    assert len(results) == 1, f"BCTC đổi giữa các lần chạy: {results}"
    print("PASS  báo cáo tài chính tất định")


# ─────────────────────────────────────────────────────────────────────
# 2. FAIL-CLOSED — mất nguồn thì không có số, không phải số bịa
# ─────────────────────────────────────────────────────────────────────
def test_mat_mang_thi_khong_co_chi_so_thay_vi_bia():
    saved = sys.modules.get("vnstock")
    sys.modules["vnstock"] = _no_network()
    fc._CACHE.clear()
    try:
        o = FinancialDataCollector().get_company_overview("FPT")
    finally:
        sys.modules.pop("vnstock", None)
        if saved is not None:
            sys.modules["vnstock"] = saved
        fc._CACHE.clear()

    assert o["available"] is False
    for k in ("pe", "eps", "beta", "market_cap_billions", "shares_outstanding"):
        assert o[k] is None, f"{k} có giá trị {o[k]!r} dù không lấy được nguồn"
    assert o["note"], "phải nói rõ vì sao không có dữ liệu"
    print(f"PASS  mất mạng -> mọi chỉ số = None, note: {o['note'][:50]}...")


def test_mat_mang_thi_bctc_va_khoi_ngoai_bao_khong_co():
    saved = sys.modules.get("vnstock")
    sys.modules["vnstock"] = _no_network()
    fc._CACHE.clear()
    try:
        fs = FinancialDataCollector().get_financial_statements("FPT")
        ft = FinancialDataCollector().get_foreign_trading_history("FPT")
    finally:
        sys.modules.pop("vnstock", None)
        if saved is not None:
            sys.modules["vnstock"] = saved
        fc._CACHE.clear()

    assert fs["available"] is False and fs["revenue"] == []
    assert ft["available"] is False and ft["net_values_billion"] == []
    print("PASS  BCTC & khối ngoại báo không có dữ liệu, danh sách rỗng")


def test_gia_tinh_tu_ohlcv_that_van_hoat_dong():
    """Phần tính từ dữ liệu giá thật KHÔNG phụ thuộc mạng — phải luôn đúng."""
    n = 250
    close = pd.Series([50_000 + i * 100 for i in range(n)], dtype=float)
    df = pd.DataFrame({"open": close, "high": close * 1.01,
                       "low": close * 0.99, "close": close,
                       "volume": [1_000_000] * n})
    saved = sys.modules.get("vnstock")
    sys.modules["vnstock"] = _no_network()
    fc._CACHE.clear()
    try:
        o = FinancialDataCollector().get_company_overview("FPT", df)
    finally:
        sys.modules.pop("vnstock", None)
        if saved is not None:
            sys.modules["vnstock"] = saved
        fc._CACHE.clear()

    assert o["price_available"] is True
    assert o["latest_price"] == close.iloc[-1]
    assert o["high_period"] == max(close) * 1.01
    assert o["avg_vol_10d"] == 1_000_000
    assert o["pct_1w"] > 0 and o["pct_period"] > 0
    # nhưng chỉ số định giá vẫn phải là None
    assert o["pe"] is None and o["market_cap_billions"] is None
    print(f"PASS  giá thật vẫn tính được (đỉnh kỳ {o['high_period']:,.0f}), "
          "chỉ số định giá vẫn None")


# ─────────────────────────────────────────────────────────────────────
# 3. TĨNH — cấm công cụ sinh số trong module dữ liệu
# ─────────────────────────────────────────────────────────────────────
def test_module_du_lieu_khong_dung_random_hay_hash():
    """financial_collector.py không được chứa np.random / random / hash().

    data_collectors.py được miễn trừ có kiểm soát: nó có bộ sinh dữ liệu dự
    phòng, nhưng bắt buộc gắn nhãn SYNTHETIC (đã có test riêng).
    """
    src = open(os.path.join(ROOT, "financial_collector.py"), encoding="utf-8").read()
    tree = ast.parse(src)

    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = ""
            if isinstance(f, ast.Name):
                name = f.id
            elif isinstance(f, ast.Attribute):
                parts = []
                cur = f
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                name = ".".join(reversed(parts))
            if name == "hash" or name.startswith(("np.random", "numpy.random", "random.")):
                offenders.append(f"dòng {node.lineno}: {name}()")

    assert not offenders, (
        "financial_collector.py dùng công cụ sinh số ngẫu nhiên: " + "; ".join(offenders))
    print("PASS  không có hash()/np.random trong financial_collector.py")


def test_data_collectors_van_gan_nhan_synthetic():
    """Bộ sinh dự phòng của data_collectors phải luôn khai báo SYNTHETIC."""
    src = open(os.path.join(ROOT, "data_collectors.py"), encoding="utf-8").read()
    assert '"status": "SYNTHETIC"' in src, \
        "nhánh dự phòng không còn khai báo SYNTHETIC — dữ liệu giả sẽ bị coi là thật"
    assert '_generate_fallback_df' in src
    print("PASS  data_collectors vẫn gắn nhãn SYNTHETIC cho dữ liệu sinh")


def test_goi_vnstock_dung_chu_ky_ham():
    """Bắt lỗi sai chữ ký hàm mà không cần mạng.

    Bối cảnh: facade `vnstock.Finance` bắt buộc tham số `source`, còn lớp
    explorer bên dưới thì không. Gọi thiếu `source` -> TypeError, và vì mọi
    lỗi đều bị nuốt thành "không có dữ liệu", triệu chứng nhìn y hệt mất mạng.
    Test này phân biệt hai thứ đó.
    """
    try:
        import vnstock
    except ImportError:
        print("SKIP  vnstock chưa cài — bỏ qua kiểm tra chữ ký")
        return

    import inspect
    checks = [
        (vnstock.Finance, dict(source="VCI", symbol="FPT",
                               period="year", show_log=False)),
        (vnstock.Trading, dict(source="VCI", symbol="FPT", show_log=False)),
    ]
    for cls, kwargs in checks:
        sig = inspect.signature(cls.__init__)
        try:
            sig.bind(None, **kwargs)          # None thay cho self
        except TypeError as e:
            raise AssertionError(
                f"{cls.__name__} gọi sai chữ ký với {kwargs}: {e}") from None

    # Đối chứng: thiếu `source` PHẢI hỏng — chứng minh test có tác dụng
    try:
        inspect.signature(vnstock.Finance.__init__).bind(None, symbol="FPT")
        raise AssertionError("thiếu `source` mà vẫn hợp lệ — test vô dụng")
    except TypeError:
        pass
    print("PASS  chữ ký gọi vnstock đúng (và test bắt được khi thiếu `source`)")


def test_doc_duoc_bang_xoay_ngang_cua_vnstock():
    """vnstock trả BCTC dạng: chỉ tiêu ở HÀNG, năm ở CỘT.

    Bản trước dò theo tên cột nên không tìm thấy gì — app hiện toàn "—"
    dù API trả về dữ liệu đầy đủ. Cột thực tế quan sát được trên bản deploy:
    ['item', 'item_en', 'item_id', '2018', ...]
    """
    import pandas as pd

    import financial_collector as fcm

    df = pd.DataFrame({
        "item": ["Chỉ số P/E", "EPS", "Beta", "Doanh thu thuần"],
        "item_en": ["P/E", "EPS (VND)", "Beta", "Net Revenue"],
        "item_id": [1, 2, 3, 4],
        "2023": [18.0, 4000.0, 1.1, 50_000.0],
        "2024": [20.0, 4200.0, 1.2, 55_000.0],
        "2025": [22.5, 4500.0, 1.3, 60_000.0],
    })

    assert fcm._is_row_oriented(df), "không nhận ra bảng xoay ngang"
    # _year_columns trả (năm, VỊ TRÍ cột) — vị trí chứ không phải nhãn, vì
    # vnstock có thể trả nhiều cột trùng nhãn (VCI trả 16 cột đều '2018').
    assert fcm._year_columns(df) == [(2023, 3), (2024, 4), (2025, 5)]

    # lấy (giá trị, năm) của năm gần nhất — năm là bắt buộc, nếu không thì
    # không phân biệt được số của 2025 với số của 2018
    assert fcm._row_latest(df, "p/e") == (22.5, 2025)
    assert fcm._row_latest(df, "eps") == (4500.0, 2025)
    assert fcm._row_latest(df, "beta") == (1.3, 2025)
    assert fcm._row_latest(df, "khong-ton-tai") == (None, None)

    # lấy cả chuỗi theo năm
    years, rev = fcm._row_series(df, "net revenue")
    assert years == ["2023", "2024", "2025"]
    assert rev == [50_000.0, 55_000.0, 60_000.0]
    print("PASS  đọc được bảng xoay ngang (chỉ tiêu ở hàng, năm ở cột)")


def test_bo_qua_nam_thieu_so_lieu():
    """Năm gần nhất trống thì lùi về năm có số liệu, không trả None."""
    import pandas as pd

    import financial_collector as fcm

    df = pd.DataFrame({
        "item_en": ["P/E"],
        "2023": [18.0], "2024": [19.0], "2025": [None],
    })
    assert fcm._row_latest(df, "p/e") == (19.0, 2024), "phải lùi về 2024 kèm năm"
    print("PASS  năm mới nhất trống -> lùi về năm có số liệu, báo đúng năm")


def test_bang_dang_cot_van_doc_duoc():
    """Không được làm hỏng đường xử lý bảng dạng cột (nếu nguồn đổi định dạng)."""
    import pandas as pd

    import financial_collector as fcm

    df = pd.DataFrame({"yearReport": [2024, 2025], "P/E": [18.0, 20.0]})
    assert not fcm._is_row_oriented(df)
    assert fcm._first_value(df, fcm._pick(df, "p/e")) == 18.0
    print("PASS  bảng dạng cột vẫn xử lý được")


def test_api_key_khong_bao_gio_lo_ra_ngoai():
    """Module nạp key không được để key lọt vào trạng thái hay thông báo UI."""
    import vnstock_auth

    SECRET = "vnstock_TESTKEY_khong_duoc_xuat_hien_o_dau_ca"
    saved_env = os.environ.get("VNSTOCK_API_KEY")
    saved_mod = sys.modules.get("vnstock")

    fake = types.ModuleType("vnstock")
    seen = {}
    fake.change_api_key = lambda k: seen.setdefault("key", k) or True
    sys.modules["vnstock"] = fake
    os.environ["VNSTOCK_API_KEY"] = SECRET

    # Cách ly nguồn secrets. _read_key() ưu tiên st.secrets hơn biến môi
    # trường, nên trên máy có .streamlit/secrets.toml thật thì key thật
    # thắng key giả của test và test đỏ — dù mã không hề đổi. Máy không có
    # secrets.toml lại xanh. Ghim st.secrets rỗng để test đo đúng thứ nó
    # định đo: key có tới được vnstock không, và có lộ ra ngoài không.
    saved_st = sys.modules.get("streamlit")
    st_gia = types.ModuleType("streamlit")
    st_gia.secrets = types.SimpleNamespace(get=lambda *a, **k: None)
    sys.modules["streamlit"] = st_gia
    try:
        status = vnstock_auth.ensure_api_key(force=True)
        msg = vnstock_auth.status_message()
    finally:
        sys.modules.pop("streamlit", None)
        if saved_st is not None:
            sys.modules["streamlit"] = saved_st
        sys.modules.pop("vnstock", None)
        if saved_mod is not None:
            sys.modules["vnstock"] = saved_mod
        os.environ.pop("VNSTOCK_API_KEY", None)
        if saved_env is not None:
            os.environ["VNSTOCK_API_KEY"] = saved_env
        vnstock_auth._STATE.update(done=False, ok=False, source="", error="")

    assert seen.get("key") == SECRET, "key chưa được chuyển tới vnstock"
    assert status["ok"] is True and status["configured"] is True
    for blob in (str(status), msg):
        assert SECRET not in blob, f"KEY BỊ LỘ trong: {blob[:120]}"
    print(f"PASS  key được nạp nhưng không lộ — UI chỉ thấy: {msg[:60]}...")


def test_thieu_key_van_chay_binh_thuong():
    """Không có key thì app vẫn phải chạy, chỉ báo trạng thái."""
    import vnstock_auth

    saved_env = os.environ.pop("VNSTOCK_API_KEY", None)
    saved_mod = sys.modules.get("vnstock")
    fake_vnai = types.ModuleType("vnai")
    fake_vnai.get_api_key = lambda: None
    saved_vnai = sys.modules.get("vnai")
    sys.modules["vnai"] = fake_vnai
    try:
        s = vnstock_auth.ensure_api_key(force=True)
        msg = vnstock_auth.status_message()
    finally:
        sys.modules.pop("vnai", None)
        if saved_vnai is not None:
            sys.modules["vnai"] = saved_vnai
        if saved_mod is not None:
            sys.modules["vnstock"] = saved_mod
        if saved_env is not None:
            os.environ["VNSTOCK_API_KEY"] = saved_env
        vnstock_auth._STATE.update(done=False, ok=False, source="", error="")

    assert s["ok"] is False and "chưa cấu hình" in s["error"]
    assert "Chưa cấu hình" in msg and "vẫn hoạt động" in msg
    print("PASS  thiếu key vẫn chạy, thông báo rõ ràng")


def test_khong_co_key_trong_ma_nguon():
    """Chống tái phạm: không file .py nào chứa key vnstock hay Gemini."""
    import glob
    import re

    offenders = []
    for path in glob.glob(os.path.join(ROOT, "*.py")) + \
            glob.glob(os.path.join(ROOT, "*", "*.py")):
        if os.sep + "tests" + os.sep in path or os.sep + ".venv" + os.sep in path:
            continue
        src = open(path, encoding="utf-8").read()
        for m in re.findall(r"""["']([A-Za-z0-9_\-.]{25,})["']""", src):
            if m.startswith("vnstock_") or m.startswith("AIza") or (
                any(c.isupper() for c in m) and any(c.islower() for c in m)
                and any(c.isdigit() for c in m)
            ):
                offenders.append(f"{os.path.basename(path)}: {m[:12]}...")
    assert not offenders, f"chuỗi giống credential trong mã nguồn: {offenders[:3]}"
    print(f"PASS  không có credential trong mã nguồn "
          f"({len(glob.glob(os.path.join(ROOT, '*.py')))} file .py gốc)")


def test_app_khong_ve_du_lieu_synthetic():
    """app.py phải kiểm tra status trước khi vẽ, không chỉ lấy df."""
    src = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
    assert "_price_status" in src, "app.py không kiểm tra status của nguồn giá"
    assert 'res.get("status"' in src, "load_stock_data vẫn bỏ qua status"
    print("PASS  app.py chặn dữ liệu SYNTHETIC trước khi vẽ")



def test_bao_cao_phien_khong_doc_diem_bang_mac_dinh_so():
    """run_daily.py không được lấy điểm qua `.get(khoá, <số>)`.

    Đây là phía TIÊU THỤ của cùng một lỗ hổng: `s.get("score", 50.0)` trong
    khi run_session() không đặt khoá "score". Không có gì nổ, không có gì
    log — mọi báo cáo phiên chỉ lặng lẽ in 50.0 cho toàn bộ 71 mã.

    Chính là luật R4 của tools/chan_bia_so_lieu.py, nhưng hook đó là
    PostToolUse và chỉ bắt Write/Edit của Claude Code, nên sửa từ IDE hay
    tay người đều lọt. Khoá lại bằng test để CI bắt được.
    """
    src = open(os.path.join(ROOT, "run_daily.py"), encoding="utf-8").read()
    loi = []
    for node in ast.walk(ast.parse(src)):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and len(node.args) == 2):
            continue
        khoa, mac_dinh = node.args
        if (isinstance(khoa, ast.Constant) and isinstance(khoa.value, str)
                and "score" in khoa.value.lower()
                and isinstance(mac_dinh, ast.Constant)
                and isinstance(mac_dinh.value, (int, float))
                and not isinstance(mac_dinh.value, bool)):
            loi.append(f"dòng {node.lineno}: .get({khoa.value!r}, {mac_dinh.value!r})")

    assert not loi, (
        "run_daily.py đọc điểm với mặc định là MỘT CON SỐ — thiếu khoá thì "
        "báo cáo in số đó như kết quả phân tích: " + " · ".join(loi))
    print("PASS  run_daily.py không đọc điểm bằng mặc định số")



# Các con số bịa trong app.py, bê nguyên từ ui_prototype.html (mockup).
# Giá trị THẬT lấy từ paper_metrics.compute() trên paper_trades.db.
SO_CUNG_TRONG_APP = {
    "636.11":    "lợi nhuận 20-Loop — sổ thật: +14,24%",
    "1,787":     "tổng số lệnh — sổ thật: 113",
    "61.2":      "win rate — sổ thật: 25,0%",
    "1.43":      "profit factor — sổ thật: 1,3396",
    "19.4":      "max drawdown — sổ thật: 9,91%",
    "7.361":     "giá trị tài khoản — không tồn tại trong DB",
    "2330649":   "PnL VNĐ của vị thế ACB dựng sẵn",
    "2,330,649": "PnL VNĐ của vị thế ACB dựng sẵn",
    "1,245.80":  "VN-Index — số cứng, không đọc từ nguồn nào",
    "22750":     "giá mặc định khi thiếu entry_price",
    "30_000_000": "vốn mỗi vị thế — bịa, dùng để tính PnL VNĐ",
    "2026-05-29": "ngày vào lệnh mặc định",
    "21,110":    "giá vào của vị thế ACB dựng sẵn",
    "21,158":    "stop-loss của vị thế ACB dựng sẵn",
    "26,052":    "take-profit của vị thế ACB dựng sẵn",
    "default_pnl": "nhánh dựng hàng ACB giả khi không đọc được sổ",
    # Thẻ "Trạng thái hệ thống AI" ở sidebar — không audit nào bắt được,
    # smoke test bằng trình duyệt mới lộ ra.
    "39 Mẫu": "số mẫu hình post-mortem — file thật có 6.327, lệch 162 lần",
    "12ms":   "độ trễ Technical Agent — không đo từ đâu",
    "Q2/2026": "kỳ báo cáo Fundamental Agent — dán cứng",
    "3 Vòng": "số vòng tranh luận — dán cứng",
    "Pha Wyckoff": "nhãn cho 4 khoảng điểm — không có phân tích Wyckoff nào",
    # Ba lời khẳng định TRẠNG THÁI mà không chỗ nào kiểm. Cùng họ với
    # market_filter.status() báo active=True trong khi cổng đóng cứng:
    # một đường sao lưu hỏng âm thầm còn tệ hơn không có đường nào.
    # Lộ ra khi smoke test app với paper_trades.db bị đổi tên — không có
    # sổ, không có kiểm tra nào, pill vẫn nói "Synced".
    "Sheets Synced": "pill topbar — chưa bao giờ gọi sheets_store.trang_thai()",
    "LIVE DATA": "thẻ TradingView MCP ở tab Pipeline — không đo từ đâu",
    "LIVE SYNC": "thẻ Google Sheets ở tab Pipeline — không đo từ đâu",
    # Topbar in ngưỡng mua bằng hằng số, trong khi thanh trượt ở sidebar
    # mới là thứ quyết định. Kéo trượt sang 65 thì topbar vẫn nói 50.
    "50.0 pts": "ngưỡng mua ở topbar — không bám theo thanh trượt",
}


def test_run_daily_khong_chep_cung_nguong_mua():
    """Ngưỡng mua chỉ được viết MỘT lần, ở dòng khai báo BUY_THRESHOLD.

    run_daily.py có BUY_THRESHOLD, và cùng một báo cáo đã in
    `{BUY_THRESHOLD:.1f}` ở dòng tiêu đề. Nhưng bộ lọc chọn TOP và hai
    nhãn "Score >= 50.0" lại chép cứng con số. Hôm nay hai giá trị bằng
    nhau nên không ai thấy; đổi ngưỡng một cái là báo cáo tự mâu thuẫn:
    tiêu đề nói ngưỡng mới, mục 2 vẫn nói 50.0, và bộ lọc vẫn lọc theo 50.0.

    Đây là ô C5 của kế hoạch. Ngày nó được trả lời, chỗ chép cứng này sẽ
    im lặng giữ nguyên hành vi cũ.

    Test đọc giá trị từ chính dòng khai báo nên không hỏng khi C5 đổi số.
    """
    import ast
    import io
    import tokenize

    duong_dan = os.path.join(ROOT, "run_daily.py")
    nguon = open(duong_dan, encoding="utf-8").read()

    gia_tri = None
    for nut in ast.parse(nguon).body:
        if isinstance(nut, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "BUY_THRESHOLD"
                for t in nut.targets):
            gia_tri = nut.value.value
    assert gia_tri is not None, "khong tim thay khai bao BUY_THRESHOLD"

    # Bỏ chú thích: ghi lại con số cũ trong comment để giải thích là việc
    # nên làm, không phải vi phạm.
    with open(duong_dan, "rb") as fh:
        toks = list(tokenize.tokenize(fh.readline))
    khong_chu_thich = "".join(
        t.string for t in toks if t.type != tokenize.COMMENT)

    dang_chu = str(gia_tri)
    so_lan = khong_chu_thich.count(dang_chu)
    assert so_lan == 1, (
        f"run_daily.py viet '{dang_chu}' {so_lan} lan; chi duoc 1 lan o dong "
        f"khai bao BUY_THRESHOLD. Moi ban chep them la mot cho se khong doi "
        f"theo khi C5 duoc tra loi.")
    print("PASS  nguong mua chi viet mot lan trong run_daily.py")


def test_app_khong_hien_so_cung_tu_mockup():
    """app.py không được hiển thị con số nào không đọc từ sổ lệnh.

    Bối cảnh: hai commit UI ngày 18/08 (`65f819d`, `8b0ebf2`) chép số từ
    `ui_prototype.html` vào `app.py` và xoá cùng lúc tích hợp `sheets_store`,
    nút khôi phục sổ từ Sheets, và cảnh báo đòn bẩy khi vốn vượt 100%.
    Kết quả: `grep -c "sheets_store\\|paper_metrics" app.py` = 0 — không một
    con số nào trên giao diện đi qua compute().

    Nặng nhất là +636,11%: chính con số mà NGUYEN-TAC-DO-LUONG.md đã kết
    luận là đòn bẩy 2,2× (quy về 100% vốn còn +155,66%), đang là ô số liệu
    lớn nhất trên màn hình.

    Riêng `default_pnl`: trên Streamlit Cloud `.gitignore` chặn `*.db` nên
    `paper_trades.db` KHÔNG tồn tại — nhánh dựng hàng ACB giả là nhánh LUÔN
    chạy, không phải nhánh dự phòng.
    """
    # Bỏ chú thích trước khi quét: ghi lại con số CŨ trong comment để giải
    # thích vì sao nó sai là việc nên làm, không phải vi phạm. Test này hỏi
    # "app HIỂN THỊ gì", không hỏi "app nhắc tới gì".
    import io
    import tokenize
    with open(os.path.join(ROOT, "app.py"), "rb") as fh:
        toks = list(tokenize.tokenize(fh.readline))
    src = "".join(t.string for t in toks if t.type != tokenize.COMMENT)

    loi = [f"{k!r} — {vi_sao}" for k, vi_sao in SO_CUNG_TRONG_APP.items()
           if k in src]
    assert not loi, (
        f"app.py còn {len(loi)} con số bịa trên mặt người đọc:\n  "
        + "\n  ".join(loi))
    print("PASS  app.py không còn số cứng từ mockup")


def test_app_doc_so_lenh_qua_paper_metrics():
    """Số liệu hiệu quả trên app phải đi qua `paper_metrics`, không tự tính.

    Cộng dồn phần trăm từng lệnh không phải một tỷ suất lợi nhuận — nó bỏ
    qua tỷ trọng vốn (bất biến 4) và lệnh chồng lấn (bất biến 7b). Chỉ
    `paper_metrics.compute()` mới trả về `peak_capital_deployed_pct` để
    biết con số đang đứng trên đòn bẩy bao nhiêu.
    """
    src = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
    assert "paper_metrics" in src, (
        "app.py không import paper_metrics — mọi số hiệu quả trên giao diện "
        "đều nằm ngoài mọi bất biến đo lường của dự án")
    print("PASS  app.py đọc số hiệu quả qua paper_metrics")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n===== {len(fns) - failed}/{len(fns)} test PASS =====")
    sys.exit(1 if failed else 0)
