"""
debate_agents.py
──────────────────────────────────────────────────────────────────────
Layer 2.5: Đội Tranh luận (Debate Council)
Các Agent đối lập nhau để thách thức phân tích, trước khi đưa ra
kết luận cuối qua Moderator. Phương pháp Adversarial Collaboration.
──────────────────────────────────────────────────────────────────────
"""
from dataclasses import dataclass


@dataclass
class DebateArgument:
    agent_name: str
    stance: str          # BULL / BEAR / NEUTRAL
    round_num: int
    statement: str
    score_impact: float  # +/- tác động lên điểm cuối


@dataclass
class DebateVerdict:
    bull_score: float
    bear_score: float
    final_adjustment: float   # điều chỉnh thêm vào / trừ khỏi master score
    rounds: list[list[DebateArgument]]
    verdict_summary: str
    key_risks: list[str]
    key_opportunities: list[str]
    confidence_level: str     # THẤP / TRUNG BÌNH / CAO / RẤT CAO


# ─────────────────────────────────────────────────────────────────────
# BULL ADVOCATE AGENT
# Nhiệm vụ: Tìm mọi lý do tích cực để bảo vệ lập trường MUA
# ─────────────────────────────────────────────────────────────────────
class BullAdvocateAgent:
    NAME = "🐂 Bull Advocate Agent"
    STANCE = "BULL"

    def argue(self, analyses: dict, round_num: int, bear_prev: list[DebateArgument]) -> DebateArgument:
        trend    = analyses.get("trend", {})
        momentum = analyses.get("momentum", {})
        volume   = analyses.get("volume", {})
        sr       = analyses.get("support_resistance", {})
        risk     = analyses.get("risk", {})
        news     = analyses.get("news", {})

        arguments = []
        impact = 0.0

        if round_num == 1:
            # Phiên 1: Trình bày lập luận TĂNG mạnh nhất
            t = trend.get("trend", "SIDEWAYS")
            if "UPTREND" in t:
                arguments.append(f"📈 Xu hướng giá đang ở pha {t} — cấu trúc thị trường hỗ trợ người mua.")
                impact += 2.0
            ma_sig = momentum.get("momentum_signal", "")
            if "BUY" in ma_sig:
                arguments.append(f"⚡ Tất cả chỉ báo động lượng ({ma_sig}) đồng thuận tín hiệu MUA.")
                impact += 1.5
            vol_sig = volume.get("volume_signal", "")
            if "CONFIRM" in vol_sig or "STRONG" in vol_sig:
                arguments.append(f"📊 Khối lượng giao dịch xác nhận xu hướng tăng ({vol_sig}) — dòng tiền đang vào cổ phiếu.")
                impact += 1.0
            pos = sr.get("position", "")
            if "HỖ TRỢ" in pos or "Cơ hội" in pos:
                arguments.append(f"📍 Giá đang ở gần vùng hỗ trợ kỹ thuật quan trọng — rủi ro downside được giới hạn.")
                impact += 1.0
            news_sent = news.get("overall_sentiment", "")
            if "POSITIVE" in news_sent:
                arguments.append(f"📰 Dòng tin tức đang tích cực ({news_sent}) — macro & ngành hỗ trợ tâm lý mua.")
                impact += 0.5
            if not arguments:
                arguments.append("📊 Dữ liệu kỹ thuật tổng thể chưa đủ mạnh để xác nhận xu hướng rõ ràng — chờ tín hiệu.")
                impact += 0.0

        elif round_num == 2:
            # Phiên 2: Phản bác lập luận BEAR từ phiên 1
            bear_stmts = " ".join([a.statement for a in bear_prev])
            if "rủi ro" in bear_stmts.lower() or "risk" in bear_stmts.lower():
                rec = risk.get("recommendations", {})
                sl = rec.get("stop_loss_pct", 7)
                tp = rec.get("take_profit_pct", 17)
                arguments.append(
                    f"🔄 Phản bác Bear: Rủi ro đã được định lượng và kiểm soát! "
                    f"Stop-loss chỉ -{sl}%, trong khi tiềm năng upside +{tp}%. "
                    f"Tỷ lệ Risk:Reward = {rec.get('risk_reward_ratio', '2.5:1')} — hoàn toàn có thể chấp nhận."
                )
                impact += 1.5
            if "giảm" in bear_stmts.lower() or "downtrend" in bear_stmts.lower():
                sharpe = (risk.get("metrics", {}) or {}).get("sharpe_ratio") or 0.0
                arguments.append(
                    f"🔄 Phản bác Bear về xu hướng: Sharpe Ratio = {sharpe:.2f}. "
                    f"Dù ngắn hạn có biến động, lịch sử dài hạn cho thấy hiệu suất sinh lời ổn định."
                )
                impact += 1.0
            arguments.append(
                "💡 Cơ hội: Những phiên điều chỉnh là thời điểm tích lũy tốt cho nhà đầu tư dài hạn. "
                "Sell-off tạo điểm mua tốt hơn, không phải tín hiệu thoát."
            )
            impact += 0.5

        elif round_num == 3:
            # Phiên 3: Kết luận Bull
            t = trend.get("trend", "")
            strength = trend.get("trend_strength", "")
            arguments.append(
                f"🏁 Kết luận BULL: Với xu hướng {t} (sức mạnh: {strength}) và xác nhận từ "
                f"nhiều chỉ báo kỹ thuật, lập trường MUA là hợp lý. "
                f"Nhà đầu tư nên áp dụng chiến lược mua từng phần (scale-in) và quản lý vốn chặt chẽ."
            )
            impact += 1.0

        return DebateArgument(
            agent_name=self.NAME, stance=self.STANCE, round_num=round_num,
            statement=" | ".join(arguments) if arguments else "Không có lập luận mới.",
            score_impact=round(impact, 2)
        )


