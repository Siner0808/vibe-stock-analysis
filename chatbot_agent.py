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

#: Câu hỏi rơi vào nhánh QUẢN TRỊ RỦI RO của `_fallback_answer`.
#: Có dấu và không dấu, vì người dùng gõ cả hai.
TU_KHOA_RUI_RO = (
    "cắt lỗ", "cat lo", "stop-loss", "stop loss", "stoploss",
    "chốt lời", "chot loi", "take-profit", "take profit", "tp1", "tp2",
    "rủi ro", "rui ro", "risk", "vào lệnh", "vao lenh", "entry",
    "tỷ trọng", "ty trong", "position",
)


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
        # `final_score` KHÔNG có mặc định 50: thiếu điểm mà in 50 là in ra
        # đúng giá trị trung tính, tức một phán quyết "không nghiêng về
        # đâu" mà không phép đo nào đứng sau. Lỗi 78.
        score = result.get("final_score")
        score = "chưa đo được" if score is None else score
        rec = result.get("recommendation", "NẮM GIỮ")
        breakdown = result.get("score_breakdown", {})
        reasons = result.get("key_reasons", [])
        debate = result.get("debate", {})
        analyses = result.get("analyses", {})
        _rr = (analyses.get("risk") or {}).get("recommendations") or {}

        # Tạo System Context phong phú nạp toàn bộ kết quả phân tích 5 Tầng
        system_context = f"""
Bạn là Trợ lý AI Chuyên gia Phân tích Chứng khoán Việt Nam chuyên nghiệp (Vibe Stock Assistant Powered by Gemini).
Bạn đang phân tích trực tiếp mã chứng khoán: [{symbol}] (Sàn {exchange}).

DỮ LIỆU PHÂN TÍCH MULTI-AGENT 5 TẦNG MỚI NHẤT:
- Điểm tổng hợp đồng thuận: {score}/100
- Khuyến nghị hành động chính thức: {rec}
- Các lý do cốt lõi từ Master Agent: {json.dumps(reasons, ensure_ascii=False)}
- Điểm chi tiết 6 Agent (`chưa đo được` nghĩa là KHÔNG có dữ liệu — đừng
  đoán thay, và đừng coi nó là điểm trung tính):
  + Trend (Xu hướng): {self._so(breakdown, 'trend_score')}/100
  + Momentum (Động lượng): {self._so(breakdown, 'momentum_score')}/100
  + Volume (Khối lượng): {self._so(breakdown, 'volume_score')}/100
  + Support & Resistance (Kháng cự/Hỗ trợ): {self._so(breakdown, 'sr_score')}/100
  + Risk (Rủi ro): {self._so(breakdown, 'risk_score')}/100
  + News (Sentiment tin tức): {self._so(breakdown, 'news_score')}/100

DỮ LIỆU DEBATE COUNCIL & SAFETY HARNESS:
- Kết quả Tranh luận Khẩn cấp: Bull Score ({debate.get('bull_score', 0)}), Bear Score ({debate.get('bear_score', 0)}), Tóm tắt: "{debate.get('verdict_summary', '')}"
- Rủi ro lớn nhất: {json.dumps(debate.get('key_risks', []), ensure_ascii=False)}
- Cơ hội lớn nhất: {json.dumps(debate.get('key_opportunities', []), ensure_ascii=False)}
- Dữ liệu Quản trị rủi ro ATR: Entry price ({self._so(_rr, 'entry_price')}), Stop-loss price ({self._so(_rr, 'stop_loss_price')}), Take-profit price ({self._so(_rr, 'take_profit_price')}), Position Sizing ({self._so(_rr, 'suggested_position_size_pct')}%).
- LƯU Ý BẮT BUỘC khi nói về TP: **TP1 và TP2 là MỨC THAM CHIẾU cho người
  đọc, KHÔNG phải lối thoát của máy** — `paper_trading.evaluate_open()`
  chỉ so `high` với TP khi cờ `CHOT_LOI_CUNG`, và cờ ấy là `False`. Máy
  thoát bằng STOP_LOSS (ATR + trailing 7% bám giá ĐÓNG CỬA cao nhất),
  SIGNAL_REVERSED, hoặc HET_DU_LIEU. Dự án KHÔNG có cơ chế thoát một
  phần, nên đừng mô tả chuyện "chốt 50% vốn".

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

    @staticmethod
    def _so(nguon: dict, khoa: str, dinh_dang: str = "{}") -> str:
        """Giá trị THẬT, hoặc chữ `chưa đo được`. KHÔNG bao giờ một con số.

        VÌ SAO (17/09/2026, lỗi 78). File này từng mang **18** cảnh báo
        `chan_bia_so_lieu` — nhiều hơn mọi file khác cộng lại — và mỗi cảnh
        báo là một `.get(khoa, <số>)`. Thiếu dữ liệu thì người đọc nhận
        `Trend 50/100`, `SL -5.0%`, `TP +10.0%`: những con số nghe đúng,
        đứng đúng chỗ một phép đo, và không phép đo nào đứng sau.

        Nặng hơn: ba con số bịa ấy **lệch khỏi chính máy** — TP1 của
        `analysis_agents` là **+20%** chứ không phải 10, TP2 là **+30%**
        chứ không phải 20.

        Cùng lớp lỗi 71, đã gỡ ở `debate_agents.py` ngày 16/09/2026. Phép
        sửa giống hệt: **thiếu thì NÓI LÀ THIẾU.**
        """
        v = (nguon or {}).get(khoa)
        if v is None or isinstance(v, bool):
            return "chưa đo được"
        try:
            return dinh_dang.format(v)
        except (ValueError, TypeError):
            return str(v)

    def _tra_loi_rui_ro(self, symbol: str, risk_recs: dict) -> str:
        """Khối quản trị rủi ro — NAY CHẠY ĐƯỢC.

        Từ khi file này ra đời tới 17/09/2026 khối này nằm **sau một
        `return`** trong cùng nhánh `if`, nên nó **chưa bao giờ chạy**; và
        nếu chạy thì nổ, vì `risk_recs` lẫn `entry_str` chưa bao giờ được
        gán. Đo bằng AST: 11 dòng trên 37 dòng của hàm là mã chết. Đo bằng
        cách CHẠY: bốn câu hỏi rủi ro đều rơi xuống nhánh trả lời chung.
        """
        d = risk_recs or {}
        if not d:
            return (
                f"🛡️ **[Multi-Agent Internal Engine] Quản trị rủi ro cho "
                f"[{symbol}]:**\n\n"
                f"Chưa có dữ liệu khuyến nghị rủi ro cho mã này — hãy chạy "
                f"**🚀 Phân tích Multi-Agent** trước.\n")

        def muc(bieu_tuong, nhan, khoa_gia, khoa_pct=None, dau=""):
            """Một dòng, hoặc chữ `chưa đo được` — KHÔNG bao giờ nửa nọ nửa kia.

            Bản đầu nối chuỗi thẳng và cho ra `-chưa đo được%`: một câu
            vừa khai là thiếu vừa mang dấu và đơn vị của một phép đo.
            """
            gia = d.get(khoa_gia)
            if gia is None:
                return f"{bieu_tuong} **{nhan}:** chưa đo được"
            ra = f"{bieu_tuong} **{nhan}:** `{gia:,.0f} VNĐ`"
            if khoa_pct:
                pct = d.get(khoa_pct)
                ra += (f" (`{dau}{pct}%`)" if pct is not None
                       else " (phần trăm: chưa đo được)")
            return ra

        dong = [
            muc("🎯", "Giá vào lệnh", "entry_price")
            + f" (vùng mua: `{self._so(d, 'entry_range')}`)",
            muc("🛑", "Stop-loss (theo ATR)", "stop_loss_price",
                "stop_loss_pct", "-"),
            muc("🎯", "TP1 (mức tham chiếu)", "take_profit_price",
                "take_profit_pct", "+"),
        ]
        # TP2 chỉ xuất hiện khi CÓ. Đánh số dựng từ danh sách nên nó không
        # nhảy cóc — bản đầu in `3.` rồi `5.` khi thiếu TP2.
        if d.get("tp2_price") is not None:
            dong.append(muc("🚀", "TP2 (mức tham chiếu thứ hai)", "tp2_price",
                            "tp2_pct", "+"))
        dong.append(
            f"💰 **Tỷ trọng gợi ý:** tối đa "
            f"**`{self._so(d, 'suggested_position_size_pct')}%`** danh mục")
        than = "\n".join(f"{i}. {x}." for i, x in enumerate(dong, 1))
        return f"""
