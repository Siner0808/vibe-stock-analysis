"""
financial_collector.py
──────────────────────────────────────────────────────────────────────
Thu thập dữ liệu tài chính doanh nghiệp từ nguồn THẬT (vnstock).

NGUYÊN TẮC BẤT BIẾN CỦA MODULE NÀY
──────────────────────────────────
KHÔNG BAO GIỜ sinh số liệu tài chính. Không random, không hash, không
giá trị mặc định "trông giống thật".

Bản cũ của file này sinh P/E, EPS, Beta, vốn hóa từ `hash(symbol)` và
báo cáo tài chính 5 năm từ `np.random`. Vì hash chuỗi trong Python được
ngẫu nhiên hoá theo tiến trình, cùng một mã cho ra P/E khác nhau sau mỗi
lần khởi động — số liệu đó không chỉ sai mà còn không ổn định.

Mọi hàm ở đây trả về dict có khoá `available`:
    available=True  → số liệu lấy từ nguồn thật, dùng được
    available=False → KHÔNG lấy được; giao diện phải hiển thị "không có
                      dữ liệu", tuyệt đối không điền số thay thế.
"""
from __future__ import annotations

import time
from typing import Any

import pandas as pd

_CACHE: dict[str, tuple[float, Any]] = {}
_TTL_SECONDS = 900          # 15 phút — số liệu cơ bản đổi rất chậm


def _cached(key: str, fn, ttl: int = _TTL_SECONDS):
    """Cache TTL tối giản, không phụ thuộc Streamlit để test được offline."""
    now = time.time()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = fn()
    _CACHE[key] = (now, value)
    return value


def _flat_columns(df: pd.DataFrame) -> dict[str, Any]:
    """Làm phẳng cột (kể cả MultiIndex) -> {tên viết thường: cột gốc}."""
    out = {}
    for col in df.columns:
        label = " ".join(str(p) for p in col) if isinstance(col, tuple) else str(col)
        out[label.strip().lower()] = col
    return out


def _pick(df: pd.DataFrame, *candidates: str):
    """Tìm cột đầu tiên khớp một trong các từ khoá. Trả None nếu không có.

    Tên cột của vnstock đổi theo nguồn và phiên bản, nên dò theo chuỗi con
    thay vì khớp tuyệt đối. Không tìm thấy thì trả None — KHÔNG đoán.
    """
    cols = _flat_columns(df)
    for cand in candidates:
        c = cand.lower()
        for label, original in cols.items():
            if c in label:
                return original
    return None


def _first_value(df: pd.DataFrame, col) -> float | None:
    if col is None or df.empty:
        return None
    try:
        val = pd.to_numeric(df[col], errors="coerce").dropna()
        return float(val.iloc[0]) if len(val) else None
    except Exception:
        return None