# ─────────────────────────────────────────────────────────────────────
# BEAR ADVOCATE AGENT
# Nhiệm vụ: Tìm mọi rủi ro tiêu cực để bảo vệ lập trường BÁN / TRÁNH
# ─────────────────────────────────────────────────────────────────────
class BearAdvocateAgent:
    NAME = "🐻 Bear Advocate Agent"
    STANCE = "BEAR"

    def argue(self, analyses: dict, round_num: int, bull_prev: list[DebateArgument]) -> DebateArgument:
        trend    = analyses.get("trend", {})
        momentum = analyses.get("momentum", {})
        volume   = analyses.get("volume", {})
        sr       = analyses.get("support_resistance", {})
        risk     = analyses.get("risk", {})
        news     = analyses.get("news", {})

        arguments = []
        impact = 0.0

        if round_num == 1:
            # Phiên 1: Trình bày lập luận GIẢM mạnh nhất
            t = trend.get("trend", "SIDEWAYS")
            if "DOWN" in t:
                arguments.append(f"📉 Xu hướng giá đang ở pha {t} — cấu trúc thị trường bất lợi cho người mua.")
                impact -= 2.0
            elif "SIDEWAYS" in t:
                arguments.append("📉 Thị trường đang sideway — không có lý do rõ ràng để mua vào, tiền sẽ bị giam lạnh.")
                impact -= 0.5

            vol_ratio = (volume.get("stats", {}) or {}).get("vol_ratio_vs_ma20") or 1.0
            if vol_ratio < 0.7:
                arguments.append(
                    f"📊 Khối lượng sụt giảm (chỉ {vol_ratio:.1f}x trung bình) — thiếu sự xác nhận từ dòng tiền. "
                    f"Mọi đợt tăng giá thiếu khối lượng đều là 'bẫy tăng' (bull trap)."
                )
                impact -= 1.5

            risk_score = risk.get("risk_score") or 50
            max_dd = (risk.get("metrics", {}) or {}).get("max_drawdown") or 0.0
            if risk_score > 60:
                arguments.append(f"🔴 Điểm rủi ro = {risk_score}/100. Max Drawdown lịch sử = -{max_dd:.1f}%. Rủi ro quá cao so với cơ hội.")
                impact -= 1.5

            news_sent = news.get("overall_sentiment", "")
            if "NEGATIVE" in news_sent:
                arguments.append(f"📰 Tin tức tiêu cực ({news_sent}) — môi trường macro bất lợi, áp lực bán từ bên ngoài.")
                impact -= 1.0

            if not arguments:
                arguments.append("⚠️ Thị trường đang ở trạng thái không rõ ràng — tốt nhất là đứng ngoài quan sát thay vì mạo hiểm.")
                impact -= 0.2

        elif round_num == 2:
            # Phiên 2: Phản bác lập luận BULL từ phiên 1
            bull_stmts = " ".join([a.statement for a in bull_prev])
            if "dòng tiền" in bull_stmts.lower() or "volume" in bull_stmts.lower():
                arguments.append(
                    "🔄 Phản bác Bull về dòng tiền: Dòng tiền vào có thể là tạm thời do các quỹ đang rebalance. "
                    "Cần xem xét tính bền vững của dòng tiền, không chỉ điểm dữ liệu ngắn hạn."
                )
                impact -= 1.0
            if "hỗ trợ" in bull_stmts.lower() or "mua" in bull_stmts.lower():
                levels = sr.get("levels", {})
                s1 = levels.get("support_1", 0)
                arguments.append(
                    f"🔄 Phản bác Bull về vùng hỗ trợ: Mức S1 = {s1:,.2f} VNĐ có thể bị phá vỡ "
                    f"nếu áp lực bán gia tăng. Hỗ trợ kỹ thuật không phải bức tường bất khả xâm phạm."
                )
                impact -= 1.0
            rsi = momentum.get("indicators_summary", {}).get("RSI")
            if rsi and rsi > 55:
                arguments.append(
                    f"🔄 RSI = {rsi:.1f} — giá đã không còn rẻ. Mua đuổi ở vùng này tăng rủi ro bị 'kẹp hàng' khi điều chỉnh."
                )
                impact -= 0.8

        elif round_num == 3:
            # Phiên 3: Kết luận Bear
            vol = (risk.get("metrics", {}) or {}).get("volatility_annual") or 0.0
            arguments.append(
                f"🏁 Kết luận BEAR: Với biến động hàng năm {vol:.1f}% và nhiều yếu tố rủi ro chưa được giải quyết, "
                f"chiến lược thận trọng (chờ đợi / giảm tỷ trọng) là tối ưu hơn là mua mới. "
                f"Kiên nhẫn là lợi thế cạnh tranh của nhà đầu tư cá nhân."
            )
            impact -= 0.8

        return DebateArgument(
            agent_name=self.NAME, stance=self.STANCE, round_num=round_num,
            statement=" | ".join(arguments) if arguments else "Không có lập luận mới.",
            score_impact=round(impact, 2)
        )


