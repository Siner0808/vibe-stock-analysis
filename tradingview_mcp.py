import json
from tradingview_ta import TA_Handler, Interval, Exchange

class TradingViewMCPProvider:
    """MCP Provider cho Nguồn dữ liệu & Chỉ báo Phân tích Kỹ thuật từ TradingView"""
    def __init__(self, symbol: str, exchange: str = "HOSE", screener: str = "vietnam"):
        self.symbol = symbol.upper()
        self.exchange = exchange.upper()
        self.screener = screener.lower()

    def get_analysis_data(self, interval=Interval.INTERVAL_1_DAY) -> dict:
        """Lấy toàn bộ dữ liệu phân tích chỉ báo từ TradingView MCP"""
        try:
            handler = TA_Handler(
                symbol=self.symbol,
                exchange=self.exchange,
                screener=self.screener,
                interval=interval
            )
            analysis = handler.get_analysis()
            
            return {
                "status": "SUCCESS",
                "source": "TradingView MCP",
                "symbol": self.symbol,
                "exchange": self.exchange,
                "recommendation": analysis.summary.get("RECOMMENDATION", "NEUTRAL"),
                "summary": analysis.summary,
                "oscillators": analysis.oscillators.get("RECOMMENDATION", "NEUTRAL"),
                "moving_averages": analysis.moving_averages.get("RECOMMENDATION", "NEUTRAL"),
                "indicators": {
                    "RSI": analysis.indicators.get("RSI"),
                    "MACD_Signal": analysis.indicators.get("MACD.macd"),
                    "Stoch_K": analysis.indicators.get("Stoch.K"),
                    "EMA20": analysis.indicators.get("EMA20"),
                    "SMA50": analysis.indicators.get("SMA50"),
                    "ADX": analysis.indicators.get("ADX")
                }
            }
        except Exception as e:
            # Fallback format nếu ticker thuộc HNX / UPCOM hoặc không tìm thấy exchange HOSE
            try:
                handler = TA_Handler(
                    symbol=self.symbol,
                    exchange="HNX",
                    screener=self.screener,
                    interval=interval
                )
                analysis = handler.get_analysis()
                return {
                    "status": "SUCCESS",
                    "source": "TradingView MCP (HNX)",
                    "symbol": self.symbol,
                    "exchange": "HNX",
                    "recommendation": analysis.summary.get("RECOMMENDATION", "NEUTRAL"),
                    "summary": analysis.summary,
                    "oscillators": analysis.oscillators.get("RECOMMENDATION", "NEUTRAL"),
                    "moving_averages": analysis.moving_averages.get("RECOMMENDATION", "NEUTRAL"),
                    "indicators": {
                        "RSI": analysis.indicators.get("RSI"),
                        "MACD_Signal": analysis.indicators.get("MACD.macd"),
                        "Stoch_K": analysis.indicators.get("Stoch.K"),
                        "EMA20": analysis.indicators.get("EMA20"),
                        "SMA50": analysis.indicators.get("SMA50"),
                        "ADX": analysis.indicators.get("ADX")
                    }
                }
            except Exception as ex:
                return {
                    "status": "ERROR",
                    "source": "TradingView MCP",
                    "symbol": self.symbol,
                    "message": str(e),
                    "recommendation": "NEUTRAL",
                    "summary": {"BUY": 0, "SELL": 0, "NEUTRAL": 0}
                }

    def to_mcp_json(self) -> str:
        """Xuất dữ liệu dạng chuẩn JSON cho MCP Server protocol"""
        return json.dumps(self.get_analysis_data(), indent=2, ensure_ascii=False)


class TradingViewAgent:
    """Agent chuyên phân tích dữ liệu kỹ thuật từ nguồn TradingView MCP"""
    def __init__(self, symbol: str):
        self.provider = TradingViewMCPProvider(symbol)

    def analyze(self) -> dict:
        data = self.provider.get_analysis_data()
        rec = data.get("recommendation", "NEUTRAL")
        
        reasons = []
        if rec in ["STRONG_BUY", "BUY"]:
            reasons.append(f"TradingView tổng hợp tín hiệu MUA: {data.get('summary')}")
        elif rec in ["STRONG_SELL", "SELL"]:
            reasons.append(f"TradingView tổng hợp tín hiệu BÁN: {data.get('summary')}")
        else:
            reasons.append(f"TradingView khuyến nghị TRUNG TÍNH (Theo dõi): {data.get('summary')}")

        return {
            "agent": "TradingView MCP Agent",
            "source": "TradingView TA Engine",
            "recommendation": rec,
            "data": data,
            "reasons": reasons
        }
