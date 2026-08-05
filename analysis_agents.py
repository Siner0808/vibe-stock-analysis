import numpy as np
import pandas as pd
from data_collectors import MarketDataPacket

# =====================================================================
# LAYER 2: SPECIALIZED ANALYSIS AGENTS (Tầng Phân tích Chuyên sâu)
# Nhận MarketDataPacket từ DataOrchestrator, không tự gọi API ngoài
# =====================================================================

class TrendAnalysisAgent:
    """
    Agent 1: Phân tích Xu hướng Giá
    - Sử dụng EMA20, SMA50, SMA200 từ TradingView + OHLCV từ VNStock
    - Xác định cấu trúc xu hướng: UPTREND / DOWNTREND / SIDEWAYS
    """
    NAME = "Trend Analysis Agent"

    def analyze(self, packet: MarketDataPacket) -> dict:
        result = {
            "agent": self.NAME,
            "trend": "SIDEWAYS",
            "trend_strength": "YẾU",
            "score": 0.0,
            "signals": [],
            "details": {}
        }
        score = 0
        signals = []

        # ---- Phân tích từ TradingView Indicators ----
        tv = packet.tv_indicators
        ema20 = tv.get("EMA20")
        sma50 = tv.get("SMA50")
        sma200 = tv.get("SMA200")
        adx = tv.get("ADX")

        if ema20 and sma50:
            if ema20 > sma50:
                score += 1.5
                signals.append("✅ EMA20 > SMA50: Xu hướng ngắn hạn tích cực (Golden alignment)")
            else:
                score -= 1.5
                signals.append("⚠️ EMA20 < SMA50: Xu hướng ngắn hạn tiêu cực")

        if sma50 and sma200:
            if sma50 > sma200:
                score += 2.0
                signals.append("✅ SMA50 > SMA200: Xu hướng trung-dài hạn TĂNG (Bull Market)")
            else:
                score -= 2.0
                signals.append("🔴 SMA50 < SMA200: Xu hướng trung-dài hạn GIẢM (Bear Market)")

        if adx:
            if adx > 25:
                signals.append(f"✅ ADX = {adx:.1f} > 25: Xu hướng có lực mạnh")
                result["trend_strength"] = "MẠNH"
            elif adx > 15:
                signals.append(f"🟡 ADX = {adx:.1f}: Xu hướng ở mức trung bình")
                result["trend_strength"] = "TRUNG BÌNH"
            else:
                signals.append(f"⚠️ ADX = {adx:.1f} < 15: Thị trường đang đi ngang, thiếu xu hướng rõ ràng")

        # ---- Phân tích từ OHLCV VNStock ----
        df = packet.ohlcv_df
        if df is not None and len(df) >= 20:
            close = df['close']
            ma10 = close.rolling(10).mean().iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]
            last = close.iloc[-1]

            if last > ma10 > ma20:
                score += 1.5
                signals.append(f"✅ Giá > MA10 > MA20: Cấu trúc giá bullish tích cực")
            elif last < ma10 < ma20:
                score -= 1.5
                signals.append(f"🔴 Giá < MA10 < MA20: Cấu trúc giá bearish")

        # Kết luận xu hướng
        if score >= 3:
            result["trend"] = "UPTREND MẠNH"
        elif score >= 1.5:
            result["trend"] = "UPTREND"
        elif score <= -3:
            result["trend"] = "DOWNTREND MẠNH"
        elif score <= -1.5:
            result["trend"] = "DOWNTREND"
        else:
            result["trend"] = "SIDEWAYS"

        result["score"] = round(score, 2)
        result["signals"] = signals
        result["details"] = {"ema20": ema20, "sma50": sma50, "sma200": sma200, "adx": adx}
        return result