# ─────────────────────────────────────────────────────────────────────
# DEVIL'S ADVOCATE AGENT
# Nhiệm vụ: Thách thức cả 2 phe, đặt câu hỏi sắc bén về các điểm mù
# ─────────────────────────────────────────────────────────────────────
class DevilsAdvocateAgent:
    NAME = "😈 Devil's Advocate Agent"
    STANCE = "NEUTRAL"

    def challenge(self, analyses: dict, bull_args: list[DebateArgument],
                  bear_args: list[DebateArgument]) -> DebateArgument:
        risk     = analyses.get("risk", {})
        trend    = analyses.get("trend", {})
        momentum = analyses.get("momentum", {})
        news     = analyses.get("news", {})

        challenges = []
        impact = 0.0

        # Thách thức về tính nhất quán dữ liệu
        rsi = momentum.get("indicators_summary", {}).get("RSI")
        t = trend.get("trend", "")
        if rsi and "UPTREND" in t and rsi > 65:
            challenges.append(
                f"❓ Mâu thuẫn dữ liệu: RSI = {rsi:.1f} (gần quá mua) nhưng trend vẫn UPTREND. "
                "Câu hỏi: Xu hướng tăng này còn dư địa bao nhiêu? Hay đã 'late to the party'?"
            )
            impact -= 0.5

        # Thách thức về thông tin bất cân xứng
        total_news = news.get("total_articles", 0)
        if total_news < 10:
            challenges.append(
                "❓ Thách thức về dữ liệu tin tức: Số lượng tin tức quá ít. "
                "Liệu có thông tin nội bộ hay sự kiện sắp diễn ra mà chúng ta chưa nắm được không?"
            )
            impact -= 0.3

        # Thách thức về thiên lệch nhận thức
        bull_total = sum(a.score_impact for a in bull_args)
        bear_total = abs(sum(a.score_impact for a in bear_args))
        if bull_total > bear_total * 1.5:
            challenges.append(
                f"❓ Cảnh báo thiên lệch xác nhận (Confirmation Bias): Lập luận BULL mạnh hơn BEAR đáng kể "
                f"({bull_total:.1f} vs {bear_total:.1f}). Hãy tự hỏi: Chúng ta đang tìm kiếm bằng chứng xác nhận điều mình muốn tin?"
            )
            impact -= 0.5

        # Thách thức về black swan
        vol = risk.get("metrics", {}).get("volatility_annual", 30)
        max_dd = risk.get("metrics", {}).get("max_drawdown", 15)
        challenges.append(
            f"❓ Black Swan Risk: Biến động {vol:.1f}%/năm và MaxDD -{max_dd:.1f}% cho thấy tài sản này "
            "có thể giảm mạnh bất ngờ. Mô hình kỹ thuật thường thất bại trước các sự kiện đuôi (tail events)."
        )
        impact -= 0.2

        # Câu hỏi về timing
        challenges.append(
            "❓ Vấn đề Timing: Ngay cả khi phân tích đúng về HƯỚNG, timing sai vẫn dẫn đến thua lỗ. "
            "Cả Bull lẫn Bear đều không nên bỏ qua yếu tố 'đúng lúc đúng chỗ'."
        )

        return DebateArgument(
            agent_name=self.NAME, stance=self.STANCE, round_num=2,
            statement=" | ".join(challenges),
            score_impact=round(impact, 2)
        )


