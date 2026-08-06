"""
chatbot_agent.py
──────────────────────────────────────────────────────────────────────
Trợ lý AI Chatbot Phân tích Chứng khoán tích hợp Google Gemini API
(Context-Aware Gemini LLM AI Stock Assistant)
Tự động nạp ngữ cảnh kết quả phân tích Multi-Agent 5 Tầng và kết nối
Google Gemini LLM (gemini-flash-latest / gemini-2.0-flash-lite)
để phản hồi thông minh thời gian thực.
──────────────────────────────────────────────────────────────────────
"""
import os
import json
import requests


def load_system_api_key() -> str | None:
    """Đọc API key hệ thống từ cấu hình ngoài. KHÔNG bao giờ hardcode key vào mã nguồn.

    Thứ tự ưu tiên:
      1. st.secrets["GEMINI_API_KEY"]  (.streamlit/secrets.toml — đã gitignore)
      2. biến môi trường GEMINI_API_KEY
      3. biến môi trường GOOGLE_API_KEY

    Trả về None nếu chưa cấu hình. Khi đó chatbot dùng _fallback_answer()
    (engine nội bộ, không cần LLM) thay vì im lặng hỏng.
    """
    try:
        import streamlit as st
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        # Không chạy trong Streamlit, hoặc chưa có secrets.toml — bỏ qua.
        pass
    return (os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or None)

class StockChatbotAgent:
    """
    Agent Trợ lý AI Chatbot thông minh dùng Gemini API:
    Kết nối trực tiếp tới Google Gemini LLM để trả lời các câu hỏi về chứng khoán,
    lập luận 5 Tầng Multi-Agent và chiến lược quản trị rủi ro.
    """
    NAME = "💬 AI Stock Assistant Chatbot (Gemini Powered)"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or load_system_api_key()

    def _call_gemini_api(self, system_instruction: str, user_prompt: str) -> tuple[bool, str]:
        """
        Gọi Google Gemini REST API hỗ trợ thử nghiệm các mô hình khả dụng:
        gemini-flash-latest, gemini-2.0-flash-lite, gemini-2.0-flash-001, gemini-flash-lite-latest, gemini-pro-latest
        """
        clean_key = (self.api_key or "").strip()
        if not clean_key:
            return False, "NO_KEY"

        models_to_try = [
            "gemini-flash-latest",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash-001",
            "gemini-flash-lite-latest",
            "gemini-pro-latest"
        ]

        last_error = ""
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
                "maxOutputTokens": 8192
            }
        }

        # Thử qua REST API với mô hình khả dụng đã kiểm tra
        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return True, parts[0].get("text", "")
                else:
                    err_json = {}
                    try:
                        err_json = res.json()
                    except Exception:
                        pass
                    msg = err_json.get("error", {}).get("message", res.text[:150])
                    last_error = f"HTTP {res.status_code} ({model_name}): {msg}"
            except Exception as e:
                last_error = f"Lỗi kết nối ({model_name}): {str(e)}"

        return False, last_error

    def answer_question(self, user_prompt: str, result: dict, user_api_key: str = None) -> str:
        if user_api_key and user_api_key.strip():
            self.api_key = user_api_key.strip()

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
- Dữ liệu Quản trị rủi ro ATR: Entry price ({analyses.get('risk', {}).get('recommendations', {}).get('entry_price', 'N/A')}), Stop-loss price ({analyses.get('risk', {}).get('recommendations', {}).get('stop_loss_price', 'N/A')}), Take-profit price ({analyses.get('risk', {}).get('recommendations', {}).get('take_profit_price', 'N/A')}), Position Sizing ({analyses.get('risk', {}).get('recommendations', {}).get('suggested_position_size_pct', 15)}%).

