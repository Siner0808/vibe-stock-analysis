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
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
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

    def collect(self, symbol: str, start: str, end: str) -> dict:
        from vnstock import Quote
        for src in ['vci', 'kbs']:
            try:
                df = Quote(symbol=symbol, source=src).history(start=start, end=end)
                if df is not None and not df.empty:
                    return {"status": "OK", "df": df, "note": f"Tải dữ liệu Real-Time thành công ({len(df)} phiên từ {src.upper()})"}
            except Exception:
                continue
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

        return packet
