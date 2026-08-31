"""
TẦNG 0.5: LỌC VĨ MÔ & XẾP HẠNG SỨC MẠNH TƯƠNG ĐỐI (Relative Strength)
- Đo sức khoẻ VN-Index → Phân loại Risk-On / Risk-Off
- Tính RS Score cho từng mã vs VN-Index
- Chỉ chuyển tiếp Top N mã RS mạnh nhất vào Tầng 2
"""
import pandas as pd
import numpy as np
from vnstock import Quote
from datetime import datetime, timedelta


VNINDEX_SYMBOL = "VNINDEX"
TOP_N = 20        # Số mã RS mạnh nhất vào phân tích chuyên sâu
RS_LOOKBACK = 63  # Số phiên để tính RS (~3 tháng giao dịch)


def fetch_vnindex(months: int = 6) -> pd.DataFrame:
    """Lấy dữ liệu VN-Index làm benchmark."""
    start = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")
    try:
        q = Quote(symbol=VNINDEX_SYMBOL, source="VCI")
        df = q.history(start=start, end=end)
        if df is not None and not df.empty:
            df["time"] = pd.to_datetime(df["time"])
            return df.sort_values("time").reset_index(drop=True)
    except Exception as e:
        print(f"  ⚠️ Không lấy được VN-Index: {e}")
    return pd.DataFrame()


def classify_market_regime(df_vnindex: pd.DataFrame) -> dict:
    """
    Phân loại chế độ thị trường:
    - RISK_ON: Xu hướng tăng rõ ràng, đủ điều kiện mua
    - RISK_OFF: Xu hướng giảm / tích lũy bất định → Đứng ngoài
    """
    if df_vnindex.empty or len(df_vnindex) < 50:
        return {"regime": "UNKNOWN", "signal": "Không đủ dữ liệu VN-Index"}
    
    close = df_vnindex["close"]
    
    # Nếu dữ liệu theo đơn vị gốc vnstock (không × 1000) → index points
    # VN-Index ~ 1000-1400 điểm
    
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    
    latest = close.iloc[-1]
    latest_ma20 = ma20.iloc[-1]
    latest_ma50 = ma50.iloc[-1]
    
    # Tính % thay đổi 1 tháng, 3 tháng
    ret_1m = (latest / close.iloc[-21] - 1) * 100 if len(close) > 21 else 0
    ret_3m = (latest / close.iloc[-63] - 1) * 100 if len(close) > 63 else 0
    
    # Breadth: bao nhiêu % ngày tăng trong 20 phiên gần nhất
    daily_returns = close.pct_change().tail(20)
    up_days_pct = (daily_returns > 0).sum() / 20 * 100
    
    # Phân loại
    regime_score = 0
    reasons = []
    
    if latest > latest_ma20:
        regime_score += 1
        reasons.append("Giá > MA20")
    if latest > latest_ma50:
        regime_score += 1
        reasons.append("Giá > MA50")
    if latest_ma20 > latest_ma50:
        regime_score += 1
        reasons.append("MA20 > MA50 (Golden Cross)")
    if ret_1m > 0:
        regime_score += 1
        reasons.append(f"Tháng +{ret_1m:.1f}%")
    if up_days_pct > 55:
        regime_score += 1
        reasons.append(f"Breadth {up_days_pct:.0f}% ngày tăng")
    
    if regime_score >= 4:
        regime = "STRONG_RISK_ON"
        emoji = "🟢"
    elif regime_score == 3:
        regime = "RISK_ON"
        emoji = "🟡"
    elif regime_score == 2:
        regime = "CAUTION"
        emoji = "🟠"
    else:
        regime = "RISK_OFF"
        emoji = "🔴"
    
    return {
        "regime": regime,
        "emoji": emoji,
        "score": regime_score,
        "vnindex_latest": latest,
        "ret_1m": ret_1m,
        "ret_3m": ret_3m,
        "breadth_pct": up_days_pct,
        "reasons": reasons,
        "allow_new_entries": regime in ["STRONG_RISK_ON", "RISK_ON"]
    }


