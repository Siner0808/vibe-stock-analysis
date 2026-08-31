"""
TẦNG 0: DATA QUALITY GATE
- Lọc nến chưa chốt (intraday incomplete candles)
- Chuẩn hóa Daily + Weekly OHLCV
- Kiểm tra tính liên tục dữ liệu (fill gaps)
"""
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from vnstock import Quote

# Base directory = thư mục cha của v3_pipeline/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist_71.json")
CACHE_DIR = os.path.join(BASE_DIR, "data_cache")
WEEKLY_CACHE_DIR = os.path.join(BASE_DIR, "data_cache_weekly")


def load_watchlist():
    with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    symbols = []
    for sector_name, tickers in data.items():
        symbols.extend(tickers)
    return list(set(symbols))


import time

def fetch_daily(symbol: str, months: int = 18) -> pd.DataFrame:
    """Ưu tiên cache local, chỉ fetch khi cần refresh, có chống nghẽn rate limit."""
    cache_path = os.path.join(CACHE_DIR, f"{symbol}.csv")
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    today = datetime.now().date()
    now = datetime.now()
    df_cache = None
    
    if os.path.exists(cache_path):
        try:
            df_cache = pd.read_csv(cache_path, parse_dates=["time"])
            if not df_cache.empty:
                last_date = df_cache["time"].max().date()
                file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
                hours_since_update = (now - file_mtime).total_seconds() / 3600.0
                
                # 1. Nếu file vừa update trong vòng 20h -> Dùng luôn
                if hours_since_update < 20:
                    return df_cache
                
                # 2. Nếu nến cuối cùng là phiên giao dịch gần nhất (kể cả qua cuối tuần <= 4 ngày) và phiên hôm nay chưa chốt (< 15:15) -> Dùng cache
                max_lag = 4 if today.weekday() == 0 else 2
                if (today - last_date).days <= max_lag and (now.hour < 15 or (now.hour == 15 and now.minute < 15)):
                    return df_cache
        except Exception:
            df_cache = None

    # Cần fetch từ API
    start = (today - timedelta(days=months * 30)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    
    for attempt in range(3):
        try:
            time.sleep(1.05)  # Tốc độ an toàn tuyệt đối (< 60 req / phút)
            q = Quote(symbol=symbol, source="VCI")
            df = q.history(start=start, end=end)
            if df is not None and not df.empty:
                df["time"] = pd.to_datetime(df["time"])
                df.to_csv(cache_path, index=False)
                return df
            break
        except Exception as e:
            err_msg = str(e).lower()
            if "rate limit" in err_msg or "too many" in err_msg or "429" in err_msg:
                print(f"  ⏳ Chạm giới hạn API tại {symbol}, chờ 20s để hồi phục...")
                time.sleep(20)
            else:
                print(f"  ⚠️ Lỗi fetch {symbol} (thử {attempt+1}): {e}")
                time.sleep(2)
    
    # Nếu fetch thất bại nhưng có cache cũ -> Dùng cache cũ dự phòng
    if df_cache is not None and not df_cache.empty:
        return df_cache
        
    return pd.DataFrame()


def build_weekly(df_daily: pd.DataFrame) -> pd.DataFrame:
    """Chuyển đổi Daily → Weekly OHLCV."""
    if df_daily.empty:
        return pd.DataFrame()
    df = df_daily.copy()
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time")
    weekly = df.resample("W-FRI").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }).dropna()
    weekly = weekly.reset_index()
    return weekly


def validate_quality(df: pd.DataFrame, symbol: str) -> dict:
    """Kiểm tra chất lượng dữ liệu và phát hiện dữ liệu xấu."""
    if df.empty:
        return {"symbol": symbol, "passed": False, "reason": "No data"}
    
    issues = []
    today = datetime.now().date()
    
    # 1. Kiểm tra nến gần nhất (không quá 3 ngày cũ)
    last_date = pd.to_datetime(df["time"].max()).date()
    lag_days = (today - last_date).days
    if lag_days > 5:  # Cho phép nghỉ lễ
        issues.append(f"Data lag {lag_days} days")
    
    # 2. Loại bỏ nến intraday chưa chốt (giờ chạy < 15:15)
    now = datetime.now()
    if now.hour < 15 or (now.hour == 15 and now.minute < 15):
        # Xóa nến hôm nay nếu chưa chốt phiên
        df = df[pd.to_datetime(df["time"]).dt.date < today]
    
    # 3. Kiểm tra độ liên tục (không quá nhiều gaps)
    df_sorted = df.sort_values("time")
    date_diffs = pd.to_datetime(df_sorted["time"]).diff().dt.days.dropna()
    long_gaps = (date_diffs > 5).sum()
    if long_gaps > 10:
        issues.append(f"Too many gaps: {long_gaps}")
    
    # 4. Chuẩn hóa giá × 1000 nếu cần (vnstock trả về đơn vị nghìn đồng)
    if df["close"].mean() < 100:
        df["open"] *= 1000
        df["high"] *= 1000
        df["low"] *= 1000
        df["close"] *= 1000
    
    passed = len(issues) == 0
    return {
        "symbol": symbol,
        "passed": passed,
        "df_clean": df,
        "issues": issues,
        "rows": len(df),
        "last_date": str(last_date),
        "lag_days": lag_days
    }


def run_quality_gate(symbols: list) -> dict:
    """Chạy Data Quality Gate cho toàn bộ danh sách mã."""
    print(f"\n{'='*60}")
    print(f"🛡️ TẦNG 0: DATA QUALITY GATE ({len(symbols)} mã)")
    print(f"{'='*60}")
    
    results = {}
    passed = 0
    failed = 0
    
    for i, sym in enumerate(symbols, 1):
        df_daily = fetch_daily(sym)
        quality = validate_quality(df_daily, sym)
        df_weekly = build_weekly(quality.get("df_clean", pd.DataFrame()))
        
        quality["df_daily"] = quality.pop("df_clean", pd.DataFrame())
        quality["df_weekly"] = df_weekly
        results[sym] = quality
        
        status = "✅" if quality["passed"] else "❌"
        issues_str = ", ".join(quality.get("issues", [])) or "OK"
        print(f"  {status} [{i:02d}/{len(symbols)}] {sym:6s} | {quality.get('rows',0)} nến | {issues_str}")
        
        if quality["passed"]:
            passed += 1
        else:
            failed += 1
    
    print(f"\n  ✅ Qua cổng: {passed} | ❌ Loại: {failed}")
    return results


if __name__ == "__main__":
    symbols = load_watchlist()
    results = run_quality_gate(symbols)
    passed_symbols = [s for s, r in results.items() if r["passed"]]
    print(f"\nKết quả: {len(passed_symbols)} mã sạch sẵn sàng cho phân tích")
