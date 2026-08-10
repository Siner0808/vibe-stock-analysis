import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

# =====================================================================
# DATA CONTRACT - Chuẩn dữ liệu chuyển giao giữa các Agent
# =====================================================================
@dataclass
class MarketDataPacket:
    """Gói dữ liệu chuẩn hóa được bàn giao giữa các tầng Agent"""
    symbol: str
    exchange: str
    timestamp: str = field(default_factory=lambda: __import__('data_quality').now_vn().isoformat())
    
    # Dữ liệu thô từ VNStock
    ohlcv_df: Optional[pd.DataFrame] = None
    
    # Dữ liệu phân tích kỹ thuật từ TradingView MCP
    tv_summary: dict = field(default_factory=dict)
    tv_indicators: dict = field(default_factory=dict)
    tv_oscillators: str = "NEUTRAL"
    tv_moving_averages: str = "NEUTRAL"
    tv_recommendation: str = "NEUTRAL"
    
    # Tin tức từ NewsOrchestrator (được bàn giao song song)
    news_packet: object = None   # NewsPacket | None

    # Metadata trạng thái
    data_quality: str = "OK"  # OK / PARTIAL / FAILED
    source_notes: list = field(default_factory=list)

# =====================================================================
# LAYER 1: DATA COLLECTION AGENTS (Tầng Thu thập Dữ liệu)
# =====================================================================
class VNStockCollectorAgent:
    """Agent thu thập dữ liệu OHLCV lịch sử từ VNStock (nguồn VCI / TCBS / DNSE)"""
    NAME = "VNStock Collector Agent"

    def _generate_fallback_df(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        dates = pd.date_range(start=start, end=end, freq='B')
        np.random.seed(hash(symbol) % 2**32)
        base_price = 128500.0 if symbol == "FPT" else 28500.0 if symbol == "HPG" else 65400.0
        returns = np.random.normal(0.0005, 0.018, len(dates))
        price_series = base_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'time': dates.strftime('%Y-%m-%d'),
            'open': price_series * (1 - np.random.uniform(0, 0.005, len(dates))),
            'high': price_series * (1 + np.random.uniform(0.002, 0.015, len(dates))),
            'low': price_series * (1 - np.random.uniform(0.002, 0.015, len(dates))),
            'close': price_series,
            'volume': np.random.randint(1000000, 8000000, len(dates))
        })
        return df

    def collect(self, symbol: str, start: str, end: str,
                exchange: str = "HOSE") -> dict:
        """Tải OHLCV và KIỂM ĐỊNH trước khi bàn giao.

        Dữ liệu không qua được kiểm định thì bị coi như không lấy được —
        thử nguồn tiếp theo. Thà thiếu còn hơn sai.
        """
        from data_quality import normalize_ohlcv, validate_ohlcv
        from vnstock import Quote

        last_report = None
        for src in ['vci', 'kbs']:
            try:
                df = Quote(symbol=symbol, source=src).history(start=start, end=end)
            except Exception:
                continue
            if df is None or df.empty:
                continue

            df = normalize_ohlcv(df)
            report = validate_ohlcv(df, symbol=symbol, exchange=exchange)
            last_report = report
            if report.blocked:
                continue          # nguồn này cho dữ liệu hỏng -> thử nguồn khác

            note = f"Tải dữ liệu thành công ({len(df)} phiên từ {src.upper()})"
            if report.warnings:
                note += " · " + report.summary()
            return {"status": "OK", "df": df, "note": note,
                    "quality": report, "source": src}

        if last_report is not None and last_report.blocked:
            return {"status": "FAILED", "df": None,
                    "note": f"Dữ liệu không qua kiểm định: {last_report.summary()}",
                    "quality": last_report, "source": ""}
        # Fallback offline generator: giữ pipeline chạy được để demo/dev,
        # NHƯNG phải báo status SYNTHETIC để tầng trên từ chối ra khuyến nghị.
        # Dữ liệu này là random walk, không phải giá thật.
        fallback_df = self._generate_fallback_df(symbol, start, end)
        return {"status": "SYNTHETIC", "df": fallback_df,
                "note": "⚠️ KHÔNG kết nối được nguồn thật — đang dùng dữ liệu MÔ PHỎNG NGẪU NHIÊN"}