class MomentumAgent:
    """
    Agent 2: Phân tích Động lượng & Sức mạnh Giá
    - Sử dụng RSI, MACD, Stochastic, CCI, Williams %R, Momentum
    - Xác định vùng quá mua/quá bán, tín hiệu đảo chiều sớm
    """
    NAME = "Momentum & Oscillator Agent"

    def analyze(self, packet: MarketDataPacket) -> dict:
        result = {
            "agent": self.NAME,
            "momentum_signal": "NEUTRAL",
            "score": 0.0,
            "signals": [],
            "indicators_summary": {}
        }
        score = 0
        signals = []
        tv = packet.tv_indicators

        # RSI
        rsi = tv.get("RSI")
        if rsi is not None:
            if rsi < 30:
                score += 2.5
                signals.append(f"✅ RSI = {rsi:.1f} - Vùng quá bán nặng (Strong Oversold), tiềm năng bật mạnh")
            elif rsi < 45:
                score += 1.0
                signals.append(f"🟡 RSI = {rsi:.1f} - Vùng yếu nhưng chưa quá bán")
            elif rsi > 75:
                score -= 2.5
                signals.append(f"🔴 RSI = {rsi:.1f} - Vùng quá mua nặng (Strong Overbought), rủi ro điều chỉnh cao")
            elif rsi > 60:
                score -= 1.0
                signals.append(f"🟡 RSI = {rsi:.1f} - Vùng mua tốt nhưng cần thận trọng")
            else:
                signals.append(f"✅ RSI = {rsi:.1f} - Vùng trung tính (40-60), chưa có tín hiệu rõ")

        # MACD
        macd = tv.get("MACD")
        macd_signal = tv.get("MACD_Signal")
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                score += 1.5
                signals.append(f"✅ MACD ({macd:.2f}) > Signal ({macd_signal:.2f}): Động lượng tăng đang tích lũy")
            else:
                score -= 1.5
                signals.append(f"🔴 MACD ({macd:.2f}) < Signal ({macd_signal:.2f}): Động lượng giảm đang thống trị")

        # Stochastic
        stoch_k = tv.get("Stoch_K")
        stoch_d = tv.get("Stoch_D")
        if stoch_k is not None:
            if stoch_k < 20:
                score += 1.5
                signals.append(f"✅ Stoch %K = {stoch_k:.1f} - Quá bán, có thể xem xét mua")
            elif stoch_k > 80:
                score -= 1.5
                signals.append(f"🔴 Stoch %K = {stoch_k:.1f} - Quá mua, cẩn thận điều chỉnh")

        # CCI & Williams %R
        cci = tv.get("CCI20")
        wr = tv.get("Williams_R")
        if cci is not None:
            if cci < -100:
                score += 1.0
                signals.append(f"✅ CCI = {cci:.1f} < -100: Oversold theo CCI")
            elif cci > 100:
                score -= 1.0
                signals.append(f"🔴 CCI = {cci:.1f} > 100: Overbought theo CCI")

        # Kết luận
        if score >= 4:
            result["momentum_signal"] = "STRONG BUY 🟢"
        elif score >= 2:
            result["momentum_signal"] = "BUY 🟢"
        elif score <= -4:
            result["momentum_signal"] = "STRONG SELL 🔴"
        elif score <= -2:
            result["momentum_signal"] = "SELL 🔴"
        else:
            result["momentum_signal"] = "NEUTRAL 🟡"

        result["score"] = round(score, 2)
        result["signals"] = signals
        result["indicators_summary"] = {
            "RSI": rsi, "MACD": macd, "Stoch_K": stoch_k, "CCI20": cci, "Williams_R": wr
        }
        return result


