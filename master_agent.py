from data_collectors import MarketDataPacket
from news_sentiment_agent import NewsSentimentAgent
from debate_agents import DebateModerator, SafetyHarnessGuardrails
from analysis_agents import (
    TrendAnalysisAgent, MomentumAgent,
    VolumeAnalysisAgent, SupportResistanceAgent, RiskManagementAgent
)

# =====================================================================
# LAYER 3: MASTER CONSENSUS AGENT  (Tầng Tổng hợp Sơ bộ)
# LAYER 4: DEBATE COUNCIL & HARNESS (Tầng Tranh luận & Safety Guardrails)
# LAYER 5: FINAL VERDICT          (Phán quyết cuối)
# =====================================================================

class MasterConsensusAgent:
    """
    Luồng thực thi THỰC TẾ (khớp với code, không phải với sơ đồ):
    L1 (Data) -> L2 (Analysis Agents) -> L3 (Master Consensus)
    -> L4 (Debate Council) -> L4b (Safety Harness) -> L5 (Final Verdict)

    Lưu ý: tầng "Post-Mortem Memory" trong sơ đồ kiến trúc CHƯA được triển
    khai — xem ghi chú cuối debate_agents.py trước khi định làm.
    """
    NAME = "Master Consensus Agent"

    def __init__(self):
        self.trend_agent    = TrendAnalysisAgent()
        self.momentum_agent = MomentumAgent()
        self.volume_agent   = VolumeAnalysisAgent()
        self.sr_agent       = SupportResistanceAgent()
        self.risk_agent     = RiskManagementAgent()
        self.news_agent     = NewsSentimentAgent()
        self.debate         = DebateModerator()
        self.harness        = SafetyHarnessGuardrails()

    # Các mức chất lượng dữ liệu KHÔNG được phép sinh khuyến nghị mua/bán.
    NO_VERDICT_QUALITY = {
        "FAILED": (
            "DỮ LIỆU KHÔNG KHẢ DỤNG ❌",
            "⚠️ Không thể kết nối hoặc không tìm thấy dữ liệu từ nguồn VNStock / TradingView",
        ),
        "SYNTHETIC": (
            "DỮ LIỆU MÔ PHỎNG — KHÔNG DÙNG ĐỂ QUYẾT ĐỊNH ⚠️",
            "⚠️ Không kết nối được nguồn giá thật. Dữ liệu đang hiển thị là chuỗi "
            "NGẪU NHIÊN sinh tự động để giữ ứng dụng chạy được. Mọi chỉ báo tính từ "
            "nó đều vô nghĩa — vui lòng thử lại khi có kết nối.",
        ),
    }

    def run(self, packet: MarketDataPacket) -> dict:
        if packet.data_quality in self.NO_VERDICT_QUALITY:
            recommendation, reason = self.NO_VERDICT_QUALITY[packet.data_quality]
            return {
                "symbol": packet.symbol,
                "exchange": packet.exchange,
                "pre_debate_score": 50.0,
                "final_score": 50,
                "recommendation": recommendation,
                "action_color": "#757575",
                "key_reasons": [reason],
                "score_breakdown": {
                    "trend_score": 50, "momentum_score": 50, "volume_score": 50,
                    "sr_score": 50, "risk_score": 50, "news_score": 50,
                    "tv_bonus": 0, "debate_adjustment": 0, "safety_adjustment": 0
                },
                "safety": {"is_safe": False, "adjusted_score": 50.0,
                           "safe_position_size": 0.0,
                           "safety_violations": ["🛡️ Không đánh giá an toàn "
                                                 "vì dữ liệu không đáng tin."]},
                "analyses": {},
                "debate": None, "data_sources": packet.source_notes,
                "data_quality": packet.data_quality
            }

        # ── LAYER 2: Phân tích chuyên sâu ────────────────────────────
        trend_res    = self.trend_agent.analyze(packet)
        momentum_res = self.momentum_agent.analyze(packet)
        volume_res   = self.volume_agent.analyze(packet)
        sr_res       = self.sr_agent.analyze(packet)
        risk_res     = self.risk_agent.analyze(packet)
        news_res     = self.news_agent.analyze(packet.news_packet) if packet.news_packet else {
            "agent": "News Sentiment Agent", "overall_sentiment": "N/A",
            "sentiment_score": 0.0, "score": 0.0,
            "signals": ["⚠️ Bỏ qua thu thập tin tức"], "breakdown": {},
            "top_positive": [], "top_negative": [], "sector_sentiment": {}, "total_articles": 0
        }

        analyses_map = {
            "trend": trend_res, "momentum": momentum_res,
            "volume": volume_res, "support_resistance": sr_res,
            "risk": risk_res, "news": news_res,
        }

        # ── LAYER 3: Tính điểm sơ bộ với Trọng số Động (Dynamic Adaptive Weights) ─
        def normalize(score, max_range=5.0):
            return max(0.0, min(100.0, 50.0 + (score / max_range) * 50.0))

        trend_norm    = normalize(trend_res["score"], 5.0)
        momentum_norm = normalize(momentum_res["score"], 6.0)
        volume_norm   = normalize(volume_res["score"], 4.0)
        sr_norm       = normalize(sr_res["score"], 4.0)
        risk_norm     = 100.0 - risk_res["risk_score"]
        news_norm     = normalize(news_res.get("score", 0.0), 5.0)

        # Chế độ Trọng số Động: Nếu Trend & Volume phát tín hiệu Breakout mạnh,
        # ưu tiên Trọng số Trend/Volume (65%) và giảm phạt quá mua RSI của Momentum.
        if trend_norm >= 60.0 and volume_norm >= 55.0:
            weights = {"trend": 0.35, "volume": 0.30, "sr": 0.15, "momentum": 0.10, "risk": 0.05, "news": 0.05}
            # Trong sóng tăng mạnh (Uptrend Surge), RSI > 70 là chuyện bình thường -> nới điểm Momentum
            momentum_norm = max(momentum_norm, 65.0)
        elif sr_norm >= 60.0: # Chế độ tích lũy hỗ trợ
            weights = {"sr": 0.30, "volume": 0.25, "trend": 0.25, "momentum": 0.10, "risk": 0.05, "news": 0.05}
        else:
            weights = {"trend": 0.22, "momentum": 0.22, "volume": 0.18, "sr": 0.13, "risk": 0.13, "news": 0.12}

        tv_rec   = packet.tv_recommendation
        tv_bonus = {"STRONG_BUY": 8, "BUY": 4, "NEUTRAL": 0,
                    "SELL": -4, "STRONG_SELL": -8}.get(tv_rec, 0)

        pre_debate_score = (
            trend_norm * weights["trend"] + momentum_norm * weights["momentum"] +
            volume_norm * weights["volume"] + sr_norm * weights["sr"] +
            risk_norm * weights["risk"] + news_norm * weights["news"]
        ) + tv_bonus
        pre_debate_score = max(5.0, min(95.0, pre_debate_score))

        # ── LAYER 4: Debate Council – Tranh luận đối lập ─────────────
        verdict = self.debate.run_debate(analyses_map, pre_debate_score)
        post_debate_score = pre_debate_score + verdict.final_adjustment

        # ── LAYER 4b: Safety Harness – chốt chặn bất biến ─────────────
        # Chạy SAU tranh luận: dù Bull thắng thuyết phục đến đâu, các quy tắc
        # cứng (bull trap, trần stop-loss, trần tỷ trọng vốn) vẫn phải áp dụng.
        safety = self.harness.evaluate_safety(analyses_map, post_debate_score)

        # ── LAYER 5: Phán quyết cuối sau tranh luận + harness ─────────
        final_score = max(5, min(95, int(safety["adjusted_score"])))

        if final_score >= 78:
            recommendation = "MUA MẠNH 🚀"; action_color = "#00e676"
        elif final_score >= 62:
            recommendation = "MUA 📈";       action_color = "#29b6f6"
        elif final_score >= 45:
            recommendation = "NẮM GIỮ 👀";   action_color = "#ffca28"
        elif final_score >= 30:
            recommendation = "BÁN 📉";        action_color = "#ff7043"
        else:
            recommendation = "BÁN MẠNH 🔴";  action_color = "#ef5350"

        # ── Luận điểm tổng hợp ────────────────────────────────────────
        key_reasons = [
            f"📈 Xu hướng: {trend_res['trend']} (Sức mạnh: {trend_res['trend_strength']})",
            f"⚡ Động lượng: {momentum_res['momentum_signal']}",
            f"📊 Khối lượng: {volume_res['volume_signal']}",
            f"📍 Vùng giá: {sr_res['position']}",
            f"🛡️ Mức rủi ro: {risk_res['risk_level']}",
            f"📡 TradingView MCP: {tv_rec} (Osc: {packet.tv_oscillators} | MA: {packet.tv_moving_averages})",
            f"📰 Tin tức: {news_res.get('overall_sentiment','N/A')} ({news_res.get('total_articles',0)} bài)",
            f"⚖️ Debate Council: Bull {verdict.bull_score:+.1f} | Bear {verdict.bear_score:+.1f} "
            f"| Điều chỉnh {verdict.final_adjustment:+.1f} | Tin cậy: {verdict.confidence_level}",
        ]
        if risk_res.get("recommendations"):
            rec = risk_res["recommendations"]
            entry_p = rec.get("entry_price", 0)
            entry_str = f"Vào lệnh={entry_p:,.0f} VNĐ | " if entry_p else ""
            tp2_str = f" | TP2 Trailing={rec.get('tp2_price',0):,.0f} VNĐ (+{rec.get('tp2_pct',0)}%)" if rec.get("tp2_price") else ""
            key_reasons.append(
                f"🎯 {entry_str}"
                f"SL={rec['stop_loss_price']:,.0f} VNĐ (-{rec['stop_loss_pct']}%) | "
                f"TP1={rec['take_profit_price']:,.0f} VNĐ (+{rec['take_profit_pct']}%)"
                f"{tp2_str} | "
                f"RR={rec['risk_reward_ratio']} | "
                f"Vốn tối đa (sau Harness): {safety['safe_position_size']}%"
            )
        # Vi phạm quy tắc an toàn phải hiển thị cho người dùng, không im lặng
        key_reasons.extend(safety["safety_violations"])

        return {
            "symbol": packet.symbol,
            "exchange": packet.exchange,
            "pre_debate_score": round(pre_debate_score, 1),
            "final_score": final_score,
            "recommendation": recommendation,
            "action_color": action_color,
            "key_reasons": key_reasons,
            "score_breakdown": {
                "trend_score":    round(trend_norm, 1),
                "momentum_score": round(momentum_norm, 1),
                "volume_score":   round(volume_norm, 1),
                "sr_score":       round(sr_norm, 1),
                "risk_score":     round(risk_norm, 1),
                "news_score":     round(news_norm, 1),
                "tv_bonus":       tv_bonus,
                "debate_adjustment": verdict.final_adjustment,
                "safety_adjustment": round(safety["adjusted_score"] - post_debate_score, 1),
            },
            "safety": safety,
            "analyses": analyses_map,
            "debate": {
                "verdict_summary":    verdict.verdict_summary,
                "bull_score":         verdict.bull_score,
                "bear_score":         verdict.bear_score,
                "final_adjustment":   verdict.final_adjustment,
                "confidence_level":   verdict.confidence_level,
                "key_risks":          verdict.key_risks,
                "key_opportunities":  verdict.key_opportunities,
                "rounds": [
                    [
                        {
                            "agent": a.agent_name, "stance": a.stance,
                            "statement": a.statement, "impact": a.score_impact
                        } for a in rnd
                    ]
                    for rnd in verdict.rounds
                ],
            },
            "data_sources":  packet.source_notes,
            "data_quality":  packet.data_quality,
        }


# =====================================================================
# PIPELINE RUNNER
# =====================================================================
def run_full_analysis(symbol: str, start: str, end: str,
                      exchange: str = "HOSE", collect_news: bool = True) -> dict:
    """
    Pipeline 5 tầng:
      Layer 1A: VNStock + TradingView MCP
      Layer 1B: News Agents (5 agents song song)
      Layer 2:  6 Analysis Agents chuyên sâu
      Layer 3:  Master Consensus (điểm sơ bộ)
      Layer 4:  Debate Council (Bull vs Bear vs Devil)
      Layer 5:  Final Verdict (phán quyết cuối)
    """
    from data_collectors import DataOrchestrator
    orchestrator = DataOrchestrator(symbol, start, end, exchange, collect_news=collect_news)
    packet = orchestrator.collect_and_handoff()
    master = MasterConsensusAgent()
    return master.run(packet)
