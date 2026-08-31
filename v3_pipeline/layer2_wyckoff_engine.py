"""
TẦNG 2: WYCKOFF ENGINE ĐA KHUNG THỜI GIAN
- Phân tích cấu trúc Wyckoff trên khung Daily
- Xác nhận chéo với khung Weekly (Confirmation)
- Phát hiện: Spring, LPS, SOS, Pha C/D/E
- Tính Wyckoff Score [0-100]
"""
import pandas as pd
import numpy as np


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Thêm các chỉ báo kỹ thuật cần thiết."""
    df = df.copy().sort_values("time").reset_index(drop=True)
    
    # MAs
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma50"] = df["close"].rolling(50).mean()
    df["ma200"] = df["close"].rolling(200).mean()
    
    # Volume MA
    df["vol_ma20"] = df["volume"].rolling(20).mean()
    
    # ATR (Average True Range)
    df["prev_close"] = df["close"].shift(1)
    df["tr"] = df.apply(lambda r: max(r["high"] - r["low"],
                                       abs(r["high"] - r["prev_close"]),
                                       abs(r["low"] - r["prev_close"])), axis=1)
    df["atr14"] = df["tr"].rolling(14).mean()
    
    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df["rsi14"] = 100 - (100 / (1 + rs))
    
    # VWAP proxy (30 phiên)
    df["vwap30"] = (df["close"] * df["volume"]).rolling(30).sum() / df["volume"].rolling(30).sum()
    
    return df


def detect_climax(df: pd.DataFrame, window: int = 60) -> dict:
    """Phát hiện Selling Climax / Buying Climax (đỉnh/đáy khối lượng cực lớn)."""
    recent = df.tail(window).copy()
    if recent.empty:
        return {}
    
    vol_std = recent["volume"].std()
    vol_mean = recent["volume"].mean()
    
    # Nến có khối lượng > mean + 2.5*std → Climax
    climax_bars = recent[recent["volume"] > vol_mean + 2.5 * vol_std]
    
    if climax_bars.empty:
        return {"has_climax": False}
    
    last_climax = climax_bars.iloc[-1]
    is_selling = last_climax["close"] < last_climax["open"]  # Nến đỏ khổng lồ
    
    return {
        "has_climax": True,
        "type": "SC" if is_selling else "BC",
        "date": str(last_climax["time"])[:10],
        "price": last_climax["close"],
        "volume": last_climax["volume"],
        "vol_multiplier": round(last_climax["volume"] / vol_mean, 1)
    }


def detect_spring(df: pd.DataFrame, lookback: int = 90) -> dict:
    """
    Phát hiện Spring: Giá test dưới vùng hỗ trợ tích lũy rồi đóng cửa trên.
    Dấu hiệu: Nến thân nhỏ, bóng dưới dài, khối lượng co cạn.
    """
    if len(df) < lookback:
        return {"has_spring": False}
    
    recent = df.tail(lookback).copy()
    support_zone_low = recent["low"].quantile(0.05)   # Đáy vùng tích lũy
    support_zone_high = recent["low"].quantile(0.20)  # Viền trên hỗ trợ
    
    for i in range(len(recent) - 1, max(len(recent) - 30, 0), -1):
        row = recent.iloc[i]
        # Điều kiện Spring: Giá chọc xuống dưới hỗ trợ nhưng đóng cửa trên
        if row["low"] < support_zone_low * 1.02 and row["close"] > support_zone_low:
            body = abs(row["close"] - row["open"])
            lower_wick = row["open"] - row["low"] if row["close"] >= row["open"] else row["close"] - row["low"]
            
            # Thân nhỏ, bóng dưới dài (≥ 2× thân)
            if lower_wick > body * 1.5 and row["volume"] < recent["vol_ma20"].iloc[i] * 1.0:
                return {
                    "has_spring": True,
                    "date": str(row["time"])[:10],
                    "price": row["close"],
                    "low": row["low"],
                    "vol_vs_ma": round(row["volume"] / recent["vol_ma20"].iloc[i], 2)
                }
    
    return {"has_spring": False}


def detect_sos_and_lps(df: pd.DataFrame) -> dict:
    """
    Phát hiện Sign of Strength (SOS) và Last Point of Support (LPS).
    SOS: Breakout mạnh trên khối lượng cao (Pha D).
    LPS: Pullback về kiểm tra SOS trên khối lượng thấp.
    """
    if len(df) < 30:
        return {"has_sos": False, "has_lps": False}
    
    recent = df.tail(60).copy().reset_index(drop=True)
    vol_ma = recent["vol_ma20"]
    
    sos_idx = None
    sos_price = None
    
    # Tìm SOS: Nến tăng mạnh với KL > 1.5× MA20
    for i in range(len(recent) - 1, max(len(recent) - 30, 0), -1):
        row = recent.iloc[i]
        is_up_candle = row["close"] > row["open"]
        is_high_vol = row["volume"] > vol_ma.iloc[i] * 1.5
        body_pct = (row["close"] - row["open"]) / row["open"] * 100
        
        if is_up_candle and is_high_vol and body_pct > 0.5:
            sos_idx = i
            sos_price = row["close"]
            break
    
    if sos_idx is None:
        return {"has_sos": False, "has_lps": False}
    
    sos_data = {
        "has_sos": True,
        "sos_date": str(recent.iloc[sos_idx]["time"])[:10],
        "sos_price": sos_price,
        "sos_vol_mult": round(recent.iloc[sos_idx]["volume"] / vol_ma.iloc[sos_idx], 1)
    }
    
    # Tìm LPS sau SOS: Pullback nhẹ trên KL thấp
    post_sos = recent.iloc[sos_idx + 1:] if sos_idx + 1 < len(recent) else pd.DataFrame()
    lps_data = {"has_lps": False}
    
    if not post_sos.empty:
        for i in range(len(post_sos)):
            row = post_sos.iloc[i]
            is_low_vol = row["volume"] < vol_ma.iloc[sos_idx + 1 + i] * 0.8
            is_pullback = row["close"] < sos_price and row["close"] > sos_price * 0.97
            
            if is_pullback and is_low_vol:
                lps_data = {
                    "has_lps": True,
                    "lps_date": str(row["time"])[:10],
                    "lps_price": row["close"],
                    "lps_vol_mult": round(row["volume"] / vol_ma.iloc[sos_idx + 1 + i], 2)
                }
                break
    
    return {**sos_data, **lps_data}


def detect_wyckoff_phase(df: pd.DataFrame) -> str:
    """Ước tính pha Wyckoff hiện tại dựa trên cấu trúc giá."""
    if len(df) < 50:
        return "UNKNOWN"
    
    close = df["close"]
    ma20 = df["ma20"]
    ma50 = df["ma50"]
    
    latest = close.iloc[-1]
    latest_ma20 = ma20.iloc[-1]
    latest_ma50 = ma50.iloc[-1]
    
    # Giá đang trên cả 2 MA và MA20 > MA50 → Markup (Pha D/E)
    if latest > latest_ma20 > latest_ma50:
        # Kiểm tra momentum: Đang tăng tốc hay chậm lại?
        ret_1w = (latest / close.iloc[-5] - 1) * 100 if len(close) > 5 else 0
        if ret_1w > 2:
            return "PHASE_E_MARKUP"
        else:
            return "PHASE_D_SOS"
    
    # Giá ≈ MA20, MA20 phẳng → Tích lũy (Pha A-C)
    elif abs(latest / latest_ma20 - 1) < 0.05 and abs(latest_ma20 / latest_ma50 - 1) < 0.08:
        return "PHASE_C_SPRING"
    
    # Giá dưới cả 2 MA → Markdown hoặc phân phối
    elif latest < latest_ma20 and latest < latest_ma50:
        return "PHASE_A_MARKDOWN"
    
    return "PHASE_BC_ACCUMULATION"


def analyze_wyckoff(symbol: str, df_daily: pd.DataFrame, df_weekly: pd.DataFrame) -> dict:
    """Phân tích Wyckoff đầy đủ cho một mã cổ phiếu."""
    if df_daily.empty:
        return {"symbol": symbol, "score": 0, "phase": "UNKNOWN", "valid": False}
    
    df_d = compute_indicators(df_daily)
    df_w = compute_indicators(df_weekly) if not df_weekly.empty else pd.DataFrame()
    
    score = 0
    signals = []
    
    # 1. Phát hiện pha Wyckoff
    phase = detect_wyckoff_phase(df_d)
    if phase in ["PHASE_D_SOS", "PHASE_E_MARKUP", "PHASE_C_SPRING"]:
        score += 25
        signals.append(f"✅ Pha: {phase}")
    
    # 2. Climax
    climax = detect_climax(df_d)
    if climax.get("has_climax") and climax.get("type") == "SC":
        score += 20
        signals.append(f"✅ Selling Climax {climax['date']} ({climax['vol_multiplier']}×)")
    
    # 3. Spring
    spring = detect_spring(df_d)
    if spring.get("has_spring"):
        score += 25
        signals.append(f"✅ Spring phát hiện {spring['date']}")
    
    # 4. SOS + LPS
    sos_lps = detect_sos_and_lps(df_d)
    if sos_lps.get("has_sos"):
        score += 15
        signals.append(f"✅ SOS {sos_lps['sos_date']} ({sos_lps['sos_vol_mult']}×)")
    if sos_lps.get("has_lps"):
        score += 10
        signals.append(f"✅ LPS Test cạn cung {sos_lps['lps_date']}")
    
    # 5. Xác nhận Weekly (Đa khung)
    weekly_confirmed = False
    if not df_w.empty:
        w_close = df_w["close"]
        w_ma20 = df_w["close"].rolling(20).mean()
        if len(w_close) >= 20 and w_close.iloc[-1] > w_ma20.iloc[-1]:
            score += 5
            weekly_confirmed = True
            signals.append("✅ Xác nhận Weekly: Giá > MA20W")
            
    # 6. ML Enhancements: Cosine, DTW, Kalman, VCP Minervini & Institutional Flow
    from ml_algorithms import (
        match_wyckoff_pattern,
        match_wyckoff_dtw,
        kalman_filter_trend,
        compute_linear_regression_channel,
        detect_vcp_pattern,
        analyze_institutional_flow
    )
    pattern_match = match_wyckoff_pattern(df_d)
    dtw_match = match_wyckoff_dtw(df_d)
    lr_channel = compute_linear_regression_channel(df_d)
    kalman_res = kalman_filter_trend(df_d["close"].values)
    vcp_res = detect_vcp_pattern(df_d)
    inst_flow = analyze_institutional_flow(symbol, df_d)
    
    if pattern_match.get("similarity", 0) >= 0.75:
        score += 8
        signals.append(f"🧠 ML Cosine: {pattern_match['best_pattern']} ({pattern_match['similarity']:.2f})")
        
    if dtw_match.get("dtw_similarity", 0) >= 75.0:
        score += 7
        signals.append(f"📈 ML DTW Elastic: {dtw_match['pattern_name_vi']} ({dtw_match['dtw_similarity']:.1f}%)")
        
    if vcp_res.get("is_vcp"):
        score += 15
        signals.extend([f"💎 VCP: {s}" for s in vcp_res.get("signals", [])[:2]])
        
    if inst_flow.get("institutional_score", 50) >= 65:
        score += 10
        signals.extend([f"🏦 Dòng tiền lớn: {s}" for s in inst_flow.get("signals", [])[:1]])
    elif inst_flow.get("institutional_score", 50) <= 30:
        score -= 10
        signals.extend([f"⚠️ {s}" for s in inst_flow.get("signals", [])[:1]])
        
    if kalman_res.get("signal") == "BULLISH_REVERSAL":
        score += 10
        signals.append("⚡ Kalman Zero-Lag: Đảo chiều tăng tức thì (Bullish Reversal)")
    elif kalman_res.get("signal") == "TRENDING_UP_STRONG":
        score += 5
        signals.append("🚀 Kalman Zero-Lag: Xu hướng tăng mạnh (Vận tốc > 0)")
        
    if lr_channel.get("signal") == "OVERBOUGHT_REVERSION":
        signals.append(f"⚠️ Kênh Hồi quy: Quá mua Z={lr_channel['z_score']:+.1f}σ")
    elif lr_channel.get("signal") in ["OVERSOLD_REVERSION", "BEARISH_PULLBACK"]:
        signals.append(f"💡 Kênh Hồi quy: Vùng tích lũy/hồi phục Z={lr_channel['z_score']:+.1f}σ")
    
    # Giá hiện tại
    latest_price = df_d["close"].iloc[-1]
    
    return {
        "symbol": symbol,
        "score": min(max(score, 0), 100),
        "phase": phase,
        "valid": score >= 50,
        "latest_price": latest_price,
        "signals": signals,
        "weekly_confirmed": weekly_confirmed,
        "pattern_match": pattern_match,
        "dtw_match": dtw_match,
        "vcp": vcp_res,
        "institutional_flow": inst_flow,
        "kalman": kalman_res,
        "lr_channel": lr_channel,
        "spring": spring,
        "sos_lps": sos_lps,
        "climax": climax,
        "df_d": df_d
    }


def run_wyckoff_engine(top_symbols: list, quality_results: dict) -> dict:
    """Entry point Tầng 2."""
    print(f"\n{'='*60}")
    print(f"⚙️ TẦNG 2: WYCKOFF ENGINE ĐA KHUNG ({len(top_symbols)} mã)")
    print(f"{'='*60}")
    
    results = {}
    for sym in top_symbols:
        info = quality_results.get(sym, {})
        df_d = info.get("df_daily", pd.DataFrame())
        df_w = info.get("df_weekly", pd.DataFrame())
        
        result = analyze_wyckoff(sym, df_d, df_w)
        results[sym] = result
        
        status = "🟢" if result["valid"] else "⚪"
        phase_short = result["phase"].replace("PHASE_", "")
        print(f"  {status} {sym:6s} | Score: {result['score']:3d}/100 | {phase_short}")
    
    valid = [(s, r) for s, r in results.items() if r["valid"]]
    print(f"\n  📊 Qua bộ lọc Wyckoff: {len(valid)}/{len(top_symbols)} mã")
    return results