class FinancialDataCollector:
    """Thu thập chỉ số định giá, BCTC và giao dịch khối ngoại từ nguồn thật."""

    NAME = "Financial Data Collector Agent"

    # ───────────────────────── Chỉ số định giá ─────────────────────────
    def get_company_overview(self, symbol: str,
                             df_ohlcv: pd.DataFrame | None = None) -> dict:
        """Chỉ số định giá.

        Tách làm hai phần với độ tin cậy khác nhau:
          - Từ OHLCV (giá, 52T, % biến động, KLTB): tính trực tiếp, luôn thật.
          - Từ API (P/E, EPS, Beta, vốn hóa, số CP): có thể None nếu không lấy được.
        """
        result: dict[str, Any] = {
            "symbol": symbol,
            "available": False,
            "price_available": False,
            "note": "",
            "diagnostic": "",
            # từ OHLCV
            "latest_price": None, "high_52w": None, "low_52w": None,
            "pct_1w": None, "pct_1m": None, "pct_1y": None, "avg_vol_10d": None,
            # từ API
            "pe": None, "eps": None, "beta": None,
            "market_cap_billions": None, "shares_outstanding": None,
        }

        # ── Phần tính từ dữ liệu giá thật ──────────────────────────────
        if df_ohlcv is not None and not df_ohlcv.empty and "close" in df_ohlcv:
            close = df_ohlcv["close"]
            latest = float(close.iloc[-1])
            mult = 1000.0 if latest < 1000 else 1.0   # nghìn đồng -> đồng
            result.update({
                "latest_price": latest * mult,
                "high_52w": float(df_ohlcv["high"].max()) * mult,
                "low_52w": float(df_ohlcv["low"].min()) * mult,
                "price_available": True,
            })
            if len(close) >= 6:
                result["pct_1w"] = (latest - close.iloc[-6]) / close.iloc[-6] * 100
            if len(close) >= 21:
                result["pct_1m"] = (latest - close.iloc[-21]) / close.iloc[-21] * 100
            if len(close) >= 200:
                result["pct_1y"] = (latest - close.iloc[-200]) / close.iloc[-200] * 100
            if "volume" in df_ohlcv and len(df_ohlcv) >= 10:
                result["avg_vol_10d"] = int(df_ohlcv["volume"].iloc[-10:].mean())

        # ── Phần lấy từ API ────────────────────────────────────────────
        ratios, diag = _cached(f"ratio:{symbol}", lambda: self._fetch_ratio(symbol))
        result["diagnostic"] = diag
        if ratios is None:
            result["note"] = f"Không lấy được chỉ số định giá. Lý do: {diag}"
            return result

        result.update(ratios)
        result["available"] = any(
            result[k] is not None for k in ("pe", "eps", "beta", "market_cap_billions")
        )
        if not result["available"]:
            result["note"] = f"Nguồn trả về dữ liệu nhưng thiếu chỉ số. {diag}"
        return result

    def _fetch_ratio(self, symbol: str) -> tuple[dict | None, str]:
        """Trả (dữ liệu, chẩn đoán). Chuỗi chẩn đoán giúp phân biệt
        'mất mạng' / 'thiếu API key' / 'tên cột không khớp' — ba nguyên nhân
        cho ra cùng một kết quả trống nhưng cần cách sửa hoàn toàn khác nhau.
        """
        try:
            from vnstock import Finance
            # `source` là tham số BẮT BUỘC của facade vnstock.Finance
            # (lớp explorer bên dưới thì không cần) — thiếu nó là TypeError.
            df = Finance(source="VCI", symbol=symbol, period="year",
                         show_log=False).ratio(lang="en", dropna=True)
        except Exception as e:
            return None, f"{type(e).__name__}: {str(e)[:160]}"
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return None, "nguồn trả về bảng rỗng"

        pe = _first_value(df, _pick(df, "p/e", "pe "))
        eps = _first_value(df, _pick(df, "eps"))
        beta = _first_value(df, _pick(df, "beta"))
        mcap = _first_value(df, _pick(df, "market capital", "market cap", "vốn hóa"))
        shares = _first_value(df, _pick(df, "outstanding share", "shares outstanding"))

        # vnstock thường trả vốn hóa theo đồng -> quy về tỷ đồng
        mcap_billions = mcap / 1e9 if mcap and mcap > 1e9 else mcap
        found = {"pe": pe, "eps": eps, "beta": beta,
                 "market_cap_billions": mcap_billions,
                 "shares_outstanding": int(shares) if shares else None}

        if all(v is None for v in found.values()):
            # Lấy được bảng nhưng không nhận ra cột nào -> in tên cột để sửa từ khoá
            sample = list(_flat_columns(df))[:8]
            return found, f"không khớp tên cột. Cột thực tế: {sample}"
        return found, "OK"

    # ───────────────────────── Báo cáo tài chính ────────────────────────
    def get_financial_statements(self, symbol: str) -> dict:
        """BCTC nhiều năm. available=False nếu không lấy được — không bịa."""
        empty = {"available": False, "note": "Không lấy được báo cáo tài chính.",
                 "years": [], "revenue": [], "net_profit": [],
                 "equity": [], "debt": [], "debt_to_equity": []}
        data = _cached(f"fs:{symbol}", lambda: self._fetch_statements(symbol))
        return data or empty

    def _fetch_statements(self, symbol: str) -> dict | None:
        try:
            from vnstock import Finance
            fin = Finance(source="VCI", symbol=symbol, period="year", show_log=False)
            inc = fin.income_statement(lang="en", dropna=True)
            bal = fin.balance_sheet(lang="en", dropna=True)
        except Exception:
            return None
        if inc is None or inc.empty:
            return None

        year_col = _pick(inc, "yearreport", "year", "kỳ")
        rev_col = _pick(inc, "revenue", "net sales", "doanh thu")
        profit_col = _pick(inc, "attribute to parent", "net profit", "lợi nhuận sau thuế")
        if year_col is None or rev_col is None:
            return None

        years = [str(y) for y in inc[year_col].tolist()]
        revenue = pd.to_numeric(inc[rev_col], errors="coerce").tolist()
        net_profit = (pd.to_numeric(inc[profit_col], errors="coerce").tolist()
                      if profit_col is not None else [None] * len(years))

        equity, debt, d2e = [], [], []
        if bal is not None and not bal.empty:
            eq_col = _pick(bal, "owner's equity", "equity", "vốn chủ")
            debt_col = _pick(bal, "liabilities", "nợ phải trả")
            if eq_col is not None:
                equity = pd.to_numeric(bal[eq_col], errors="coerce").tolist()
            if debt_col is not None:
                debt = pd.to_numeric(bal[debt_col], errors="coerce").tolist()
            if equity and debt:
                d2e = [round(d / e, 2) if e else None for d, e in zip(debt, equity)]

        # Sắp xếp năm tăng dần cho biểu đồ
        order = sorted(range(len(years)), key=lambda i: years[i])
        pick = lambda xs: [xs[i] for i in order] if len(xs) == len(years) else xs

        return {"available": True, "note": "Nguồn: vnstock (VCI)",
                "years": pick(years), "revenue": pick(revenue),
                "net_profit": pick(net_profit), "equity": pick(equity),
                "debt": pick(debt), "debt_to_equity": pick(d2e)}

    # ──────────────────────── Giao dịch khối ngoại ──────────────────────
    def get_foreign_trading_history(self, symbol: str, days: int = 10) -> dict:
        """Giao dịch NĐTNN.

        Nguồn VCI hiện không cung cấp dữ liệu này qua vnstock. Trả về
        available=False để giao diện ẩn biểu đồ, thay vì vẽ số ngẫu nhiên
        như bản cũ.
        """
        empty = {"available": False,
                 "note": "Nguồn dữ liệu hiện không cung cấp giao dịch khối ngoại.",
                 "dates": [], "net_values_billion": [],
                 "buy_val_billion": [], "sell_val_billion": []}
        data = _cached(f"ft:{symbol}:{days}",
                       lambda: self._fetch_foreign(symbol, days))
        return data or empty

    def _fetch_foreign(self, symbol: str, days: int) -> dict | None:
        try:
            from vnstock import Trading
            df = Trading(source="VCI", symbol=symbol,
                         show_log=False).foreign_trade()
        except Exception:
            return None
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return None

        date_col = _pick(df, "date", "ngày", "time")
        net_col = _pick(df, "net", "ròng")
        buy_col = _pick(df, "buy", "mua")
        sell_col = _pick(df, "sell", "bán")
        if date_col is None or net_col is None:
            return None

        sub = df.head(days).iloc[::-1]
        to_billion = lambda c: (pd.to_numeric(sub[c], errors="coerce") / 1e9).round(2).tolist() \
            if c is not None else []
        return {"available": True, "note": "Nguồn: vnstock",
                "dates": [str(d)[:10] for d in sub[date_col].tolist()],
                "net_values_billion": to_billion(net_col),
                "buy_val_billion": to_billion(buy_col),
                "sell_val_billion": to_billion(sell_col)}
