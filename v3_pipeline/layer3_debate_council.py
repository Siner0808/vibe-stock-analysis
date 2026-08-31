"""
TẦNG 3: HỘI ĐỒNG PHẢN BIỆN 3 CHIỀU
- Bull Agent: Tìm luận điểm tăng giá
- Bear Agent: Phát hiện rủi ro & kịch bản giảm
- Devil's Advocate Agent: Phản biện cả 2 để tìm góc khuất
- Output: consensus_score [0-100] và final_verdict
"""
import pandas as pd
import numpy as np
from typing import Tuple


def bull_agent(symbol: str, wyckoff_result: dict, df_d: pd.DataFrame) -> dict:
    """🐂 Xây dựng luận điểm MUA (Bullish Case)."""
    arguments = []
    score = 0
    
    if df_d.empty or len(df_d) < 20:
        return {"score": 0, "arguments": [], "target_price": None}
    
    close = df_d["close"]
    volume = df_d["volume"]
    latest = close.iloc[-1]
    vol_ma = df_d["vol_ma20"].iloc[-1] if "vol_ma20" in df_d else volume.rolling(20).mean().iloc[-1]
    
    # 1. Luận điểm Wyckoff
    if wyckoff_result.get("score", 0) >= 60:
        score += 25
        arguments.append(f"Wyckoff Score {wyckoff_result['score']}/100 — Cấu trúc tích lũy xác nhận")
    
    if wyckoff_result.get("spring", {}).get("has_spring"):
        score += 20
        arguments.append(f"Spring đã Test cạn nguồn cung — Giá chốt trên vùng hỗ trợ")
    
    if wyckoff_result.get("sos_lps", {}).get("has_sos"):
        score += 15
        arguments.append(f"SOS xác nhận dòng tiền lớn đang hấp thu")
    
    # 2. Luận điểm Volume (Tiền vào)
    if volume.iloc[-3:].mean() > vol_ma * 1.3:
        score += 10
        arguments.append(f"Khối lượng 3 phiên gần nhất > MA20 (Tiền lớn đang gom)")
    
    # 3. Luận điểm Trend
    ma20 = df_d["ma20"].iloc[-1] if "ma20" in df_d else close.rolling(20).mean().iloc[-1]
    ma50 = df_d["ma50"].iloc[-1] if "ma50" in df_d else close.rolling(50).mean().iloc[-1]
    
    if latest > ma20 > ma50:
        score += 15
        arguments.append("Giá > MA20 > MA50 — Xu hướng tăng xác nhận đa khung")
    
    # 4. Momentum (RSI không quá mua)
    rsi = df_d["rsi14"].iloc[-1] if "rsi14" in df_d else 50
    if 40 < rsi < 70:
        score += 10
        arguments.append(f"RSI {rsi:.0f} — Vùng Momentum tốt, chưa quá mua")
    
    # 5. Mục tiêu giá (Target)
    # Chuan hoa gia ve don vi VND (neu can)
    price_vnd = latest * 1000.0 if latest < 500 else float(latest)
    atr_vnd = (df_d["atr14"].iloc[-1] if "atr14" in df_d else latest * 0.015)
    if atr_vnd < 500:
        atr_vnd *= 1000.0
        
    target_price = price_vnd + max(atr_vnd * 4, price_vnd * 0.15)
    
    return {
        "score": min(score, 100),
        "arguments": arguments,
        "target_price": round(target_price, -2),
        "entry_zone": round(price_vnd, -2)
    }