NHIỆM VỤ CỦA BẠN:
1. Trả lời câu hỏi của nhà đầu tư một cách sắc bén, súc tích (khoảng 300 - 450 từ), khách quan và khoa học dựa trên dữ liệu 5 Tầng trên.
2. Luôn giữ kỷ luật quản trị rủi ro (không bao giờ khuyên nới Stop-loss hay bắt đáy vô căn cứ khi đang Downtrend/Bán).
3. Trả lời bằng tiếng Việt trình bày chuẩn GitHub Markdown, sử dụng icon sinh động.
4. Đảm bảo HOÀN THÀNH TRỌN VẸN câu trả lời, có kết bài rõ ràng, tuyệt đối không bao giờ được dừng giữa chừng.
"""

        # Gọi Gemini LLM API
        success, gemini_output = self._call_gemini_api(system_context, user_prompt)
        if success:
            return gemini_output
        elif gemini_output != "NO_KEY":
            # Nếu API báo lỗi
            return f"""
⚠️ **Không thể kết nối với Google Gemini API:**

`Chi tiết lỗi: {gemini_output}`

---

""" + self._fallback_answer(user_prompt, symbol, exchange, score, rec, breakdown, reasons, analyses)

        # Fallback engine nếu hoàn toàn không có Key
        return self._fallback_answer(user_prompt, symbol, exchange, score, rec, breakdown, reasons, analyses)

    def _fallback_answer(self, user_prompt, symbol, exchange, score, rec, breakdown, reasons, analyses):
        prompt_lower = user_prompt.lower()
        reasons_str = "\n".join([f"• {r}" for r in reasons])

        if any(w in prompt_lower for w in ["tại sao", "tai sao", "khuyên nghị", "khuyen nghi", "lý do", "ly do", "sao lại"]):
            return f"""
🤖 **[Multi-Agent Internal Engine] Giải thích Khuyến nghị cho [{symbol}]:**

• **Điểm đồng thuận 5 Tầng:** `{score}/100`  
• **Khuyến nghị chính thức:** **{rec}** (Sàn: {exchange})

**Các luận điểm chính từ Master Agent:**
{reasons_str}

**Điểm chi tiết từng Agent:**
- 📈 Trend: `{breakdown.get('trend_score', 50)}/100` | ⚡ Momentum: `{breakdown.get('momentum_score', 50)}/100`
- 📊 Volume: `{breakdown.get('volume_score', 50)}/100` | 📍 S&R: `{breakdown.get('sr_score', 50)}/100`
- 🛡️ Risk: `{breakdown.get('risk_score', 50)}/100` | 📰 News: `{breakdown.get('news_score', 50)}/100`
"""
        elif any(w in prompt_lower for w in ["stop-loss", "stop loss", "cắt lỗ", "cat lo", "chốt lời", "chot loi", "vốn", "von", "vào lệnh", "vung gia", "gia mua", "mua"]):
            risk_recs = analyses.get("risk", {}).get("recommendations", {})
            entry_p = risk_recs.get("entry_price") or 0
            entry_str = f"`{entry_p:,.0f} VNĐ`" if entry_p else "`Giá tham chiếu hiện tại`"
            return f"""
🛡️ **[Multi-Agent Internal Engine] Quản trị Rủi ro & Đi vốn cho [{symbol}]:**

1. 🎯 **Giá vào lệnh (Entry Price):** {entry_str} (Vùng mua đề xuất: `{risk_recs.get('entry_range', 'N/A')} VNĐ`).
2. 🛑 **Hard Stop-Loss (Cắt lỗ kỷ luật):** `{risk_recs.get('stop_loss_price', 0):,.0f} VNĐ` (`-{risk_recs.get('stop_loss_pct', 7.0)}%`).
3. 🎯 **Take-Profit (Chốt lời mục tiêu):** `{risk_recs.get('take_profit_price', 0):,.0f} VNĐ` (`+{risk_recs.get('take_profit_pct', 15.0)}%`).
4. 💰 **Tỷ lệ Đi vốn an toàn:** Max **`{risk_recs.get('suggested_position_size_pct', 15.0)}%`** danh mục.
"""
        else:
            return f"""
🤖 **[Multi-Agent Internal Engine] Trợ lý AI cho mã [{symbol}]:**

Mã **{symbol}** có điểm đồng thuận **{score}/100** với khuyến nghị **{rec}**.
Luận điểm chính: {reasons[0] if reasons else 'Đang theo dõi tín hiệu thị trường.'}
"""
