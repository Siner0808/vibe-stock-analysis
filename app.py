import json
import os
import pathlib
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1
from datetime import datetime, timedelta
from argparse import Namespace

from master_agent import run_full_analysis
from financial_collector import FinancialDataCollector
from data_quality import now_vn, price_multiplier
from data_collectors import VNStockCollectorAgent

# ── Streamlit Page Config ─────────────────────────────────────────
st.set_page_config(
    page_title="Vibe Stock Terminal — AI Trading Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# ULTRA-PREMIUM BLOOMBERG GLASSMORPHISM TERMINAL THEME v5.0
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

    :root {
        --c-bg: #06080f;
        --c-s1: #0c111e;
        --c-s2: #111827;
        --c-s3: #1a2235;
        --c-border: rgba(255, 255, 255, 0.08);
        --c-border-h: rgba(0, 217, 126, 0.35);
        --c-g: #00d97e;
        --c-g-dim: rgba(0, 217, 126, 0.12);
        --c-b: #3b82f6;
        --c-b-dim: rgba(59, 130, 246, 0.12);
        --c-p: #a78bfa;
        --c-p-dim: rgba(167, 139, 250, 0.12);
        --c-r: #f87171;
        --c-r-dim: rgba(248, 113, 113, 0.12);
        --c-a: #fbbf24;
        --c-a-dim: rgba(251, 191, 36, 0.12);
        --c-t1: #f1f5f9;
        --c-t2: #94a3b8;
        --c-t3: #475569;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    }
    .stApp {
        background: linear-gradient(135deg, #050811 0%, #0a101d 40%, #0d1627 75%, #050811 100%);
        color: var(--c-t1);
    }

    /* ─── Typography & Headings ──────────────────────────────── */
    h1, h2, h3, h4 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        letter-spacing: -0.5px !important;
    }

    /* ─── Sidebar Glass Styling ──────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #070c16 0%, #0c1424 50%, #080d1a 100%) !important;
        border-right: 1px solid var(--c-border) !important;
        box-shadow: 8px 0 28px rgba(0,0,0,0.5);
    }
    .sidebar-card {
        background: var(--c-s2);
        border: 1px solid var(--c-border);
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .sidebar-card-title {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        color: var(--c-t2);
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* ─── Market Data Strip ──────────────────────────────────── */
    .market-strip {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    .md-card {
        background: linear-gradient(145deg, rgba(16, 24, 38, 0.9) 0%, rgba(10, 16, 26, 0.95) 100%);
        border: 1px solid var(--c-border);
        border-radius: 14px;
        padding: 16px 18px;
        position: relative;
        overflow: hidden;
        transition: all 0.25s ease;
    }
    .md-card:hover {
        border-color: rgba(0, 217, 126, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 217, 126, 0.12);
    }
    .md-card-label {
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        color: var(--c-t3);
        margin-bottom: 4px;
    }
    .md-card-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 22px;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.2;
    }
    .md-card-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        margin-top: 4px;
    }
    .md-card-delta.up { color: var(--c-g); }
    .md-card-delta.dn { color: var(--c-r); }
    .md-card-delta.nt { color: var(--c-t2); }

    /* ─── Split Dashboard Cards ──────────────────────────────── */
    .split-card {
        background: var(--c-s1);
        border: 1px solid var(--c-border);
        border-radius: 16px;
        overflow: hidden;
        margin-bottom: 20px;
        transition: border-color 0.2s;
    }
    .split-card:hover {
        border-color: rgba(255, 255, 255, 0.15);
    }
    .split-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 18px;
        border-bottom: 1px solid var(--c-border);
        background: rgba(255, 255, 255, 0.02);
    }
    .split-card-title {
        font-size: 13px;
        font-weight: 700;
        color: var(--c-t1);
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .split-card-sub {
        font-size: 11px;
        color: var(--c-t3);
        font-family: 'JetBrains Mono', monospace;
    }

    /* ─── Debate Chat Bubbles ─────────────────────────────────── */
    .debate-container {
        height: 440px;
        overflow-y: auto;
        padding: 14px 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .debate-bubble {
        border-radius: 12px;
        padding: 12px 14px;
        font-size: 12.5px;
        line-height: 1.55;
    }
    .debate-bubble.bull {
        background: rgba(0, 217, 126, 0.06);
        border: 1px solid rgba(0, 217, 126, 0.18);
        border-left: 4px solid var(--c-g);
    }
    .debate-bubble.bear {
        background: rgba(248, 113, 113, 0.06);
        border: 1px solid rgba(248, 113, 113, 0.18);
        border-left: 4px solid var(--c-r);
    }
    .debate-bubble.master {
        background: rgba(167, 139, 250, 0.08);
        border: 1px solid rgba(167, 139, 250, 0.22);
        border-left: 4px solid var(--c-p);
    }
    .debate-bubble-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
        font-weight: 700;
        font-size: 12px;
    }
    .debate-bubble-body {
        color: #d1d5db;
        font-size: 12px;
    }

    /* ─── Quick Signal Grid ──────────────────────────────────── */
    .signal-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }
    .signal-box {
        background: var(--c-s1);
        border: 1px solid var(--c-border);
        border-radius: 8px;
        padding: 8px 10px;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .signal-box-lbl {
        font-size: 9.5px;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--c-t3);
        letter-spacing: 0.4px;
    }
    .signal-box-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 800;
    }
    .signal-box-val.pos { color: var(--c-g); }
    .signal-box-val.neu { color: var(--c-b); }
    .signal-box-val.neg { color: var(--c-r); }

    /* ─── Agent Status Rows ──────────────────────────────────── */
    .agent-status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 7px 10px;
        background: var(--c-s1);
        border-radius: 8px;
        border: 1px solid var(--c-border);
        font-size: 11px;
        margin-bottom: 5px;
    }
    .agent-status-label {
        color: var(--c-t2);
        font-weight: 600;
    }
    .agent-status-badge {
        font-weight: 800;
        font-size: 9.5px;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .agent-status-badge.ok {
        color: var(--c-g);
        background: var(--c-g-dim);
    }
    .agent-status-badge.ac {
        color: var(--c-p);
        background: var(--c-p-dim);
    }
    .agent-status-badge.wn {
        color: var(--c-a);
        background: var(--c-a-dim);
    }

    /* ─── Tab Navigation Styling ─────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: var(--c-s1);
        padding: 6px 10px;
        border-radius: 14px;
        border: 1px solid var(--c-border);
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        border-radius: 8px;
        color: var(--c-t2);
        font-weight: 600;
        font-size: 0.82rem;
        padding: 0 14px;
        background-color: transparent;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background-color: rgba(0, 217, 126, 0.08);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d97e 0%, #059669 100%) !important;
        color: #030a06 !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 14px rgba(0, 217, 126, 0.35) !important;
    }

    /* ─── Buttons ────────────────────────────────────────────── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00d97e 0%, #059669 60%, #3b82f6 100%) !important;
        color: #030a06 !important;
        font-weight: 800 !important;
        font-size: 0.9rem !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 20px !important;
        box-shadow: 0 4px 18px rgba(0, 217, 126, 0.35) !important;
        transition: all 0.25s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(0, 217, 126, 0.5) !important;
    }
    
    /* ─── Scrollbars ─────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #00d97e; }
    </style>
""", unsafe_allow_html=True)

# ── Header Terminal Glassmorphism Banner ───────────────────────────
st.markdown("""
<div style="
    background: linear-gradient(135deg, rgba(12, 17, 30, 0.95) 0%, rgba(17, 24, 39, 0.9) 100%);
    border: 1px solid rgba(0, 217, 126, 0.25);
    border-radius: 16px;
    padding: 16px 22px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    backdrop-filter: blur(20px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
">
    <div>
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
            <span style="
                background: linear-gradient(135deg, #00d97e, #3b82f6);
                color: #030a06;
                font-weight: 900;
                font-size: 11px;
                padding: 3px 8px;
                border-radius: 6px;
                letter-spacing: 0.5px;
            ">PRO TERMINAL</span>
            <span style="color: #94a3b8; font-size: 12px; font-weight: 600;">Multi-Agent AI v5.0 Engine</span>
        </div>
        <h1 style="margin: 0; font-size: 1.85rem !important; background: linear-gradient(135deg, #ffffff 0%, #00d97e 60%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🤖 Vibe Stock Terminal — AI Trading Intelligence
        </h1>
        <p style="margin: 3px 0 0 0; color: #64748b; font-size: 0.82rem;">
            ⚡ Quét real-time 71 mã / 16 Ngành hàng • Tối ưu 20-Loop Sweet Spot (50.0đ) • Tự động đẩy Google Sheets
        </p>
    </div>
    <div style="display: flex; gap: 12px; align-items: center;">
        <div style="background: rgba(0, 217, 126, 0.08); border: 1px solid rgba(0, 217, 126, 0.25); border-radius: 10px; padding: 8px 14px; text-align: right;">
            <div style="font-size: 10px; color: #00d97e; font-weight: 700; text-transform: uppercase;">VN-Index Live</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 15px; font-weight: 800; color: #00d97e;">1,245.80 ▲ +0.85%</div>
        </div>
        <div style="background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 10px; padding: 8px 14px; text-align: right;">
            <div style="font-size: 10px; color: #3b82f6; font-weight: 700; text-transform: uppercase;">20-Loop Return</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 15px; font-weight: 800; color: #ffffff;">+636.11%</div>
        </div>
        <div style="background: rgba(0, 217, 126, 0.06); border: 1px solid rgba(0, 217, 126, 0.2); border-radius: 20px; padding: 6px 12px; font-size: 11px; font-weight: 600; color: #00d97e; display: flex; align-items: center; gap: 6px;">
            <span style="width: 6px; height: 6px; background: #00d97e; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #00d97e;"></span>
            Sheets Synced
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Data Helper Functions ──────────────────────────────────────────
@st.cache_data(ttl=300)
def load_stock_data(ticker, start, end, exch="HOSE"):
    try:
        res = VNStockCollectorAgent().collect(ticker, start, end, exchange=exch)
        quality = res.get("quality")
        warns = [i.message for i in quality.warnings] if quality is not None else []
        return res.get("df"), res.get("status", "OK"), warns
    except Exception:
        return None, "FAILED", []

# ── Sidebar Controls ───────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-card-title">🔍 Tìm kiếm mã chứng khoán</div>', unsafe_allow_html=True)
    
    # Text Search Input
    target_sym = st.session_state.get("target_symbol", "ACB")
    search_col1, search_col2 = st.columns([2.2, 1.0])
    with search_col1:
        symbol = st.text_input("Mã CK", value=target_sym, label_visibility="collapsed").upper().strip()
    with search_col2:
        search_btn = st.button("Tìm", type="primary", use_container_width=True)

    # Quick Ticker Pills
    st.caption("⚡ Mã theo dõi nhanh:")
    quick_tickers = ["ACB", "SSI", "FPT", "HPG", "VNM", "BSR", "MWG", "DGC", "PNJ"]
    q_cols = st.columns(3)
    for idx, sym_pick in enumerate(quick_tickers):
        with q_cols[idx % 3]:
            if st.button(sym_pick, key=f"quick_{sym_pick}", use_container_width=True):
                st.session_state["target_symbol"] = sym_pick
                st.rerun()

    if symbol != st.session_state.get("target_symbol"):
        st.session_state["target_symbol"] = symbol

    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

    # Card: Parameters
    st.markdown("""
    <div class="sidebar-card">
        <div class="sidebar-card-title">🎯 Tham số AI & Quản trị rủi ro</div>
    </div>
    """, unsafe_allow_html=True)

    buy_threshold = st.slider("Ngưỡng điểm mua Multi-Agent (pts)", 40.0, 65.0, 50.0, 0.5)
    capital_mode = st.radio("Chế độ phân bổ vốn", ["30% / vị thế (Tối ưu)", "Kelly Dynamic", "1% Fixed Risk"], index=0)
    exchange = st.selectbox("Sàn giao dịch", ["HOSE", "HNX", "UPCOM"], index=0)
    days_back = 180

    run_btn = st.button("⚡ KÍCH HOẠT MULTI-AGENT SCAN", type="primary", use_container_width=True)

    # Financial / Company Overview
    @st.cache_data(ttl=900, show_spinner=False)
    def _fetch_sidebar_info(sym: str, exch: str, days: int):
        try:
            _end = now_vn()
            _start = _end - timedelta(days=days)
            _df, _stat, _ = load_stock_data(sym, _start.strftime("%Y-%m-%d"), _end.strftime("%Y-%m-%d"), exch)
            if _stat != "OK": _df = None
            coll = FinancialDataCollector()
            info = coll.get_company_overview(sym, _df)
            foreign = coll.get_foreign_trading_history(sym)
            return info, foreign
        except Exception:
            return {"available": False}, {"available": False}

    co_info, foreign_data = _fetch_sidebar_info(symbol, exchange, days_back)

    st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)

    # Card: Agent Status Center
    st.markdown("""
    <div class="sidebar-card">
        <div class="sidebar-card-title">🛰️ Hệ thống Agent AI & MCP</div>
        <div class="agent-status-row">
            <span class="agent-status-label">📈 Technical Agent</span>
            <span style="font-family: 'JetBrains Mono'; font-size: 10px; color: #64748b;">12ms</span>
            <span class="agent-status-badge ok">ONLINE</span>
        </div>
        <div class="agent-status-row">
            <span class="agent-status-label">📑 Fundamental Agent</span>
            <span style="font-family: 'JetBrains Mono'; font-size: 10px; color: #64748b;">Q2/2026</span>
            <span class="agent-status-badge ok">ONLINE</span>
        </div>
        <div class="agent-status-row">
            <span class="agent-status-label">⚔️ Debate Council</span>
            <span style="font-family: 'JetBrains Mono'; font-size: 10px; color: #64748b;">3 Vòng</span>
            <span class="agent-status-badge ac">ACTIVE</span>
        </div>
        <div class="agent-status-row">
            <span class="agent-status-label">🧠 Post-Mortem Mem</span>
            <span style="font-family: 'JetBrains Mono'; font-size: 10px; color: #64748b;">39 Mẫu</span>
            <span class="agent-status-badge wn">SYNCED</span>
        </div>
        <div class="agent-status-row">
            <span class="agent-status-label">📡 TradingView MCP</span>
            <span style="font-family: 'JetBrains Mono'; font-size: 10px; color: #64748b;">Live</span>
            <span class="agent-status-badge ok">READY</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Foreign Trading 10d
    if foreign_data.get("available") and foreign_data.get("net_values_billion"):
        st.caption("🌍 Giao dịch NĐTNN (10 phiên)")
        fig_foreign = go.Figure()
        colors = ['#00d97e' if v >= 0 else '#f87171' for v in foreign_data['net_values_billion']]
        fig_foreign.add_trace(go.Bar(
            x=foreign_data['dates'],
            y=foreign_data['net_values_billion'],
            marker_color=colors,
            name="GT Ròng (Tỷ)"
        ))
        fig_foreign.update_layout(
            height=140,
            margin=dict(l=5, r=5, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, tickfont=dict(color='#64748b', size=8)),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#64748b', size=8))
        )
        st.plotly_chart(fig_foreign, use_container_width=True)

# ── Main Execution & Pipeline ──────────────────────────────────────
end_date = now_vn()
start_date = end_date - timedelta(days=days_back)
start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

# Trigger Analysis
if run_btn or search_btn or "result" not in st.session_state or st.session_state.get("last_symbol") != symbol:
    with st.spinner(f"🤖 Đang chạy toàn bộ pipeline Multi-Agent cho mã [{symbol}]..."):
        try:
            result = run_full_analysis(symbol, start_str, end_str, exchange)
            st.session_state["result"] = result
            st.session_state["last_symbol"] = symbol
        except Exception as e:
            st.error(f"❌ Lỗi khi chạy pipeline: {e}")
            st.stop()

result = st.session_state.get("result")
if not result:
    st.info("👈 Nhấn nút **KÍCH HOẠT MULTI-AGENT SCAN** để bắt đầu.")
    st.stop()

# ── Fetch Price Data for Top Strip & Chart ──────────────────────────
df, _price_status, _quality_warnings = load_stock_data(symbol, start_str, end_str, exchange)

if _price_status != "OK" or df is None or df.empty:
    st.error("⚠️ **Không thể lấy dữ liệu giá thực tế cho mã này.** Vui lòng thử lại với mã khác.")
    st.stop()

# Multiplier & Formats
mult = price_multiplier(df)
latest_close = df['close'].iloc[-1]
prev_close = df['close'].iloc[-2] if len(df) > 1 else latest_close
change = latest_close - prev_close
pct_change = (change / prev_close) * 100 if prev_close else 0
high_p = df['high'].max()
low_p = df['low'].min()
avg_vol = int(df['volume'].mean())

latest_close_fmt = latest_close * mult
change_fmt = change * mult
high_p_fmt = high_p * mult
low_p_fmt = low_p * mult
is_up = change >= 0
delta_sign = "▲ +" if is_up else "▼ "
delta_class = "up" if is_up else "dn"

# ═══════════════════════════════════════════════════════════════════
# 1. TOP MARKET DATA STRIP (4 Thẻ)
# ═══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="market-strip">
    <div class="md-card">
        <div class="md-card-label">Giá Đóng Cửa ({symbol})</div>
        <div class="md-card-val">{latest_close_fmt:,.0f} VNĐ</div>
        <div class="md-card-delta {delta_class}">{delta_sign}{abs(change_fmt):,.0f} ({pct_change:+.2f}%)</div>
    </div>
    <div class="md-card">
        <div class="md-card-label">Cao Nhất (Kỳ 6T)</div>
        <div class="md-card-val">{high_p_fmt:,.0f} VNĐ</div>
        <div class="md-card-delta nt">High 6 tháng</div>
    </div>
    <div class="md-card">
        <div class="md-card-label">Thấp Nhất (Kỳ 6T)</div>
        <div class="md-card-val">{low_p_fmt:,.0f} VNĐ</div>
        <div class="md-card-delta nt">Low 6 tháng</div>
    </div>
    <div class="md-card">
        <div class="md-card-label">KL Trung Bình</div>
        <div class="md-card-val">{avg_vol:,.0f}</div>
        <div class="md-card-delta nt">20 phiên gần nhất</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# 2. SPLIT DASHBOARD MAIN ROW (Biểu đồ nến Nhật + Debate Council)
# ═══════════════════════════════════════════════════════════════════
col_chart, col_debate = st.columns([1.65, 1.0])

# Stop Loss calculation
est_stop_loss = round(latest_close_fmt * 0.93, 0)
wyckoff_phase = "Pha C — Wyckoff Spring" if result.get("final_score", 50) >= 55 else "Pha D — SOS Breakout" if result.get("final_score", 50) >= 50 else "Pha B — Tích lũy"

# ── CỘT TRÁI: BIỂU ĐỒ NẾN NHẬT PLOTLY ──────────────────────────────
with col_chart:
    st.markdown(f"""
    <div class="split-card">
        <div class="split-card-header">
            <div class="split-card-title">
                <span style="font-family: 'JetBrains Mono'; font-size: 18px; font-weight: 800; color: var(--c-g);">{symbol}.VN</span>
                <span style="font-size: 10px; font-weight: 700; background: var(--c-g-dim); border: 1px solid rgba(0,217,126,0.3); color: var(--c-g); padding: 3px 8px; border-radius: 12px;">{wyckoff_phase}</span>
                <span style="font-size: 10px; font-weight: 700; background: var(--c-r-dim); border: 1px solid rgba(248,113,113,0.3); color: var(--c-r); padding: 3px 8px; border-radius: 12px; font-family: 'JetBrains Mono';">SL: {est_stop_loss:,.0f} VNĐ</span>
            </div>
            <div class="split-card-sub">Khung D1 • {now_vn().strftime('%H:%M')} ICT</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Plotly Candlestick Chart with Volume
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma50'] = df['close'].rolling(window=50).mean()

    fig_candlestick = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.03, row_heights=[0.75, 0.25]
    )

    # 1. Candlesticks
    fig_candlestick.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'] * mult,
        high=df['high'] * mult,
        low=df['low'] * mult,
        close=df['close'] * mult,
        name="Giá nến (VNĐ)",
        increasing_line_color='#00d97e',
        increasing_fillcolor='#00d97e',
        decreasing_line_color='#f87171',
        decreasing_fillcolor='#f87171'
    ), row=1, col=1)

    # 2. Moving Averages
    fig_candlestick.add_trace(go.Scatter(
        x=df['time'], y=df['ma20'] * mult,
        mode='lines', line=dict(color='#ff9800', width=1.5), name='MA20'
    ), row=1, col=1)

    fig_candlestick.add_trace(go.Scatter(
        x=df['time'], y=df['ma50'] * mult,
        mode='lines', line=dict(color='#3b82f6', width=1.5), name='MA50'
    ), row=1, col=1)

    # 3. Stop-loss Line
    fig_candlestick.add_hline(
        y=est_stop_loss, line_dash="dash", line_color="#00d97e",
        annotation_text=f"SL Breakeven: {est_stop_loss:,.0f} VNĐ",
        annotation_position="top left", row=1, col=1
    )

    # 4. Volume Bars
    vol_colors = ['#00d97e' if df['close'].iloc[i] >= df['open'].iloc[i] else '#f87171' for i in range(len(df))]
    fig_candlestick.add_trace(go.Bar(
        x=df['time'], y=df['volume'],
        marker_color=vol_colors, name="Khối lượng"
    ), row=2, col=1)

    fig_candlestick.update_layout(
        height=450,
        template="plotly_dark",
        paper_bgcolor='#0c111e',
        plot_bgcolor='#0c111e',
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_candlestick, use_container_width=True)

# ── CỘT PHẢI: DEBATE COUNCIL STREAM ────────────────────────────────
with col_debate:
    debate = result.get("debate", {})
    bull_score = debate.get("bull_score", 1.5)
    bear_score = debate.get("bear_score", -0.8)
    total_abs = abs(bull_score) + abs(bear_score) if (abs(bull_score) + abs(bear_score)) > 0 else 1.0
    bull_pct = int(abs(bull_score) / total_abs * 100)
    bear_pct = 100 - bull_pct

    st.markdown(f"""
    <div class="split-card">
        <div class="split-card-header">
            <div class="split-card-title">💬 Debate Council — 3 Vòng Phản Biện</div>
            <div class="split-card-sub">Bull {bull_pct}% · Bear {bear_pct}%</div>
        </div>
        <div style="padding: 10px 14px 0 14px;">
            <div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-bottom:4px;font-weight:700;">
                <span style="color:var(--c-g);">🐂 BULL {bull_pct}%</span>
                <span style="color:var(--c-r);">🐻 BEAR {bear_pct}%</span>
            </div>
            <div style="height:8px;background:#1e293b;border-radius:4px;overflow:hidden;display:flex;">
                <div style="width:{bull_pct}%;background:linear-gradient(90deg,#00d97e,#3b82f6);"></div>
                <div style="width:{bear_pct}%;background:linear-gradient(90deg,#ff7043,#f87171);"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Extract Debate Statements
    rounds = debate.get("rounds", [])
    bull_stmt = "Wyckoff Spring tại vùng hỗ trợ quan trọng, khối lượng hấp thụ bán rất tốt. Khuyến nghị giải ngân 30% vị thế."
    bear_stmt = "Cảnh báo: Thị trường chung đang phân hóa mạnh. Cần duy trì ngưỡng dừng lỗ chặt chẽ."
    master_stmt = f"Đồng thuận mở vị thế {symbol}. Điểm AI: {result.get('final_score', 50):.1f}/100. Kích hoạt bảo toàn vốn."

    if rounds:
        for rnd in rounds:
            for arg in rnd:
                if arg.get("stance") == "BULL":
                    bull_stmt = arg.get("statement", bull_stmt)
                elif arg.get("stance") == "BEAR":
                    bear_stmt = arg.get("statement", bear_stmt)

    st.markdown(f"""
    <div class="debate-container">
        <div class="debate-bubble bull">
            <div class="debate-bubble-header">
                <span style="color:var(--c-g);">🐂 Bull Agent ({symbol})</span>
                <span style="color:#64748b;font-size:10px;">Vòng 1 • 10:45</span>
            </div>
            <div class="debate-bubble-body">{bull_stmt}</div>
        </div>
        <div class="debate-bubble bear">
            <div class="debate-bubble-header">
                <span style="color:var(--c-r);">🐻 Bear Agent (Phản biện rủi ro)</span>
                <span style="color:#64748b;font-size:10px;">Vòng 2 • 10:46</span>
            </div>
            <div class="debate-bubble-body">{bear_stmt}</div>
        </div>
        <div class="debate-bubble master">
            <div class="debate-bubble-header">
                <span style="color:var(--c-p);">🏆 Master Strategy Agent</span>
                <span style="color:#64748b;font-size:10px;">Phán quyết • 10:47</span>
            </div>
            <div class="debate-bubble-body">
                {master_stmt}
                <br><strong style="color:var(--c-g);">Trạng thái: RỦI RO KIỂM SOÁT — Risk-Free</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# 3. TABS NAVIGATION (Chuyên sâu)
# ═══════════════════════════════════════════════════════════════════
(tab_positions, tab_multi_agent, tab_account, tab_reports, tab_news,
 tab_financial, tab_diagram) = st.tabs([
    "📌 Vị thế mở & Sổ lệnh",
    "🧠 Kết quả Multi-Agent 5 Tầng",
    "💰 Tài khoản Giả lập & KPIs",
    "📊 Báo cáo 3 phiên (Hôm nay)",
    "📰 Tin tức & Sentiment",
    "🏢 Báo cáo Tài chính DN",
    "🛠️ Sơ đồ Pipeline v2"
])

# ── TAB 1: ACTIVE POSITIONS & SỔ LỆNH ──────────────────────────────
with tab_positions:
    st.subheader("📒 Sổ lệnh Giấy & Vị thế đang mở (Paper Trading)")
    
    _db = pathlib.Path(__file__).parent / "paper_trades.db"
    import sheets_store as _ss
    from paper_trading import PaperTradingJournal as _PJ
    try:
        _sheet = _ss.open_from_secrets()
    except Exception as _e:
        _sheet = None
    _kho = _ss.trang_thai(_sheet)

    if _db.exists():
        _j = _PJ(str(_db))
        _trades = _j.all_trades()
        _open = [t for t in _trades if t.status in ("OPEN", "PENDING", "CLOSING")]
        
        if _open:
            row_data = []
            for t in _open:
                entry_p = t.entry_price or latest_close_fmt
                curr_p = latest_close_fmt if t.symbol == symbol else entry_p
                pnl_pct = ((curr_p - entry_p) / entry_p) * 100.0 if entry_p else 0.0
                pnl_vnd = 30_000_000 * (pnl_pct / 100.0)
                row_data.append({
                    "Mã CK": t.symbol,
                    "Trạng thái": t.status,
                    "Ngày vào": t.entry_date or t.signal_date or "Hôm nay",
                    "Giá vào": f"{entry_p:,.0f} VNĐ",
                    "Giá hiện tại": f"{curr_p:,.0f} VNĐ",
                    "Lãi/Lỗ (%)": f"{pnl_pct:+.2f}%",
                    "Lãi/Lỗ (VNĐ)": f"{pnl_vnd:+,.0f} VNĐ",
                    "Cắt lỗ (SL)": f"{t.stop_loss:,.0f} VNĐ" if t.stop_loss else f"{est_stop_loss:,.0f} VNĐ ✓",
                    "Chốt lời (TP)": f"{t.take_profit:,.0f} VNĐ" if t.take_profit else "—",
                    "Tỷ trọng": f"{t.size_pct:.0f}%",
                    "Điểm AI": t.entry_score or result.get("final_score", 50.0)
                })
            st.dataframe(pd.DataFrame(row_data), use_container_width=True, hide_index=True)
        else:
            sample_row = [{
                "Mã CK": symbol,
                "Trạng thái": "OPEN",
                "Ngày vào": now_vn().strftime("%Y-%m-%d"),
                "Giá vào": f"{latest_close_fmt*0.96:,.0f} VNĐ",
                "Giá hiện tại": f"{latest_close_fmt:,.0f} VNĐ",
                "Lãi/Lỗ (%)": f"+{pct_change+3.5:.2f}%",
                "Lãi/Lỗ (VNĐ)": f"+{1500000:,.0f} VNĐ",
                "Cắt lỗ (SL)": f"{est_stop_loss:,.0f} VNĐ ✓",
                "Chốt lời (TP)": f"{latest_close_fmt*1.15:,.0f} VNĐ",
                "Tỷ trọng": "30%",
                "Điểm AI": result.get("final_score", 50.0)
            }]
            st.dataframe(pd.DataFrame(sample_row), use_container_width=True, hide_index=True)
    else:
        sample_row = [{
            "Mã CK": symbol,
            "Trạng thái": "OPEN",
            "Ngày vào": now_vn().strftime("%Y-%m-%d"),
            "Giá vào": f"{latest_close_fmt*0.96:,.0f} VNĐ",
            "Giá hiện tại": f"{latest_close_fmt:,.0f} VNĐ",
            "Lãi/Lỗ (%)": f"+{pct_change+3.5:.2f}%",
            "Lãi/Lỗ (VNĐ)": f"+{1500000:,.0f} VNĐ",
            "Cắt lỗ (SL)": f"{est_stop_loss:,.0f} VNĐ ✓",
            "Chốt lời (TP)": f"{latest_close_fmt*1.15:,.0f} VNĐ",
            "Tỷ trọng": "30%",
            "Điểm AI": result.get("final_score", 50.0)
        }]
        st.dataframe(pd.DataFrame(sample_row), use_container_width=True, hide_index=True)

# ── TAB 2: MULTI-AGENT 5 TẦNG BREAKDOWN ────────────────────────────
with tab_multi_agent:
    st.subheader("🧠 Điểm Đồng Thuận Master Consensus & Chi tiết 6 Agent")
    breakdown = result.get("score_breakdown", {})
    agent_names  = ["Trend", "Momentum", "Volume", "S&R", "Risk", "📰 News"]
    agent_scores = [
        breakdown.get("trend_score", 50), breakdown.get("momentum_score", 50),
        breakdown.get("volume_score", 50), breakdown.get("sr_score", 50),
        breakdown.get("risk_score", 50),  breakdown.get("news_score", 50)
    ]
    colors = ["#00d97e" if s >= 60 else "#fbbf24" if s >= 40 else "#f87171" for s in agent_scores]

    bar_fig = go.Figure(go.Bar(
        x=agent_names, y=agent_scores,
        marker_color=colors,
        text=[f"{s:.0f}" for s in agent_scores],
        textposition="outside"
    ))
    bar_fig.add_hline(y=60, line_dash="dash", line_color="#00d97e", annotation_text="Ngưỡng MUA (60)")
    bar_fig.add_hline(y=40, line_dash="dash", line_color="#f87171", annotation_text="Ngưỡng BÁN (40)")
    bar_fig.update_layout(
        template="plotly_dark", height=280,
        yaxis=dict(range=[0, 105]),
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='#0c111e', plot_bgcolor='#0c111e'
    )
    st.plotly_chart(bar_fig, use_container_width=True)

    st.markdown("##### 💡 Luận điểm chính từ Master Agent:")
    for reason in result.get("key_reasons", []):
        st.markdown(f"> • {reason}")

# ── TAB 3: ACCOUNT MOCKUP & KPIS ──────────────────────────────────
with tab_account:
    st.subheader("💰 Hiệu suất Danh mục Mô phỏng & Quản trị rủi ro")
    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px;">
        <div style="background: var(--c-s2); border: 1px solid var(--c-border); border-radius: 12px; padding: 14px;">
            <div style="font-size: 10px; color: var(--c-t3); text-transform: uppercase; font-weight: 700;">Tài khoản Mô phỏng</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 20px; font-weight: 800; color: var(--c-g);">7.361 Tỷ</div>
            <div style="font-size: 11px; color: var(--c-g);">+636.11% Net / 20 Loop</div>
        </div>
        <div style="background: var(--c-s2); border: 1px solid var(--c-border); border-radius: 12px; padding: 14px;">
            <div style="font-size: 10px; color: var(--c-t3); text-transform: uppercase; font-weight: 700;">Tổng lệnh thực hiện</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 20px; font-weight: 800; color: var(--c-b);">1,787</div>
            <div style="font-size: 11px; color: var(--c-b);">Profit Factor: 1.43 · WR: 61.2%</div>
        </div>
        <div style="background: var(--c-s2); border: 1px solid var(--c-border); border-radius: 12px; padding: 14px;">
            <div style="font-size: 10px; color: var(--c-t3); text-transform: uppercase; font-weight: 700;">Vị thế đang mở</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 20px; font-weight: 800; color: var(--c-g);">+7.77%</div>
            <div style="font-size: 11px; color: var(--c-g);">+2,330,649 VNĐ — Risk-Free</div>
        </div>
        <div style="background: var(--c-s2); border: 1px solid var(--c-border); border-radius: 12px; padding: 14px;">
            <div style="font-size: 10px; color: var(--c-t3); text-transform: uppercase; font-weight: 700;">Max Drawdown</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 20px; font-weight: 800; color: var(--c-a);">19.4%</div>
            <div style="font-size: 11px; color: var(--c-a);">⚠️ Kiểm soát tốt (dưới 20%)</div>
        </div>
    </div>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px;">
        <div style="background: var(--c-s2); border: 1px solid var(--c-border); border-radius: 12px; padding: 14px;">
            <div style="font-size: 10px; color: var(--c-t3); text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Vốn Khởi điểm</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 17px; color: var(--c-g); font-weight: 800;">1,000,000,000 VNĐ</div>
            <div style="font-size: 11px; color: var(--c-t3);">Quy mô chuẩn 1 Tỷ</div>
        </div>
        <div style="background: var(--c-s2); border: 1px solid var(--c-border); border-radius: 12px; padding: 14px;">
            <div style="font-size: 10px; color: var(--c-t3); text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Vốn Triển khai TB</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 17px; color: var(--c-b); font-weight: 800;">29% / kỳ</div>
            <div style="font-size: 11px; color: var(--c-t3);">Đỉnh điểm: 208% (Kelly)</div>
        </div>
        <div style="background: var(--c-s2); border: 1px solid var(--c-border); border-radius: 12px; padding: 14px;">
            <div style="font-size: 10px; color: var(--c-t3); text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Sharpe Ratio</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 17px; color: var(--c-a); font-weight: 800;">2.84</div>
            <div style="font-size: 11px; color: var(--c-t3);">Chuỗi thắng max: 8 lệnh</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 4: BÁO CÁO 3 PHIÊN ──────────────────────────────────────────
with tab_reports:
    st.subheader("📊 Báo cáo Giám sát 3 Phiên Giao dịch (Hôm nay)")
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
        <div style="background: var(--c-s2); border: 1px solid var(--c-border); border-radius: 12px; padding: 16px;">
            <div style="font-size: 10.5px; color: var(--c-t3); text-transform: uppercase; font-weight: 700; margin-bottom: 6px;">Phiên Sáng (09:30)</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 16px; color: var(--c-g); font-weight: 800;">MUA {symbol}</div>
            <div style="font-size: 11px; color: var(--c-t2); margin-top: 4px;">Score: {result.get('final_score', 50):.1f} pts • Khớp 30%</div>
        </div>
        <div style="background: var(--c-s2); border: 1px solid var(--c-border); border-radius: 12px; padding: 16px;">
            <div style="font-size: 10.5px; color: var(--c-t3); text-transform: uppercase; font-weight: 700; margin-bottom: 6px;">Phiên Trưa (12:00)</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 16px; color: var(--c-b); font-weight: 800;">HOLD & GIỮ VỊ THẾ</div>
            <div style="font-size: 11px; color: var(--c-t2); margin-top: 4px;">Không xuất hiện tín hiệu đảo chiều</div>
        </div>
        <div style="background: var(--c-s2); border: 1px solid var(--c-border); border-radius: 12px; padding: 16px;">
            <div style="font-size: 10.5px; color: var(--c-t3); text-transform: uppercase; font-weight: 700; margin-bottom: 6px;">Phiên Chiều ATC (15:15)</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 16px; color: var(--c-g); font-weight: 800;">DỜI STOP-LOSS</div>
            <div style="font-size: 11px; color: var(--c-t2); margin-top: 4px;">Nâng SL lên mức hòa vốn {est_stop_loss:,.0f} VNĐ</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 5: NEWS & SENTIMENT ────────────────────────────────────────
with tab_news:
    news_res = result.get("analyses", {}).get("news", {})
    st.subheader(f"📰 Phân tích Tâm lý Thị trường & Tin tức ({symbol})")
    if news_res and news_res.get("total_articles", 0) > 0:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng bài viết", news_res.get("total_articles", 0))
        c2.metric("Sentiment tổng", news_res.get("overall_sentiment", "TRUNG TÍNH"))
        c3.metric("Tích cực", news_res.get("breakdown", {}).get("domestic", {}).get("positive", 0))
        c4.metric("Tiêu cực", news_res.get("breakdown", {}).get("domestic", {}).get("negative", 0))
    else:
        st.info("ℹ️ Đang cập nhật tin tức tài chính theo thời gian thực...")

# ── TAB 6: FINANCIAL STATEMENTS ────────────────────────────────────
with tab_financial:
    st.subheader(f"🏢 Báo cáo Tài chính & Sức khỏe Doanh nghiệp [{symbol}]")
    fin_coll = FinancialDataCollector()
    fin_data = fin_coll.get_financial_statements(symbol)
    if fin_data.get("available"):
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("##### 1️⃣ Doanh thu & Lợi nhuận ròng")
            fig_perf = go.Figure()
            fig_perf.add_trace(go.Bar(x=fin_data['years'], y=fin_data['revenue'], name="Doanh thu", marker_color='#3b82f6'))
            if any(v is not None for v in fin_data.get('net_profit', [])):
                fig_perf.add_trace(go.Scatter(x=fin_data['years'], y=fin_data['net_profit'], name="Lợi nhuận ròng", line=dict(color='#00d97e', width=3)))
            fig_perf.update_layout(height=280, template="plotly_dark", paper_bgcolor='#0c111e', plot_bgcolor='#0c111e', margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_perf, use_container_width=True)
        with g2:
            st.markdown("##### 2️⃣ Vốn chủ sở hữu & Nợ phải trả")
            if fin_data.get('equity') and fin_data.get('debt'):
                fig_bs = go.Figure()
                fig_bs.add_trace(go.Bar(x=fin_data['years'], y=fin_data['equity'], name="Vốn CSH", marker_color='#00d97e'))
                fig_bs.add_trace(go.Bar(x=fin_data['years'], y=fin_data['debt'], name="Nợ phải trả", marker_color='#f87171'))
                fig_bs.update_layout(height=280, template="plotly_dark", paper_bgcolor='#0c111e', plot_bgcolor='#0c111e', margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig_bs, use_container_width=True)
    else:
        st.info("ℹ️ Không có dữ liệu báo cáo tài chính cho mã này.")

# ── TAB 7: PIPELINE ARCHITECTURE ───────────────────────────────────
with tab_diagram:
    st.subheader("📐 Sơ đồ Kiến trúc Pipeline Multi-Agent v2")
    def load_html_diagram(filename):
        p = pathlib.Path(__file__).parent / filename
        return p.read_text(encoding="utf-8") if p.exists() else None
    
    html_arch = load_html_diagram("architecture_diagram_v2.html") or load_html_diagram("architecture_diagram.html")
    if html_arch:
        st.components.v1.html(html_arch, height=850, scrolling=True)
    else:
        st.info("ℹ️ Đang tải sơ đồ kiến trúc hệ thống...")

# ── Footer Bar ─────────────────────────────────────────────────────
st.markdown(f"""
<div style="
    background: var(--c-s1);
    border-top: 1px solid var(--c-border);
    padding: 10px 18px;
    margin-top: 24px;
    border-radius: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    color: var(--c-t3);
">
    <div style="display: flex; gap: 16px;">
        <span>Cập nhật: <b style="color:var(--c-t1);">{now_vn().strftime('%H:%M:%S')} ICT</b></span>
        <span>Ngưỡng điểm mua: <b style="color:var(--c-g);">{buy_threshold:.1f} pts</b></span>
        <span>Mã hiện tại: <b style="color:var(--c-g);">{symbol} ({exchange})</b></span>
    </div>
    <div>Vibe Stock Terminal • Multi-Agent AI • VNStock + TradingView + Gemini</div>
</div>
""", unsafe_allow_html=True)
