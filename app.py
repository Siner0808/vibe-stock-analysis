import json
import streamlit as st
import streamlit.components.v1
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from master_agent import run_full_analysis
from chatbot_agent import StockChatbotAgent, DEFAULT_GEMINI_KEY
from financial_collector import FinancialDataCollector

# Streamlit Page Config
st.set_page_config(
    page_title="Vibe Coding - AI Multi-Agent Stock Analysis",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #0e1117; }
    .score-ring { text-align: center; }
    .agent-card {
        background: linear-gradient(135deg, #1e222d 0%, #131722 100%);
        border-radius: 12px; padding: 16px;
        border-left: 4px solid #00e676;
        margin-bottom: 12px;
    }
    .agent-card.warn { border-left-color: #ffca28; }
    .agent-card.danger { border-left-color: #ef5350; }
    h2 { color: #00e676; }
    h3 { color: #29b6f6 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Vibe Coding — AI Multi-Agent Stock Analysis Platform")
st.caption("Pipeline 5 tầng: Data Collection → Analysis Agents → Consensus → Debate Council → Final Verdict")

# ---- Sidebar ----
with st.sidebar:
    st.header("⚙️ Cấu hình phân tích")
    symbol = st.text_input("Mã chứng khoán", value=st.session_state.get("target_symbol", "FPT")).upper()
    exchange = st.selectbox("Sàn giao dịch", ["HOSE", "HNX", "UPCOM"], index=0)
    days_back = st.slider("Số ngày lịch sử", min_value=60, max_value=365, value=200)
    gemini_key_input = st.text_input("🔑 Gemini API Key", value=st.session_state.get("gemini_api_key", DEFAULT_GEMINI_KEY), type="password", help="Hệ thống đã tự động tích hợp Gemini API Key chính thức của bạn").strip()
    if gemini_key_input:
        st.session_state["gemini_api_key"] = gemini_key_input
    effective_gemini_key = st.session_state.get("gemini_api_key", DEFAULT_GEMINI_KEY)
    
    run_btn = st.button("🚀 Chạy phân tích Multi-Agent", type="primary", use_container_width=True)
    
    st.divider()
    
    st.markdown("""
    **🏗️ Kiến trúc 5 Tầng:**
    - 📦 **L1A** VNStock + TradingView
    - 📰 **L1B** News Agents (5 agents)
    - 🔬 **L2** 6 Analysis Agents chuyên sâu
    - 🧠 **L3** Master Consensus Score
    - ⚖️ **L4** Debate Council (Bull/Bear/Devil)
    - 🏆 **L5** Phán quyết Cuối cùng
    """)

    st.divider()
    
    # Financial Collector Quick Sidebar Summary
    fin_coll = FinancialDataCollector()
    co_info = fin_coll.get_company_overview(symbol)
    foreign_data = fin_coll.get_foreign_trading_history(symbol)

    st.subheader(f"🌐 Chỉ số Định giá ({symbol})")
    st.caption(f"Vốn hóa: **{co_info['market_cap_billions']:,.0f} tỷ VNĐ**")
    st.markdown(f"""
    - **P/E:** `{co_info['pe']}` | **EPS:** `{co_info['eps']:,.0f} VNĐ`
    - **Beta:** `{co_info['beta']}` | **KL 10 phiên:** `{co_info['avg_vol_10d']:,.0f}`
    - **52T Thấp - Cao:** `{co_info['low_52w']:,.1f}` - `{co_info['high_52w']:,.1f}` VNĐ
    - **% Biến động (1Tuần/1Tháng/1Năm):**  
      `{co_info['pct_1w']:+.2f}%` | `{co_info['pct_1m']:+.2f}%` | `{co_info['pct_1y']:+.2f}%`
    """)

    st.markdown("##### 🌍 Giao dịch NĐTNN (10 phiên)")
    # Draw mini foreign net buying bar chart
    fig_foreign = go.Figure()
    colors = ['#00e676' if v >= 0 else '#ef5350' for v in foreign_data['net_values_billion']]
    fig_foreign.add_trace(go.Bar(
        x=foreign_data['dates'],
        y=foreign_data['net_values_billion'],
        marker_color=colors,
        name="GT Ròng (Tỷ VNĐ)"
    ))
    fig_foreign.update_layout(
        height=180,
        margin=dict(l=10, r=10, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(color='#888', size=9)),
        yaxis=dict(showgrid=True, gridcolor='#222', tickfont=dict(color='#888', size=9))
    )
    st.plotly_chart(fig_foreign, use_container_width=True)

end_date = datetime.now()
start_date = end_date - timedelta(days=days_back)
start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

# ---- Run analysis ----
if run_btn or "result" not in st.session_state or st.session_state.get("last_symbol") != symbol:
    with st.spinner(f"🤖 Đang chạy toàn bộ pipeline phân tích cho mã [{symbol}]..."):
        try:
            result = run_full_analysis(symbol, start_str, end_str, exchange)
            st.session_state["result"] = result
            st.session_state["last_symbol"] = symbol
        except Exception as e:
            st.error(f"❌ Lỗi khi chạy pipeline: {e}")
            st.stop()

result = st.session_state.get("result")
if not result:
    st.info("👈 Nhấn nút **Chạy phân tích Multi-Agent** để bắt đầu.")
    st.stop()

# ---- Header Metrics ----
# Lấy giá từ OHLCV
@st.cache_data(ttl=300)
def load_stock_data(ticker, start, end):
    try:
        from data_collectors import VNStockCollectorAgent
        res = VNStockCollectorAgent().collect(ticker, start, end)
        return res.get("df")
    except Exception:
        return None

df = load_stock_data(symbol, start_str, end_str)

if df is not None and not df.empty:
    latest_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2] if len(df) > 1 else latest_close
    change = latest_close - prev_close
    pct_change = (change / prev_close) * 100 if prev_close else 0
    high_p = df['high'].max()
    low_p = df['low'].min()
    avg_vol = int(df['volume'].mean())

    # Tự động quy đổi giá từ Nghìn đồng sang VNĐ chuẩn (ví dụ 65.41 -> 65,410 VNĐ)
    mult = 1000.0 if latest_close < 1000 else 1.0
    latest_close_fmt = latest_close * mult
    change_fmt = change * mult
    high_p_fmt = high_p * mult
    low_p_fmt = low_p * mult

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Giá đóng cửa", f"{latest_close_fmt:,.0f} VNĐ", f"{change_fmt:+,.0f} ({pct_change:+.2f}%)")
    c2.metric("Cao nhất (kỳ)", f"{high_p_fmt:,.0f} VNĐ")
    c3.metric("Thấp nhất (kỳ)", f"{low_p_fmt:,.0f} VNĐ")
    c4.metric("KL Trung bình", f"{avg_vol:,.0f}")
    c5.metric("Chất lượng dữ liệu", result.get("data_quality", "OK"))

st.divider()

# ---- TABS ----
tab_terminal, tab_main, tab_debate, tab_detail, tab_news, tab_chart, tab_diagram, tab_chat, tab_raw = st.tabs([
    "📊 Tổng quan Terminal",
    "🧠 Kết quả Multi-Agent 5 Tầng",
    "⚖️ Debate Council",
    "🔬 Chi tiết từng Agent",
    "📰 Tin tức & Sentiment",
    "📈 Đồ thị Kỹ thuật Pro",
    "📐 Sơ đồ Pipeline",
    "💬 Trợ lý Chatbot AI",
    "📄 Dữ liệu thô"
])

# =====================================================================
# TAB 0: VIBE STOCK TERMINAL PRO FINANCIAL DASHBOARD
# =====================================================================
with tab_terminal:
    fin_coll = FinancialDataCollector()
    fin_data = fin_coll.get_financial_statements(symbol)

    st.title(f"🏢 CTCP / Doanh nghiệp [{symbol}] ({exchange})")
    st.caption(f"Cập nhật lúc: {datetime.now().strftime('%H:%M:%S')} | Việt Nam (GMT+7)")

    # 1. Main Candlestick Chart
    st.subheader(f"📈 Đồ thị Kỹ thuật Nến Nhật & Khối lượng ({symbol})")
    if df is not None and not df.empty:
        fig_main = go.Figure()
        
        # Moving Averages
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()

        mult = 1000.0 if df['close'].iloc[-1] < 1000 else 1.0

        fig_main.add_trace(go.Candlestick(
            x=df['time'],
            open=df['open'] * mult,
            high=df['high'] * mult,
            low=df['low'] * mult,
            close=df['close'] * mult,
            name="Giá nến (VNĐ)",
            increasing_line_color='#00e676',
            increasing_fillcolor='#00e676',
            decreasing_line_color='#ef5350',
            decreasing_fillcolor='#ef5350'
        ))
        
        fig_main.add_trace(go.Scatter(
            x=df['time'], y=df['ma20'] * mult,
            mode='lines', line=dict(color='#ff9800', width=1.5), name='MA20'
        ))
        fig_main.add_trace(go.Scatter(
            x=df['time'], y=df['ma50'] * mult,
            mode='lines', line=dict(color='#29b6f6', width=1.5), name='MA50'
        ))

        fig_main.update_layout(
            height=420,
            template="plotly_dark",
            paper_bgcolor='#131722',
            plot_bgcolor='#131722',
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_main, use_container_width=True)

    st.divider()

    # 2. Lưới 4 Biểu đồ Tài chính BCTC Grid (2x2 Layout)
    st.subheader("📊 Báo cáo Tài chính & Sức khỏe Doanh nghiệp (5 Năm)")

    grid_row1_col1, grid_row1_col2 = st.columns(2)
    grid_row2_col1, grid_row2_col2 = st.columns(2)

    # ── Biểu đồ 1: Hiệu suất Kinh doanh (Doanh thu vs LNST) ───────────
    with grid_row1_col1:
        st.markdown("##### 1️⃣ Hiệu suất Kinh doanh (Doanh thu & Lợi nhuận ròng)")
        fig_perf = go.Figure()
        fig_perf.add_trace(go.Bar(
            x=fin_data['years'], y=fin_data['revenue'],
            name="Doanh thu thuần (Tỷ)", marker_color='#29b6f6'
        ))
        fig_perf.add_trace(go.Scatter(
            x=fin_data['years'], y=fin_data['net_profit'],
            name="Lợi nhuận ròng (Tỷ)", mode='lines+markers',
            line=dict(color='#ffca28', width=3)
        ))
        fig_perf.update_layout(
            height=300, template="plotly_dark", paper_bgcolor='#1e222d', plot_bgcolor='#1e222d',
            margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_perf, use_container_width=True)

    # ── Biểu đồ 2: Kết quả Kinh doanh Chi tiết ───────────────────────
    with grid_row1_col2:
        st.markdown("##### 2️⃣ Kết quả Kinh doanh (Cơ cấu Doanh thu & Chi phí)")
        fig_inc = go.Figure()
        fig_inc.add_trace(go.Bar(x=fin_data['years'], y=fin_data['revenue'], name="Doanh thu", marker_color='#00e676'))
        fig_inc.add_trace(go.Bar(x=fin_data['years'], y=fin_data['cogs'], name="Giá vốn HB", marker_color='#ef5350'))
        fig_inc.add_trace(go.Bar(x=fin_data['years'], y=fin_data['gross_profit'], name="LN Gộp", marker_color='#ab47bc'))
        fig_inc.update_layout(
            barmode='group', height=300, template="plotly_dark", paper_bgcolor='#1e222d', plot_bgcolor='#1e222d',
            margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_inc, use_container_width=True)

    # ── Biểu đồ 3: Tài sản & Vốn chủ sở hữu ──────────────────────────
    with grid_row2_col1:
        st.markdown("##### 3️⃣ Tài sản & Vốn chủ sở hữu (Nợ vay vs VCSH)")
        fig_bs = go.Figure()
        fig_bs.add_trace(go.Bar(x=fin_data['years'], y=fin_data['equity'], name="Vốn CSH (Tỷ)", marker_color='#26a69a'))
        fig_bs.add_trace(go.Bar(x=fin_data['years'], y=fin_data['debt'], name="Nợ vay (Tỷ)", marker_color='#ff7043'))
        fig_bs.add_trace(go.Scatter(
            x=fin_data['years'], y=fin_data['debt_to_equity'],
            name="Tỷ lệ Nợ/VCSH", yaxis="y2", mode='lines+markers', line=dict(color='#ffee58', width=2)
        ))
        fig_bs.update_layout(
            barmode='stack', height=300, template="plotly_dark", paper_bgcolor='#1e222d', plot_bgcolor='#1e222d',
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis2=dict(overlaying='y', side='right', showgrid=False, title="Tỷ lệ Nợ/VCSH"),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_bs, use_container_width=True)

    # ── Biểu đồ 4: Vị thế Tài chính (Ngắn hạn vs Dài hạn) ─────────────
    with grid_row2_col2:
        st.markdown("##### 4️⃣ Vị thế Tài chính (Tài sản vs Nợ Ngắn/Dài hạn)")
        fig_pos = go.Figure()
        latest_idx = -1
        fig_pos.add_trace(go.Bar(
            x=['Tài sản Ngắn hạn', 'Tài sản Dài hạn', 'Nợ Ngắn hạn', 'Nợ Dài hạn'],
            y=[
                fin_data['short_assets'][latest_idx],
                fin_data['long_assets'][latest_idx],
                fin_data['short_liabilities'][latest_idx],
                fin_data['long_liabilities'][latest_idx]
            ],
            marker_color=['#29b6f6', '#00e676', '#ef5350', '#ff9800']
        ))
        fig_pos.update_layout(
            height=300, template="plotly_dark", paper_bgcolor='#1e222d', plot_bgcolor='#1e222d',
            margin=dict(l=10, r=10, t=20, b=10), showlegend=False
        )
        st.plotly_chart(fig_pos, use_container_width=True)

with tab_main:
    final_score = result["final_score"]
    recommendation = result["recommendation"]
    action_color = result["action_color"]

    # Score Gauge
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=final_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Điểm đồng thuận (0-100)", 'font': {'size': 18, 'color': '#b0bec5'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#b0bec5'},
            'bar': {'color': action_color},
            'steps': [
                {'range': [0, 30], 'color': '#1a1a2e'},
                {'range': [30, 45], 'color': '#1e222d'},
                {'range': [45, 62], 'color': '#252c3a'},
                {'range': [62, 78], 'color': '#1b2a1e'},
                {'range': [78, 100], 'color': '#0d2318'},
            ],
            'threshold': {'line': {'color': action_color, 'width': 4}, 'thickness': 0.75, 'value': final_score}
        }
    ))
    gauge.update_layout(
        height=280, template="plotly_dark",
        margin=dict(l=30, r=30, t=30, b=10),
        font={'color': '#ffffff'}
    )

    col_gauge, col_rec = st.columns([1, 1.5])
    with col_gauge:
        st.plotly_chart(gauge, use_container_width=True)
    with col_rec:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e222d, #131722);
                        padding: 28px; border-radius: 14px;
                        border: 2px solid {action_color}; text-align: center; margin-top: 10px;">
                <p style="color:#b0bec5; margin:0; font-size:0.95rem;">🧠 Master Consensus Agent — Khuyến nghị cuối</p>
                <h1 style="color:{action_color}; margin: 14px 0; font-size: 2.4rem;">{recommendation}</h1>
                <p style="color:#78909c; font-size:0.85rem; margin:0;">Mã: <b style="color:#ffffff">{result.get('symbol', symbol)}</b> &nbsp;|&nbsp; Sàn: <b style="color:#ffffff">{result.get('exchange', exchange)}</b></p>
            </div>
        """, unsafe_allow_html=True)

    breakdown = result.get("score_breakdown", {})
    agent_names  = ["Trend", "Momentum", "Volume", "S&R", "Risk", "📰 News"]
    agent_scores = [
        breakdown.get("trend_score", 50), breakdown.get("momentum_score", 50),
        breakdown.get("volume_score", 50), breakdown.get("sr_score", 50),
        breakdown.get("risk_score", 50),  breakdown.get("news_score", 50)
    ]
    colors = ["#00e676" if s >= 60 else "#ffca28" if s >= 40 else "#ef5350" for s in agent_scores]

    bar_fig = go.Figure(go.Bar(
        x=agent_names, y=agent_scores,
        marker_color=colors,
        text=[f"{s:.0f}" for s in agent_scores],
        textposition="outside"
    ))
    bar_fig.add_hline(y=60, line_dash="dash", line_color="#00e676", annotation_text="Ngưỡng MUA (60)")
    bar_fig.add_hline(y=40, line_dash="dash", line_color="#ef5350", annotation_text="Ngưỡng BÁN (40)")
    bar_fig.update_layout(
        template="plotly_dark", height=300,
        yaxis=dict(range=[0, 105]),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(bar_fig, use_container_width=True)

    # Key Reasons
    st.subheader("💡 Luận điểm chính từ Master Agent")
    for reason in result["key_reasons"]:
        st.markdown(f"> {reason}")

    # Data sources
    with st.expander("📡 Nguồn dữ liệu đã sử dụng"):
        for note in result.get("data_sources", []):
            st.write(f"• {note}")

# ════════════════════════════════════════════════════════════════
with tab_debate:
    debate = result.get("debate")
    if not debate:
        st.warning("⚠️ Chưa có dữ liệu Debate Council. Hãy chạy phân tích trước.")
    else:
        pre  = result.get("pre_debate_score", 50)
        post = result["final_score"]
        adj  = debate["final_adjustment"]

        # ── Header verdict ────────────────────────────────────────
        conf_color = {"RẤT CAO 🟢": "#00e676", "CAO 🟡": "#ffca28",
                      "TRUNG BÌNH 🟠": "#ff7043", "THẤP 🔴": "#ef5350"}.get(
            debate["confidence_level"], "#90a4ae")

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a0828,#0d1117);
                    border:2px solid {conf_color}; border-radius:14px;
                    padding:22px; margin-bottom:18px; text-align:center;">
          <p style="color:#b0bec5;margin:0;font-size:.9rem;">⚖️ Debate Council — Phán quyết sau 3 vòng tranh luận</p>
          <h2 style="color:{conf_color};margin:10px 0;">{debate['verdict_summary']}</h2>
        </div>
        """, unsafe_allow_html=True)

        # ── Score before/after ────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Điểm trước tranh luận", f"{pre:.1f}", help="Master Consensus Score (pre-debate)")
        c2.metric("Bull Score tổng", f"{debate['bull_score']:+.2f}")
        c3.metric("Bear Score tổng", f"{debate['bear_score']:+.2f}")
        c4.metric("Điều chỉnh cuối", f"{adj:+.1f}",
                  delta=f"→ {post}", delta_color="normal")

        # ── Debate progress bar ───────────────────────────────────
        bull_abs = abs(debate["bull_score"])
        bear_abs = abs(debate["bear_score"])
        total_abs = bull_abs + bear_abs if (bull_abs + bear_abs) > 0 else 1
        bull_pct = int(bull_abs / total_abs * 100)
        bear_pct = 100 - bull_pct

        st.markdown(f"""
        <div style="margin:16px 0 8px 0;">
          <div style="display:flex;justify-content:space-between;font-size:.85rem;color:#90a4ae;">
            <span>🐂 BULL {bull_pct}%</span>
            <span>🐻 BEAR {bear_pct}%</span>
          </div>
          <div style="height:14px;background:#1e222d;border-radius:8px;overflow:hidden;display:flex;">
            <div style="width:{bull_pct}%;background:linear-gradient(90deg,#00e676,#29b6f6);"></div>
            <div style="width:{bear_pct}%;background:linear-gradient(90deg,#ff7043,#ef5350);"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Round-by-round transcript ─────────────────────────────
        st.subheader("📜 Biên bản Tranh luận (3 Vòng)")
        round_titles = ["🔔 Vòng 1 — Khai mạc: Trình bày lập luận",
                        "🔥 Vòng 2 — Phản biện chéo & Thách thức",
                        "🏁 Vòng 3 — Kết luận của từng phe"]
        stance_colors = {"BULL": "#00e676", "BEAR": "#ef5350", "NEUTRAL": "#ffca28"}

        for rnd_idx, (rnd, rnd_title) in enumerate(zip(debate["rounds"], round_titles)):
            with st.expander(rnd_title, expanded=(rnd_idx == 0)):
                for arg in rnd:
                    sc = stance_colors.get(arg["stance"], "#90a4ae")
                    impact_str = f"{arg['impact']:+.1f} điểm"
                    st.markdown(f"""
                    <div style="background:#1e222d;border-left:4px solid {sc};
                                border-radius:8px;padding:14px 16px;margin-bottom:10px;">
                      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                        <span style="color:{sc};font-weight:700;font-size:.95rem;">{arg['agent']}</span>
                        <span style="background:{sc}22;color:{sc};padding:2px 10px;
                                     border-radius:20px;font-size:.78rem;">{impact_str}</span>
                      </div>
                      <p style="color:#cfd8dc;margin:0;font-size:.88rem;line-height:1.6;">
                        {arg['statement'].replace(' | ', '<br>• ')}
                      </p>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Risks & Opportunities ─────────────────────────────────
        col_risk, col_opp = st.columns(2)
        with col_risk:
            st.markdown("### 🔴 Rủi ro đã xác định")
            for r in debate["key_risks"]:
                st.markdown(f"- ⚠️ {r}")
        with col_opp:
            st.markdown("### 🟢 Cơ hội đã xác định")
            for o in debate["key_opportunities"]:
                st.markdown(f"- ✅ {o}")

        st.info(f"🛡️ **Độ tin cậy Debate Council:** {debate['confidence_level']} — "
                "Dựa trên mức độ đồng thuận/bất đồng giữa các phe tranh luận.")

with tab_detail:
    analyses = result.get("analyses", {})
    if not analyses:
        st.warning("⚠️ Không thể tải dữ liệu phân tích chi tiết cho mã này.")
    else:
        agent_list = [
            ("📈 Trend Analysis Agent", analyses.get("trend", {}), "trend"),
            ("⚡ Momentum & Oscillator Agent", analyses.get("momentum", {}), "momentum"),
            ("📊 Volume Analysis Agent", analyses.get("volume", {}), "volume"),
            ("📍 Support & Resistance Agent", analyses.get("support_resistance", {}), "sr"),
            ("🛡️ Risk Management Agent", analyses.get("risk", {}), "risk"),
        ]

        for title, data, key in agent_list:
            with st.expander(f"{title}", expanded=False):
                signals = data.get("signals", [])
                for s in signals:
                    st.markdown(f"- {s}")
                if key == "risk" and "recommendations" in data:
                    rec = data["recommendations"]
                    st.divider()
                    r1, r2, r3 = st.columns(3)
                    r1.metric("Stop-loss", f"{rec['stop_loss_price']:,.2f} VNĐ", f"-{rec['stop_loss_pct']}%", delta_color="inverse")
                    r2.metric("Take-profit", f"{rec['take_profit_price']:,.2f} VNĐ", f"+{rec['take_profit_pct']}%")
                    r3.metric("Phân bổ vốn", f"{rec['suggested_position_size_pct']}%", f"RR {rec['risk_reward_ratio']}")
                if key == "sr" and "levels" in data:
                    lvl = data["levels"]
                    st.divider()
                    l1, l2, l3 = st.columns(3)
                    l1.metric("Đỉnh 52 tuần", f"{lvl.get('high_52w',0):,.2f}")
                    l2.metric("Đáy 52 tuần", f"{lvl.get('low_52w',0):,.2f}")
                    l3.metric("% Từ đáy", f"{lvl.get('pct_from_low',0):.1f}%")

with tab_news:
    news_res = result.get("analyses", {}).get("news", {})
    if not news_res or news_res.get("total_articles", 0) == 0:
        st.warning("⚠️ Không thu thập được tin tức. Hãy kiểm tra kết nối internet hoặc bật tùy chọn thu thập tin tức.")
    else:
        # ── Header Metrics ──────────────────────────────────────────
        col_s, col_t, col_p, col_n = st.columns(4)
        col_s.metric("📰 Tổng bài viết", news_res["total_articles"])
        col_t.metric("🌡️ Sentiment tổng", news_res["overall_sentiment"])
        col_p.metric("✅ Bài tích cực", news_res["breakdown"].get("domestic", {}).get("positive", 0) +
                     news_res["breakdown"].get("international", {}).get("positive", 0))
        col_n.metric("🔴 Bài tiêu cực", news_res["breakdown"].get("domestic", {}).get("negative", 0) +
                     news_res["breakdown"].get("international", {}).get("negative", 0))

        st.divider()

        # ── Phân tích Sentiment theo Nguồn ─────────────────────────
        st.subheader("📊 Điểm Sentiment theo Nguồn")
        bd = news_res.get("breakdown", {})
        src_names = []
        src_scores = []
        src_labels_map = {"domestic": "🇻🇳 Trong nước", "international": "🌏 Quốc tế", "macro": "📊 Vĩ mô"}
        for k, label in src_labels_map.items():
            if k in bd:
                src_names.append(label)
                src_scores.append(bd[k]["score"])

        if src_names:
            src_colors = ["#00e676" if s > 10 else "#ef5350" if s < -10 else "#ffca28" for s in src_scores]
            src_fig = go.Figure(go.Bar(
                x=src_names, y=src_scores,
                marker_color=src_colors,
                text=[f"{s:+.1f}" for s in src_scores], textposition="outside"
            ))
            src_fig.add_hline(y=0, line_color="#b0bec5")
            src_fig.update_layout(
                template="plotly_dark", height=250,
                yaxis_title="Điểm sentiment (-100 → +100)",
                margin=dict(l=20, r=20, t=10, b=20)
            )
            st.plotly_chart(src_fig, use_container_width=True)

        # ── Heatmap Sentiment theo Ngành ───────────────────────────
        st.subheader("🏭 Sentiment theo Ngành (14 ngành)")
        sector_sent = news_res.get("sector_sentiment", {})
        if sector_sent:
            sec_labels  = [v["label"] for v in sector_sent.values()]
            sec_scores  = [v["score"] for v in sector_sent.values()]
            sec_totals  = [v["total"] for v in sector_sent.values()]

            sec_colors = ["#00e676" if s > 15 else "#ef5350" if s < -15 else "#ffca28" for s in sec_scores]
            sec_fig = go.Figure(go.Bar(
                x=sec_labels, y=sec_scores,
                marker_color=sec_colors,
                customdata=[[t] for t in sec_totals],
                hovertemplate="<b>%{x}</b><br>Score: %{y:+.1f}<br>Bài: %{customdata[0]}<extra></extra>",
                text=[f"{s:+.0f}" for s in sec_scores], textposition="outside"
            ))
            sec_fig.add_hline(y=0, line_color="#b0bec5")
            sec_fig.update_layout(
                template="plotly_dark", height=380,
                yaxis_title="Sentiment Score",
                xaxis_tickangle=-35,
                margin=dict(l=20, r=20, t=10, b=100)
            )
            st.plotly_chart(sec_fig, use_container_width=True)

        # ── Top tin tức ─────────────────────────────────────────────
        col_pos, col_neg = st.columns(2)
        with col_pos:
            st.markdown("### ✅ Top Tin tức Tích cực")
            for item in news_res.get("top_positive", []):
                url = item.get("url", "#")
                link = f"[{item['title'][:80]}...]({url})" if url and url != "#" else item['title'][:80]
                st.markdown(f"**{link}**  \n`{item['source']}` — {item.get('category','')}")
                st.divider()

        with col_neg:
            st.markdown("### 🔴 Top Tin tức Tiêu cực")
            for item in news_res.get("top_negative", []):
                url = item.get("url", "#")
                link = f"[{item['title'][:80]}...]({url})" if url and url != "#" else item['title'][:80]
                st.markdown(f"**{link}**  \n`{item['source']}` — {item.get('category','')}")
                st.divider()

        # ── Tín hiệu từ News Agent ──────────────────────────────────
        with st.expander("📋 Chi tiết tín hiệu News Sentiment Agent", expanded=False):
            for sig in news_res.get("signals", []):
                st.markdown(f"- {sig}")

with tab_chart:

    if df is not None and not df.empty:
        st.subheader(f"📊 Đồ thị Nến Nhật ({symbol})")
        df['MA20'] = df['close'].rolling(20).mean()
        df['MA50'] = df['close'].rolling(50).mean()

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df['time'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="Nến Nhật (OHLC)",
            increasing_line_color='#00e676',
            increasing_fillcolor='#00e676',
            decreasing_line_color='#ef5350',
            decreasing_fillcolor='#ef5350'
        ))
        fig.add_trace(go.Scatter(x=df['time'], y=df['MA20'], mode='lines', name='MA20 (Ngắn hạn)', line=dict(color='#ff9800', width=2)))
        fig.add_trace(go.Scatter(x=df['time'], y=df['MA50'], mode='lines', name='MA50 (Trung hạn)', line=dict(color='#2196f3', width=2)))
        fig.update_layout(
            template="plotly_dark", height=520,
            xaxis_rangeslider_visible=False,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Volume chart
        vol_colors = ['#00e676' if df['close'].iloc[i] >= df['open'].iloc[i] else '#ef5350'
                      for i in range(len(df))]
        vol_fig = go.Figure(go.Bar(x=df['time'], y=df['volume'], marker_color=vol_colors, name='Volume'))
        vol_fig.update_layout(template="plotly_dark", height=180, margin=dict(l=20, r=20, t=5, b=20))
        st.plotly_chart(vol_fig, use_container_width=True)
    else:
        st.warning("⚠️ Không có dữ liệu chuỗi nến OHLCV để vẽ đồ thị.")

with tab_diagram:
    st.subheader("📐 Sơ đồ Kiến trúc System & Luồng Vận hành Multi-Agent")
    import pathlib

    def load_html_diagram(filename):
        paths = [
            pathlib.Path(__file__).parent / filename,
            pathlib.Path(r"C:\Users\cuong\.gemini\antigravity\brain\94db5080-33a8-473d-9aa7-24e6bc20d5a5") / filename
        ]
        for p in paths:
            if p.exists():
                return p.read_text(encoding="utf-8")
        return None

    d_tab1, d_tab2, d_tab3 = st.tabs([
        "🏛️ Sơ đồ 1: Kiến trúc System 5 Tầng (Loop & Debate Council)",
        "🛡️ Sơ đồ 2: Safety Harness & Vòng lặp Post-Mortem (Xử lý Bẫy)",
        "📊 Sơ đồ 3: Pipeline Luồng Dữ liệu Chi tiết"
    ])

    with d_tab1:
        html1 = load_html_diagram("architecture_diagram.html")
        if html1:
            st.components.v1.html(html1, height=920, scrolling=True)
        else:
            st.warning("⚠️ Chưa tìm thấy file architecture_diagram.html")

    with d_tab2:
        html2 = load_html_diagram("emergency_flow_diagram.html")
        if html2:
            st.components.v1.html(html2, height=920, scrolling=True)
        else:
            st.warning("⚠️ Chưa tìm thấy file emergency_flow_diagram.html")

    with d_tab3:
        html3 = load_html_diagram("pipeline_diagram.html")
        if html3:
            st.components.v1.html(html3, height=920, scrolling=True)
        else:
            st.warning("⚠️ Chưa tìm thấy file pipeline_diagram.html")

with tab_chat:
    st.subheader(f"💬 Trợ lý AI Chatbot Phân tích ({symbol})")
    st.caption("Chatbot tự động nắm ngữ cảnh kết quả phân tích Multi-Agent 5 Tầng mới nhất để giải đáp mọi thắc mắc của bạn.")

    bot_agent = StockChatbotAgent()

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": f"Xin chào! Tôi là Trợ lý AI Chatbot. Bạn có thắc mắc gì về kết quả phân tích mã **{symbol}** (Điểm số: {result.get('final_score', 50)}/100 - Khuyến nghị: {result.get('recommendation', '')}) không?"
            }
        ]

    # Quick prompt buttons
    st.markdown("##### 💡 Câu hỏi gợi ý nhanh:")
    q_col1, q_col2, q_col3 = st.columns(3)
    quick_query = None
    if q_col1.button(f"❓ Tại sao {symbol} cho khuyến nghị này?", use_container_width=True):
        quick_query = f"Tại sao mã {symbol} lại cho khuyến nghị hiện tại?"
    if q_col2.button(f"🛡️ Stop-loss & quản trị vốn ra sao?", use_container_width=True):
        quick_query = f"Mức Stop-loss và tỷ lệ đi vốn an toàn cho mã {symbol} là bao nhiêu?"
    if q_col3.button(f"⚖️ Phán quyết Bull vs Bear tranh luận gì?", use_container_width=True):
        quick_query = f"Phe Bull và Bear đã tranh luận những gì về mã {symbol}?"

    # Display message history
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input(f"Hỏi AI Trợ lý về mã chứng khoán {symbol}...") or quick_query

    if user_input:
        st.session_state["chat_messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("🤖 AI Gemini đang suy nghĩ và tổng hợp từ kết quả 5 Tầng..."):
                response = bot_agent.answer_question(user_input, result, user_api_key=effective_gemini_key)
                st.markdown(response)
                st.session_state["chat_messages"].append({"role": "assistant", "content": response})

with tab_raw:
    st.subheader("📄 JSON Output toàn bộ kết quả phân tích")
    raw_output = {k: v for k, v in result.items() if k != "analyses"}
    st.code(json.dumps(raw_output, indent=2, ensure_ascii=False, default=str), language="json")
    if df is not None:
        st.subheader("📋 Bảng dữ liệu OHLCV thô")
        st.dataframe(df.sort_values(by='time', ascending=False), use_container_width=True)
