import json
import os
import streamlit as st
import streamlit.components.v1
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from master_agent import run_full_analysis
from financial_collector import FinancialDataCollector
from data_quality import now_vn, price_multiplier

# Streamlit Page Config
st.set_page_config(
    page_title="Vibe Coding - AI Multi-Agent Stock Analysis",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# ULTRA-PREMIUM DARK TERMINAL THEME v3 — "Aurora Midnight"
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* ─── Animated Aurora Background ─────────────────────────── */
    @keyframes auroraShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes neonPulse {
        0%, 100% { box-shadow: 0 0 8px rgba(0,230,118,0.15); }
        50%      { box-shadow: 0 0 20px rgba(0,230,118,0.35); }
    }
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes gradientBorder {
        0%   { border-color: rgba(0,230,118,0.3); }
        50%  { border-color: rgba(41,182,246,0.5); }
        100% { border-color: rgba(0,230,118,0.3); }
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #070a10 0%, #0d1220 30%, #0a1628 60%, #070a10 100%);
        background-size: 400% 400%;
        animation: auroraShift 25s ease infinite;
        color: #e0e6ed;
    }

    /* ─── Typography ─────────────────────────────────────────── */
    h1 {
        background: linear-gradient(135deg, #ffffff 0%, #00e676 45%, #29b6f6 75%, #ab47bc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.8px;
        font-size: 2rem !important;
        animation: fadeSlideUp 0.6s ease-out;
    }
    h2 {
        color: #00e676 !important;
        font-weight: 700 !important;
        text-shadow: 0 0 20px rgba(0,230,118,0.15);
    }
    h3 {
        color: #29b6f6 !important;
        font-weight: 700 !important;
    }
    p, li, span { color: #cfd8dc; }

    /* ─── Sidebar Glass Panel ────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c111a 0%, #111827 50%, #0e1420 100%) !important;
        border-right: 1px solid rgba(0,230,118,0.1) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #b0bec5;
        font-size: 0.9rem;
    }
    [data-testid="stSidebar"] .stSubheader {
        color: #00e676 !important;
    }

    /* ─── Glassmorphic Agent Cards ────────────────────────────── */
    .agent-card {
        background: linear-gradient(145deg, rgba(22,28,40,0.85) 0%, rgba(14,18,28,0.95) 100%);
        border-radius: 16px;
        padding: 22px;
        border: 1px solid rgba(255,255,255,0.06);
        border-left: 5px solid #00e676;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04);
        margin-bottom: 16px;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        transition: all 0.3s cubic-bezier(0.25,0.46,0.45,0.94);
        animation: fadeSlideUp 0.5s ease-out;
    }
    .agent-card:hover {
        transform: translateY(-3px) scale(1.005);
        box-shadow: 0 16px 48px rgba(0,230,118,0.12), inset 0 1px 0 rgba(255,255,255,0.06);
        border-color: rgba(0,230,118,0.25);
    }
    .agent-card.warn  { border-left-color: #ffca28; }
    .agent-card.danger { border-left-color: #ef5350; }

    /* ─── Metric Cards — Neon Glow ───────────────────────────── */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #141c2b 0%, #0e1420 100%);
        border: 1px solid rgba(0,230,118,0.15);
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        animation: gradientBorder 4s ease infinite;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(0,230,118,0.5);
        box-shadow: 0 8px 30px rgba(0,230,118,0.15);
        transform: translateY(-2px);
    }
    [data-testid="stMetricLabel"] {
        color: #78909c !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 1.35rem !important;
    }
    [data-testid="stMetricDelta"] > div {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 500 !important;
    }

    /* ─── Pill Tab Navigation ────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: linear-gradient(135deg, #0e1420 0%, #141c2b 100%);
        padding: 8px 10px;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.05);
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        overflow-x: auto;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 10px;
        color: #78909c;
        font-weight: 600;
        font-size: 0.82rem;
        padding: 0 14px;
        background-color: transparent;
        border: 1px solid transparent;
        transition: all 0.25s ease;
        white-space: nowrap;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #e0e6ed;
        background-color: rgba(0,230,118,0.06);
        border-color: rgba(0,230,118,0.15);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00e676 0%, #00c853 50%, #00b0ff 100%) !important;
        color: #050b14 !important;
        font-weight: 800 !important;
        border: none !important;
        box-shadow: 0 4px 18px rgba(0,230,118,0.35), 0 0 40px rgba(0,230,118,0.08);
    }

    /* ─── Primary Action Button ──────────────────────────────── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a237e 0%, #4a148c 50%, #880e4f 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 28px !important;
        box-shadow: 0 6px 24px rgba(74,20,140,0.4) !important;
        transition: all 0.3s cubic-bezier(0.25,0.46,0.45,0.94) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 10px 36px rgba(136,14,79,0.5) !important;
        background: linear-gradient(135deg, #283593 0%, #6a1b9a 50%, #ad1457 100%) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0) scale(0.98) !important;
    }

    /* ─── Input Fields & Selects ──────────────────────────────── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea textarea {
        background-color: #111827 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
        color: #e0e6ed !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus {
        border-color: rgba(0,230,118,0.5) !important;
        box-shadow: 0 0 0 3px rgba(0,230,118,0.1) !important;
    }

    /* ─── Expanders ──────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #141c2b, #0e1420) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        color: #b0bec5 !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    .streamlit-expanderHeader:hover {
        border-color: rgba(0,230,118,0.3) !important;
        color: #00e676 !important;
    }
    .streamlit-expanderContent {
        background-color: #0e1420 !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }

    /* ─── Dividers ───────────────────────────────────────────── */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent 0%, rgba(0,230,118,0.25) 50%, transparent 100%) !important;
        margin: 20px 0 !important;
    }

    /* ─── Chat Message Bubbles ───────────────────────────────── */
    [data-testid="stChatMessage"] {
        background: linear-gradient(145deg, #141c2b 0%, #0e1420 100%) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 16px !important;
        padding: 16px 20px !important;
        margin-bottom: 12px;
        animation: fadeSlideUp 0.4s ease-out;
    }

    /* ─── Plotly Chart Containers ─────────────────────────────── */
    [data-testid="stPlotlyChart"] {
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    /* ─── Success / Info / Warning / Error Alerts ─────────────── */
    .stAlert {
        border-radius: 12px !important;
        border-left-width: 5px !important;
        backdrop-filter: blur(8px);
    }

    /* ─── Custom Dark Scrollbars ──────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #1e293b, #334155);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #00e676, #00b0ff);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Vibe Stock Terminal — Pro AI Multi-Agent Trading Intelligence")
st.caption("⚡ Real-time Pipeline 5 tầng: Data Collection → Analysis Agents → Consensus → Debate Council → Final Verdict")

# ---- Sidebar ----
@st.cache_data(ttl=300)
def load_stock_data(ticker, start, end, exch="HOSE"):
    """Trả (df, status). PHẢI kiểm tra status — bộ thu thập có nhánh dự phòng
    sinh dữ liệu ngẫu nhiên (SYNTHETIC) để giữ ứng dụng chạy được. Dữ liệu đó
    không bao giờ được vẽ lên biểu đồ hay hiển thị như giá thật.

    Định nghĩa TRƯỚC sidebar để sidebar dùng được ngay trong lần chạy đầu —
    nếu không, các chỉ số tính từ giá sẽ hiện "—" cho tới lần rerun sau.
    """
    try:
        from data_collectors import VNStockCollectorAgent
        res = VNStockCollectorAgent().collect(ticker, start, end, exchange=exch)
        quality = res.get("quality")
        warns = [i.message for i in quality.warnings] if quality is not None else []
        return res.get("df"), res.get("status", "OK"), warns
    except Exception:
        return None, "FAILED", []


with st.sidebar:
    st.header("🔍 Tìm kiếm mã CK")
    symbol = st.text_input("Mã chứng khoán", value=st.session_state.get("target_symbol", "FPT")).upper()
    exchange = st.selectbox("Sàn giao dịch", ["HOSE", "HNX", "UPCOM"], index=0)
    days_back = 180  # Cố định 6 tháng — yêu cầu sản phẩm.
    # Mọi nhãn thời gian trong giao diện phải SUY RA từ cửa sổ này
    # (co_info["period_label"]), không được ghi cứng "52 tuần"/"1 năm".

    run_btn = st.button("⚡ Phân tích ngay", type="primary", use_container_width=True)

    st.divider()

    # Financial Collector Quick Sidebar Summary (Cached & Fail-Safe)
    @st.cache_data(ttl=900, show_spinner=False)
    def _fetch_sidebar_info(sym: str, exch: str, days: int):
        try:
            _end = now_vn()
            _start = _end - timedelta(days=days)
            _df, _stat, _ = load_stock_data(
                sym, _start.strftime("%Y-%m-%d"), _end.strftime("%Y-%m-%d"), exch)
            if _stat != "OK":
                _df = None
            coll = FinancialDataCollector()
            info = coll.get_company_overview(sym, _df)
            foreign = coll.get_foreign_trading_history(sym)
            return info, foreign
        except Exception:
            return {"available": False}, {"available": False}

    co_info, foreign_data = _fetch_sidebar_info(symbol, exchange, days_back)

    def _fmt(value, spec="", suffix=""):
        """Định dạng số, trả '—' nếu không có dữ liệu."""
        if value is None:
            return "—"
        try:
            return f"{value:{spec}}{suffix}" if spec else f"{value}{suffix}"
        except (ValueError, TypeError):
            return "—"

    _period = co_info.get("period_label") or "kỳ"
    st.subheader(f"🌐 Chỉ số Định giá ({symbol})")
    if co_info.get("market_cap_billions") is not None:
        st.caption(f"Vốn hóa: **{co_info['market_cap_billions']:,.0f} tỷ VNĐ**")

    st.markdown(f"""
    - **P/E:** `{_fmt(co_info['pe'], ',.2f')}` | **EPS:** `{_fmt(co_info['eps'], ',.0f', ' VNĐ')}`
    - **Beta:** `{_fmt(co_info['beta'], ',.2f')}` | **KL 10 phiên:** `{_fmt(co_info['avg_vol_10d'], ',.0f')}`
    - **Thấp - Cao ({_period}):** `{_fmt(co_info['low_period'], ',.0f')}` - `{_fmt(co_info['high_period'], ',.0f')}` VNĐ
    - **% Biến động (1 Tuần / 1 Tháng / {_period}):**
      `{_fmt(co_info['pct_1w'], '+.2f', '%')}` | `{_fmt(co_info['pct_1m'], '+.2f', '%')}` | `{_fmt(co_info['pct_period'], '+.2f', '%')}`
    """)
    if not co_info.get("available") and co_info.get("note"):
        st.caption(f"ℹ️ {co_info['note']}")

    st.markdown("##### 🌍 Giao dịch NĐTNN (10 phiên)")
    if foreign_data.get("available") and foreign_data.get("net_values_billion"):
        fig_foreign = go.Figure()
        colors = ['#00e676' if v >= 0 else '#ef5350'
                  for v in foreign_data['net_values_billion']]
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
    else:
        st.caption(f"ℹ️ {foreign_data.get('note', 'Không có dữ liệu.')}")

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

    with st.expander("🔑 Cấu hình API Key", expanded=False):
        from vnstock_auth import status_message as _vn_key_status
        st.caption(f"**vnstock:** {_vn_key_status()}")

end_date = now_vn()
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
df, _price_status, _quality_warnings = load_stock_data(
    symbol, start_str, end_str, exchange)

if _price_status != "OK":
    df = None          # chặn mọi thứ vẽ từ dữ liệu không đáng tin
    st.error(
        "⚠️ **Không kết nối được nguồn giá thật.** Ứng dụng không hiển thị "
        "biểu đồ hay chỉ số cho tới khi có dữ liệu thật — thà thiếu còn hơn sai. "
        "Vui lòng thử lại sau."
    )
else:
    st.session_state["last_ohlcv_df"] = df
    # Cảnh báo mức nhẹ: dữ liệu dùng được nhưng có điểm đáng lưu ý.
    # Lỗi nặng đã bị chặn ở tầng thu thập nên không tới được đây.
    if _quality_warnings:
        st.warning("🟡 **Lưu ý về dữ liệu:** " + " · ".join(_quality_warnings))

if df is not None and not df.empty:
    latest_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2] if len(df) > 1 else latest_close
    change = latest_close - prev_close
    pct_change = (change / prev_close) * 100 if prev_close else 0
    high_p = df['high'].max()
    low_p = df['low'].min()
    avg_vol = int(df['volume'].mean())

    # Tự động quy đổi giá từ Nghìn đồng sang VNĐ chuẩn (ví dụ 65.41 -> 65,410 VNĐ)
    mult = price_multiplier(df)   # quyết định từ trung vị cả chuỗi
    latest_close_fmt = latest_close * mult
    change_fmt = change * mult
    high_p_fmt = high_p * mult
    low_p_fmt = low_p * mult

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Giá đóng cửa", f"{latest_close_fmt:,.0f} VNĐ", f"{change_fmt:+,.0f} ({pct_change:+.2f}%)")
    c2.metric("Cao nhất (kỳ)", f"{high_p_fmt:,.0f} VNĐ")
    c3.metric("Thấp nhất (kỳ)", f"{low_p_fmt:,.0f} VNĐ")
    c4.metric("KL Trung bình", f"{avg_vol:,.0f}")

st.divider()

# ---- TABS ----
(tab_terminal, tab_main, tab_debate, tab_detail, tab_news,
 tab_paper, tab_diagram) = st.tabs([
    "📊 Tổng quan Terminal",
    "🧠 Kết quả Multi-Agent 5 Tầng",
    "⚖️ Debate Council",
    "🔬 Chi tiết từng Agent",
    "📰 Tin tức & Sentiment",
    "📒 Sổ lệnh Agent",
    "📐 Sơ đồ Pipeline"
])

# =====================================================================
# TAB 0: VIBE STOCK TERMINAL PRO FINANCIAL DASHBOARD
# =====================================================================
with tab_terminal:
    fin_coll = FinancialDataCollector()
    fin_data = fin_coll.get_financial_statements(symbol)

    st.title(f"🏢 CTCP / Doanh nghiệp [{symbol}] ({exchange})")
    st.caption(f"Cập nhật lúc: {now_vn().strftime('%H:%M:%S %d/%m')} | Việt Nam (GMT+7)")

    # 1. Main Candlestick Chart
    st.subheader(f"📈 Đồ thị Kỹ thuật Nến Nhật & Khối lượng ({symbol})")
    if df is not None and not df.empty:
        fig_main = go.Figure()
        
        # Moving Averages
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()

        mult = price_multiplier(df)

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

    # 2. Biểu đồ Báo cáo tài chính — CHỈ vẽ từ số liệu thật
    # Bản cũ có 4 biểu đồ, nhưng 2 trong số đó (cơ cấu giá vốn, tài sản
    # ngắn/dài hạn) được dựng từ tỷ lệ tự đặt (cogs = doanh thu × 0.65 v.v.)
    # chứ không phải số liệu công bố. Đã gỡ. Chỉ giữ phần lấy được từ nguồn.
    st.subheader("📊 Báo cáo Tài chính & Sức khỏe Doanh nghiệp")

    if not fin_data.get("available"):
        st.info(
            f"ℹ️ {fin_data.get('note', 'Không có dữ liệu báo cáo tài chính.')}\n\n"
            "Ứng dụng không hiển thị số liệu ước tính thay thế."
        )
    else:
        st.caption(f"Nguồn: {fin_data.get('note', 'vnstock')}")
        grid_col1, grid_col2 = st.columns(2)

        # ── Doanh thu & Lợi nhuận ròng ─────────────────────────────────
        with grid_col1:
            st.markdown("##### 1️⃣ Doanh thu & Lợi nhuận ròng")
            fig_perf = go.Figure()
            fig_perf.add_trace(go.Bar(
                x=fin_data['years'], y=fin_data['revenue'],
                name="Doanh thu thuần", marker_color='#29b6f6'
            ))
            if any(v is not None for v in fin_data.get('net_profit', [])):
                fig_perf.add_trace(go.Scatter(
                    x=fin_data['years'], y=fin_data['net_profit'],
                    name="Lợi nhuận ròng", mode='lines+markers',
                    line=dict(color='#ffca28', width=3)
                ))
            fig_perf.update_layout(
                height=300, template="plotly_dark", paper_bgcolor='#1e222d',
                plot_bgcolor='#1e222d', margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig_perf, use_container_width=True)

        # ── Vốn chủ sở hữu & Nợ phải trả ───────────────────────────────
        with grid_col2:
            st.markdown("##### 2️⃣ Vốn chủ sở hữu & Nợ phải trả")
            if fin_data.get('equity') and fin_data.get('debt'):
                fig_bs = go.Figure()
                fig_bs.add_trace(go.Bar(x=fin_data['years'], y=fin_data['equity'],
                                        name="Vốn CSH", marker_color='#26a69a'))
                fig_bs.add_trace(go.Bar(x=fin_data['years'], y=fin_data['debt'],
                                        name="Nợ phải trả", marker_color='#ff7043'))
                if fin_data.get('debt_to_equity'):
                    fig_bs.add_trace(go.Scatter(
                        x=fin_data['years'], y=fin_data['debt_to_equity'],
                        name="Nợ/VCSH", yaxis="y2", mode='lines+markers',
                        line=dict(color='#ffee58', width=2)
                    ))
                fig_bs.update_layout(
                    barmode='stack', height=300, template="plotly_dark",
                    paper_bgcolor='#1e222d', plot_bgcolor='#1e222d',
                    margin=dict(l=10, r=10, t=20, b=10),
                    yaxis2=dict(overlaying='y', side='right', showgrid=False),
                    legend=dict(orientation="h", y=1.1)
                )
                st.plotly_chart(fig_bs, use_container_width=True)
            else:
                st.info("ℹ️ Nguồn dữ liệu không có bảng cân đối kế toán cho mã này.")

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
                    r0, r1, r2, r3, r4 = st.columns(5)
                    entry_p = rec.get("entry_price", 0)
                    r0.metric("Giá vào lệnh", f"{entry_p:,.0f} VNĐ" if entry_p else "—", "Vùng mua đề xuất")
                    r1.metric("Stop-loss (ATR)", f"{rec['stop_loss_price']:,.0f} VNĐ", f"-{rec['stop_loss_pct']}%", delta_color="inverse")
                    r2.metric("TP1 (Chốt 50%)", f"{rec['take_profit_price']:,.0f} VNĐ", f"+{rec['take_profit_pct']}%")
                    tp2_p = rec.get("tp2_price", 0)
                    r3.metric("TP2 Trailing (Gồng)", f"{tp2_p:,.0f} VNĐ" if tp2_p else "—", f"+{rec.get('tp2_pct',0)}%")
                    r4.metric("Phân bổ vốn", f"{rec['suggested_position_size_pct']}%", f"RR {rec['risk_reward_ratio']}")
                if key == "sr" and "levels" in data:
                    lvl = data["levels"]
                    st.divider()
                    l1, l2, l3 = st.columns(3)
                    _lbl = lvl.get('period_label', 'kỳ')
                    l1.metric(f"Đỉnh {_lbl}", f"{lvl.get('high_period',0):,.2f}")
                    l2.metric(f"Đáy {_lbl}", f"{lvl.get('low_period',0):,.2f}")
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



with tab_paper:
    st.subheader("📒 Sổ lệnh Giấy của Agent")
    st.caption("Ghi lại mọi quyết định của agent để kiểm chứng hiệu quả. "
               "**Không đặt lệnh thật** — đây là sổ theo dõi, không phải "
               "công cụ giao dịch.")

    import pathlib as _pl

    _db = _pl.Path(__file__).parent / "paper_trades.db"
    if not _db.exists():
        st.info("ℹ️ Sổ lệnh giấy chưa có dữ liệu lịch sử. Bạn có thể nhấn nút dưới đây để khởi tạo sổ lệnh tự động.")
        if st.button("🚀 Khởi tạo Sổ Lệnh Giấy (Seed Demo Data)", type="primary", use_container_width=True):
            with st.spinner("⚡ Đang nạp dữ liệu lịch sử và tạo sổ lệnh..."):
                try:
                    from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS
                    args = Namespace(db=str(_db), symbols=",".join(CUSTOM_WATCHLIST_SYMBOLS), min_history=60, stride=2, buy_threshold=50.0)
                    cmd_seed(args)
                    st.success("✅ Đã khởi tạo sổ lệnh thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Không thể khởi tạo tự động: {e}")
    else:
        from paper_metrics import compute as _perf
        from paper_trading import PaperTradingJournal as _PJ

        _j = _PJ(str(_db))
        _trades = _j.all_trades()
        _closed = [t for t in _trades if t.status == "CLOSED"]
        _open = [t for t in _trades if t.status in ("OPEN", "PENDING", "CLOSING")]
        _perf_res = _perf(_trades)
        st.markdown("### 📌 DANH SÁCH LỆNH ĐANG MỞ & CHỜ KHỚP (ACTIVE POSITIONS)")
        if _open:
            def _get_entry_display(t):
                if t.entry_price:
                    return f"{t.entry_price:,.0f} VNĐ"
                if t.status == "PENDING" and t.stop_loss:
                    est_p = round(t.stop_loss / 0.95, 0)
                    return f"~{est_p:,.0f} VNĐ (Đề xuất)"
                return "Chờ khớp phiên tới"

            st.dataframe(pd.DataFrame([{
                "Mã": t.symbol,
                "Trạng thái": t.status,
                "Ngày vào": t.entry_date or t.signal_date or "Chờ phiên sau",
                "Giá vào": _get_entry_display(t),
                "Cắt lỗ (SL)": f"{t.stop_loss:,.0f} VNĐ" if t.stop_loss else "—",
                "Chốt lời (TP)": f"{t.take_profit:,.0f} VNĐ" if t.take_profit else "—",
                "Vốn": f"{getattr(t, 'position_size_pct', 30):.0f}%",
                "Điểm vào": t.entry_score,
            } for t in _open]), use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ **Hiện tại không có lệnh nào đang mở.** Tất cả vị thế đã được đóng / cắt lỗ / chốt lời an toàn.")

        st.divider()

        if _perf_res is None:
            st.warning(f"Có {len(_trades)} lệnh nhưng chưa lệnh nào đóng.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Lệnh đã đóng", f"{_perf_res.n_trades}")
            c2.metric("Tỷ lệ thắng", f"{_perf_res.win_rate:.0%}")
            c3.metric("Kỳ vọng/lệnh", f"{_perf_res.expectancy:+.2f}%",
                      help="Đã trừ phí môi giới hai chiều và thuế bán")
            c4.metric("Sụt giảm tối đa", f"{_perf_res.max_drawdown_pct:.1f}%")

            from paper_metrics import expectancy_significant as _sig
            _s = _sig(_trades)
            if _s["expectancy"] is None:
                st.warning(f"⚠️ {_s['verdict']}")
            elif _s["significant"]:
                st.success(f"✅ {_s['verdict']} — kỳ vọng {_s['expectancy']:+.2f}% "
                           f"[KTC 95%: {_s['ci'][0]:+.2f}%, {_s['ci'][1]:+.2f}%]")
            else:
                st.warning(
                    f"⚠️ {_s['verdict']}\n\n"
                    f"Kỳ vọng {_s['expectancy']:+.2f}% nhưng khoảng tin cậy "
                    f"[{_s['ci'][0]:+.2f}%, {_s['ci'][1]:+.2f}%] chứa 0 — "
                    "chưa kết luận được gì. Cần thêm mẫu.")

            st.markdown("##### Lý do đóng lệnh")
            _labels = {"STOP_LOSS": "Chạm cắt lỗ", "TAKE_PROFIT": "Chạm chốt lời",
                       "SIGNAL_REVERSED": "Tín hiệu đảo chiều",
                       "MAX_HOLD": "Hết hạn nắm giữ"}
            _rows = [{"Lý do": _labels.get(k, k), "Số lệnh": v,
                      "Tỷ lệ": f"{v / _perf_res.n_trades:.0%}"}
                     for k, v in sorted(_perf_res.by_exit_reason.items(),
                                        key=lambda x: -x[1])]
            st.dataframe(pd.DataFrame(_rows), use_container_width=True,
                         hide_index=True)

        if _closed:
            st.markdown("##### Lệnh gần nhất")
            st.dataframe(pd.DataFrame([{
                "Mã": t.symbol, "Vào": t.entry_date, "Ra": t.exit_date,
                "Giá vào": f"{t.entry_price:,.0f}",
                "Giá ra": f"{t.exit_price:,.0f}",
                "Lý do": _labels.get(t.exit_reason, t.exit_reason),
                "Lãi/lỗ sau phí": f"{t.net_return_pct():+.2f}%",
                "Điểm vào": t.entry_score,
            } for t in _closed[-25:][::-1]]), use_container_width=True,
                hide_index=True)

        # ── Xem lại từng quyết định trên biểu đồ ──────────────────────
        if _closed:
            st.divider()
            st.markdown("##### 🔍 Xem lại quyết định trên biểu đồ")
            st.caption("Vùng mờ bên phải là phần agent **chưa biết** khi ra "
                       "quyết định. Che nó đi mới đánh giá được: với thông tin "
                       "có lúc đó, quyết định này có hợp lý không?")

            _opts = {
                f"{t.symbol} · {t.signal_date} · {t.net_return_pct():+.2f}% "
                f"({t.exit_reason})": t
                for t in _closed[::-1][:100]
            }
            _pick = st.selectbox("Chọn lệnh", list(_opts.keys()))
            _t = _opts[_pick]

            try:
                from backtest import data as _btd
                _price_df = _btd.load(_t.symbol)
                if _price_df is None or _price_df.empty:
                    _end_d = now_vn().strftime("%Y-%m-%d")
                    _price_df = _btd.fetch_one(_t.symbol, "2024-01-01", _end_d)
            except Exception:
                _price_df = None

            if _price_df is None or _price_df.empty:
                st.warning(f"⚠️ Chưa có dữ liệu giá của {_t.symbol}. Đang kết nối lại nguồn dữ liệu...")
            else:
                import trade_review as _tr
                st.plotly_chart(_tr.build_figure(_price_df, _t),
                                use_container_width=True)
                st.caption(f"**Kết cục:** {_tr.outcome_summary(_t)}")

                _ctx = _tr.decision_context(_j, _t)
                if _ctx:
                    _c1, _c2 = st.columns([1, 2])
                    with _c1:
                        st.markdown("**Điểm lúc quyết định**")
                        st.metric("Tổng", _ctx["score"])
                        for _k, _v in (_ctx.get("components") or {}).items():
                            if _k.endswith("_score"):
                                st.caption(f"{_k.replace('_score','')}: {_v}")
                    with _c2:
                        st.markdown("**Lý do agent đưa ra lúc đó**")
                        for _r in (_ctx.get("reasons") or [])[:8]:
                            st.caption(f"• {_r}")

        _skipped = _j.decisions(acted=False)
        _all = _j.decisions()
        st.caption(
            f"Đã ghi {len(_all):,} quyết định — vào lệnh {len(_all) - len(_skipped):,}, "
            f"bỏ qua {len(_skipped):,}. Ghi cả quyết định không vào lệnh để sổ "
            "không bị thiên lệch chọn mẫu."
        )
        st.info(
            "ℹ️ Sổ này chỉ đo **tín hiệu**. Giao dịch thật còn có trượt giá, "
            "khớp một phần và tâm lý — kết quả thực tế sẽ thấp hơn. "
            "Dưới ~100 lệnh, mọi kết luận đều mong manh."
        )

with tab_diagram:
    st.subheader("📐 Sơ đồ Kiến trúc System & Luồng Vận hành Multi-Agent")
    import pathlib

    def load_html_diagram(filename):
        # Chỉ tìm cạnh mã nguồn. Đường dẫn tuyệt đối theo máy cá nhân đã bị gỡ
        # vì dự án sẽ không chạy được trên máy/CI khác.
        # Cần thư mục khác? Đặt biến môi trường VIBE_DIAGRAM_DIR.
        paths = [pathlib.Path(__file__).parent / filename]
        extra = os.environ.get("VIBE_DIAGRAM_DIR")
        if extra:
            paths.append(pathlib.Path(extra) / filename)
        for p in paths:
            if p.exists():
                return p.read_text(encoding="utf-8")
        return None

    d_tab1, d_tab2, d_tab3 = st.tabs([
        "🏛️ Sơ đồ 1: Kiến trúc System Multi-Agent (Debate Council & Feedback Loop)",
        "🛡️ Sơ đồ 2: Engine Tất định & Phản biện Khác hãng (Architecture v2)",
        "📊 Sơ đồ 3: Pipeline Luồng Dữ liệu Chi tiết"
    ])

    with d_tab1:
        html1 = load_html_diagram("architecture_diagram.html")
        if html1:
            st.components.v1.html(html1, height=1000, scrolling=True)
        else:
            st.warning("⚠️ Chưa tìm thấy file architecture_diagram.html")

    with d_tab2:
        html2 = load_html_diagram("architecture_diagram_v2.html") or load_html_diagram("emergency_flow_diagram.html")
        if html2:
            st.components.v1.html(html2, height=1000, scrolling=True)
        else:
            st.warning("⚠️ Chưa tìm thấy file architecture_diagram_v2.html")

    with d_tab3:
        html3 = load_html_diagram("pipeline_diagram.html")
        if html3:
            st.components.v1.html(html3, height=1000, scrolling=True)
        else:
            st.warning("⚠️ Chưa tìm thấy file pipeline_diagram.html")


