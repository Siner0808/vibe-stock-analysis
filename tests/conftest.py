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
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
