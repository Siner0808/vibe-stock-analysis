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


# ─────────────────────────────────────────────────────────────────────
# Xử lý bảng XOAY NGANG (row-oriented)
# vnstock trả báo cáo tài chính dưới dạng: mỗi HÀNG là một chỉ tiêu
# (cột `item` / `item_en` chứa tên), mỗi CỘT là một năm ('2018', '2019'...).
# Đây là lý do việc dò theo tên cột không tìm thấy gì.
# ─────────────────────────────────────────────────────────────────────
NAME_COLUMNS = ("item_en", "item", "chỉ tiêu", "index")


def _year_columns(df: pd.DataFrame) -> list:
    """Các cột là năm, sắp xếp tăng dần."""
    found = []
    for col in df.columns:
        label = str(col[-1] if isinstance(col, tuple) else col).strip()
        if label.isdigit() and 1990 <= int(label) <= 2100:
            found.append((int(label), col))
    return [c for _, c in sorted(found)]


def _is_row_oriented(df: pd.DataFrame) -> bool:
    cols = _flat_columns(df)
    has_name = any(any(n == lbl or n in lbl for lbl in cols) for n in NAME_COLUMNS)
    return has_name and bool(_year_columns(df))


def _name_series(df: pd.DataFrame) -> pd.Series:
    """Ghép mọi cột tên chỉ tiêu thành một chuỗi để dò từ khoá."""
    cols = _flat_columns(df)
    parts = []
    for n in NAME_COLUMNS:
        for lbl, original in cols.items():
            if n == lbl or n in lbl:
                parts.append(df[original].astype(str))
    if not parts:
        return pd.Series([""] * len(df), index=df.index)
    out = parts[0]
    for p in parts[1:]:
        out = out + " | " + p
    return out.str.lower()


def _row_latest(df: pd.DataFrame, *keywords: str) -> float | None:
    """Tìm hàng theo tên chỉ tiêu, trả giá trị của năm gần nhất có số liệu."""
    years = _year_columns(df)
    if not years:
        return None
    names = _name_series(df)
    for kw in keywords:
        hit = names.str.contains(kw.lower(), regex=False, na=False)
        if not hit.any():
            continue
        row = df[hit].iloc[0]
        for col in reversed(years):          # từ năm mới nhất lùi dần
            val = pd.to_numeric(pd.Series([row[col]]), errors="coerce").iloc[0]
            if pd.notna(val):
                return float(val)
    return None