class TradingViewCollectorAgent:
    """Agent thu thập chỉ báo kỹ thuật thời gian thực từ TradingView MCP"""
    NAME = "TradingView MCP Collector Agent"

    def collect(self, symbol: str, exchange: str = "HOSE") -> dict:
        from tradingview_ta import TA_Handler, Interval
        for exc in [exchange, "HNX", "UPCOM"]:
            try:
                handler = TA_Handler(
                    symbol=symbol, exchange=exc,
                    screener="vietnam", interval=Interval.INTERVAL_1_DAY
                )
                analysis = handler.get_analysis()
                return {
                    "status": "OK",
                    "exchange_found": exc,
                    "recommendation": analysis.summary.get("RECOMMENDATION", "NEUTRAL"),
                    "summary": analysis.summary,
                    "oscillators": analysis.oscillators.get("RECOMMENDATION", "NEUTRAL"),
                    "moving_averages": analysis.moving_averages.get("RECOMMENDATION", "NEUTRAL"),
                    "indicators": {
                        "RSI": analysis.indicators.get("RSI"),
                        "MACD": analysis.indicators.get("MACD.macd"),
                        "MACD_Signal": analysis.indicators.get("MACD.signal"),
                        "Stoch_K": analysis.indicators.get("Stoch.K"),
                        "Stoch_D": analysis.indicators.get("Stoch.D"),
                        "EMA20": analysis.indicators.get("EMA20"),
                        "SMA50": analysis.indicators.get("SMA50"),
                        "SMA200": analysis.indicators.get("SMA200"),
                        "ADX": analysis.indicators.get("ADX"),
                        "ATR": analysis.indicators.get("ATR"),
                        "BB_Upper": analysis.indicators.get("BB.upper"),
                        "BB_Lower": analysis.indicators.get("BB.lower"),
                        "CCI20": analysis.indicators.get("CCI20"),
                        "Williams_R": analysis.indicators.get("W.R"),
                        "Mom": analysis.indicators.get("Mom"),
                    },
                    "note": f"Lấy dữ liệu từ sàn {exc}"
                }
            except Exception:
                continue
        return {
            "status": "FAILED", "exchange_found": None,
            "recommendation": "NEUTRAL", "summary": {}, "oscillators": "NEUTRAL",
            "moving_averages": "NEUTRAL", "indicators": {}, "note": "Không kết nối được TradingView"
        }


