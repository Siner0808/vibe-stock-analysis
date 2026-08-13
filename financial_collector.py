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

import datetime as _dt
import time
from typing import Any

import pandas as pd

# Chỉ số định giá cũ hơn ngần này năm thì BỎ, không hiện lên giao diện.
# Báo cáo năm chốt sau vài tháng nên năm liền trước là bình thường; cách
# hai năm trở lên thì nguồn đang trả dữ liệu hỏng, không phải dữ liệu trễ.
NAM_TOI_DA_CU = 2

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


def _year_columns(df: pd.DataFrame) -> list[tuple[int, int]]:
    """[(năm, VỊ TRÍ cột)] tăng dần, mỗi năm một lần.

    Trả về VỊ TRÍ chứ không phải nhãn cột, vì vnstock có thể trả nhiều cột
    trùng nhãn: nguồn VCI cho ACB trả 16 cột đều tên `'2018'`. Khi đó
    `row['2018']` trả về một Series chứ không phải một số, `pd.to_numeric`
    ra NaN, và mọi chỉ số im lặng thành None — đúng triệu chứng P/E, EPS,
    Beta hiện `—` trên giao diện.

    Trùng năm thì giữ cột cuối cùng. Bảng như vậy thường là hỏng, nhưng
    việc chặn nó là của chốt độ tươi bên dưới, không phải của hàm này.
    """
    theo_nam: dict[int, int] = {}
    for pos, col in enumerate(df.columns):
        label = str(col[-1] if isinstance(col, tuple) else col).strip()
        if label.isdigit() and 1990 <= int(label) <= 2100:
            theo_nam[int(label)] = pos
    return sorted(theo_nam.items())


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


def _row_latest(df: pd.DataFrame, *keywords: str) -> tuple[float | None, int | None]:
    """Tìm hàng theo tên chỉ tiêu, trả (giá trị, NĂM) của năm gần nhất có số.

    Trả kèm năm là bắt buộc: không có nó thì không phân biệt được P/E của
    2025 với P/E của 2018, và một con số cũ 8 năm hiện lên giao diện y hệt
    một con số hiện tại.
    """
    years = _year_columns(df)
    if not years:
        return None, None
    names = _name_series(df)
    for kw in keywords:
        hit = names.str.contains(kw.lower(), regex=False, na=False)
        if not hit.any():
            continue
        row = df[hit].iloc[0]
        for nam, pos in reversed(years):     # từ năm mới nhất lùi dần
            val = pd.to_numeric(pd.Series([row.iloc[pos]]), errors="coerce").iloc[0]
            if pd.notna(val):
                return float(val), nam
    return None, None


def _loc_qua_cu(chi_so: dict[str, tuple[float | None, int | None]],
                nam_min: int) -> tuple[dict[str, float | None], list[str]]:
    """Bỏ chỉ số cũ hơn `nam_min`. Trả (giá trị đã lọc, danh sách đã bỏ).

    Một con số cũ hiện trên giao diện trông y hệt một con số hiện tại —
    người đọc không có cách nào phân biệt. Nguồn VCI trả P/E 2018 cho ACB;
    hiện nó ra như chỉ số hôm nay là bịa số, chỉ khác là nguồn bịa hộ.

    Thà để trống và nói rõ lý do, còn hơn hiện một con số sai trông hợp lý.
    """
    ket_qua: dict[str, float | None] = {}
    da_bo: list[str] = []
    for ten, (gia_tri, nam) in chi_so.items():
        if gia_tri is not None and nam is not None and nam < nam_min:
            ket_qua[ten] = None
            da_bo.append(f"{ten} ({nam})")
        else:
            ket_qua[ten] = gia_tri
    return ket_qua, da_bo


