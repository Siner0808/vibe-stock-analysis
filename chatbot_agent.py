"""
chatbot_agent.py
──────────────────────────────────────────────────────────────────────
Trợ lý AI Chatbot Phân tích Chứng khoán tích hợp Google Gemini API
(Context-Aware Gemini LLM AI Stock Assistant)
Tự động nạp ngữ cảnh kết quả phân tích Multi-Agent 5 Tầng và kết nối
Google Gemini LLM (gemini-1.5-flash / gemini-2.0-flash) để phản hồi tự nhiên.
──────────────────────────────────────────────────────────────────────
"""
import os
import json
import requests

class StockChatbotAgent:
    """
    Agent Trợ lý AI Chatbot thông minh dùng Gemini API:
    Kết nối trực tiếp tới Google Gemini LLM để trả lời các câu hỏi về chứng khoán,
    lập luận 5 Tầng Multi-Agent và chiến lược quản trị rủi ro.
    """
    NAME = "💬 AI Stock Assistant Chatbot (Gemini Powered)"

    def __init__(self, api_key: str = None):
        self.api_key = (
            api_key 
            or os.environ.get("GEMINI_API_KEY") 
            or os.environ.get("GOOGLE_API_KEY")
        )

    def _call_gemini_api(self, system_instruction: str, user_prompt: str) -> str:
        """Gọi trực tiếp Google Gemini REST API (gemini-1.5-flash / gemini-2.0-flash)"""
        if not self.api_key:
            return None

        # Endpoint Google Gemini v1beta REST API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{system_instruction}\n\n---\nCâu hỏi của nhà đầu tư: {user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024
            }
        }

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            elif res.status_code == 400 or res.status_code == 403:
                # API Key không hợp lệ hoặc bị chặn
                return None
        except Exception:
            pass

        # Thử thư viện SDK google.generativeai nếu REST API gặp sự cố
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"{system_instruction}\n\nCâu hỏi: {user_prompt}"
            resp = model.generate_content(full_prompt)
            if resp and resp.text:
                return resp.text
        except Exception:
            pass

        return None

    def answer_question(self, user_prompt: str, result: dict, user_api_key: str = None) -> str:
        if user_api_key:
            self.api_key = user_api_key

        if not result or result.get("data_quality") == "FAILED":
            return (
                "⚠️ Hiện tại chưa có dữ liệu phân tích Multi-Agent cho mã cổ phiếu này "
                "hoặc kết nối dữ liệu bị gián đoạn. Vui lòng bấm nút **🚀 Chạy phân tích Multi-Agent** ở thanh Sidebar để cập nhật dữ liệu trước khi chat nhé!"
            )

        symbol = result.get("symbol", "Cổ phiếu")
        exchange = result.get("exchange", "HOSE")
        score = result.get("final_score", 50)
        rec = result.get("recommendation", "NẮM GIỮ")
        breakdown = result.get("score_breakdown", {})
        reasons = result.get("key_reasons", [])
        debate = result.get("debate", {})
        analyses = result.get("analyses", {})

        # Tạo System Context phong phú nạp toàn bộ kết quả phân tích 5 Tầng
        system_context = f"""
Bạn là Trợ lý AI Chuyên gia Phân tích Chứng khoán Việt Nam chuyên nghiệp (Vibe Stock Assistant Powered by Gemini).
Bạn đang phân tích trực tiếp mã chứng khoán: [{symbol}] (Sàn {exchange}).

DỮ LIỆU PHÂN TÍCH MULTI-AGENT 5 TẦNG MỚI NHẤT:
- Điểm tổng hợp đồng thuận: {score}/100
- Khuyến nghị hành động chính thức: {rec}
- Các lý do cốt lõi từ Master Agent: {json.dumps(reasons, ensure_ascii=False)}
- Điểm chi tiết 6 Agent:
  + Trend (Xu hướng): {breakdown.get('trend_score', 50)}/100
  + Momentum (Động lượng): {breakdown.get('momentum_score', 50)}/100
  + Volume (Khối lượng): {breakdown.get('volume_score', 50)}/100
  + Support & Resistance (Kháng cự/Hỗ trợ): {breakdown.get('sr_score', 50)}/100
  + Risk (Rủi ro): {breakdown.get('risk_score', 50)}/100
  + News (Sentiment tin tức): {breakdown.get('news_score', 50)}/100

DỮ LIỆU DEBATE COUNCIL & SAFETY HARNESS:
- Kết quả Tranh luận Khẩn cấp: Bull Score ({debate.get('bull_score', 0)}), Bear Score ({debate.get('bear_score', 0)}), Tóm tắt: "{debate.get('verdict_summary', '')}"
- Rủi ro lớn nhất: {json.dumps(debate.get('key_risks', []), ensure_ascii=False)}
- Cơ hội lớn nhất: {json.dumps(debate.get('key_opportunities', []), ensure_ascii=False)}
- Dữ liệu Quản trị rủi ro ATR: Stop-loss price ({analyses.get('risk', {}).get('recommendations', {}).get('stop_loss_price', 'N/A')}), Position Sizing ({analyses.get('risk', {}).get('recommendations', {}).get('suggested_position_size_pct', 15)}%).

NHIỆM VỤ CỦA BẠN:
1. Trả lời câu hỏi của nhà đầu tư một cách sắc bén, ngắn gọn, khách quan và khoa học dựa trên dữ liệu 5 Tầng trên.
2. Luôn giữ kỷ luật quản trị rủi ro (không bao giờ khuyên nới Stop-loss hay bắt đáy vô căn cứ khi đang Downtrend/Bán).
3. Trả lời bằng tiếng Việt trình bày chuẩn GitHub Markdown, sử dụng icon sinh động.
"""

        # Thử gọi Gemini LLM
        gemini_response = self._call_gemini_api(system_context, user_prompt)
        if gemini_response:
            return gemini_response

        # ── FALLBACK ENGINE (Nếu chưa nạp Gemini API Key hoặc lỗi mạng API) ────
        prompt_lower = user_prompt.lower()
        reasons_str = "\n".join([f"• {r}" for r in reasons])

        if any(w in prompt_lower for w in ["tại sao", "tai sao", "khuyên nghị", "khuyen nghi", "lý do", "ly do", "sao lại"]):
            return f"""
🤖 **[Gemini Engine Fallback] Trả lời giải thích Khuyến nghị cho [{symbol}]:**

• **Điểm đồng thuận 5 Tầng:** `{score}/100`  
• **Khuyến nghị chính thức:** **{rec}** (Sàn: {exchange})

**Các luận điểm chính từ Master Agent:**
{reasons_str}

**Điểm chi tiết từng Agent:**
- 📈 Trend: `{breakdown.get('trend_score', 50)}/100` | ⚡ Momentum: `{breakdown.get('momentum_score', 50)}/100`
- 📊 Volume: `{breakdown.get('volume_score', 50)}/100` | 📍 S&R: `{breakdown.get('sr_score', 50)}/100`
- 🛡️ Risk: `{breakdown.get('risk_score', 50)}/100` | 📰 News: `{breakdown.get('news_score', 50)}/100`

🔑 *Mẹo: Nhập Gemini API Key ở Sidebar để mở khóa Gemini LLM thông minh 100%!*
"""
        elif any(w in prompt_lower for w in ["stop-loss", "stop loss", "cắt lỗ", "cat lo", "chốt lời", "chot loi", "vốn", "von"]):
            risk_recs = analyses.get("risk", {}).get("recommendations", {})
            return f"""
🛡️ **[Gemini Engine Fallback] Quản trị Rủi ro & Đi vốn cho [{symbol}]:**

1. 🛑 **Hard Stop-Loss (Cắt lỗ kỷ luật):** `{risk_recs.get('stop_loss_price', 0):,.2f} VNĐ` (`-{risk_recs.get('stop_loss_pct', 7.0)}%`).
2. 🎯 **Take-Profit (Chốt lời mục tiêu):** `{risk_recs.get('take_profit_price', 0):,.2f} VNĐ` (`+{risk_recs.get('take_profit_pct', 15.0)}%`).
3. 💰 **Tỷ lệ Đi vốn an toàn:** Max **`{risk_recs.get('suggested_position_size_pct', 15.0)}%`** danh mục.

🔑 *Mẹo: Nhập Gemini API Key ở Sidebar để mở khóa Gemini LLM thông minh 100%!*
"""
        else:
            return f"""
🤖 **[Gemini Engine Fallback] Trợ lý AI cho mã [{symbol}]:**

Mã **{symbol}** có điểm đồng thuận **{score}/100** với khuyến nghị **{rec}**.
Luận điểm chính: {reasons[0] if reasons else 'Đang theo dõi tín hiệu thị trường.'}

🔑 *Bạn có thể nhập **Gemini API Key** ở thanh Sidebar để kích hoạt Gemini LLM trả lời tự nhiên và sâu sắc nhất!*
"""