def _row_series(df: pd.DataFrame, *keywords: str) -> tuple[list[str], list[float | None]]:
    """Trả (danh sách năm, chuỗi giá trị) cho một chỉ tiêu."""
    years = _year_columns(df)
    if not years:
        return [], []
    labels = [str(c[-1] if isinstance(c, tuple) else c) for c in years]
    names = _name_series(df)
    for kw in keywords:
        hit = names.str.contains(kw.lower(), regex=False, na=False)
        if hit.any():
            row = df[hit].iloc[0]
            vals = pd.to_numeric(pd.Series([row[c] for c in years]),
                                 errors="coerce")
            return labels, [None if pd.isna(v) else float(v) for v in vals]
    return labels, []


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
            from data_quality import price_multiplier
            mult = price_multiplier(df_ohlcv)
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
            from vnstock_auth import ensure_api_key
            ensure_api_key()          # idempotent, không cần key vẫn chạy tiếp

            from vnstock import Finance
            # `source` là tham số BẮT BUỘC của facade vnstock.Finance
            # (lớp explorer bên dưới thì không cần) — thiếu nó là TypeError.
            df = Finance(source="VCI", symbol=symbol, period="year",
                         show_log=False).ratio(lang="en", dropna=True)
        except Exception as e:
            return None, f"{type(e).__name__}: {str(e)[:160]}"
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return None, "nguồn trả về bảng rỗng"

        if _is_row_oriented(df):
            # Dạng thường gặp: chỉ tiêu ở hàng, năm ở cột
            get = lambda *kw: _row_latest(df, *kw)
            layout = "hàng-chỉ-tiêu"
        else:
            get = lambda *kw: _first_value(df, _pick(df, *kw))
            layout = "cột-chỉ-tiêu"

        pe = get("p/e", "pe ratio", "price to earning")
        eps = get("eps", "earning per share")
        beta = get("beta")
        mcap = get("market capital", "market cap", "vốn hóa")
        shares = get("outstanding share", "shares outstanding", "khối lượng lưu hành")

        # Nguồn trả vốn hóa theo đồng -> quy về tỷ đồng
        mcap_billions = mcap / 1e9 if mcap and mcap > 1e9 else mcap
        found = {"pe": pe, "eps": eps, "beta": beta,
                 "market_cap_billions": mcap_billions,
                 "shares_outstanding": int(shares) if shares else None}

        if all(v is None for v in found.values()):
            # Lấy được bảng nhưng không nhận ra chỉ tiêu nào -> in mẫu để sửa từ khoá
            if _is_row_oriented(df):
                sample = _name_series(df).head(10).tolist()
                return found, (f"bảng {layout} nhưng không khớp từ khoá. "
                               f"Chỉ tiêu thực tế: {sample}")
            sample = list(_flat_columns(df))[:10]
            return found, f"bảng {layout}, cột thực tế: {sample}"
        return found, f"OK ({layout})"

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
            from vnstock_auth import ensure_api_key
            ensure_api_key()

            from vnstock import Finance
            fin = Finance(source="VCI", symbol=symbol, period="year", show_log=False)
            inc = fin.income_statement(lang="en", dropna=True)
            bal = fin.balance_sheet(lang="en", dropna=True)
        except Exception:
            return None
        if inc is None or inc.empty:
            return None

        if _is_row_oriented(inc):
            # Chỉ tiêu ở hàng, năm ở cột — dạng vnstock thực sự trả về
            years, revenue = _row_series(inc, "net revenue", "revenue",
                                         "net sales", "doanh thu thuần", "doanh thu")
            _, net_profit = _row_series(inc, "attribute to parent",
                                        "profit after tax", "net profit",
                                        "lợi nhuận sau thuế")
            equity = debt = []
            if bal is not None and not bal.empty and _is_row_oriented(bal):
                _, equity = _row_series(bal, "owner's equity", "equity", "vốn chủ")
                _, debt = _row_series(bal, "liabilities", "nợ phải trả")
        else:
            year_col = _pick(inc, "yearreport", "year", "kỳ")
            rev_col = _pick(inc, "revenue", "net sales", "doanh thu")
            profit_col = _pick(inc, "attribute to parent", "net profit",
                               "lợi nhuận sau thuế")
            if year_col is None or rev_col is None:
                return None
            years = [str(y) for y in inc[year_col].tolist()]
            revenue = pd.to_numeric(inc[rev_col], errors="coerce").tolist()
            net_profit = (pd.to_numeric(inc[profit_col], errors="coerce").tolist()
                          if profit_col is not None else [None] * len(years))
            equity = debt = []
            if bal is not None and not bal.empty:
                eq_col = _pick(bal, "owner's equity", "equity", "vốn chủ")
                debt_col = _pick(bal, "liabilities", "nợ phải trả")
                if eq_col is not None:
                    equity = pd.to_numeric(bal[eq_col], errors="coerce").tolist()
                if debt_col is not None:
                    debt = pd.to_numeric(bal[debt_col], errors="coerce").tolist()
            order = sorted(range(len(years)), key=lambda i: years[i])
            pick = lambda xs: [xs[i] for i in order] if len(xs) == len(years) else xs
            years, revenue, net_profit = pick(years), pick(revenue), pick(net_profit)
            equity, debt = pick(equity), pick(debt)

        if not years or not revenue:
            return None

        d2e = ([round(d / e, 2) if (d is not None and e) else None
                for d, e in zip(debt, equity)] if equity and debt else [])

        return {"available": True, "note": "Nguồn: vnstock (VCI)",
                "years": years, "revenue": revenue, "net_profit": net_profit,
                "equity": equity, "debt": debt, "debt_to_equity": d2e}

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
