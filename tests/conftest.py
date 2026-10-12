"""Trả lại các biến toàn cục bị test vá, sau MỖI test.

VÌ SAO CÓ FILE NÀY
──────────────────
`tests/test_paper_trading.py` thay `paper_runner._analyze` bằng một hàm giả
ở bốn chỗ và không chỗ nào trả lại. Sau khi file đó chạy xong, MỌI file test
chạy sau nó đều nhận một hàm chấm điểm giả cho tới hết phiên pytest.

Hậu quả nặng hơn một test đỏ. Test đỏ thì biết ngay — đúng cách chuyện này
bị phát hiện ngày 21/08/2026, khi `tests/test_walkforward.py` gọi
`_mo_phong()` và nhận `KeyError: 'AAA'` vì hàm giả chỉ biết hai mã "AA" và
"BB". Nhưng một test khác hoàn toàn có thể XANH bằng điểm giả, và khi đó nó
trông như đã kiểm pipeline thật trong khi không kiểm gì cả.

Đây là lần thứ hai dự án mất thời gian vì cùng một kiểu rò: lần trước là
`market_filter.is_vni_bullish` bị vá ở mức module.

PHẠM VI CÓ CHỦ Ý HẸP
────────────────────
Chỉ trả lại `paper_runner._analyze`. KHÔNG đụng tới:

  `paper_trading.CHO_PHEP_MO_LENH_MOI` và `market_filter.is_vni_bullish`
  — hai thứ này bị vá ở MỨC MODULE trong `tests/test_sheets_store.py`, tức
  chỉ chạy một lần lúc import. Trả lại chúng sau mỗi test sẽ làm chính file
  đó hỏng từ test thứ hai trở đi. Chúng cần dọn tại chỗ, không dọn ở đây.

Thà sửa hẹp và đúng còn hơn sửa rộng và làm hỏng thứ khác.

GÁC THỨ HAI: KHÔNG TEST NÀO ĐƯỢC ĐỌC/GHI VN-INDEX THẬT (BƯỚC 184)
────────────────────────────────────────────────────────────────
Phần vá mức module ở trên có một hệ quả ngược: chạy CẢ BỘ thì
`tests/test_sheets_store.py` phủ `is_vni_bullish = True` lên mọi file chạy
sau nó, nên không test nào chạm VN-INDEX thật. Chạy RIÊNG TỪNG FILE (cổng 4,
cả trên CI) thì phần vá ấy không tồn tại, và hai test
(`test_chuong_bai_hoc` · `test_walkforward`) gọi `market_filter.get_vni_df()`
THẬT: máy có cache thì kết quả phụ thuộc dữ liệu ở máy; CI (cache rỗng) thì
tải mạng rồi GHI `backtest/cache/VNINDEX.csv`. Cùng một test, hai hành vi theo
CÁCH CHẠY.

Gác dưới đây KHÔNG trả lại phần vá mức module (xem trên). Nó chỉ canh MỘT
điều: trong lúc một test chạy, `market_filter.get_vni_df` THẬT bị gọi khi
`backtest.data.CACHE_DIR` vẫn là đường chưa ai vá ⇒ test ĐỎ, trước khi hàm
thật kịp chạm đĩa hay mạng. Test cố ý chạm hàm thật phải trỏ `CACHE_DIR` sang
`tmp_path` (như `test_noi_cache_an_toan.py`); test không cố ý thì vá
`is_vni_bullish` hoặc `get_vni_df`.

GIỚI HẠN: gác chỉ canh `market_filter.get_vni_df`. Một module giữ sẵn bản
tham chiếu (`from market_filter import get_vni_df`) đi vòng qua nó; hiện không
module nào của repo làm vậy (kiểm bằng `grep`, không bằng gác).
"""
import functools
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# nodeid -> thông điệp của lần gọi `get_vni_df` THẬT đầu tiên trong test ấy.
_VI_PHAM_VNINDEX: dict[str, str] = {}


def _cache_con_la_cua_repo(btd) -> bool:
    """`CACHE_DIR` đang trỏ vào đường chưa ai vá (mặc định, hoặc `VIBE_CACHE_DIR`)?

    So với đường TÍNH LẠI từ môi trường chứ không với giá trị `CACHE_DIR` lúc
    vào test: một file vá `CACHE_DIR` ở mức module sẽ làm giá trị lúc vào test
    đã là đường vá, và gác tự im.
    """
    mac_dinh = Path(os.environ.get("VIBE_CACHE_DIR", "") or btd._CACHE_MAC_DINH)
    return Path(btd.CACHE_DIR).resolve() == mac_dinh.resolve()


@pytest.fixture(autouse=True)
def gac_khong_doc_vnindex_that(request):
    """Bọc `market_filter.get_vni_df` suốt một test; gọi THẬT trên cache của repo thì ĐỎ."""
    import market_filter
    from backtest import data as btd

    goc = market_filter.get_vni_df
    ten = request.node.nodeid

    @functools.wraps(goc)
    def gac(*a, **k):
        if _cache_con_la_cua_repo(btd):
            thong_diep = (
                f"{ten} gọi market_filter.get_vni_df() THẬT trong khi "
                f"backtest.data.CACHE_DIR vẫn là đường của repo "
                f"({btd.CACHE_DIR}). Cache có sẵn thì kết quả phụ thuộc dữ "
                f"liệu ở máy; cache rỗng thì tải mạng rồi GHI VNINDEX.csv. "
                f"Sửa: monkeypatch.setattr(market_filter, 'is_vni_bullish', "
                f"lambda *a, **k: True) hoặc vá 'get_vni_df'; nếu cố ý chạm "
                f"hàm thật thì trỏ backtest.data.CACHE_DIR sang tmp_path.")
            _VI_PHAM_VNINDEX.setdefault(ten, thong_diep)
            raise AssertionError(thong_diep)
        return goc(*a, **k)

    # `functools.wraps` KHÔNG sao chép `cache_clear`/`cache_info` của lru_cache.
    # Hàm đã bị bọc bởi một lớp khác (ví dụ ống nghe đo đạc) có thể thiếu một trong
    # hai, nên chỉ chuyển cái đang có thay vì nổ ở MỌI test.
    for ten_thuoc_tinh in ("cache_clear", "cache_info"):
        if hasattr(goc, ten_thuoc_tinh):
            setattr(gac, ten_thuoc_tinh, getattr(goc, ten_thuoc_tinh))
    market_filter.get_vni_df = gac
    try:
        yield
    finally:
        if market_filter.get_vni_df is gac:
            market_filter.get_vni_df = goc


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    """Nếu code của test NUỐT lỗi của gác, test vẫn ĐỎ."""
    try:
        ket_qua = yield
    finally:
        thong_diep = _VI_PHAM_VNINDEX.pop(item.nodeid, None)
    if thong_diep:
        pytest.fail(thong_diep, pytrace=False)
    return ket_qua


@pytest.fixture(autouse=True)
def tra_lai_analyze():
    """Chụp `paper_runner._analyze` trước mỗi test, đặt lại sau."""
    import paper_runner

    goc = paper_runner._analyze
    try:
        yield
    finally:
        if paper_runner._analyze is not goc:
            paper_runner._analyze = goc
            # Điểm đã ghi nhớ được tính bằng hàm giả — bỏ đi cùng với nó.
            paper_runner._ANALYZE_CACHE.clear()