class VolumeAnalysisAgent:
    """
    Agent 3: Phân tích Khối lượng Giao dịch
    - Sử dụng OHLCV từ VNStock
    - Đánh giá sức mạnh đột biến khối lượng, xác nhận xu hướng
    """
    NAME = "Volume Analysis Agent"

    def analyze(self, packet: MarketDataPacket) -> dict:
        result = {
            "agent": self.NAME,
            "volume_signal": "NEUTRAL",
            "score": 0.0,
            "signals": [],
            "stats": {}
        }
        df = packet.ohlcv_df
        if df is None or len(df) < 20:
            result["signals"].append("⚠️ Không đủ dữ liệu khối lượng để phân tích")
            return result

        score = 0
        signals = []
        vol = df['volume']
        close = df['close']

        vol_ma20 = vol.rolling(20).mean()
        vol_ma5 = vol.rolling(5).mean()
        last_vol = vol.iloc[-1]
        last_vol_ma20 = vol_ma20.iloc[-1]
        last_vol_ma5 = vol_ma5.iloc[-1]
        vol_ratio = last_vol / last_vol_ma20 if last_vol_ma20 > 0 else 1.0

        # Phân tích đột biến khối lượng
        if vol_ratio > 2.0:
            signals.append(f"🚀 Khối lượng đột biến: {vol_ratio:.1f}x trung bình 20 phiên - Tín hiệu cực mạnh")
            score += 2.5
        elif vol_ratio > 1.5:
            signals.append(f"✅ Khối lượng cao: {vol_ratio:.1f}x trung bình - Xác nhận tín hiệu")
            score += 1.5
        elif vol_ratio < 0.5:
            signals.append(f"⚠️ Khối lượng thấp: {vol_ratio:.1f}x trung bình - Thiếu xác nhận")
            score -= 1.0

        # Volume MA5 so với MA20 (xu hướng khối lượng ngắn hạn)
        if last_vol_ma5 > last_vol_ma20 * 1.2:
            score += 1.0
            signals.append("✅ MA5 Khối lượng > MA20: Hoạt động giao dịch đang tăng cường")
        elif last_vol_ma5 < last_vol_ma20 * 0.8:
            score -= 0.5
            signals.append("🟡 MA5 Khối lượng < MA20: Thị trường đang trầm lắng")

        # On-Balance Volume (OBV) đơn giản
        df = df.copy()
        df['obv'] = (np.sign(close.diff()) * vol).cumsum()
        obv_trend = df['obv'].iloc[-5:].diff().mean()
        if obv_trend > 0:
            score += 1.0
            signals.append("✅ OBV đang tăng: Dòng tiền đang vào cổ phiếu")
        else:
            score -= 0.5
            signals.append("🔴 OBV đang giảm: Dòng tiền đang rút ra")

        if score >= 3:
            result["volume_signal"] = "STRONG VOLUME CONFIRM 🚀"
        elif score >= 1.5:
            result["volume_signal"] = "VOLUME CONFIRM ✅"
        elif score <= -1.5:
            result["volume_signal"] = "VOLUME WEAK ⚠️"
        else:
            result["volume_signal"] = "NEUTRAL 🟡"

        result["score"] = round(score, 2)
        result["signals"] = signals
        result["stats"] = {
            "last_volume": int(last_vol),
            "avg_vol_20": int(last_vol_ma20),
            "vol_ratio_vs_ma20": round(vol_ratio, 2),
        }
        return result


