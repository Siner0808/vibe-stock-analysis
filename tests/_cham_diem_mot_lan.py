"""Chấm điểm MỘT gói dữ liệu cố định, in ra JSON. Không phải test.

Tồn tại để `test_post_mortem.py` gọi được nó như một TIẾN TRÌNH RIÊNG.
Bất biến 2 nói về trạng thái trên ĐĨA, mà trạng thái trên đĩa thì không
quan sát được từ trong cùng một tiến trình: `_ENGINE_CACHE` ở mức module
giữ nguyên bộ nhớ đã nạp, nên chấm lại lần hai trong cùng tiến trình sẽ
cho cùng điểm dù file trên đĩa đã đổi.

`post_mortem_learning.MEMORY_FILE` là đường dẫn TƯƠNG ĐỐI, nên thư mục
làm việc của tiến trình quyết định đọc bộ nhớ nào. Người gọi đặt cwd.
"""
import json

import numpy as np
import pandas as pd

from data_collectors import MarketDataPacket
from master_agent import MasterConsensusAgent


def goi_du_lieu():
    n = 140
    close = 50_000 * np.power(1.002, np.arange(n))
    return pd.DataFrame({
        "time": pd.bdate_range("2026-01-01", periods=n).strftime("%Y-%m-%d"),
        "open": close * 0.998, "high": close * 1.006,
        "low": close * 0.994, "close": close,
        "volume": np.full(n, 2_000_000)})


if __name__ == "__main__":
    import os
    from post_mortem_learning import get_learning_engine

    may = get_learning_engine()
    p = MarketDataPacket(symbol="TST", exchange="HOSE", ohlcv_df=goi_du_lieu())
    kq = MasterConsensusAgent().run(p)
    print(json.dumps({
        "final_score": kq["final_score"],
        "post_mortem_bat": bool(may.enabled),
        "so_mau_doc_duoc": len(may.sl_patterns),
        "thu_muc": os.getcwd(),
    }))
