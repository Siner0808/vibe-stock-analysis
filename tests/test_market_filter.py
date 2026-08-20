"""Cổng VN-INDEX phải LỘ RA khi nó tự tắt — ô C1.

Sự cố thật, đo ngày 20/08/2026 bằng cách chạy hàm:

    market_filter.status()        = {'active': True, ... → 2026-08-07}
    is_vni_bullish('2026-08-20')  = False
    is_vni_bullish('2030-01-01')  = False

Cache dừng ở 07/08 (close 1768,06 · MA50 1799,29). `is_vni_bullish` lấy
`sub.iloc[-1]` nên với MỌI ngày sau 07/08 nó đọc đúng dòng 07/08 và trả
False vĩnh viễn — trong khi cờ `active` báo XANH vì df nạp được.

14 ngày, 0 lệnh, không ai biết. Chỗ nguy hiểm không phải *mất* dữ liệu:
mất thì fail-open còn nhìn thấy được. Nguy hiểm là **dữ liệu cũ trông
giống dữ liệu mới** — nó fail-closed âm thầm, đúng chiều tệ nhất.

Ô C1 đã chọn: quá hạn ⇒ DỪNG PHIÊN QUÉT, ngưỡng 3 phiên.

Độ cũ đo so với `signal_date` ĐANG CHẤM, không so với hôm nay — nếu không
backtest năm 2024 sẽ nổ oan trên cache chạy tới 2026.
"""
import contextlib
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))

import numpy as np
import pandas as pd

# Nạp một BẢN SAO RIÊNG của market_filter thay vì dùng module dùng chung.
#
# `tests/test_paper_trading.py` ghim `market_filter.is_vni_bullish` thành
# `lambda _: True` ở mức module — hợp lý cho file đó (nó kiểm sổ lệnh, không
# kiểm bộ lọc), nhưng lời ghim đó sống suốt tiến trình. File này kiểm CHÍNH
# bộ lọc, nên nếu dùng module dùng chung thì nó đo cái lambda chứ không đo
# mã thật, và kết quả đổi theo THỨ TỰ chạy — đúng loại ô nhiễm đã làm một
# test đỏ khi chạy cả bộ mà xanh khi chạy riêng.
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("market_filter_ban_sao", GOC / "market_filter.py")
mf = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(mf)


def _cache_gia(ngay_cuoi: str, n: int = 120, tren_ma: bool = True):
    """Chuỗi VN-INDEX kết thúc ở `ngay_cuoi`, nằm trên hoặc dưới MA50."""
    ngay = pd.bdate_range(end=ngay_cuoi, periods=n).strftime("%Y-%m-%d")
    if tren_ma:
        close = 1000 * np.power(1.002, np.arange(n))      # tăng dần -> trên MA
    else:
        close = 1000 * np.power(0.998, np.arange(n))      # giảm dần -> dưới MA
    return pd.DataFrame({"time": ngay, "close": close})


@contextlib.contextmanager
def _ghim(df):
    """Ghim dữ liệu cho bộ lọc, bỏ qua cache thật trên đĩa.

    Là context manager chứ không phải hàm thường: `mf._btd` là module
    `backtest.data` DÙNG CHUNG cả dự án. Vá nó rồi không trả lại thì mọi
    test chạy sau trong cùng tiến trình đều đọc dữ liệu giả — đúng loại ô
    nhiễm đã làm một test đỏ khi chạy cả bộ mà xanh khi chạy riêng.

    Cũng ghim `fetch_one` để bộ test không đi mạng: runner CI chạy offline.
    """
    goc_load, goc_fetch = mf._btd.load, mf._btd.fetch_one
    mf.get_vni_df.cache_clear()
    mf._btd.load = lambda _ma: df
    mf._btd.fetch_one = lambda *a, **k: None
    try:
        yield
    finally:
        mf._btd.load, mf._btd.fetch_one = goc_load, goc_fetch
        mf.get_vni_df.cache_clear()


def test_cache_qua_han_thi_status_bao_KHONG_hoat_dong():
    with _ghim(_cache_gia("2026-07-01")):
        st = mf.status(hom_nay="2026-08-20")
        assert st["active"] is False, f"cache cũ 7 tuần mà vẫn báo active: {st}"
        assert st.get("tuoi_phien", 0) > 3, f"không báo tuổi dữ liệu: {st}"
        print(f"PASS  cache cũ -> active=False, tuổi {st['tuoi_phien']} phiên")


def test_cache_qua_han_thi_is_vni_bullish_NO_chu_khong_tra_False():
    """Trả False lặng lẽ là chặn hết mà không ai biết — đúng lỗi 14 ngày."""
    with _ghim(_cache_gia("2026-07-01")):
        try:
            mf.is_vni_bullish("2026-08-20")
        except mf.CacheQuaHanError as e:
            assert "2026-07-01" in str(e), f"lỗi không nói dữ liệu tới ngày nào: {e}"
            print("PASS  cache quá hạn -> NỔ, không trả False lặng lẽ")
            return
        raise AssertionError("cache cũ 7 tuần mà vẫn trả về một phán quyết")


def test_cache_tuoi_trong_nguong_thi_chay_binh_thuong():
    with _ghim(_cache_gia("2026-08-18")):
        assert mf.is_vni_bullish("2026-08-20") is True
        assert mf.status(hom_nay="2026-08-20")["active"] is True
        print("PASS  lệch 2 phiên -> vẫn chạy, vẫn active")


def test_backtest_ngay_cu_KHONG_bi_no_oan():
    """Cache chạy tới 2026 mà chấm phiên 2024 thì KHÔNG hề quá hạn."""
    with _ghim(_cache_gia("2026-08-18", n=700)):
        assert mf.is_vni_bullish("2024-03-01") in (True, False)
        print("PASS  chấm ngày trong vùng dữ liệu -> không nổ")


def test_cache_giam_gia_van_tra_False_binh_thuong():
    """Quá hạn khác với xu hướng giảm. Giảm thật thì vẫn phải chặn được."""
    with _ghim(_cache_gia("2026-08-18", tren_ma=False)):
        assert mf.is_vni_bullish("2026-08-19") is False
        print("PASS  VN-INDEX dưới MA50 -> chặn, đúng chức năng")


def test_khong_co_du_lieu_thi_van_fail_open_nhung_LO_RA():
    """Mất dữ liệu thì cho qua — nhưng status phải nói ra."""
    with _ghim(None):
        assert mf.is_vni_bullish("2026-08-20") is True
        st = mf.status(hom_nay="2026-08-20")
        assert st["active"] is False and "KHÔNG" in st["note"].upper()
        print("PASS  mất dữ liệu -> fail-open, nhưng status báo TẮT")


if __name__ == "__main__":
    for f in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        f()