# ─────────────────────────────────────────────────────────────────────
# DEBATE MODERATOR (Chủ toạ Phiên tranh luận)
# Điều phối 3 phiên tranh luận, tổng kết và đưa ra điều chỉnh cuối
# ─────────────────────────────────────────────────────────────────────
class DebateModerator:
    """
    Chủ toạ điều phối toàn bộ phiên tranh luận 3 vòng:
    - Vòng 1: Bull & Bear mở bài lập luận
    - Vòng 2: Phản biện chéo + Devil's Advocate thách thức
    - Vòng 3: Tóm lược và kết luận điều chỉnh điểm
    """
    NAME = "⚖️ Debate Moderator"

    def __init__(self):
        self.bull  = BullAdvocateAgent()
        self.bear  = BearAdvocateAgent()
        self.devil = DevilsAdvocateAgent()

    def run_debate(self, analyses: dict, initial_score: float) -> DebateVerdict:
        all_rounds: list[list[DebateArgument]] = []
        bull_history: list[DebateArgument] = []
        bear_history: list[DebateArgument] = []

        # ── Vòng 1: Khai mạc — mỗi phe trình bày lập luận mạnh nhất ──
        r1_bull = self.bull.argue(analyses, round_num=1, bear_prev=[])
        r1_bear = self.bear.argue(analyses, round_num=1, bull_prev=[])
        bull_history.append(r1_bull)
        bear_history.append(r1_bear)
        all_rounds.append([r1_bull, r1_bear])

        # ── Vòng 2: Phản biện chéo + Devil's Advocate ──────────────────
        r2_bull  = self.bull.argue(analyses, round_num=2, bear_prev=bear_history)
        r2_bear  = self.bear.argue(analyses, round_num=2, bull_prev=bull_history)
        r2_devil = self.devil.challenge(analyses, bull_history, bear_history)
        bull_history.append(r2_bull)
        bear_history.append(r2_bear)
        all_rounds.append([r2_bull, r2_bear, r2_devil])

        # ── Vòng 3: Kết luận ────────────────────────────────────────────
        r3_bull = self.bull.argue(analyses, round_num=3, bear_prev=bear_history)
        r3_bear = self.bear.argue(analyses, round_num=3, bull_prev=bull_history)
        all_rounds.append([r3_bull, r3_bear])

        # ── Tính toán điều chỉnh điểm ───────────────────────────────────
        bull_total = sum(a.score_impact for a in bull_history + [r3_bull])
        bear_total = sum(a.score_impact for a in bear_history + [r3_bear])
        devil_adj  = r2_devil.score_impact

        # Điều chỉnh cuối: Trọng số Bull 40% + Bear 40% + Devil 20%
        debate_adjustment = (bull_total * 0.4 + bear_total * 0.4 + devil_adj * 0.2)
        debate_adjustment = max(-8, min(8, debate_adjustment))  # giới hạn ±8 điểm

        # ── Tổng hợp điểm rủi ro và cơ hội ─────────────────────────────
        key_risks = []
        key_opportunities = []

        risk = analyses.get("risk", {})
        trend = analyses.get("trend", {})
        momentum = analyses.get("momentum", {})

        vol = (risk.get("metrics", {}) or {}).get("volatility_annual") or 0.0
        max_dd = (risk.get("metrics", {}) or {}).get("max_drawdown") or 0.0
        sharpe = (risk.get("metrics", {}) or {}).get("sharpe_ratio") or 0.0
        rsi = (momentum.get("indicators_summary", {}) or {}).get("RSI") or 50.0

        if max_dd > 20: key_risks.append(f"Max Drawdown cao: -{max_dd:.1f}%")
        if vol > 35:    key_risks.append(f"Biến động hàng năm cao: {vol:.1f}%")
        if rsi > 70:    key_risks.append(f"RSI quá mua: {rsi:.1f} — nguy cơ điều chỉnh")
        # Ở đây từng có: `if bull_total < 0: key_risks.append(...)`.
        # Gỡ 28/08/2026 — nhánh KHÔNG THỂ chạy. Bull cộng vô điều kiện
        # +0,5 (vòng 2) và +1,0 (vòng 3), mọi nhánh khác chỉ `+=`, nên
        # sàn của `bull_total` là +1,5; đo 262 lượt thật thấy thấp nhất
        # +1,50. Ý ĐỊNH của nó — cảnh báo khi phe tăng yếu hơn phe giảm
        # — vẫn hợp lý, nhưng phải viết theo `bull_total + bear_total`
        # (hai phe ngược dấu), không phải so bull_total với 0. Chưa
        # viết lại vì làm vậy là ĐỔI cảnh báo hiển thị, cần người quyết.
        # Quy ước dấu được gác ở tests/test_dau_hieu_tranh_luan.py.
        key_risks.append("Rủi ro sự kiện vĩ mô bất ngờ (FED, NHNN, địa chính trị)")

        if sharpe > 1:   key_opportunities.append(f"Sharpe Ratio tốt: {sharpe:.2f} — hiệu quả sinh lời lịch sử")
        if rsi < 40:     key_opportunities.append(f"RSI quá bán: {rsi:.1f} — vùng tích lũy hấp dẫn")
        t = trend.get("trend", "")
        if "UPTREND" in t: key_opportunities.append(f"Xu hướng {t} được xác nhận bởi nhiều chỉ báo")
        key_opportunities.append("Chiến lược mua từng phần (DCA) giảm thiểu rủi ro timing")
        key_opportunities.append("Stop-loss kỷ luật bảo vệ vốn, giữ tỷ lệ Risk:Reward tích cực")

        # ── Đánh giá độ tin cậy của toàn bộ phân tích ───────────────────
        agreement = abs(bull_total + bear_total)  # gần 0 = hai phe đồng thuận nhau
        if agreement < 2:
            confidence = "RẤT CAO 🟢"   # hai phe gần như đồng ý
        elif agreement < 4:
            confidence = "CAO 🟡"
        elif agreement < 6:
            confidence = "TRUNG BÌNH 🟠"
        else:
            confidence = "THẤP 🔴"      # hai phe tranh luận gay gắt, không chắc chắn

        # ── Tóm tắt phán quyết ──────────────────────────────────────────
        adj_score = initial_score + debate_adjustment
        if adj_score >= 70:
            direction = "TĂNG"
        elif adj_score >= 50:
            direction = "TRUNG TÍNH NGHIÊNG TĂNG"
        elif adj_score >= 35:
            direction = "TRUNG TÍNH NGHIÊNG GIẢM"
        else:
            direction = "GIẢM"

        verdict_summary = (
            f"Sau {sum(len(r) for r in all_rounds)} lượt tranh luận từ 3 Agent đối lập, "
            f"Phán quyết Debate Council: Xu hướng {direction}. "
            f"Bull Score: {bull_total:+.1f} | Bear Score: {bear_total:+.1f} | Devil Adj: {devil_adj:+.1f}. "
            f"Điều chỉnh điểm: {debate_adjustment:+.1f} | Độ tin cậy: {confidence}."
        )

        return DebateVerdict(
            bull_score=round(bull_total, 2),
            bear_score=round(bear_total, 2),
            final_adjustment=round(debate_adjustment, 2),
            rounds=all_rounds,
            verdict_summary=verdict_summary,
            key_risks=key_risks,
            key_opportunities=key_opportunities,
            confidence_level=confidence,
        )