def bear_agent(symbol: str, wyckoff_result: dict, df_d: pd.DataFrame) -> dict:
    """🐻 Xây dựng luận điểm BÁN / KHÔNG MUA (Bearish Case)."""
    arguments = []
    score = 0
    
    if df_d.empty or len(df_d) < 20:
        return {"score": 100, "arguments": ["Không đủ dữ liệu để phân tích"], "risk_price": None}
    
    close = df_d["close"]
    volume = df_d["volume"]
    latest = close.iloc[-1]
    price_vnd = latest * 1000.0 if latest < 500 else float(latest)
    
    # 1. Rủi ro: Giá đã chạy xa (Extended)
    ma20 = df_d["ma20"].iloc[-1] if "ma20" in df_d else close.rolling(20).mean().iloc[-1]
    if latest > ma20 * 1.15:
        score += 25
        arguments.append(f"⚠️ Giá xa MA20 {((latest/ma20-1)*100):.1f}% — Nguy cơ retracement")
    
    # 2. RSI Quá mua
    rsi = df_d["rsi14"].iloc[-1] if "rsi14" in df_d else 50
    if rsi > 70:
        score += 20
        arguments.append(f"⚠️ RSI {rsi:.0f} > 70 — Vùng quá mua, rủi ro điều chỉnh")
    
    # 3. Không có Spring / Bằng chứng Wyckoff yếu
    if wyckoff_result.get("score", 0) < 40:
        score += 20
        arguments.append("⚠️ Wyckoff Score thấp — Chưa có bằng chứng tích lũy rõ ràng")
    
    # 4. Volume giảm trong xu hướng tăng (Divergence)
    recent_vol = volume.tail(5).mean()
    older_vol = volume.tail(20).head(15).mean()
    if recent_vol < older_vol * 0.7 and latest > close.tail(20).iloc[0]:
        score += 15
        arguments.append("⚠️ Giá tăng nhưng Volume phân kỳ giảm — Thiếu Tiền lớn xác nhận")
    
    # 5. Gần vùng kháng cự lịch sử
    high_52w = df_d["high"].tail(252).max() if len(df_d) > 252 else df_d["high"].max()
    high_52w_vnd = high_52w * 1000.0 if high_52w < 500 else high_52w
    if price_vnd > high_52w_vnd * 0.95:
        score += 15
        arguments.append(f"⚠️ Giá gần đỉnh 52 tuần {high_52w_vnd:,.0f}đ — Cung bán tiềm năng")
    
    # Mức stop loss phòng thủ (SL 6% hoặc theo ATR)
    atr_vnd = (df_d["atr14"].iloc[-1] if "atr14" in df_d else latest * 0.015)
    if atr_vnd < 500:
        atr_vnd *= 1000.0
    risk_price = price_vnd - min(atr_vnd * 2.5, price_vnd * 0.06)
    
    return {
        "score": min(score, 100),
        "arguments": arguments,
        "risk_price": round(risk_price, -2),
        "max_loss_pct": round((risk_price / price_vnd - 1) * 100, 2)
    }



def devils_advocate(bull: dict, bear: dict, symbol: str) -> dict:
    """😈 Devil's Advocate: Phân tích các kịch bản không ai muốn nghĩ đến."""
    arguments = []
    
    # 1. Bẫy thanh khoản
    if bull["score"] > 70 and bear["score"] < 30:
        arguments.append("😈 Luận điểm Bull quá áp đảo — Cảnh báo bẫy đồng thuận tâm lý đám đông")
    
    # 2. Môi trường vĩ mô (không dự báo được)
    arguments.append("😈 Tin tức/sự kiện vĩ mô bất ngờ (Fed, chiến tranh thương mại) có thể phủ nhận mọi phân tích kỹ thuật")
    
    # 3. Rủi ro thanh khoản cổ phiếu nhỏ
    arguments.append(f"😈 Nếu cần thoát gấp và KL sụt → Có thể bị kẹt ở {symbol}")
    
    # 4. Vấn đề kế toán / quản trị
    arguments.append("😈 Chưa kiểm tra BCTC Q2/2026 — Có thể có rủi ro ẩn trong Nợ/Margin")
    
    return {"arguments": arguments}


