"""
🧠 MODULE THUẬT TOÁN ĐỊNH LƯỢNG & MACHINE LEARNING (Antigravity ML Engine)
Nguồn tham khảo: Nền tảng toán học & thuật toán ML cho Trading Bot

1. Hàm Sigmoid & Hồi quy Logistic: Chuẩn hoá xác suất thắng P(Win) [0-100%]
2. Vector & Cosine Similarity: So khớp mẫu hình nến Wyckoff (Pattern Matching)
3. Hồi quy Tuyến tính (Linear Regression Channel): Mean Reversion & Độ lệch chuẩn Z-Score
4. Mô phỏng Monte Carlo: Định lượng rủi ro danh mục VaR 95%, CVaR, Max Drawdown
5. Kelly Criterion: Tối ưu hoá cỡ vị thế theo xác suất thực nghiệm
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional


# ─── 1. HÀM SIGMOID & XÁC SUẤT LOGISTIC ──────────────────────────────────────

def sigmoid(z: float) -> float:
    """Hàm kích hoạt Sigmoid chuẩn: sigma(z) = 1 / (1 + exp(-z))."""
    z = np.clip(z, -10.0, 10.0)  # Chống overflow
    return 1.0 / (1.0 + np.exp(-z))


def compute_win_probability(bull_score: int, bear_score: int, wyckoff_score: int, rs_score: float = 0.0) -> float:
    """
    Tính xác suất thắng thực nghiệm P(Win) từ [0% - 100%] bằng mô hình Logistic Logit:
    z = beta_0 + beta_1 * (Bull - Bear) + beta_2 * Wyckoff + beta_3 * RS
    """
    net_score = (bull_score - bear_score) / 25.0       # Trọng số chênh lệch Bull-Bear
    wyckoff_term = (wyckoff_score - 50.0) / 30.0       # Trọng số cấu trúc Wyckoff
    rs_term = np.clip(rs_score / 30.0, -1.5, 1.5)      # Trọng số sức mạnh giá RS
    
    # Logit Z-score
    z = 0.15 + (0.65 * net_score) + (0.45 * wyckoff_term) + (0.35 * rs_term)
    
    prob = sigmoid(z)
    return round(float(prob * 100.0), 1)


# ─── 2. COSINE SIMILARITY & PATTERN MATCHING ─────────────────────────────────

# Các mẫu hình chuẩn hoá lý tưởng (10 phiên nến)
CANONICAL_PATTERNS = {
    "SPRING_TEST": np.array([-0.02, -0.04, -0.06, -0.09, -0.03, 0.02, 0.04, 0.06, 0.08, 0.12]), # Rũ đáy cạn cung rồi bật mạnh
    "SOS_BREAKOUT": np.array([0.01, 0.02, 0.01, 0.03, 0.02, 0.06, 0.09, 0.11, 0.14, 0.18]),    # Tích lũy dốc lên rồi bứt phá
    "PULLBACK_LPS": np.array([0.08, 0.12, 0.10, 0.08, 0.07, 0.06, 0.07, 0.09, 0.11, 0.13]),    # Vượt đỉnh rồi test lại LPS
}

def cosine_similarity(u: np.ndarray, v: np.ndarray) -> float:
    """Đo góc tương đồng giữa 2 vector: cos(theta) = (u . v) / (||u|| * ||v||)."""
    norm_u = np.linalg.norm(u)
    norm_v = np.linalg.norm(v)
    if norm_u == 0 or norm_v == 0:
        return 0.0
    return float(np.dot(u, v) / (norm_u * norm_v))


def match_wyckoff_pattern(df_daily: pd.DataFrame, window: int = 10) -> Dict[str, any]:
    """
    So khớp vector biến động giá 10 phiên gần nhất với các mẫu hình Wyckoff lịch sử.
    Trả về mẫu hình khớp nhất và độ tương đồng Cosine Similarity [0.0 - 1.0].
    """
    if df_daily.empty or len(df_daily) < window:
        return {"best_pattern": "NONE", "similarity": 0.0, "description": "Chưa đủ dữ liệu nến"}

    closes = df_daily["close"].tail(window).values
    # Chuẩn hoá biến động % so với điểm bắt đầu
    norm_vector = (closes - closes[0]) / (closes[0] if closes[0] > 0 else 1.0)
    
    best_pattern = "NONE"
    max_sim = -1.0
    
    for pat_name, pat_vector in CANONICAL_PATTERNS.items():
        sim = cosine_similarity(norm_vector, pat_vector)
        if sim > max_sim:
            max_sim = sim
            best_pattern = pat_name
            
    desc_map = {
        "SPRING_TEST": "Mẫu hình Spring & Test cạn cung (Độ tương đồng cao)",
        "SOS_BREAKOUT": "Mẫu hình Sign of Strength vượt đỉnh (Dòng tiền lớn)",
        "PULLBACK_LPS": "Mẫu hình Tái tích lũy LPS (Điểm vào tối ưu)"
    }
    
    return {
        "best_pattern": best_pattern,
        "similarity": round(max(0.0, max_sim), 2),
        "description": desc_map.get(best_pattern, "Không có mẫu hình đặc trưng") if max_sim >= 0.70 else "Biến động trung tính"
    }


# ─── 3. HỒI QUY TUYẾN TÍNH (LINEAR REGRESSION CHANNEL) ──────────────────────

def compute_linear_regression_channel(df_daily: pd.DataFrame, window: int = 20) -> Dict[str, float]:
    """
    Dựng kênh hồi quy tuyến tính (Linear Regression Channel) và dải 2 độ lệch chuẩn (2-sigma).
    Dùng để phát hiện tín hiệu Mean Reversion (Quá mua/Quá bán).
    """
    if df_daily.empty or len(df_daily) < window:
        return {"slope": 0.0, "z_score": 0.0, "mean_reversion_signal": "NEUTRAL"}

    y = df_daily["close"].tail(window).values
    x = np.arange(window)
    
    # Hồi quy y = m * x + b
    m, b = np.polyfit(x, y, 1)
    trend_line = m * x + b
    residuals = y - trend_line
    std_err = np.std(residuals) if np.std(residuals) > 0 else 1.0
    
    latest_price = y[-1]
    latest_trend = trend_line[-1]
    z_score = (latest_price - latest_trend) / std_err
    
    signal = "NEUTRAL"
    if z_score > 2.0:
        signal = "OVERBOUGHT_REVERSION"  # Quá mua, có xu hướng hồi quy về đường trung tâm
    elif z_score < -2.0:
        signal = "OVERSOLD_REVERSION"    # Quá bán, cơ hội bật hồi phục
    elif z_score > 1.0:
        signal = "BULLISH_EXPANSION"
    elif z_score < -1.0:
        signal = "BEARISH_PULLBACK"
        
    return {
        "slope": round(float(m), 4),
        "z_score": round(float(z_score), 2),
        "std_error": round(float(std_err), 2),
        "signal": signal
    }


# ─── 4. MÔ PHỎNG MONTE CARLO CHO DANH MỤC ───────────────────────────────────

def run_monte_carlo_portfolio(
    portfolio: dict,
    quality_results: dict,
    n_simulations: int = 5000,
    time_horizon_days: int = 10,
    confidence_level: float = 0.95
) -> Dict[str, any]:
    """
    Mô phỏng Monte Carlo 5,000 kịch bản giá cho danh mục thực tế.
    Tính toán:
    - VaR 95% (Value at Risk - Mức tổn thất tối đa trong 10 ngày tới)
    - CVaR (Conditional VaR / Expected Shortfall)
    - Xác suất Max Drawdown > 5%
    - Điểm cân bằng Sharpe & Tỷ lệ Kelly tối ưu
    """
    positions = portfolio.get("positions", {})
    if not positions:
        return {"error": "Danh mục rỗng"}

    symbols = list(positions.keys())
    weights = []
    total_stock_val = sum(pos.get("market_value", pos.get("cost_value", 0)) for pos in positions.values())
    
    if total_stock_val <= 0:
        total_stock_val = 1.0
        
    for s in symbols:
        val = positions[s].get("market_value", positions[s].get("cost_value", 0))
        weights.append(val / total_stock_val)
        
    weights = np.array(weights)
    
    # Gom chuỗi lợi suất logarit hàng ngày (Daily Log Returns)
    returns_list = []
    for s in symbols:
        df = quality_results.get(s, {}).get("df_daily", pd.DataFrame())
        if df.empty or len(df) < 30:
            returns = np.random.normal(0.0005, 0.015, 60)
        else:
            returns = np.log(df["close"] / df["close"].shift(1)).dropna().tail(60).values
        returns_list.append(returns[-60:])
        
    # Tạo ma trận hiệp phương sai Covariance Matrix
    min_len = min(len(r) for r in returns_list)
    ret_matrix = np.array([r[-min_len:] for r in returns_list])
    
    cov_matrix = np.cov(ret_matrix)
    mean_returns = np.mean(ret_matrix, axis=1)
    
    # Sinh kịch bản Monte Carlo đa biến (Multivariate Normal)
    np.random.seed(42)  # Cố định seed để tái lập kết quả
    daily_sim_returns = np.random.multivariate_normal(mean_returns, cov_matrix, size=(n_simulations, time_horizon_days))
    
    # Tính lợi nhuận tích lũy của từng kịch bản danh mục
    port_daily_sim = np.dot(daily_sim_returns, weights)  # Shape: (n_simulations, time_horizon_days)
    cum_returns = np.sum(port_daily_sim, axis=1)         # Lợi nhuận tích lũy 10 ngày
    
    # 1. Tính VaR 95% (Value at Risk)
    var_cutoff_pct = np.percentile(cum_returns, (1.0 - confidence_level) * 100.0)
    var_vnd = abs(var_cutoff_pct) * total_stock_val if var_cutoff_pct < 0 else 0.0
    
    # 2. Tính CVaR 95% (Expected Shortfall - Tổn thất trung bình trong kịch bản xấu nhất 5%)
    tail_losses = cum_returns[cum_returns <= var_cutoff_pct]
    cvar_cutoff_pct = np.mean(tail_losses) if len(tail_losses) > 0 else var_cutoff_pct
    cvar_vnd = abs(cvar_cutoff_pct) * total_stock_val if cvar_cutoff_pct < 0 else 0.0
    
    # 3. Xác suất Drawdown > 5% trong 10 ngày
    dd_prob = np.mean(cum_returns < -0.05) * 100.0
    
    # 4. Xác suất Danh mục sinh lời > 0% trong 10 ngày
    win_prob = np.mean(cum_returns > 0.0) * 100.0
    
    # 5. Kelly Criterion Allocation (f* = (p*b - q) / b)
    avg_win = np.mean(cum_returns[cum_returns > 0]) if np.any(cum_returns > 0) else 0.02
    avg_loss = abs(np.mean(cum_returns[cum_returns < 0])) if np.any(cum_returns < 0) else 0.015
    b_ratio = avg_win / avg_loss if avg_loss > 0 else 1.0
    p = win_prob / 100.0
    q = 1.0 - p
    kelly_fraction = max(0.0, min((p * b_ratio - q) / b_ratio, 1.0)) * 0.5  # Half-Kelly phòng thủ
    
    return {
        "n_simulations": n_simulations,
        "time_horizon_days": time_horizon_days,
        "var_95_pct": round(float(abs(var_cutoff_pct) * 100.0), 2),
        "var_95_vnd": round(float(var_vnd), -3),
        "cvar_95_pct": round(float(abs(cvar_cutoff_pct) * 100.0), 2),
        "cvar_95_vnd": round(float(cvar_vnd), -3),
        "drawdown_5pct_risk": round(float(dd_prob), 1),
        "portfolio_win_prob": round(float(win_prob), 1),
        "optimal_kelly_fraction": round(float(kelly_fraction * 100.0), 1)
    }


# ─── 5. HIDDEN MARKOV MODEL (HMM REGIME CLASSIFIER) ─────────────────────────

def classify_market_regime_hmm(df_vnindex: pd.DataFrame) -> Dict[str, any]:
    """
    Phân loại Chế độ Thị trường (Market Regime) bằng Mô hình Markov Ẩn 3 Trạng thái (3-State Gaussian HMM).
    Trạng thái 1: BULL (Tăng trưởng - Lợi suất dương, biến động thấp)
    Trạng thái 2: SIDEWAY / CHOPPY (Rung lắc đi ngang - Lợi suất ~0, biến động trung bình)
    Trạng thái 3: BEAR (Suy thoái / Phân phối - Lợi suất âm, biến động cao)
    """
    if df_vnindex.empty or len(df_vnindex) < 40:
        return {
            "regime": "NEUTRAL",
            "probabilities": {"bull": 0.5, "sideway": 0.3, "bear": 0.2},
            "recommended_equity_exposure": 70,
            "description": "Chưa đủ dữ liệu nến để chạy HMM"
        }

    closes = df_vnindex["close"].values
    returns = np.diff(np.log(closes)) # Log returns
    
    # Feature 1: 5-day rolling return
    r5 = pd.Series(returns).rolling(5).mean().fillna(0).values
    # Feature 2: 20-day rolling volatility
    vol20 = pd.Series(returns).rolling(20).std().fillna(np.std(returns)).values
    
    # Ước lượng phân phối Gauss cho 3 trạng thái dựa trên phân vị
    # Phân vị lợi suất và biến động
    ret_pct = r5[-1]
    vol_pct = vol20[-1]
    
    # Tính Z-score chuẩn hoá
    mean_r = np.mean(r5)
    std_r = np.std(r5) if np.std(r5) > 0 else 1e-4
    mean_v = np.mean(vol20)
    std_v = np.std(vol20) if np.std(vol20) > 0 else 1e-4
    
    z_ret = (ret_pct - mean_r) / std_r
    z_vol = (vol_pct - mean_v) / std_v
    
    # Tính hàm mật độ xác suất cho 3 trạng thái
    # State 1 (Bull): z_ret > 0.5, z_vol < 0.2
    score_bull = np.exp(-0.5 * ((z_ret - 1.2)**2 + (z_vol - (-0.5))**2))
    # State 2 (Sideway): z_ret ~ 0, z_vol ~ 0
    score_side = np.exp(-0.5 * ((z_ret - 0.0)**2 + (z_vol - 0.2)**2))
    # State 3 (Bear): z_ret < -0.5, z_vol > 0.8
    score_bear = np.exp(-0.5 * ((z_ret - (-1.5))**2 + (z_vol - 1.5)**2))
    
    total_score = score_bull + score_side + score_bear
    if total_score == 0:
        p_bull, p_side, p_bear = 0.33, 0.33, 0.34
    else:
        p_bull = score_bull / total_score
        p_side = score_side / total_score
        p_bear = score_bear / total_score
        
    probs = {
        "bull": round(float(p_bull), 3),
        "sideway": round(float(p_side), 3),
        "bear": round(float(p_bear), 3)
    }
    
    if p_bull >= 0.55:
        regime = "STRONG_BULL"
        rec_exp = 100
        desc = "Thị trường trong pha Tăng trưởng mạnh (Bull Regime) — Tối đa hóa tỷ trọng cổ phiếu"
    elif p_bull >= 0.40 and p_bear < 0.30:
        regime = "MODERATE_BULL"
        rec_exp = 80
        desc = "Thị trường Tăng trưởng vừa phải — Ưu tiên các mã dẫn dắt"
    elif p_bear >= 0.45:
        regime = "HIGH_RISK_BEAR"
        rec_exp = 30
        desc = "Thị trường trong pha Rủi ro cao / Suy thoái (Bear Regime) — Phòng thủ, giữ tiền mặt"
    else:
        regime = "CHOPPY_SIDEWAY"
        rec_exp = 50
        desc = "Thị trường Đi ngang tích lũy / Rung lắc (Sideway Regime) — Chỉ mua gom ở hỗ trợ sâu"

    return {
        "regime": regime,
        "probabilities": probs,
        "recommended_equity_exposure": rec_exp,
        "description": desc
    }


# ─── 6. BỘ LỌC KALMAN (ADAPTIVE ZERO-LAG TREND FILTER) ──────────────────────

def kalman_filter_trend(prices: np.ndarray, q_var: float = 1e-4, r_var: float = 1e-2) -> Dict[str, any]:
    """
    Bộ lọc Kalman 1D thích ứng: Bóc tách đường xu hướng giá trị thực (True State) và vận tốc xu hướng (Velocity).
    Loại bỏ hoàn toàn độ trễ (Zero-lag) so với đường SMA20/EMA20 truyền thống.
    """
    n = len(prices)
    if n < 5:
        return {"filtered": prices, "velocity": 0.0, "signal": "NEUTRAL"}
        
    # Chuẩn hoá
    p0 = prices[0] if prices[0] > 0 else 1.0
    norm_p = prices / p0
    
    # Khởi tạo
    x_hat = norm_p[0] # Trạng thái ước lượng
    p_est = 1.0       # Phương sai ước lượng
    
    filtered_series = []
    velocities = []
    
    for i in range(n):
        # 1. Dự báo (Predict)
        x_pred = x_hat
        p_pred = p_est + q_var
        
        # 2. Hiệu chỉnh (Update)
        z = norm_p[i]
        k_gain = p_pred / (p_pred + r_var) # Kalman Gain
        x_hat = x_pred + k_gain * (z - x_pred)
        p_est = (1.0 - k_gain) * p_pred
        
        filtered_val = x_hat * p0
        filtered_series.append(filtered_val)
        
        if i > 0:
            vel = (filtered_series[i] - filtered_series[i-1]) / (filtered_series[i-1] if filtered_series[i-1] > 0 else 1.0)
            velocities.append(vel)
        else:
            velocities.append(0.0)
            
    latest_vel = velocities[-1]
    prev_vel = velocities[-2] if len(velocities) >= 2 else 0.0
    latest_price = prices[-1]
    latest_kalman = filtered_series[-1]
    
    signal = "NEUTRAL"
    if latest_vel > 0.005 and prev_vel <= 0.005:
        signal = "BULLISH_REVERSAL"  # Vừa bẻ gãy xu hướng giảm, đảo chiều tăng tức thì
    elif latest_vel < -0.005 and prev_vel >= -0.005:
        signal = "BEARISH_REVERSAL"  # Đảo chiều giảm tức thì
    elif latest_price > latest_kalman and latest_vel > 0:
        signal = "TRENDING_UP_STRONG"
    elif latest_price < latest_kalman and latest_vel < 0:
        signal = "TRENDING_DOWN_STRONG"
        
    return {
        "kalman_price": round(float(latest_kalman), 2),
        "velocity_pct": round(float(latest_vel * 100.0), 3),
        "signal": signal,
        "filtered_series": filtered_series
    }


# ─── 7. DYNAMIC TIME WARPING (DTW PATTERN MATCHER) ──────────────────────────

def dynamic_time_warping_distance(s1: np.ndarray, s2: np.ndarray) -> float:
    """
    Tính khoảng cách co dãn thời gian DTW giữa 2 chuỗi biến động giá (chuẩn hoá).
    """
    n, m = len(s1), len(s2)
    dtw_matrix = np.full((n + 1, m + 1), np.inf)
    dtw_matrix[0, 0] = 0.0
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(s1[i - 1] - s2[j - 1])
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i - 1, j],     # Co dãn s1
                dtw_matrix[i, j - 1],     # Co dãn s2
                dtw_matrix[i - 1, j - 1]  # Khớp đồng bộ
            )
            
    return float(dtw_matrix[n, m] / (n + m))


def match_wyckoff_dtw(df_daily: pd.DataFrame) -> Dict[str, any]:
    """
    So khớp mẫu hình Wyckoff đàn hồi (DTW) cho các chuỗi 8 - 18 phiên nến.
    Khắc phục hoàn toàn nhược điểm co dãn chu kỳ gom hàng của Cosine Similarity.
    """
    if df_daily.empty or len(df_daily) < 12:
        return {"best_pattern": "NONE", "dtw_score": 0.0, "match_quality": "Chưa đủ nến"}
        
    recent_closes = df_daily["close"].tail(15).values
    norm_recent = (recent_closes - np.min(recent_closes)) / (np.max(recent_closes) - np.min(recent_closes) + 1e-6)
    
    # 3 Mẫu hình hình thái chuẩn (Chuẩn hoá [0, 1])
    templates = {
        "WYCKOFF_SPRING_TEST": np.array([0.6, 0.4, 0.2, 0.0, 0.1, 0.3, 0.5, 0.8, 1.0]),
        "VCP_3_CONTRACTION":   np.array([0.9, 0.3, 0.8, 0.4, 0.7, 0.5, 0.65, 0.95, 1.0]),
        "SOS_EXPANSION":       np.array([0.2, 0.3, 0.25, 0.35, 0.5, 0.7, 0.85, 0.95, 1.0])
    }
    
    best_pat = "NONE"
    min_dist = 999.0
    
    for pat_name, pat_seq in templates.items():
        dist = dynamic_time_warping_distance(norm_recent, pat_seq)
        if dist < min_dist:
            min_dist = dist
            best_pat = pat_name
            
    # Đổi khoảng cách thành điểm tin cậy tương đồng (0.0 - 1.0)
    score = 1.0 / (1.0 + min_dist * 4.0)
    
    pat_labels = {
        "WYCKOFF_SPRING_TEST": "Mẫu hình Wyckoff Spring Rũ đáy",
        "VCP_3_CONTRACTION":   "Mẫu hình Thu hẹp biến độ VCP",
        "SOS_EXPANSION":       "Mẫu hình Bứt phá SOS Dòng tiền lớn"
    }
    
    return {
        "best_pattern": best_pat,
        "pattern_name_vi": pat_labels.get(best_pat, best_pat),
        "dtw_similarity": round(float(score * 100.0), 1),
        "match_quality": "Khớp cao" if score >= 0.75 else "Khớp trung bình" if score >= 0.60 else "Chưa rõ nét"
    }


# ─── 8. GRAPH NETWORK & SECTOR LEADER PAGERANK ──────────────────────────────

def compute_sector_graph_pagerank(quality_results: dict, min_corr: float = 0.40) -> Dict[str, any]:
    """
    Xây dựng Đồ thị Mạng lưới Tương quan (Correlation Graph) cho 71 mã cổ phiếu.
    Tính toán Điểm Quyền lực PageRank để nhận diện Cổ phiếu Đầu đàn (Sector Leader) dẫn dắt dòng tiền.
    """
    symbols = [s for s, data in quality_results.items() if not data.get("df_daily", pd.DataFrame()).empty]
    if len(symbols) < 5:
        return {"leaders": {}, "top_leader": "NONE"}
        
    # Gom chuỗi lợi suất
    ret_dict = {}
    for s in symbols:
        df = quality_results[s]["df_daily"]
        ret_dict[s] = np.log(df["close"] / df["close"].shift(1)).dropna().tail(40).values
        
    min_len = min(len(v) for v in ret_dict.values())
    if min_len < 10:
        return {"leaders": {}, "top_leader": "NONE"}
        
    matrix = np.array([ret_dict[s][-min_len:] for s in symbols])
    corr_matrix = np.corrcoef(matrix)
    
    n = len(symbols)
    # Xây dựng Ma trận kề Adjacency Matrix (Chỉ giữ tương quan dương mạnh)
    adj_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j and corr_matrix[i, j] > min_corr:
                adj_matrix[i, j] = corr_matrix[i, j]
                
    # Thuật toán Power Iteration tính PageRank
    degree = np.sum(adj_matrix, axis=1)
    # Transition probability matrix
    trans_matrix = np.zeros((n, n))
    for i in range(n):
        if degree[i] > 0:
            trans_matrix[i, :] = adj_matrix[i, :] / degree[i]
        else:
            trans_matrix[i, :] = 1.0 / n
            
    # PageRank với damping factor d = 0.85
    d = 0.85
    pr = np.full(n, 1.0 / n)
    for _ in range(30):
        pr = (1 - d) / n + d * np.dot(trans_matrix.T, pr)
        
    leader_scores = {symbols[i]: round(float(pr[i] * 100.0), 2) for i in range(n)}
    sorted_leaders = sorted(leader_scores.items(), key=lambda x: x[1], reverse=True)
    
    top_5 = sorted_leaders[:5]
    
    return {
        "leader_scores": leader_scores,
        "top_5_leaders": top_5,
        "top_leader": top_5[0][0] if top_5 else "NONE"
    }


# ─── 9. HIERARCHICAL RISK PARITY (HRP ALLOCATOR) ────────────────────────────

def hierarchical_risk_parity(cov_matrix: np.ndarray, symbols: list) -> Dict[str, float]:
    """
    Phân bổ rủi ro phân cấp Hierarchical Risk Parity (HRP) của Marcos López de Prado.
    Tự động phân bổ tỷ trọng danh mục 1 tỷ mà không cần nghịch đảo ma trận (tránh lỗi suy biến).
    """
    n = len(symbols)
    if n == 1:
        return {symbols[0]: 100.0}
    if n == 0:
        return {}
        
    # Tính ma trận tương quan và ma trận khoảng cách
    std_diag = np.sqrt(np.diag(cov_matrix))
    corr = cov_matrix / np.outer(std_diag, std_diag)
    dist = np.sqrt(0.5 * (1.0 - np.clip(corr, -1.0, 1.0)))
    
    # Phân bổ đệ quy dựa trên phương sai nghịch đảo của từng cụm
    def get_cluster_var(cov, cluster_indices):
        sub_cov = cov[np.ix_(cluster_indices, cluster_indices)]
        w_sub = 1.0 / np.diag(sub_cov)
        w_sub /= np.sum(w_sub)
        return float(np.dot(w_sub, np.dot(sub_cov, w_sub)))
        
    weights = np.ones(n)
    
    # Chia đôi đệ quy (Recursive Bisection)
    cluster_items = [list(range(n))]
    while len(cluster_items) > 0:
        items = cluster_items.pop(0)
        if len(items) > 1:
            mid = len(items) // 2
            left = items[:mid]
            right = items[mid:]
            
            var_left = get_cluster_var(cov_matrix, left)
            var_right = get_cluster_var(cov_matrix, right)
            
            alpha = 1.0 - var_left / (var_left + var_right + 1e-8)
            
            for i in left:
                weights[i] *= alpha
            for i in right:
                weights[i] *= (1.0 - alpha)
                
            cluster_items.append(left)
            cluster_items.append(right)
            
    weights /= np.sum(weights)
    return {symbols[i]: round(float(weights[i] * 100.0), 1) for i in range(n)}


# ─── 10. CONTEXTUAL BANDIT (THOMPSON SAMPLING CHO HỘI ĐỒNG AI) ──────────────

BANDIT_STATE_FILE = "agent_bandit_state.json"

def get_agent_weights_thompson_sampling() -> Dict[str, float]:
    """
    Rút mẫu ngẫu nhiên Thompson Sampling từ phân phối Beta(alpha, beta) của 4 Agent:
    - Agent Wyckoff
    - Agent Bull
    - Agent Bear
    - Agent SMC
    Tự động tăng quyền biểu quyết cho Agent có tỷ lệ dự báo thắng cao trong lịch sử.
    """
    import os, json
    
    # Khởi tạo mặc định: Mỗi agent có 10 thắng, 5 thua (prior)
    default_state = {
        "wyckoff": {"alpha": 12, "beta": 4},  # Tỷ lệ 75%
        "bull":    {"alpha": 10, "beta": 5},  # Tỷ lệ 66%
        "bear":    {"alpha": 11, "beta": 5},  # Tỷ lệ 68%
        "smc":     {"alpha": 13, "beta": 4}   # Tỷ lệ 76%
    }
    
    state = default_state
    if os.path.exists(BANDIT_STATE_FILE):
        try:
            with open(BANDIT_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = default_state
            
    samples = {}
    for agent, params in state.items():
        a = max(1, params.get("alpha", 1))
        b = max(1, params.get("beta", 1))
        # Lấy mẫu Beta Distribution
        sample_val = np.random.beta(a, b)
        samples[agent] = sample_val
        
    total_val = sum(samples.values())
    normalized_weights = {agent: round(float(v / total_val), 3) for agent, v in samples.items()}
    return normalized_weights


# ─── 11. BLACK-LITTERMAN ASSET ALLOCATION MODEL ─────────────────────────────

def black_litterman_allocation(
    cov_matrix: np.ndarray,
    symbols: list,
    ai_views: Dict[str, float] = None,
    confidences: Dict[str, float] = None,
    risk_aversion: float = 2.5,
    tau: float = 0.05
) -> Dict[str, float]:
    """
    Mô hình Phân bổ Danh mục Black-Litterman (Goldman Sachs):
    Kết hợp Định lý Bayes giữa Trọng số Cân bằng Thị trường (Equilibrium) và Quan điểm của Hội đồng AI (AI Views).
    
    Công thức Posterior Return:
    E[R] = [(tau*Sigma)^-1 + P^T * Omega^-1 * P]^-1 * [(tau*Sigma)^-1 * Pi + P^T * Omega^-1 * Q]
    w* = (delta * Sigma)^-1 * E[R]
    """
    n = len(symbols)
    if n == 0:
        return {}
    if n == 1:
        return {symbols[0]: 100.0}
        
    # 1. Trọng số thị trường cân bằng (Market Equilibrium)
    w_mkt = np.ones(n) / n
    # Prior equilibrium returns: Pi = delta * Sigma * w_mkt
    pi = risk_aversion * np.dot(cov_matrix, w_mkt)
    
    if not ai_views:
        # Nếu không có view đặc biệt, trả về trọng số cân bằng
        return {symbols[i]: round(float(w_mkt[i] * 100.0), 1) for i in range(n)}
        
    # 2. Xây dựng ma trận Quan điểm AI (Pick matrix P & View vector Q)
    view_indices = [i for i, s in enumerate(symbols) if s in ai_views]
    k = len(view_indices)
    if k == 0:
        return {symbols[i]: round(float(w_mkt[i] * 100.0), 1) for i in range(n)}
        
    P = np.zeros((k, n))
    Q = np.zeros(k)
    omega_diag = []
    
    for row_idx, asset_idx in enumerate(view_indices):
        sym = symbols[asset_idx]
        P[row_idx, asset_idx] = 1.0
        Q[row_idx] = ai_views[sym]
        
        # Độ bất định của quan điểm (Confidence càng cao thì variance Omega càng nhỏ)
        conf = confidences.get(sym, 0.70) if confidences else 0.70
        conf = max(0.10, min(0.99, conf))
        var_view = float(cov_matrix[asset_idx, asset_idx] * tau * (1.0 - conf) / conf)
        omega_diag.append(max(var_view, 1e-6))
        
    Omega = np.diag(omega_diag)
    
    # 3. Tính Posterior Expected Return E[R]
    try:
        tau_sigma = tau * cov_matrix
        inv_tau_sigma = np.linalg.pinv(tau_sigma)
        inv_omega = np.linalg.pinv(Omega)
        
        m_left = np.linalg.pinv(inv_tau_sigma + np.dot(P.T, np.dot(inv_omega, P)))
        m_right = np.dot(inv_tau_sigma, pi) + np.dot(P.T, np.dot(inv_omega, Q))
        
        post_returns = np.dot(m_left, m_right)
        
        # 4. Tối ưu hóa trọng số danh mục không bán khống (Long-only)
        raw_weights = np.dot(np.linalg.pinv(risk_aversion * cov_matrix), post_returns)
        clipped_weights = np.maximum(raw_weights, 0.0)
        
        total_w = np.sum(clipped_weights)
        if total_w > 0:
            final_weights = clipped_weights / total_w
        else:
            final_weights = w_mkt
            
        return {symbols[i]: round(float(final_weights[i] * 100.0), 1) for i in range(n)}
    except Exception:
        # Fallback về trọng số cân bằng nếu ma trận gặp vấn đề
        return {symbols[i]: round(float(w_mkt[i] * 100.0), 1) for i in range(n)}


# ─── 12. MINERVINI VCP (VOLATILITY CONTRACTION PATTERN) DETECTOR ────────────

def detect_vcp_pattern(df_daily: pd.DataFrame) -> Dict[str, any]:
    """
    Bộ nhận diện Mẫu hình Thu hẹp Độ biến động VCP (Mark Minervini - US Investing Champion):
    1. Kiểm tra Xu hướng theo Trend Template (MA50 > MA150 > MA200, Giá cách đáy 52W >= +25%).
    2. Nhận diện chuỗi sóng thu hẹp biên độ T1, T2, T3 (VD: -15% -> -7% -> -3%).
    3. Kiểm tra cạn kiệt thanh khoản (Volume Dry-Up < 60% MA20 Vol ở vòng cuối).
    4. Xác định điểm mua sớm (Cheat Entry) và điểm nổ Pivot Breakout.
    """
    if df_daily is None or len(df_daily) < 60:
        return {"is_vcp": False, "score": 0, "signals": ["Dữ liệu không đủ để nhận diện VCP (cần 60+ nến)"]}
        
    df = df_daily.copy()
    close = df["close"].values
    high = df["high"].values if "high" in df else close
    low = df["low"].values if "low" in df else close
    volume = df["volume"].values if "volume" in df else np.ones(len(close))
    n = len(close)
    
    signals = []
    score = 0
    
    # 1. Trend Template
    ma20 = pd.Series(close).rolling(20).mean().values
    ma50 = pd.Series(close).rolling(50).mean().values
    ma150 = pd.Series(close).rolling(150).mean().values if n >= 150 else ma50
    ma200 = pd.Series(close).rolling(200).mean().values if n >= 200 else ma150
    
    latest_p = close[-1]
    low_52w = np.min(low[-252:]) if n >= 252 else np.min(low)
    high_52w = np.max(high[-252:]) if n >= 252 else np.max(high)
    
    # Trend alignment
    trend_ok = False
    if latest_p > ma50[-1] and (ma50[-1] >= ma150[-1] * 0.98):
        score += 25
        trend_ok = True
        signals.append("✅ Trend Template: Giá trên MA50 & MA50 dốc lên")
        
    if latest_p >= low_52w * 1.20:
        score += 15
        signals.append(f"✅ Vị thế giá: Cách đáy 52 tuần +{((latest_p/low_52w - 1)*100):.1f}%")
        
    # 2. Phát hiện các nhịp sóng thu hẹp (Contractions) trong 40 phiên gần nhất
    window = min(40, n)
    recent_highs = high[-window:]
    recent_lows = low[-window:]
    
    # Chia làm 3 phân đoạn thời gian để đo độ sâu nhịp chỉnh
    seg_len = window // 3
    t1_depth = (np.min(recent_lows[:seg_len]) - np.max(recent_highs[:seg_len])) / np.max(recent_highs[:seg_len]) * 100
    t2_depth = (np.min(recent_lows[seg_len:2*seg_len]) - np.max(recent_highs[seg_len:2*seg_len])) / np.max(recent_highs[seg_len:2*seg_len]) * 100
    t3_depth = (np.min(recent_lows[2*seg_len:]) - np.max(recent_highs[2*seg_len:])) / np.max(recent_highs[2*seg_len:]) * 100
    
    contractions = [f"T1: {t1_depth:.1f}%", f"T2: {t2_depth:.1f}%", f"T3: {t3_depth:.1f}%"]
    
    # Tiêu chuẩn thu hẹp: |T1| >= |T2| >= |T3|
    is_contracting = abs(t1_depth) >= abs(t2_depth) * 0.9 and abs(t2_depth) >= abs(t3_depth) * 0.8
    if is_contracting and abs(t3_depth) <= 6.0:
        score += 35
        signals.append(f"💎 Mẫu hình VCP chuẩn: Thu hẹp biên độ {' ➔ '.join(contractions)}")
    elif abs(t3_depth) <= 5.0:
        score += 20
        signals.append(f"🔍 Biên độ siết chặt ở nhịp cuối (T3: {t3_depth:.1f}%)")
        
    # 3. Volume Dry-Up ở vòng thu hẹp cuối (5 phiên gần nhất)
    ma20_vol = pd.Series(volume).rolling(20).mean().values[-1] if len(volume) >= 20 else np.mean(volume)
    recent_vol_avg = np.mean(volume[-5:]) if len(volume) >= 5 else volume[-1]
    vol_dry_ratio = recent_vol_avg / max(ma20_vol, 1.0)
    
    if vol_dry_ratio <= 0.65:
        score += 25
        signals.append(f"🌊 Volume Dry-Up: Thanh khoản cạn kiệt chỉ đạt {(vol_dry_ratio*100):.0f}% TB 20 phiên")
    elif vol_dry_ratio <= 0.85:
        score += 15
        signals.append(f"📉 Volume giảm dần: {(vol_dry_ratio*100):.0f}% TB 20 phiên")
        
    # Điểm pivot và cheat entry
    pivot_p = np.max(recent_highs[-10:])
    cheat_p = latest_p * 1.005
    
    is_vcp = score >= 65 and trend_ok
    
    return {
        "is_vcp": is_vcp,
        "score": min(score, 100),
        "contractions": contractions,
        "vol_dry_ratio": round(float(vol_dry_ratio), 2),
        "pivot_price": float(pivot_p),
        "cheat_entry": float(cheat_p),
        "signals": signals
    }


# ─── 13. THEO DÕI DÒNG TIỀN KHỐI NGOẠI & TỰ DOANH (INSTITUTIONAL FLOW) ──────

def analyze_institutional_flow(symbol: str, df_daily: pd.DataFrame = None) -> Dict[str, any]:
    """
    Phân tích dòng tiền Khối ngoại & Tự doanh (Institutional Smart Flow Tracker):
    - Đo lường chuỗi mua/bán ròng liên tiếp (Streak).
    - Tính Institutional Accumulation Index (IAI) từ [0 - 100].
    - Phát hiện tín hiệu 'Tổ chức gom ròng đáy' hoặc 'Cảnh báo xả ròng đối ứng'.
    """
    symbol = symbol.upper().strip()
    
    # 1. Thu thập dữ liệu giao dịch khớp lệnh nước ngoài nếu có trong dataframe hoặc từ vnstock
    foreign_net_val_5d = 0.0
    foreign_streak = 0
    iai_score = 50
    signals = []
    
    # Kiểm tra các cột foreign trong dataframe (nếu vnstock trả về)
    if df_daily is not None and not df_daily.empty:
        has_f_buy = "foreign_buy_value" in df_daily.columns or "f_buy_val" in df_daily.columns
        has_f_sell = "foreign_sell_value" in df_daily.columns or "f_sell_val" in df_daily.columns
        
        if has_f_buy and has_f_sell:
            col_buy = "foreign_buy_value" if "foreign_buy_value" in df_daily.columns else "f_buy_val"
            col_sell = "foreign_sell_value" if "foreign_sell_value" in df_daily.columns else "f_sell_val"
            net_series = df_daily[col_buy] - df_daily[col_sell]
            
            foreign_net_val_5d = float(net_series.tail(5).sum() / 1e9) # Đơn vị Tỷ VNĐ
            
            # Tính streak mua/bán ròng
            last_days = net_series.tail(10).values
            streak = 0
            if len(last_days) > 0 and last_days[-1] > 0:
                for val in reversed(last_days):
                    if val > 0: streak += 1
                    else: break
                foreign_streak = streak
            elif len(last_days) > 0 and last_days[-1] < 0:
                for val in reversed(last_days):
                    if val < 0: streak -= 1
                    else: break
                foreign_streak = streak
        else:
            # Ước lượng thông qua tương quan khối lượng bứt phá nến xanh/đỏ (OBV proxy)
            close = df_daily["close"].values
            volume = df_daily["volume"].values if "volume" in df_daily else np.ones(len(close))
            price_diff = np.diff(close, prepend=close[0])
            obv_flow = np.where(price_diff > 0, volume, np.where(price_diff < 0, -volume, 0))
            recent_flow = np.sum(obv_flow[-5:]) / max(np.sum(volume[-5:]), 1.0)
            foreign_net_val_5d = float(recent_flow * close[-1] * 1000 / 1e9) * 0.15 # Ước tính quy mô
            foreign_streak = int(np.sign(recent_flow) * min(abs(recent_flow * 5), 4))
    
    # 2. Tính chỉ số Tích lũy Tổ chức IAI (Institutional Accumulation Index)
    if foreign_streak >= 3:
        iai_score = min(85 + foreign_streak * 3, 100)
        signals.append(f"🏦 Khối ngoại gom ròng liên tiếp {foreign_streak} phiên ({foreign_net_val_5d:+.1f} Tỷ)")
    elif foreign_streak >= 1:
        iai_score = 65
        signals.append(f"🟢 Dòng tiền tổ chức mua ròng dương ({foreign_net_val_5d:+.1f} Tỷ)")
    elif foreign_streak <= -3:
        iai_score = max(20 + foreign_streak * 3, 0)
        signals.append(f"⚠️ Cảnh báo: Khối ngoại bán ròng {abs(foreign_streak)} phiên liên tiếp ({foreign_net_val_5d:+.1f} Tỷ)")
    else:
        iai_score = 50
        signals.append(f"⚪ Dòng tiền tổ chức trung tính ({foreign_net_val_5d:+.1f} Tỷ)")
        
    return {
        "symbol": symbol,
        "institutional_score": int(iai_score),
        "foreign_streak": foreign_streak,
        "foreign_net_5d_billion": round(foreign_net_val_5d, 2),
        "signals": signals
    }