# ─────────────────────────────────────────────────────────────────────
# AGENTIC SAFETY HARNESS GUARDRAILS (Tầng 4: Khung Giám sát An toàn)
# ─────────────────────────────────────────────────────────────────────
class SafetyHarnessGuardrails:
    """
    Tầng Khung An toàn (Safety Harness) kiểm tra các quy tắc bất biến:
    1. Giới hạn lỗ tối đa (Hard ATR Stop-Loss Enforcement)
    2. Phân bổ vị thế an toàn (Max Position Sizing <= 25%)
    3. Bộ lọc chống hoảng loạn (Anti-Panic Shakeout Filter)
    """
    NAME = "🛡️ Safety Harness Guardrails"

    def evaluate_safety(self, analyses: dict, initial_verdict_score: float) -> dict:
        risk = analyses.get("risk", {})
        recommendations = risk.get("recommendations", {})
        sl_pct = recommendations.get("stop_loss_pct", 7.0)
        pos_size = recommendations.get("suggested_position_size_pct", 15.0)

        safety_violations = []
        is_safe = True
        adjusted_score = initial_verdict_score

        # Rule 1: Khống chế tỷ lệ lỗ tối đa không quá 10%
        if sl_pct > 10.0:
            safety_violations.append(f"🔴 Vi phạm Risk Guardrail: Mức Stop-loss {sl_pct}% vượt trần 10%. Ép giảm tỷ trọng.")
            pos_size = min(pos_size, 10.0)
            is_safe = False

        # Rule 2: Khống chế quy mô vị thế tối đa 25% danh mục
        if pos_size > 25.0:
            safety_violations.append(f"⚠️ Vi phạm Position Sizing: Tỷ lệ vốn {pos_size}% quá cao. Harness hạ xuống 20%.")
            pos_size = 20.0

        # Rule 3: Bộ lọc rủi ro bẫy giá (Bull Trap Risk Adjustment)
        trend = analyses.get("trend", {})
        if "DOWNTREND" in trend.get("trend", "") and initial_verdict_score > 60:
            safety_violations.append("🛡️ Harness Warning: Xu hướng chung là DOWNTREND nhưng điểm MUA cao. Trừ 10 điểm phạt rủi ro Bull Trap.")
            adjusted_score -= 10.0
            is_safe = False

        return {
            "is_safe": is_safe,
            "adjusted_score": max(5.0, min(95.0, adjusted_score)),
            "safe_position_size": pos_size,
            "safety_violations": safety_violations
        }


