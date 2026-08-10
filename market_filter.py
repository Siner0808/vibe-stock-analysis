"""
market_filter.py
──────────────────────────────────────────────────────────────────────
Bộ lọc xu hướng thị trường chung: VN-INDEX dưới MA50 thì không mở lệnh mới.

BẢN TRƯỚC HỎNG ÂM THẦM
Không có cache VNINDEX thì `get_vni_df()` gọi thẳng ra mạng; hỏng mạng thì
trả None, và `is_vni_bullish()` trả True cho mọi ngày. Tức là bộ lọc TẮT
hoàn toàn mà không ai biết — mọi báo cáo vẫn ghi "đã lọc theo xu hướng thị
trường" trong khi thực tế không lọc gì.

Ba thay đổi:
  • Tải được thì GHI RA CACHE, để lần sau không phụ thuộc mạng nữa.
  • `status()` cho biết bộ lọc đang bật hay tắt, để báo cáo nói đúng sự thật.
  • Không còn ngày kết thúc cứng trong code (bản trước ghi "2026-08-06",
    sẽ cũ dần rồi lọc sai mà không báo).

Vẫn giữ nguyên tắc hỏng-thì-cho-qua: bộ lọc này chỉ CHẶN lệnh, nên khi
không có dữ liệu, cho qua là lựa chọn ít gây hại hơn. Nhưng nó phải LỘ RA.
"""
from __future__ import annotations

import functools
from datetime import date

import pandas as pd

from backtest import data as _btd

MA_WINDOW = 50
_STATUS = {"active": False, "note": "chưa nạp", "rows": 0}


@functools.lru_cache(maxsize=1)
def get_vni_df():
    """Nạp VN-INDEX kèm MA50. Tải từ mạng đúng một lần rồi ghi ra cache."""
    global _STATUS
    try:
        df = _btd.load("VNINDEX")
        source = "cache"

        if df is None or df.empty:
            df = _btd.fetch_one("VNINDEX", "2020-01-01", date.today().isoformat())
            source = "mạng"
            if df is not None and not df.empty:
                try:
                    _btd.CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    df.to_csv(_btd.cache_path("VNINDEX"), index=False)
                    source = "mạng (đã ghi cache)"
                except Exception:
                    pass

        if df is None or df.empty:
            _STATUS = {"active": False, "rows": 0,
                       "note": "KHÔNG có dữ liệu VN-INDEX — bộ lọc TẮT, "
                               "mọi lệnh đều qua được"}
            return None

        df = df.copy()
        df["time"] = df["time"].astype(str)
        df = df.sort_values("time").reset_index(drop=True)
        df["vni_ma50"] = df["close"].rolling(MA_WINDOW).mean()
        _STATUS = {"active": True, "rows": len(df),
                   "note": f"VN-INDEX {df['time'].iloc[0]} → {df['time'].iloc[-1]} "
                           f"({len(df)} phiên, nguồn: {source})"}
        return df
    except Exception as e:
        _STATUS = {"active": False, "rows": 0,
                   "note": f"lỗi nạp VN-INDEX ({type(e).__name__}) — bộ lọc TẮT"}
        return None


def status() -> dict:
    """Bộ lọc có thật sự đang hoạt động không.

    Báo cáo nào nói "đã lọc theo xu hướng thị trường" đều phải gọi hàm này
    trước, nếu không nó đang khẳng định một điều có thể không đúng.
    """
    get_vni_df()
    return dict(_STATUS)


def is_vni_bullish(signal_date: str) -> bool:
    """VN-INDEX tại `signal_date` có nằm trên MA50 không.

    Chỉ dùng dữ liệu tới hết `signal_date` — không nhìn trộm phiên sau.
    """
    vni_df = get_vni_df()
    if vni_df is None or vni_df.empty:
        return True

    sub = vni_df[vni_df["time"] <= signal_date]
    if sub.empty:
        return True

    latest = sub.iloc[-1]
    if pd.notna(latest.get("vni_ma50")):
        return float(latest["close"]) >= float(latest["vni_ma50"])
    return True
