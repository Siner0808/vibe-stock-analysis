from data_collectors import MarketDataPacket
from news_sentiment_agent import NewsSentimentAgent
from debate_agents import DebateModerator, SafetyHarnessGuardrails
from fundamental_agent import FundamentalAgent
from analysis_agents import (
    TrendAnalysisAgent, MomentumAgent,
    VolumeAnalysisAgent, SupportResistanceAgent, RiskManagementAgent
)

# =====================================================================
# TRỌNG SỐ CỦA AGENT CƠ BẢN — MẶC ĐỊNH 0, ĐỌC TRƯỚC KHI ĐỔI
# =====================================================================
# Điểm cơ bản (0-100) tham gia theo dạng CỘNG LỆCH: `(điểm - 50) * trọng
# số`. Nhờ vậy trọng số 0 cho ra đúng con số như trước khi có agent này —
# kiểm được bằng mắt, không cần chạy lại cả sổ lệnh để chứng minh.
#
# Vì sao để 0: chưa ai CHẠY phép đo. (Tới 22/08/2026 lý do còn mạnh hơn
# — không đo ĐƯỢC, vì gói cộng đồng chỉ trả 8 quý và lực phát hiện ~10%.
# Gói tài trợ mở giới hạn đó lên ~34 quý, lực phát hiện ~46% ở IC 0,05.)
# Ba thiên lệch còn lại — số liệu điều chỉnh hồi tố, thiên lệch sống sót,
# cửa sổ nằm trong vùng đã tối ưu — KHÔNG đổi và đều đẩy kết quả ĐẸP lên.
#
# Quy tắc số 1 của `NGUYEN-TAC-DO-LUONG.md`: nếu một thay đổi làm con số
# đẹp lên đáng kể, giả định đầu tiên phải là có lỗi. Bật trọng số rồi thấy
# lãi tăng chính là kịch bản đó.
TRONG_SO_CO_BAN = 0.0

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

    def __init__(self, doc_co_ban: bool = False):
        # `doc_co_ban` MẶC ĐỊNH TẮT, và mặc định đó là một rào chắn chứ
        # không phải một lựa chọn hiệu năng.
        #
        # Bảng chỉ số theo NĂM mà nguồn trả về là trạng thái HIỆN TẠI, đã
        # gồm mọi lần điều chỉnh hồi tố, và không kèm ngày công bố. Đưa nó
        # vào một phiên năm 2022 là chấm phiên đó bằng số liệu năm 2025 —
        # nhìn trộm tương lai ở dạng thô nhất (bất biến 1).
        #
        # `backtest/engine.py` và `paper_runner.py` dựng agent này bằng
        # constructor rỗng, nên chúng giữ nguyên hành vi cũ và không phát
        # sinh lời gọi mạng nào. Chỉ `run_full_analysis()` — đường phân
        # tích MỘT mã tại thời điểm HIỆN TẠI — mới bật nó lên.
        self.doc_co_ban     = doc_co_ban
        self.trend_agent    = TrendAnalysisAgent()
        self.momentum_agent = MomentumAgent()
        self.volume_agent   = VolumeAnalysisAgent()
        self.sr_agent       = SupportResistanceAgent()
        self.risk_agent     = RiskManagementAgent()
        self.news_agent     = NewsSentimentAgent()
        self.fundamental_agent = FundamentalAgent()
        self.debate         = DebateModerator()
        self.harness        = SafetyHarnessGuardrails()

    def _phan_tich_co_ban(self, packet: MarketDataPacket) -> dict:
        """Kết quả Agent Cơ Bản, hoặc một kết quả 'không đọc' rõ ràng.

        Không bao giờ ném: một lỗi mạng ở tầng cơ bản không được làm hỏng
        cả lượt chấm kỹ thuật.
        """
        if not self.doc_co_ban:
            return {"agent": FundamentalAgent.NAME, "symbol": packet.symbol,
                    "available": False, "diem": None,
                    "xep_hang": "KHÔNG ĐỌC",
                    "signals": ["🟡 Không đọc báo cáo tài chính ở đường chạy "
                                "này (backtest / sổ lệnh giấy) — dữ liệu cơ "
                                "bản theo năm không có ngày công bố nên "
                                "dùng cho phiên quá khứ là nhìn trộm."],
                    "canh_bao": [], "nhom": "", "nam": None, "chi_so": None}
        try:
            return self.fundamental_agent.analyze(packet.symbol)
        except Exception as e:
            return {"agent": FundamentalAgent.NAME, "symbol": packet.symbol,
                    "available": False, "diem": None,
                    "xep_hang": "KHÔNG CÓ DỮ LIỆU",
                    "signals": [f"⚠️ Agent Cơ Bản lỗi: "
                                f"{type(e).__name__}: {str(e)[:120]}"],
                    "canh_bao": [], "nhom": "", "nam": None, "chi_so": None}

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

    @staticmethod
    def _session_date(packet: MarketDataPacket) -> str | None:
        """Ngày của phiên cuối trong gói dữ liệu — mốc thời gian agent đang đứng.

        Dùng để chặn mọi cơ chế học hỏi khỏi việc đọc dữ liệu sau mốc này.
        """
        df = packet.ohlcv_df
        try:
            if df is not None and len(df) and "time" in df.columns:
                return str(df["time"].iloc[-1])[:10]
        except Exception:
            pass
        return None

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
                    "fundamental_score": None, "fundamental_adjustment": 0.0,
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

        fund_res = self._phan_tich_co_ban(packet)

        analyses_map = {
            "trend": trend_res, "momentum": momentum_res,
            "volume": volume_res, "support_resistance": sr_res,
            "risk": risk_res, "news": news_res, "fundamental": fund_res,
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
            weights = {"trend": 0.35, "volume": 0.30, "sr": 0.15, "momentum": 0.10, "risk": 0.10, "news": 0.0}
            # Trong sóng tăng mạnh (Uptrend Surge), RSI > 70 là chuyện bình thường -> nới điểm Momentum
            momentum_norm = max(momentum_norm, 65.0)
        elif sr_norm >= 60.0: # Chế độ tích lũy hỗ trợ
            weights = {"sr": 0.30, "volume": 0.25, "trend": 0.25, "momentum": 0.10, "risk": 0.10, "news": 0.0}
        else:
            weights = {"trend": 0.25, "momentum": 0.25, "volume": 0.20, "sr": 0.15, "risk": 0.15, "news": 0.0}

        tv_rec   = packet.tv_recommendation
        tv_bonus = {"STRONG_BUY": 8, "BUY": 4, "NEUTRAL": 0,
                    "SELL": -4, "STRONG_SELL": -8}.get(tv_rec, 0)

        # Bộ nhớ mẫu hình cắt lỗ. MẶC ĐỊNH TẮT — xem đầu post_mortem_learning.py.
        # `as_of` là ngày của phiên đang chấm; thiếu nó thì điểm phạt luôn bằng 0,
        # nên cơ chế này không thể nhìn trộm các lệnh lỗ xảy ra sau ngày đó.
        sl_penalty = 0.0
        try:
            from post_mortem_learning import get_learning_engine
            engine = get_learning_engine()
            if engine.enabled:
                current_bd = {
                    "trend_score": int(trend_norm),
                    "momentum_score": int(momentum_norm),
                    "volume_score": int(volume_norm)
                }
                _phien = self._session_date(packet)
                # HAI truc thoi gian, hai muc dich khac nhau:
                #   as_of          -> chong nhin trom tuong lai (bat bien 1)
                #   phien_hien_tai -> giu tinh tai lap (bat bien 2)
                # Mot minh as_of khong du: mot lenh tin hieu thang 1 dong bang
                # cat lo hom nay se LOT hang rao thu nhat, roi lam lech diem
                # cua chinh phien hom nay. Do la su co 47-vs-59.
                sl_penalty = engine.get_penalty_for_pattern(
                    current_bd, as_of=_phien, phien_hien_tai=_phien)
        except Exception:
            pass

        # Cộng LỆCH so với mốc 50, không trộn vào bộ trọng số phía trên.
        # Trọng số 0 -> số hạng này bằng 0 -> điểm y hệt trước khi có Agent
        # Cơ Bản. Đọc một dòng là biết, không phải chạy lại cả sổ lệnh.
        dong_gop_co_ban = 0.0
        if TRONG_SO_CO_BAN and fund_res.get("diem") is not None:
            dong_gop_co_ban = (fund_res["diem"] - 50.0) * TRONG_SO_CO_BAN

        pre_debate_score = (
            trend_norm * weights["trend"] + momentum_norm * weights["momentum"] +
            volume_norm * weights["volume"] + sr_norm * weights["sr"] +
            risk_norm * weights["risk"]
        ) + tv_bonus + sl_penalty + dong_gop_co_ban
        pre_debate_score = max(5.0, min(95.0, pre_debate_score))

        # ── LAYER 4: Debate Council – Tranh luận đối lập ─────────────
        verdict = self.debate.run_debate(analyses_map, pre_debate_score)
        
        # Vô hiệu hóa ảnh hưởng của Debate Council (chỉ gây nhiễu +-0.9, xem luong-phan-tich.html)
        post_debate_score = pre_debate_score

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
            (f"📑 Cơ bản ({fund_res.get('nhom') or '?'}, BCTC "
             f"{fund_res.get('nam')}): {fund_res['xep_hang']} "
             f"{fund_res['diem']:.0f}/100 · ảnh hưởng điểm "
             f"{dong_gop_co_ban:+.1f}"
             if fund_res.get("available")
             else f"📑 Cơ bản: {fund_res['xep_hang']}"),
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
                "fundamental_score": fund_res.get("diem"),
                "fundamental_adjustment": round(dong_gop_co_ban, 2),
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
      Layer 2:  6 Analysis Agents chuyên sâu + Agent Cơ Bản
      Layer 3:  Master Consensus (điểm sơ bộ)
      Layer 4:  Debate Council (Bull vs Bear vs Devil)
      Layer 5:  Final Verdict (phán quyết cuối)

    Đây là đường chạy PHÂN TÍCH MỘT MÃ TẠI THỜI ĐIỂM HIỆN TẠI, nên Agent
    Cơ Bản được bật. Backtest và sổ lệnh giấy dựng `MasterConsensusAgent()`
    trực tiếp và giữ mặc định tắt — xem ghi chú ở `__init__`.
    """
    from data_collectors import DataOrchestrator
    orchestrator = DataOrchestrator(symbol, start, end, exchange, collect_news=collect_news)
    packet = orchestrator.collect_and_handoff()
    master = MasterConsensusAgent(doc_co_ban=True)
    return master.run(packet)