🛡️ **[Multi-Agent Internal Engine] Quản trị rủi ro cho [{symbol}]:**

{than}

> ⚠️ **TP1 và TP2 là MỨC THAM CHIẾU cho người đọc, KHÔNG phải lối thoát
> của máy.** `paper_trading.evaluate_open()` chỉ so `high` với TP khi
> `CHOT_LOI_CUNG`, và cờ ấy là `False`. Ba lối thoát máy thật sự dùng:
> **STOP_LOSS** (ATR, cộng trailing 7% bám giá **ĐÓNG CỬA** cao nhất, chỉ
> nâng không hạ) · **SIGNAL_REVERSED** · **HET_DU_LIEU**.
>
> Và dự án **không có cơ chế thoát MỘT PHẦN nào**: `evaluate_open` đóng
> trọn vị thế hoặc không đóng.
"""

    def _fallback_answer(self, user_prompt, symbol, exchange, score, rec, breakdown, reasons, analyses):
        """Trả lời khi không gọi được Gemini.

        BA nhánh, và nhánh thứ hai mới có từ 17/09/2026 — trước đó nó nằm
        sau một `return` nên không bao giờ chạy (lỗi 78).
        """
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
- 📈 Trend: `{self._so(breakdown, 'trend_score')}/100` | ⚡ Momentum: `{self._so(breakdown, 'momentum_score')}/100`
- 📊 Volume: `{self._so(breakdown, 'volume_score')}/100` | 📍 S&R: `{self._so(breakdown, 'sr_score')}/100`
- 🛡️ Risk: `{self._so(breakdown, 'risk_score')}/100` | 📰 News: `{self._so(breakdown, 'news_score')}/100`
"""
        if any(w in prompt_lower for w in TU_KHOA_RUI_RO):
            return self._tra_loi_rui_ro(
                symbol, (analyses.get("risk") or {}).get("recommendations"))
        else:
            return f"""
🤖 **[Multi-Agent Internal Engine] Trợ lý AI cho mã [{symbol}]:**

Mã **{symbol}** có điểm đồng thuận **{score}/100** với khuyến nghị **{rec}**.
Luận điểm chính: {reasons[0] if reasons else 'Đang theo dõi tín hiệu thị trường.'}
"""