def compute_rs_score(df_stock: pd.DataFrame, df_vnindex: pd.DataFrame, lookback: int = 63) -> float:
    """
    Tính Relative Strength (RS) Score:
    RS = (Hiệu suất cổ phiếu / Hiệu suất VN-Index) trong N phiên.
    RS > 1 → Mạnh hơn thị trường.
    """
    if df_stock.empty or df_vnindex.empty:
        return 0.0
    
    # Cắt N phiên gần nhất
    stock_close = df_stock.sort_values("time")["close"].tail(lookback)
    vnindex_close = df_vnindex.sort_values("time")["close"].tail(lookback)
    
    if len(stock_close) < 2 or len(vnindex_close) < 2:
        return 0.0
    
    ret_stock = stock_close.iloc[-1] / stock_close.iloc[0] - 1
    ret_vnindex = vnindex_close.iloc[-1] / vnindex_close.iloc[0] - 1
    
    if ret_vnindex == 0:
        return 0.0
    
    rs = ret_stock / abs(ret_vnindex) if ret_vnindex != 0 else 0
    return round(rs, 4)


def rank_by_rs(quality_results: dict, df_vnindex: pd.DataFrame, top_n: int = TOP_N) -> list:
    """Xếp hạng tất cả mã theo RS và trả về Top N."""
    rs_data = []
    for sym, info in quality_results.items():
        if not info["passed"]:
            continue
        df_daily = info["df_daily"]
        rs = compute_rs_score(df_daily, df_vnindex, RS_LOOKBACK)
        rs_data.append({"symbol": sym, "rs_score": rs})
    
    rs_df = pd.DataFrame(rs_data).sort_values("rs_score", ascending=False)
    top_list = rs_df.head(top_n)["symbol"].tolist()
    return top_list, rs_df


def run_macro_filter(quality_results: dict) -> dict:
    """Entry point Tầng 0.5."""
    print(f"\n{'='*60}")
    print(f"🎯 TẦNG 0.5: LỌC VĨ MÔ, HMM REGIME & XẾP HẠNG RS")
    print(f"{'='*60}")
    
    df_vnindex = fetch_vnindex()
    regime = classify_market_regime(df_vnindex)
    
    # 🧠 HMM Probabilistic Regime Classification
    from ml_algorithms import classify_market_regime_hmm, compute_sector_graph_pagerank
    hmm_res = classify_market_regime_hmm(df_vnindex)
    regime["hmm"] = hmm_res
    
    print(f"\n  {regime['emoji']} CHẾ ĐỘ THỊ TRƯỜNG: {regime['regime']} (Score: {regime['score']}/5)")
    print(f"  🧠 HMM State: {hmm_res['regime']} (Bull: {hmm_res['probabilities']['bull']*100:.1f}% | Side: {hmm_res['probabilities']['sideway']*100:.1f}% | Bear: {hmm_res['probabilities']['bear']*100:.1f}%)")
    print(f"  VN-Index: {regime.get('vnindex_latest', 0):,.1f} | 1M: {regime.get('ret_1m', 0):+.1f}% | 3M: {regime.get('ret_3m', 0):+.1f}%")
    print(f"  Lý do: {' | '.join(regime['reasons'])}")
    
    # 🕸️ Sector Leader Graph & PageRank
    pagerank_res = compute_sector_graph_pagerank(quality_results)
    top_leaders = pagerank_res.get("top_5_leaders", [])
    if top_leaders:
        leaders_str = ", ".join([f"{s} ({sc:.1f})" for s, sc in top_leaders])
        print(f"  🕸️ Cổ phiếu Đầu đàn (PageRank Leaders): {leaders_str}")
    
    if not regime["allow_new_entries"]:
        print(f"\n  🔴 RISK-OFF: Thị trường không thuận lợi, tạm dừng mở lệnh mới.")
        return {"regime": regime, "top_symbols": [], "rs_df": pd.DataFrame(), "df_vnindex": df_vnindex, "sector_graph": pagerank_res}
    
    print(f"\n  ✅ RISK-ON: Quét Top {TOP_N} mã RS mạnh nhất...")
    top_symbols, rs_df = rank_by_rs(quality_results, df_vnindex, TOP_N)
    
    print(f"\n  Top {min(10, len(top_symbols))} RS Score:")
    for i, row in rs_df.head(10).iterrows():
        bar = "█" * int(min(max(row['rs_score'] * 10, 0), 20))
        print(f"    {row['symbol']:6s} RS: {row['rs_score']:+.3f} {bar}")
    
    return {
        "regime": regime,
        "top_symbols": top_symbols,
        "rs_df": rs_df,
        "df_vnindex": df_vnindex,
        "sector_graph": pagerank_res
    }