# ─────────────────────────────────────────────────────────────────────
# GHI CHÚ THIẾT KẾ — Post-Mortem / Feedback Loop (CHƯA TRIỂN KHAI)
# ─────────────────────────────────────────────────────────────────────
# Sơ đồ kiến trúc có mô tả một tầng "Post-Mortem Learning" tự rút kinh
# nghiệm từ các lần thua (bull trap, chạm stop-loss, thiên nga đen) rồi
# điều chỉnh trọng số cho các phiên sau.
#
# Bản cài đặt cũ (class PostMortemLearningAgent) đã bị gỡ vì:
#   1. Nó chỉ trả về dict cứng theo if/else, không ghi vào bất kỳ đâu.
#      "Negative Memory DB" mà docstring nhắc tới chưa từng tồn tại.
#   2. Không nơi nào gọi nó — chỉ được khởi tạo rồi bỏ đó.
#   3. Nếu bật lên nguyên trạng, nó sẽ GÂY HẠI: tăng trọng số Bear sau
#      mỗi lần thua gần đây là học theo chế độ thị trường vừa qua, không
#      phải học quy luật. Thị trường đảo chiều thì logic này sai ngược.
#
# ĐIỀU KIỆN để triển khai thật (đừng bật trước khi có đủ):
#   - Có backtest chứng minh hệ thống chấm điểm hiện tại có giá trị.
#   - Có cách đo tách bạch "kỹ năng" khỏi "may rủi thị trường chung".
#   - Có cơ chế phát hiện chế độ thị trường đổi để vô hiệu bài học cũ.

