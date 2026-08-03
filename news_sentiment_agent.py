"""
news_sentiment_agent.py
──────────────────────────────────────────────────────────────────────
Agent phân tích cảm xúc & tác động của tin tức đến thị trường.
Nhận NewsPacket từ NewsOrchestrator, xuất bản điểm sentiment tổng hợp.
──────────────────────────────────────────────────────────────────────
"""
from news_collectors import NewsPacket, NewsItem
from collections import Counter

SECTOR_LABEL = {
    "banking":          "🏦 Ngân hàng",
    "real_estate":      "🏢 Bất động sản",
    "technology":       "💻 Công nghệ",
    "steel_materials":  "⚙️ Thép & Vật liệu",
    "oil_gas":          "🛢️ Dầu khí",
    "agriculture":      "🌾 Nông nghiệp",
    "consumer_retail":  "🛍️ Tiêu dùng & Bán lẻ",
    "healthcare_pharma":"💊 Y tế & Dược phẩm",
    "aviation_logistics":"✈️ Hàng không & Logistics",
    "electricity_energy":"⚡ Điện & Năng lượng",
    "securities_finance":"📈 Chứng khoán & Tài chính",
    "textiles_apparel": "👗 Dệt may",
    "crypto_blockchain":"🔗 Crypto & Blockchain",
    "global_macro":     "🌏 Kinh tế vĩ mô toàn cầu",
    "macro":            "📊 Kinh tế vĩ mô",
    "corporate":        "🏭 Doanh nghiệp",
    "stock_market":     "📉 Thị trường chứng khoán",
    "investment":       "💰 Đầu tư",
    "interest_rate":    "🏛️ Lãi suất & Chính sách tiền tệ",
    "policy":           "📜 Chính sách tài chính",
}