def compute_consensus(bull: dict, bear: dict, wyckoff_score: int = 50, agent_weights: dict = None) -> Tuple[int, str]:
    """Tính điểm đồng thuận cuối cùng có trọng số Thompson Sampling thích ứng."""
    if agent_weights:
        w_bull = agent_weights.get("bull", 0.30)
        w_bear = agent_weights.get("bear", 0.30)
        w_wyck = agent_weights.get("wyckoff", 0.40)
        weighted_score = (bull["score"] * w_bull) - (bear["score"] * w_bear) + ((wyckoff_score - 50) * w_wyck)
        net = weighted_score * 2.0
    else:
        net = bull["score"] - bear["score"]
    
    if net >= 50:
        verdict = "STRONG_BUY"
        consensus = min(net + 50, 100)
    elif net >= 25:
        verdict = "BUY"
        consensus = 60 + net // 2
    elif net >= 0:
        verdict = "WATCH"
        consensus = 50
    elif net >= -25:
        verdict = "HOLD_OFF"
        consensus = 40
    else:
        verdict = "AVOID"
        consensus = max(net + 50, 0)
    
    return int(consensus), verdict


def run_debate_council(wyckoff_results: dict, quality_results: dict) -> dict:
    """Entry point Tầng 3."""
    print(f"\n{'='*60}")
    print(f"⚖️ TẦNG 3: HỘI ĐỒNG PHẢN BIỆN 3 CHIỀU (THOMPSON SAMPLING & SIGMOID)")
    print(f"{'='*60}")
    
    from ml_algorithms import get_agent_weights_thompson_sampling, compute_win_probability
    agent_weights = get_agent_weights_thompson_sampling()
    print(f"  🤖 Trọng số Agent (Thompson Sampling): Bull: {agent_weights['bull']:.2f} | Bear: {agent_weights['bear']:.2f} | Wyckoff: {agent_weights['wyckoff']:.2f}")
    
    debate_results = {}
    valid_symbols = [s for s, r in wyckoff_results.items() if r.get("valid")]
    
    for sym in valid_symbols:
        wyckoff = wyckoff_results[sym]
        df_d = quality_results.get(sym, {}).get("df_daily", pd.DataFrame())
        
        if "ma20" not in df_d.columns and not df_d.empty:
            # Thêm indicators nếu chưa có
            from layer2_wyckoff_engine import compute_indicators
            df_d = compute_indicators(df_d)
        
        bull = bull_agent(sym, wyckoff, df_d)
        bear = bear_agent(sym, wyckoff, df_d)
        devil = devils_advocate(bull, bear, sym)
        consensus, verdict = compute_consensus(bull, bear, wyckoff_score=wyckoff.get("score", 50), agent_weights=agent_weights)
        
        # 🧠 ML Enhancement: Xác suất thắng thực nghiệm qua hàm Sigmoid
        win_prob = compute_win_probability(bull["score"], bear["score"], wyckoff.get("score", 50))
        
        # R:R Ratio
        target = bull.get("target_price")
        risk = bear.get("risk_price")
        entry = bull.get("entry_zone", df_d["close"].iloc[-1] if not df_d.empty else 0)
        rr_ratio = None
        if target and risk and entry:
            reward = target - entry
            risk_amt = entry - risk
            if risk_amt > 0:
                rr_ratio = round(reward / risk_amt, 2)
        
        debate_results[sym] = {
            "symbol": sym,
            "consensus_score": consensus,
            "win_probability": win_prob,
            "verdict": verdict,
            "bull": bull,
            "bear": bear,
            "devil": devil,
            "rr_ratio": rr_ratio,
            "entry_price": entry,
            "target_price": target,
            "stop_loss": risk
        }
        
        verdict_emoji = {"STRONG_BUY": "🟢🟢", "BUY": "🟢", "WATCH": "🟡", "HOLD_OFF": "🟠", "AVOID": "🔴"}.get(verdict, "⚪")
        rr_str = f"R:R {rr_ratio:.1f}" if rr_ratio else "N/A"
        print(f"  {verdict_emoji} {sym:6s} | Bull: {bull['score']:2d} | Bear: {bear['score']:2d} | Consensus: {consensus:3d} (P_win: {win_prob:4.1f}%) | {verdict:12s} | {rr_str}")
    
    strong = [s for s, r in debate_results.items() if r["verdict"] in ["STRONG_BUY", "BUY"]]
    print(f"\n  🎯 Đủ điều kiện vào lệnh: {len(strong)} mã")
    return debate_results