class SupportResistanceAgent:
    """
    Agent 4: Phân tích Vùng Hỗ trợ & Kháng cự + Bollinger Bands
    - Sử dụng OHLCV + BB_Upper, BB_Lower từ TradingView
    """
    NAME = "Support & Resistance Agent"

    def analyze(self, packet: MarketDataPacket) -> dict:
        result = {
            "agent": self.NAME,
            "position": "NEUTRAL",
            "score": 0.0,
            "signals": [],
            "levels": {}
        }
        df = packet.ohlcv_df
        tv = packet.tv_indicators
        if df is None or len(df) < 20:
            result["signals"].append("⚠️ Không đủ dữ liệu phân tích vùng giá")
            return result

        score = 0
        signals = []
        close = df['close']
        high = df['high']
        low = df['low']
        last_close = close.iloc[-1]

        # Vùng hỗ trợ/kháng cự tính trên TOÀN BỘ kỳ dữ liệu có thật.
        # Nhãn suy ra từ dữ liệu, không ghi cứng "52 tuần" — với cửa sổ 6
        # tháng thì nhãn đó sai, dù con số vẫn đúng.
        from data_quality import period_label, period_span_days
        _label = period_label(period_span_days(df))
        high_period = high.max()
        low_period = low.min()
        pct_from_low = ((last_close - low_period) / (high_period - low_period) * 100
                        if high_period != low_period else 50)

        signals.append(f"📍 Giá hiện tại cách đáy {_label}: {pct_from_low:.1f}%")
        if pct_from_low < 20:
            score += 2.0
            signals.append(f"✅ Gần vùng đáy {_label} - Điểm tích lũy hấp dẫn")
        elif pct_from_low > 80:
            score -= 1.5
            signals.append(f"🔴 Gần vùng đỉnh {_label} - Rủi ro từ vùng kháng cự mạnh")

        # Bollinger Bands từ TradingView
        bb_upper = tv.get("BB_Upper")
        bb_lower = tv.get("BB_Lower")
        if bb_upper and bb_lower and last_close:
            bb_width = bb_upper - bb_lower
            bb_pos = (last_close - bb_lower) / bb_width * 100 if bb_width > 0 else 50

            if bb_pos < 15:
                score += 2.0
                signals.append(f"✅ Giá chạm dải BB Lower ({bb_lower:.2f}): Vùng mua tiềm năng theo BB")
            elif bb_pos > 85:
                score -= 2.0
                signals.append(f"🔴 Giá chạm dải BB Upper ({bb_upper:.2f}): Vùng bán tiềm năng theo BB")
            else:
                signals.append(f"🟡 Giá đang ở giữa dải BB: {bb_pos:.1f}% (Lower: {bb_lower:.2f} / Upper: {bb_upper:.2f})")

        # Pivot Points (tính từ phiên gần nhất)
        last_h = high.iloc[-1]
        last_l = low.iloc[-1]
        last_c = close.iloc[-1]
        pivot = (last_h + last_l + last_c) / 3
        r1 = 2 * pivot - last_l
        s1 = 2 * pivot - last_h
        signals.append(f"📐 Pivot Points: P={pivot:.2f} | R1={r1:.2f} | S1={s1:.2f}")

        result["score"] = round(score, 2)
        result["signals"] = signals
        result["levels"] = {
            "high_period": round(high_period, 2),
            "low_period": round(low_period, 2),
            "period_label": _label,
            "pct_from_low": round(pct_from_low, 2),
            "pivot": round(pivot, 2),
            "resistance_1": round(r1, 2),
            "support_1": round(s1, 2),
            "bb_upper": bb_upper,
            "bb_lower": bb_lower
        }
        if score >= 2:
            result["position"] = "GẦN VÙNG HỖ TRỢ - Cơ hội mua"
        elif score <= -2:
            result["position"] = "GẦN VÙNG KHÁNG CỰ - Thận trọng"
        else:
            result["position"] = "TRUNG GIAN - Quan sát"
        return result


