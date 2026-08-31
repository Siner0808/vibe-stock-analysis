"""
top_stocks_screener.py
──────────────────────────────────────────────────────────────────────
Top 5 Stock Investment Screener Engine
Scans top Vietnamese market stocks in parallel through the 5-Layer
Multi-Agent Analysis Pipeline to discover the Top 5 Investment Picks.
──────────────────────────────────────────────────────────────────────
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import pandas as pd
from master_agent import run_full_analysis

# Default Stock Universe (VN30 & High Liquidity Bluechips)
DEFAULT_UNIVERSE = [
    "FPT", "HPG", "VHM", "VNM", "TCB", 
    "MBB", "MWG", "SSI", "VCB", "DGC", 
    "VCI", "ACB", "STB", "REE", "VRE"
]

def analyze_single_ticker(ticker: str, start_str: str, end_str: str) -> dict | None:
    try:
        # Pass collect_news=False for fast lightweight batch scanning (~0.2s per ticker)
        res = run_full_analysis(ticker, start_str, end_str, exchange="HOSE", collect_news=False)
        if res.get("data_quality") != "FAILED":
            return res
    except Exception as e:
        print(f"Error scanning ticker {ticker}: {e}")
    return None

def get_top_5_stocks(universe: list[str] = None, max_workers: int = 4) -> list[dict]:
    """
    Scans a universe of tickers in parallel and returns the Top 5 stocks
    sorted by their final multi-agent consensus score.
    """
    if not universe:
        universe = DEFAULT_UNIVERSE

    from data_quality import now_vn
    end_date = now_vn()
    start_date = end_date - timedelta(days=200)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_single_ticker, ticker, start_str, end_str): ticker for ticker in universe}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    # Sort descending by final_score
    results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    
    # Return top 5
    return results[:5]