class DataOrchestrator:
    """
    Điều phối tầng thu thập: nhận dữ liệu từ VNStock, TradingView VÀ
    NewsOrchestrator song song; đóng gói vào MarketDataPacket chuẩn hóa
    để bàn giao cho AnalysisPipeline.
    """
    def __init__(self, symbol: str, start: str, end: str,
                 exchange: str = "HOSE", collect_news: bool = True):
        self.symbol = symbol.upper()
        self.start = start
        self.end = end
        self.exchange = exchange
        self.collect_news = collect_news
        self.vnstock_agent = VNStockCollectorAgent()
        self.tv_agent = TradingViewCollectorAgent()

    def _compute_local_indicators(self, df: pd.DataFrame) -> dict:
        """Tự tính toán các chỉ báo kỹ thuật cốt lõi từ OHLCV để phục vụ backtest."""
        if df is None or len(df) < 20:
            return {}
        
        close = df['close']
        high = df['high']
        low = df['low']
        
        inds = {}
        # MAs
        inds['EMA20'] = close.ewm(span=20, adjust=False).mean().iloc[-1]
        inds['SMA50'] = close.rolling(50).mean().iloc[-1] if len(df) >= 50 else None
        inds['SMA200'] = close.rolling(200).mean().iloc[-1] if len(df) >= 200 else None
        
        # RSI (14)
        delta = close.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        inds['RSI'] = (100 - (100 / (1 + rs))).iloc[-1]
        
        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        inds['MACD'] = macd.iloc[-1]
        inds['MACD_Signal'] = signal.iloc[-1]
        
        # Bollinger Bands (20, 2)
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        inds['BB_Upper'] = (sma20 + 2 * std20).iloc[-1]
        inds['BB_Lower'] = (sma20 - 2 * std20).iloc[-1]
        
        # Stochastic (14, 3, 3)
        low14 = low.rolling(14).min()
        high14 = high.rolling(14).max()
        stoch_k = 100 * (close - low14) / (high14 - low14)
        stoch_d = stoch_k.rolling(3).mean()
        inds['Stoch_K'] = stoch_k.iloc[-1]
        inds['Stoch_D'] = stoch_d.iloc[-1]
        
        # Williams %R (14)
        inds['Williams_R'] = ((high14 - close) / (high14 - low14) * -100).iloc[-1]
        
        # ATR (14)
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        inds['ATR'] = tr.rolling(14).mean().iloc[-1]
        
        return inds

    def collect_and_handoff(self) -> MarketDataPacket:
        import concurrent.futures
        packet = MarketDataPacket(symbol=self.symbol, exchange=self.exchange)

        # ── Thu thập 3 nguồn dữ liệu song song ──────────────────────
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            f_vn   = pool.submit(self.vnstock_agent.collect, self.symbol, self.start, self.end)
            f_tv   = pool.submit(self.tv_agent.collect, self.symbol, self.exchange)
            if self.collect_news:
                from news_collectors import NewsOrchestrator
                f_news = pool.submit(NewsOrchestrator(self.symbol).collect_and_handoff)
            else:
                f_news = None

            vnstock_result = f_vn.result()
            tv_result      = f_tv.result()
            if f_news:
                try:
                    packet.news_packet = f_news.result(timeout=35)
                    packet.source_notes.append(
                        f"[News] {packet.news_packet.total_articles} bài viết đã thu thập"
                    )
                except Exception as e:
                    packet.source_notes.append(f"[News] Lỗi thu thập tin tức: {e}")

        # ── Ghi dữ liệu VNStock ──────────────────────────────────────
        packet.ohlcv_df = vnstock_result.get("df")
        packet.source_notes.append(f"[VNStock] {vnstock_result['note']}")

        # ── Ghi dữ liệu TradingView ──────────────────────────────────
        if tv_result["status"] == "OK":
            packet.tv_summary         = tv_result["summary"]
            packet.tv_indicators      = tv_result["indicators"]
            packet.tv_oscillators     = tv_result["oscillators"]
            packet.tv_moving_averages = tv_result["moving_averages"]
            packet.tv_recommendation  = tv_result["recommendation"]
            packet.exchange           = tv_result["exchange_found"]
        packet.source_notes.append(f"[TradingView] {tv_result['note']}")

        # ── Đánh giá chất lượng tổng thể ────────────────────────────
        # SYNTHETIC được xét TRƯỚC: giá là random walk, mọi chỉ báo tính từ nó
        # đều vô nghĩa, nên không được phép ra khuyến nghị dù TradingView có OK.
        if vnstock_result["status"] == "SYNTHETIC":
            packet.data_quality = "SYNTHETIC"
        elif vnstock_result["status"] == "OK" and tv_result["status"] == "OK":
            packet.data_quality = "OK"
        elif vnstock_result["status"] == "OK":
            packet.data_quality = "PARTIAL"
        else:
            packet.data_quality = "FAILED"

        # TỰ ĐỘNG TÍNH TOÁN CHỈ BÁO LOCAL TỪ OHLCV (Cực kỳ quan trọng cho Backtest)
        # TradingView MCP luôn trả về dữ liệu realtime hiện tại -> Gây sai lệch trong quá khứ.
        # Ta cần tính các chỉ báo này từ chính OHLCV lịch sử để đưa vào tv_indicators.
        if packet.ohlcv_df is not None and len(packet.ohlcv_df) >= 20:
            local_inds = self._compute_local_indicators(packet.ohlcv_df)
            # Ghi đè vào tv_indicators để các Agent Tầng 2 có thể đọc được
            packet.tv_indicators.update({k: v for k, v in local_inds.items() if v is not None})
            packet.source_notes.append("[Local] Đã tự tính RSI, MACD, BB, MAs... từ OHLCV lịch sử")

        return packet
