"""bo_nho_do_app.py — bộ nhớ cho phép đo nặng mà APP vẽ lại ở MỖI lượt chạy (BƯỚC 275, lát 3).

`paper_metrics.expectancy_significant` bootstrap 5.000 lượt × (số lệnh đóng) lần rút, chạy lại mỗi
lần người dùng bấm gì đó dù sổ lệnh không đổi (đo 13/11/2026: phần lớn một lượt vẽ lại ~1 giây ở
máy). Hàm ấy chỉ đọc `_returns(trades)`, `iters` và `seed`, mà `random.Random(seed)` cho cùng một
chuỗi rút khi cùng đầu vào — nên kết quả là hàm THUẦN của bộ ba đó. Bộ nhớ ở đây khoá theo NỘI DUNG
(chuỗi lợi nhuận từng lệnh đóng), không theo danh tính đối tượng: sổ đổi một lệnh là tính lại.

Chỉ APP nhập module này (gác AST ở `tests/test_bo_nho_do_app_275.py`): đường quét, backtest và
điều kiện dừng vẫn gọi thẳng `paper_metrics`, không qua bộ nhớ.
"""
from __future__ import annotations

import copy
import threading
from collections import OrderedDict

import paper_metrics

TOI_DA_MUC = 8
_BO_NHO: "OrderedDict[tuple, dict]" = OrderedDict()
_KHOA = threading.Lock()
SO_LAN_TINH = 0     # đo/kiểm: số lần thật sự bootstrap


def xoa() -> None:
    with _KHOA:
        _BO_NHO.clear()


def expectancy_significant_nho(trades, iters: int = 5000, seed: int = 0) -> dict:
    """Y hệt `paper_metrics.expectancy_significant(trades, iters, seed)`, nhớ theo nội dung sổ."""
    global SO_LAN_TINH
    khoa = (tuple(paper_metrics._returns(trades)), iters, seed)
    with _KHOA:
        if khoa in _BO_NHO:
            _BO_NHO.move_to_end(khoa)
            return copy.deepcopy(_BO_NHO[khoa])
        kq = paper_metrics.expectancy_significant(trades, iters, seed)
        SO_LAN_TINH += 1
        _BO_NHO[khoa] = copy.deepcopy(kq)
        while len(_BO_NHO) > TOI_DA_MUC:
            _BO_NHO.popitem(last=False)
        return kq
