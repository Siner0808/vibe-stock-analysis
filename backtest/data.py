"""Tải và cache dữ liệu OHLCV lịch sử để backtest chạy lặp lại được.

Nguyên tắc: tải MỘT LẦN xuống đĩa, mọi lần backtest sau đọc từ cache.
Backtest phải tất định — cùng dữ liệu vào, cùng kết quả ra.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).parent / "cache"

# Ảnh chụp rổ VN30 (cập nhật 08/2026). Rổ VN30 được HOSE cơ cấu định kỳ,
# nên đây là danh sách tham chiếu — dùng --symbols để chỉ định rổ khác.
#
# CẢNH BÁO SURVIVORSHIP BIAS: backtest trên rổ VN30 HIỆN TẠI sẽ cho kết quả
# lạc quan hơn thực tế, vì các mã bị loại khỏi rổ (thường do kém) không có
# mặt. Đây là hạn chế đã biết, xem README.md.
VN30_SNAPSHOT = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
]


def cache_path(symbol: str) -> Path:
    return CACHE_DIR / f"{symbol.upper()}.csv"


def fetch_one(symbol: str, start: str, end: str, pause: float = 0.4) -> pd.DataFrame | None:
    """Tải OHLCV từ vnstock. Trả None nếu không lấy được (KHÔNG sinh dữ liệu giả)."""
    from vnstock import Quote

    for src in ("vci", "kbs"):
        try:
            df = Quote(symbol=symbol, source=src).history(start=start, end=end)
            if df is not None and not df.empty:
                time.sleep(pause)          # lịch sự với API
                return df
        except Exception:
            continue
    return None


def download(symbols: list[str], start: str, end: str,
             force: bool = False) -> dict[str, int]:
    """Tải và ghi cache. Trả về {symbol: số phiên}. Bỏ qua mã đã có cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    result: dict[str, int] = {}
    for i, sym in enumerate(symbols, 1):
        path = cache_path(sym)
        if path.exists() and not force:
            result[sym] = len(pd.read_csv(path))
            print(f"[{i}/{len(symbols)}] {sym}: đã có cache ({result[sym]} phiên)")
            continue
        df = fetch_one(sym, start, end)
        if df is None or df.empty:
            print(f"[{i}/{len(symbols)}] {sym}: ❌ không tải được — BỎ QUA")
            continue
        df.to_csv(path, index=False)
        result[sym] = len(df)
        print(f"[{i}/{len(symbols)}] {sym}: ✅ {len(df)} phiên")
    return result


def load(symbol: str) -> pd.DataFrame | None:
    """Đọc từ cache, chuẩn hoá cột và sắp xếp theo thời gian tăng dần."""
    path = cache_path(symbol)
    if not path.exists():
        return None
    df = pd.read_csv(path)
    required = {"time", "open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        return None
    df = df.sort_values("time").reset_index(drop=True)
    return df


def load_all(symbols: list[str] | None = None) -> dict[str, pd.DataFrame]:
    symbols = symbols or VN30_SNAPSHOT
    out = {}
    for sym in symbols:
        df = load(sym)
        if df is not None and len(df) > 0:
            out[sym] = df
    return out