def _row_series(df: pd.DataFrame, *keywords: str) -> tuple[list[str], list[float | None]]:
    """Trả (danh sách năm, chuỗi giá trị) cho một chỉ tiêu."""
    years = _year_columns(df)
    if not years:
        return [], []
    labels = [str(nam) for nam, _ in years]
    names = _name_series(df)
    for kw in keywords:
        hit = names.str.contains(kw.lower(), regex=False, na=False)
        if hit.any():
            row = df[hit].iloc[0]
            vals = pd.to_numeric(pd.Series([row.iloc[pos] for _, pos in years]),
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
            # Tên trường nói rõ "period" = kỳ dữ liệu thực có, KHÔNG phải 52 tuần.
            # Nhãn hiển thị lấy từ `period_label`, suy ra từ dữ liệu thật.
            "latest_price": None, "high_period": None, "low_period": None,
            "period_label": "", "period_days": 0,
            "pct_1w": None, "pct_1m": None, "pct_period": None, "avg_vol_10d": None,
            # từ API
            "pe": None, "eps": None, "beta": None,
            "market_cap_billions": None, "shares_outstanding": None,
        }

        # ── Phần tính từ dữ liệu giá thật ──────────────────────────────
        if df_ohlcv is not None and not df_ohlcv.empty and "close" in df_ohlcv:
            from data_quality import (period_label, period_span_days,
                                      price_multiplier)
            close = df_ohlcv["close"]
            latest = float(close.iloc[-1])
            mult = price_multiplier(df_ohlcv)
            span = period_span_days(df_ohlcv)
            result.update({
                "latest_price": latest * mult,
                # Đỉnh/đáy TRONG KỲ DỮ LIỆU CÓ THẬT, không phải 52 tuần.
                "high_period": float(df_ohlcv["high"].max()) * mult,
                "low_period": float(df_ohlcv["low"].min()) * mult,
                "period_days": span,
                "period_label": period_label(span),
                "price_available": True,
            })
            if len(close) >= 6:
                result["pct_1w"] = (latest - close.iloc[-6]) / close.iloc[-6] * 100
            if len(close) >= 21:
                result["pct_1m"] = (latest - close.iloc[-21]) / close.iloc[-21] * 100
            first = float(close.iloc[0])
            if first:
                result["pct_period"] = (latest - first) / first * 100
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
            from vnstock.api.financial import Finance
        except Exception as e:
            return None, f"{type(e).__name__}: {str(e)[:160]}"

        # KBS TRƯỚC, VCI sau. Đo ngày 13/08/2026 trên ACB:
        #   KBS → cột 2025/2024/2023/2022 rõ ràng, có P/E, EPS, Beta
        #   VCI → 16 cột đều tên '2018', dữ liệu bốn quý lặp lại bốn lần
        # VCI vẫn giữ làm dự phòng vì nó có Vốn hoá và Số CP lưu hành, hai
        # chỉ tiêu KBS không trả. Chốt độ tươi bên dưới lo phần dữ liệu cũ.
        df, loi = None, []
        for nguon in ("KBS", "VCI"):
            try:
                thu = Finance(source=nguon, symbol=symbol, period="year",
                              show_log=False).ratio(lang="en", dropna=True)
            except Exception as e:
                loi.append(f"{nguon}: {type(e).__name__}")
                continue
            if thu is not None and isinstance(thu, pd.DataFrame) and not thu.empty:
                df, self._nguon_ratio = thu, nguon
                break
            loi.append(f"{nguon}: bảng rỗng")

        if df is None:
            return None, "; ".join(loi) or "nguồn trả về bảng rỗng"

        if _is_row_oriented(df):
            # Dạng thường gặp: chỉ tiêu ở hàng, năm ở cột
            get = lambda *kw: _row_latest(df, *kw)
            layout = "hàng-chỉ-tiêu"
        else:
            get = lambda *kw: (_first_value(df, _pick(df, *kw)), None)
            layout = "cột-chỉ-tiêu"

        # Từ khoá riêng nhất đặt trước, để không khớp nhầm chỉ tiêu khác.
        pe, nam_pe = get("pe_ratio", "p/e", "price to earning")
        eps, nam_eps = get("trailing_eps", "(eps)", "earning per share")
        beta, nam_beta = get("beta")
        mcap, nam_mcap = get("market capital", "market cap", "vốn hóa")
        shares, _ = get("outstanding share", "shares outstanding",
                        "khối lượng lưu hành")

        nam_min = _dt.date.today().year - NAM_TOI_DA_CU
        loc, qua_cu = _loc_qua_cu(
            {"P/E": (pe, nam_pe), "EPS": (eps, nam_eps),
             "Beta": (beta, nam_beta), "vốn hoá": (mcap, nam_mcap)}, nam_min)
        pe, eps, beta, mcap = (loc["P/E"], loc["EPS"], loc["Beta"], loc["vốn hoá"])

        # Nguồn trả vốn hóa theo đồng -> quy về tỷ đồng
        mcap_billions = mcap / 1e9 if mcap and mcap > 1e9 else mcap
        found = {"pe": pe, "eps": eps, "beta": beta,
                 "market_cap_billions": mcap_billions,
                 "shares_outstanding": int(shares) if shares else None,
                 "nam_du_lieu": nam_pe or nam_eps or nam_beta}

        nguon = getattr(self, "_nguon_ratio", "?")

        if all(v is None for v in found.values()):
            if qua_cu:
                return found, (f"{nguon} chỉ có dữ liệu quá cũ: "
                               f"{', '.join(qua_cu)} — cần từ {nam_min} trở lại "
                               f"đây. Đã BỎ thay vì hiện như chỉ số hiện tại.")
            # Lấy được bảng nhưng không nhận ra chỉ tiêu nào -> in mẫu để sửa từ khoá
            if _is_row_oriented(df):
                sample = _name_series(df).head(10).tolist()
                return found, (f"{nguon}: bảng {layout} nhưng không khớp từ khoá. "
                               f"Chỉ tiêu thực tế: {sample}")
            sample = list(_flat_columns(df))[:10]
            return found, f"{nguon}: bảng {layout}, cột thực tế: {sample}"

        ghi_chu = f"OK ({nguon}, {layout}"
        if found["nam_du_lieu"]:
            ghi_chu += f", số liệu năm {found['nam_du_lieu']}"
        if qua_cu:
            ghi_chu += f"; đã bỏ vì quá cũ: {', '.join(qua_cu)}"
        return found, ghi_chu + ")"

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
