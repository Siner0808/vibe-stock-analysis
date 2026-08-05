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
    assert o["high_52w"] == max(close) * 1.01
    assert o["avg_vol_10d"] == 1_000_000
    assert o["pct_1w"] > 0 and o["pct_1y"] > 0
    # nhưng chỉ số định giá vẫn phải là None
    assert o["pe"] is None and o["market_cap_billions"] is None
    print(f"PASS  giá thật vẫn tính được (52T cao {o['high_52w']:,.0f}), "
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


def test_app_khong_ve_du_lieu_synthetic():
    """app.py phải kiểm tra status trước khi vẽ, không chỉ lấy df."""
    src = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
    assert "_price_status" in src, "app.py không kiểm tra status của nguồn giá"
    assert 'res.get("status"' in src, "load_stock_data vẫn bỏ qua status"
    print("PASS  app.py chặn dữ liệu SYNTHETIC trước khi vẽ")


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
