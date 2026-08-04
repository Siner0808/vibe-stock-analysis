"""
chatbot_agent.py
──────────────────────────────────────────────────────────────────────
Trợ lý AI Chatbot Phân tích Chứng khoán (Context-Aware AI Stock Assistant)
Tự động tích hợp kết quả phân tích Multi-Agent 5 Tầng để trả lời
mọi thắc mắc của nhà đầu tư theo thời gian thực.
──────────────────────────────────────────────────────────────────────
"""
import re

class StockChatbotAgent:
    """
    Agent Trợ lý AI Chatbot thông minh:
    Giải thích kết quả phân tích, khuyến nghị đầu tư, tranh luận Bull/Bear,
    và tư vấn quản trị rủi ro dựa trên ngữ cảnh Multi-Agent.
    """
    NAME = "💬 AI Stock Assistant Chatbot"

    def answer_question(self, user_prompt: str, result: dict) -> str:
        if not result or result.get("data_quality") == "FAILED":
            return (
                "⚠️ Hiện tại chưa có dữ liệu phân tích Multi-Agent cho mã cổ phiếu này "
                "hoặc kết nối dữ liệu bị gián đoạn. Vui lòng bấm nút **🚀 Chạy phân tích Multi-Agent** ở thanh Sidebar để cập nhật dữ liệu mới nhất trước khi chat với tôi nhé!"
            )

        prompt_lower = user_prompt.lower()
        symbol = result.get("symbol", "cổ phiếu")
        exchange = result.get("exchange", "HOSE")
        score = result.get("final_score", 50)
        rec = result.get("recommendation", "NẮM GIỮ")
        breakdown = result.get("score_breakdown", {})
        reasons = result.get("key_reasons", [])
        debate = result.get("debate", {})
        analyses = result.get("analyses", {})

        # ── HỎI VỀ KHUYẾN NGHỊ / TẠI SAO BÁN HOẶC MUA ───────────────────
        if any(w in prompt_lower for w in ["tại sao", "tai sao", "khuyên nghị", "khuyen nghi", "lý do", "ly do", "sao lại"]):
            reasons_str = "\n".join([f"• {r}" for r in reasons])
            return f"""
🤖 **Giải thích Khuyến nghị cho mã [{symbol}]:**

• **Điểm đồng thuận 5 Tầng:** `{score}/100`  
• **Phán quyết cuối:** **{rec}** (Sàn: {exchange})

**Các luận điểm chính từ Master Agent:**
{reasons_str}

**Chi tiết điểm số từng Agent:**
- 📈 Trend (Xu hướng): `{breakdown.get('trend_score', 50)}/100`
- ⚡ Momentum (Động lượng): `{breakdown.get('momentum_score', 50)}/100`
- 📊 Volume (Khối lượng): `{breakdown.get('volume_score', 50)}/100`
- 📍 S&R (Vùng hỗ trợ/kháng cự): `{breakdown.get('sr_score', 50)}/100`
- 🛡️ Risk (Rủi ro): `{breakdown.get('risk_score', 50)}/100`
- 📰 News (Sentiment tin tức): `{breakdown.get('news_score', 50)}/100`

💡 *Nếu điểm dưới 45, hệ thống sẽ khuyến nghị BÁN/KHÔNG MUA để bảo vệ vị thế vốn trước các rủi ro kỹ thuật hoặc bẫy giá (Bull Trap).*
"""

        # ── HỎI VỀ STOP-LOSS / CẮT LỖ / ĐI VỐN ──────────────────────────
        elif any(w in prompt_lower for w in ["stop-loss", "stop loss", "cắt lỗ", "cat lo", "chốt lời", "chot loi", "vốn", "von", "quản trị", "quan tri"]):
            risk_data = analyses.get("risk", {})
            recs = risk_data.get("recommendations", {})
            sl_p = recs.get("stop_loss_price", 0)
            sl_pct = recs.get("stop_loss_pct", 7.0)
            tp_p = recs.get("take_profit_price", 0)
            tp_pct = recs.get("take_profit_pct", 15.0)
            pos_sz = recs.get("suggested_position_size_pct", 15.0)
            rr = recs.get("risk_reward_ratio", "2.1:1")

            return f"""
🛡️ **Khung Quản trị Rủi ro & Đi vốn (Safety Harness) cho [{symbol}]:**

1. 🛑 **Mức Cắt lỗ kỷ luật (Hard Stop-Loss):**
   - Giá cắt lỗ: `{sl_p:,.2f} VNĐ` (tương đương `-{sl_pct}%` từ điểm vào).
   - Quy tắc Safety Harness: Tuyệt đối không nới Stop-loss khi giá vi phạm ngưỡng kỷ luật!

2. 🎯 **Mức Chốt lời mục tiêu (Take-Profit):**
   - Giá mục tiêu: `{tp_p:,.2f} VNĐ` (tương đương `+{tp_pct}%`).
   - Tỷ lệ Risk : Reward = `{rr}`.

3. 💰 **Tỷ lệ Phân bổ vốn an toàn (Position Sizing):**
   - Khuyến nghị đi vốn: Max **`{pos_sz}%`** tổng giá trị danh mục.
   - Không gia tăng tỷ trọng khi cổ phiếu đang trong xu hướng giảm (Downtrend).
"""

        # ── HỎI VỀ TRANH LUẬN BULL / BEAR / DEBATE ───────────────────────
        elif any(w in prompt_lower for w in ["tranh luận", "tranh luan", "debate", "bull", "bear", "đối lập", "doi lap"]):
            if not debate:
                return "⚠️ Hiện chưa có dữ liệu chi tiết từ Debate Council."
            
            b_score = debate.get("bull_score", 0)
            be_score = debate.get("bear_score", 0)
            conf = debate.get("confidence_level", "TRUNG BÌNH")
            risks = "\n".join([f"• {r}" for r in debate.get("key_risks", [])])
            opps = "\n".join([f"• {o}" for o in debate.get("key_opportunities", [])])

            return f"""
⚖️ **Kết quả Tranh luận Khẩn cấp (Debate Council) cho [{symbol}]:**

• **Bull Advocate Score (🐂):** `{b_score:+.1f}` điểm  
• **Bear Advocate Score (🐻):** `{be_score:+.1f}` điểm  
• **Độ tin cậy của Hội đồng:** `{conf}`

🔴 **Rủi ro lớn nhất do Bear Agent & Devil's Advocate đưa ra:**
{risks}

🟢 **Cơ hội lớn nhất do Bull Agent đưa ra:**
{opps}

💡 *Tóm tắt:* {debate.get('verdict_summary', '')}
"""

        # ── HỎI VỀ TIN TỨC / VI MÔ ───────────────────────────────────────
        elif any(w in prompt_lower for w in ["tin tức", "tin tuc", "news", "vĩ mô", "vi mo", "sentiment"]):
            news_data = analyses.get("news", {})
            total_art = news_data.get("total_articles", 0)
            overall_s = news_data.get("overall_sentiment", "N/A")
            top_pos = news_data.get("top_positive", [])
            top_neg = news_data.get("top_negative", [])

            pos_titles = "\n".join([f"• {a['title'][:70]}... ({a['source']})" for a in top_pos[:2]])
            neg_titles = "\n".join([f"• {a['title'][:70]}... ({a['source']})" for a in top_neg[:2]])

            return f"""
📰 **Tổng hợp Tin tức & Sentiment cho mã [{symbol}]:**

• **Tổng số bài báo đã thu thập:** `{total_art}` bài  
• **Sentiment chung:** `{overall_s}`

✅ **Tin tức tích cực tiêu biểu:**
{pos_titles if pos_titles else "• Chưa ghi nhận tin tức tích cực đột biến."}

🔴 **Tin tức rủi ro / tiêu cực tiêu biểu:**
{neg_titles if neg_titles else "• Chưa ghi nhận tin tức tiêu cực lớn."}
"""

        # ── CÂU HỎI TỔNG QUÁT / TƯ VẤN CÓ NÊN MUA KHÔNG ───────────────────
        else:
            return f"""
🤖 **Trả lời từ AI Stock Assistant cho mã [{symbol}]:**

Dựa trên phân tích 5 Tầng mới nhất cho mã **{symbol}**:
- **Khuyến nghị hiện tại:** **{rec}** (Điểm số: `{score}/100`).
- **Xu hướng chính:** `{reasons[0] if reasons else 'Đang cập nhật'}`.
- **Lời khuyên hành động:** 
  {"• Nếu bạn ĐANG CÓ HÀNG: Nên xem xét chốt lời / hạ tỷ trọng hoặc cắt lỗ bảo vệ vốn." if score < 50 else "• Nếu bạn ĐANG MUỐN MUA: Có thể tham khảo tích lũy từng phần (DCA) theo vùng hỗ trợ."}

💬 *Bạn có thể hỏi thêm tôi về:*
1. *"Tại sao mã này lại cho khuyến nghị {rec}?"*
2. *"Mức Stop-loss và tỷ lệ phân bổ vốn an toàn là bao nhiêu?"*
3. *"Phe Bull và Bear tranh luận những gì về {symbol}?"*
"""
