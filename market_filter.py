"""
market_filter.py
──────────────────────────────────────────────────────────────────────
Bộ lọc Xu hướng Thị trường Chung (VN-INDEX Market Regime Filter).
Nếu VN-INDEX < MA50 (Downtrend/Điều chỉnh): Trả về False -> KHÔNG MUA (Cash is King).
"""
import functools
import pandas as pd
from backtest import data as _btd

@functools.lru_cache(maxsize=1)
def get_vni_df():
    try:
        df = _btd.load("VNINDEX")
        if df is None or df.empty:
            df = _btd.fetch_one("VNINDEX", "2024-01-01", "2026-08-06")
        if df is not None and not df.empty:
            df = df.copy()
            df['time'] = df['time'].astype(str)
            df['vni_ma50'] = df['close'].rolling(50).mean()
            return df
    except Exception as e:
        pass
    return None

def is_vni_bullish(signal_date: str) -> bool:
    """Kiểm tra VN-INDEX tại signal_date có nằm trên MA50 hay không."""
    vni_df = get_vni_df()
    if vni_df is None or vni_df.empty:
        return True  # Fallback nếu không có data
    
    sub = vni_df[vni_df['time'] <= signal_date]
    if sub.empty:
        return True
    
    latest = sub.iloc[-1]
    if pd.notna(latest.get('vni_ma50')):
        return float(latest['close']) >= float(latest['vni_ma50'])
    return True