class NewsSentimentAgent:
    """
    Agent 6: Phân tích Cảm xúc Tin tức (News Sentiment)
    ─────────────────────────────────────────────────────
    - Nhận NewsPacket từ NewsOrchestrator
    - Tổng hợp sentiment theo nguồn: trong nước / quốc tế / vĩ mô / ngành
    - Tính điểm tổng hợp từ -100 (cực tiêu cực) đến +100 (cực tích cực)
    - Xác định top 5 tin nổi bật tích cực & tiêu cực
    - Bàn giao kết quả phân tích sang MasterConsensusAgent
    """
    NAME = "News Sentiment Agent 📰"

    def _score_items(self, items: list[NewsItem]) -> tuple[int, int, int, float]:
        """Trả về (pos, neg, neutral, weighted_score)"""
        pos = sum(1 for i in items if i.sentiment_hint == "POSITIVE")
        neg = sum(1 for i in items if i.sentiment_hint == "NEGATIVE")
        neu = len(items) - pos - neg
        total = len(items) if items else 1
        weighted = ((pos - neg) / total) * 100
        return pos, neg, neu, round(weighted, 2)

    def analyze(self, packet: NewsPacket) -> dict:
        if not packet or packet.status == "FAILED":
            return {
                "agent": self.NAME,
                "overall_sentiment": "NEUTRAL",
                "sentiment_score": 0.0,
                "score": 0.0,
                "signals": ["⚠️ Không thu thập được tin tức để phân tích"],
                "breakdown": {},
                "top_positive": [],
                "top_negative": [],
                "sector_sentiment": {},
                "total_articles": 0,
            }

        signals = []
        breakdown = {}
        all_items_flat: list[NewsItem] = []

        # ── Tin trong nước ──────────────────────────────────────────
        p, n, neu, ws = self._score_items(packet.domestic_news)
        breakdown["domestic"] = {"positive": p, "negative": n, "neutral": neu, "score": ws}
        all_items_flat.extend(packet.domestic_news)
        if ws >= 20:
            signals.append(f"🇻🇳 Tin trong nước tích cực: {p} bài +, {n} bài - (score {ws:+.0f})")
        elif ws <= -20:
            signals.append(f"🇻🇳 Tin trong nước tiêu cực: {p} bài +, {n} bài - (score {ws:+.0f})")
        else:
            signals.append(f"🇻🇳 Tin trong nước trung tính (score {ws:+.0f})")

        # ── Tin quốc tế ─────────────────────────────────────────────
        p, n, neu, ws = self._score_items(packet.international_news)
        breakdown["international"] = {"positive": p, "negative": n, "neutral": neu, "score": ws}
        all_items_flat.extend(packet.international_news)
        if ws >= 20:
            signals.append(f"🌏 Tin quốc tế tích cực: {p}+/{n}- (score {ws:+.0f})")
        elif ws <= -20:
            signals.append(f"🌏 Tin quốc tế tiêu cực: {p}+/{n}- (score {ws:+.0f})")
        else:
            signals.append(f"🌏 Tin quốc tế trung tính (score {ws:+.0f})")

        # ── Tin vĩ mô ───────────────────────────────────────────────
        p, n, neu, ws = self._score_items(packet.macro_news)
        breakdown["macro"] = {"positive": p, "negative": n, "neutral": neu, "score": ws}
        all_items_flat.extend(packet.macro_news)
        if ws <= -25:
            signals.append(f"📊 Vĩ mô tiêu cực (FED/NHNN/IMF) score {ws:+.0f} — Áp lực lên thị trường")
        elif ws >= 25:
            signals.append(f"📊 Vĩ mô tích cực (nới lỏng/tăng trưởng) score {ws:+.0f}")
        else:
            signals.append(f"📊 Vĩ mô trung tính (score {ws:+.0f})")

        # ── Từng ngành ──────────────────────────────────────────────
        sector_sentiment: dict[str, dict] = {}
        for sec, items in packet.sector_news.items():
            p, n, neu, ws = self._score_items(items)
            label = SECTOR_LABEL.get(sec, sec)
            sector_sentiment[sec] = {
                "label": label,
                "positive": p, "negative": n, "neutral": neu,
                "score": ws, "total": len(items)
            }
        all_items_flat.extend(
            item for sec_items in packet.sector_news.values() for item in sec_items
        )

        # ── Top tin nổi bật ─────────────────────────────────────────
        top_positive = sorted(
            [i for i in all_items_flat if i.sentiment_hint == "POSITIVE"],
            key=lambda x: x.title, reverse=True
        )[:5]
        top_negative = sorted(
            [i for i in all_items_flat if i.sentiment_hint == "NEGATIVE"],
            key=lambda x: x.title, reverse=True
        )[:5]

        # ── Tính điểm tổng hợp có trọng số ──────────────────────────
        dom_s  = breakdown["domestic"]["score"]
        intl_s = breakdown["international"]["score"]
        mac_s  = breakdown["macro"]["score"]

        # Top ảnh hưởng sector (lấy global_macro + securities + banking)
        sector_key_score = 0.0
        for key in ["global_macro", "securities_finance", "banking", "macro"]:
            if key in sector_sentiment:
                sector_key_score += sector_sentiment[key]["score"]
        sector_key_score /= 4.0

        overall_score = (
            dom_s  * 0.30 +
            intl_s * 0.30 +
            mac_s  * 0.25 +
            sector_key_score * 0.15
        )
        overall_score = max(-100, min(100, overall_score))

        # ── Phân loại tổng hợp ──────────────────────────────────────
        if overall_score >= 30:
            overall_sentiment = "POSITIVE 📰🟢"
        elif overall_score <= -30:
            overall_sentiment = "NEGATIVE 📰🔴"
        elif overall_score >= 10:
            overall_sentiment = "SLIGHTLY POSITIVE 🟡"
        elif overall_score <= -10:
            overall_sentiment = "SLIGHTLY NEGATIVE 🟠"
        else:
            overall_sentiment = "NEUTRAL 📰⚪"

        # Quy đổi sang thang Agent score -5 → +5
        agent_score = overall_score / 20.0

        signals.append(
            f"📰 Tổng hợp {packet.total_articles} bài từ "
            f"{len(packet.domestic_news)} trong nước + "
            f"{len(packet.international_news)} quốc tế + "
            f"{sum(len(v) for v in packet.sector_news.values())} ngành"
        )

        return {
            "agent": self.NAME,
            "overall_sentiment": overall_sentiment,
            "sentiment_score": round(overall_score, 2),
            "score": round(agent_score, 2),
            "signals": signals,
            "breakdown": breakdown,
            "top_positive": [
                {"title": i.title, "source": i.source, "category": SECTOR_LABEL.get(i.category, i.category), "url": i.url}
                for i in top_positive
            ],
            "top_negative": [
                {"title": i.title, "source": i.source, "category": SECTOR_LABEL.get(i.category, i.category), "url": i.url}
                for i in top_negative
            ],
            "sector_sentiment": sector_sentiment,
            "total_articles": packet.total_articles,
        }
