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

    # Nạp API key từ cấu hình NGOÀI mã nguồn (biến môi trường hoặc
    # .streamlit/secrets.toml). Idempotent, không in key ra đâu cả.
    try:
        from vnstock_auth import ensure_api_key
        ensure_api_key()
    except Exception:
        pass

    for src in ("kbs", "tcbs", "vci", "dnse"):
        try:
            df = Quote(symbol=symbol, source=src).history(start=start, end=end)
            if df is not None and not df.empty:
                time.sleep(1.0)          # lịch sự với API, tăng lên 1.0s để tránh block
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


#: Cache bắt đầu muộn hơn mốc yêu cầu tối đa ngần này ngày thì vẫn coi là đủ.
#: Đủ rộng để nuốt Tết Nguyên đán, quãng nghỉ dài nhất của thị trường VN.
SKIP_TOLERANCE_DAYS = 14


def _within_days(have_from: str, want_from: str, tol: int) -> bool:
    """`have_from` có sớm hơn, hoặc muộn hơn `want_from` không quá `tol` ngày?"""
    try:
        a = pd.Timestamp(have_from)
        b = pd.Timestamp(want_from)
    except Exception:
        return False
    return (a - b).days <= tol


def _norm_time(df: pd.DataFrame) -> pd.DataFrame:
    """Quy cột `time` về chuỗi YYYY-MM-DD.

    Cache trên đĩa là CSV nên `time` đọc ra là chuỗi; vnstock trả về
    Timestamp. Trộn hai loại trong cùng một cột làm mọi phép so sánh và sắp
    xếp ném TypeError. Chuẩn hoá ngay tại chỗ ghép là nơi duy nhất cần biết
    về khác biệt này.
    """
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"], errors="coerce").dt.strftime("%Y-%m-%d")
    return df.dropna(subset=["time"])


def extend_history(symbols: list[str], start: str, end: str,
                   pause: float = 0.4) -> dict[str, tuple[str, str, int]]:
    """Nối dài cache VỀ QUÁ KHỨ cho những mã chưa có đủ lịch sử.

    `download()` bỏ qua mọi mã đã có file cache. Hợp lý khi chỉ cần dữ liệu
    mới, nhưng nó khiến một mã tải lần đầu với 13 tháng sẽ MÃI MÃI chỉ có 13
    tháng. Đó là lý do rổ 50 mã hiện tại có 28 mã bắt đầu từ 2025-07 trong
    khi 13 mã khác có từ 2023-11 — và vì thế giai đoạn 2024 chỉ được đại diện
    bởi một nhóm nhỏ, làm mọi kết quả nghiêng về giai đoạn gần nhất.

    Hàm này tải lại trọn khoảng rồi HỢP NHẤT với cache cũ (giữ bản ghi cũ khi
    trùng ngày), nên chạy nhiều lần vẫn an toàn.

    Trả về {symbol: (ngày_đầu, ngày_cuối, số_phiên)} cho các mã có thay đổi.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    changed: dict[str, tuple[str, str, int]] = {}

    for i, sym in enumerate(symbols, 1):
        path = cache_path(sym)
        old = pd.read_csv(path) if path.exists() else None

        if old is not None and len(old) and "time" in old.columns:
            have_from = str(old["time"].min())[:10]
            # Dung sai vài ngày: mốc yêu cầu thường rơi vào ngày nghỉ hoặc
            # cuối tuần, nên phiên đầu tiên có thật luôn muộn hơn một chút.
            # So bằng dấu <= sẽ khiến những mã đó bị tải lại MỖI LẦN chạy.
            if _within_days(have_from, start, SKIP_TOLERANCE_DAYS):
                print(f"[{i}/{len(symbols)}] {sym}: đã có từ {have_from} — bỏ qua")
                continue
        else:
            have_from = None

        fresh = fetch_one(sym, start, end, pause=pause)
        if fresh is None or fresh.empty:
            print(f"[{i}/{len(symbols)}] {sym}: ❌ không tải được — giữ nguyên cache")
            continue

        # Cache đọc từ CSV có `time` là CHUỖI, vnstock trả về Timestamp. Nối
        # hai loại lại rồi sắp xếp thì pandas ném
        # "'<' not supported between instances of 'Timestamp' and 'str'".
        # Quy cả hai về chuỗi YYYY-MM-DD trước khi ghép.
        fresh = _norm_time(fresh)
        old = None if old is None else _norm_time(old)

        merged = fresh if old is None else pd.concat([old, fresh], ignore_index=True)
        # Trùng ngày -> giữ bản ghi CŨ. Dữ liệu cũ đã dùng để sinh các lệnh
        # trong sổ; thay nó bằng bản mới (có thể đã điều chỉnh cổ tức) sẽ làm
        # các kết quả trước đó không tái dựng được nữa.
        merged = (merged.drop_duplicates(subset="time", keep="first")
                        .sort_values("time").reset_index(drop=True))
        merged.to_csv(path, index=False)

        d0, d1 = str(merged["time"].iloc[0])[:10], str(merged["time"].iloc[-1])[:10]
        changed[sym] = (d0, d1, len(merged))
        was = f"{have_from} → " if have_from else "(mới) "
        print(f"[{i}/{len(symbols)}] {sym}: ✅ {was}{d0}  ({len(merged)} phiên)")

    return changed


def coverage(symbols: list[str]) -> pd.DataFrame:
    """Bảng độ phủ dữ liệu: mỗi mã có từ ngày nào tới ngày nào, bao nhiêu phiên.

    Nhìn bảng này TRƯỚC khi diễn giải bất kỳ kết quả backtest nào. Một rổ mà
    nửa số mã chỉ có dữ liệu năm gần nhất sẽ cho ra con số nói về năm đó,
    không phải về cả giai đoạn ghi trên tiêu đề.
    """
    rows = []
    for sym in symbols:
        df = load(sym)
        if df is None or df.empty:
            rows.append({"symbol": sym, "from": None, "to": None, "sessions": 0})
            continue
        rows.append({"symbol": sym,
                     "from": str(df["time"].iloc[0])[:10],
                     "to": str(df["time"].iloc[-1])[:10],
                     "sessions": len(df)})
    return pd.DataFrame(rows).sort_values("from", na_position="first")


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