class RiskManagementAgent:
    """
    Agent 5: Quản trị Rủi ro & Sizing
    - Tính toán ATR, Volatility, Sharpe, MaxDD
    - Đề xuất Stop-loss, Take-profit, Tỷ lệ vốn phân bổ
    """
    NAME = "Risk Management Agent"

    def analyze(self, packet: MarketDataPacket) -> dict:
        result = {
            "agent": self.NAME,
            "risk_level": "MEDIUM",
            "risk_score": 50,
            "signals": [],
            "metrics": {},
            "recommendations": {}
        }
        df = packet.ohlcv_df
        tv = packet.tv_indicators
        if df is None or len(df) < 20:
            result["signals"].append("⚠️ Không đủ dữ liệu quản trị rủi ro")
            return result

        df = df.copy()
        close = df['close']
        last_close = close.iloc[-1]

        # Volatility
        daily_ret = close.pct_change().dropna()
        vol_annual = daily_ret.std() * np.sqrt(252) * 100

        # Max Drawdown
        cum_max = close.cummax()
        drawdown = (close - cum_max) / cum_max
        max_dd = abs(drawdown.min()) * 100

        # ATR (Average True Range)
        atr_raw = tv.get("ATR")
        atr_pct = (atr_raw / last_close * 100) if atr_raw else vol_annual / 16

        # Sharpe Ratio (giả định risk-free = 4.5%/năm)
        mean_ret_annual = daily_ret.mean() * 252 * 100
        sharpe = (mean_ret_annual - 4.5) / vol_annual if vol_annual > 0 else 0

        # Risk scoring
        risk_score = 50
        signals = []

        if vol_annual > 40:
            risk_score += 20
            signals.append(f"🔴 Biến động cao: {vol_annual:.1f}%/năm - Rủi ro lớn")
        elif vol_annual > 25:
            risk_score += 10
            signals.append(f"🟡 Biến động trung bình: {vol_annual:.1f}%/năm")
        else:
            risk_score -= 10
            signals.append(f"✅ Biến động thấp: {vol_annual:.1f}%/năm - Ổn định")

        if max_dd > 30:
            risk_score += 15
            signals.append(f"🔴 Max Drawdown lớn: -{max_dd:.1f}%")
        elif max_dd > 15:
            risk_score += 5
            signals.append(f"🟡 Max Drawdown vừa: -{max_dd:.1f}%")
        else:
            signals.append(f"✅ Max Drawdown thấp: -{max_dd:.1f}%")

        if sharpe > 1.5:
            risk_score -= 15
            signals.append(f"✅ Sharpe Ratio cao: {sharpe:.2f} - Hiệu quả sinh lời tốt")
        elif sharpe > 0.5:
            risk_score -= 5
            signals.append(f"🟡 Sharpe Ratio: {sharpe:.2f}")
        else:
            risk_score += 10
            signals.append(f"🔴 Sharpe Ratio thấp: {sharpe:.2f} - Hiệu quả sinh lời kém")

        risk_score = max(10, min(90, risk_score))

        # Recommendations: Tính toán chính xác tỷ lệ Stop-Loss & Take-Profit chuẩn quản trị rủi ro
        # Quy đổi atr_fraction chuẩn phần thập phân (ví dụ: 3.95% -> 0.0395)
        if atr_raw and atr_raw > 0 and last_close > 0:
            atr_fraction = (atr_raw / last_close) if atr_raw < last_close else (atr_raw / (last_close * 1000.0))
        else:
            atr_fraction = (vol_annual / 100.0) / 16.0

        # Kỷ luật Hard Stop-Loss ATR: giới hạn trong khoảng 3% (0.03) đến 8% (0.08)
        sl_fraction = max(0.03, min(0.08, atr_fraction * 2.0))
        tp_fraction = sl_fraction * 2.2 # Risk:Reward Ratio 2.2:1

        from data_quality import price_multiplier
        unit_mult = price_multiplier(df)
        last_close_vnd = last_close * unit_mult

        stop_loss_price = last_close_vnd * (1.0 - sl_fraction)
        take_profit_price = last_close_vnd * (1.0 + tp_fraction)
        position_pct = max(5, min(25, int(100 / risk_score * 10)))

        if risk_score > 70:
            result["risk_level"] = "CAO 🔴"
        elif risk_score > 45:
            result["risk_level"] = "TRUNG BÌNH 🟡"
        else:
            result["risk_level"] = "THẤP ✅"

        result["risk_score"] = risk_score
        result["signals"] = signals
        result["metrics"] = {
            "volatility_annual": round(vol_annual, 2),
            "max_drawdown": round(max_dd, 2),
            "sharpe_ratio": round(sharpe, 2),
            "atr_pct": round(sl_fraction * 50, 2),
        }
        result["recommendations"] = {
            "stop_loss_price": round(stop_loss_price, 0),
            "stop_loss_pct": round(sl_fraction * 100, 1),
            "take_profit_price": round(take_profit_price, 0),
            "take_profit_pct": round(tp_fraction * 100, 1),
            "suggested_position_size_pct": position_pct,
            "risk_reward_ratio": "2.2:1"
        }
        return result
