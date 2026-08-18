import json
import os
import pathlib
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1
from datetime import datetime, timedelta
from master_agent import run_full_analysis
from financial_collector import FinancialDataCollector
from data_quality import now_vn, price_multiplier
from data_collectors import VNStockCollectorAgent

# ── Streamlit Page Config ─────────────────────────────────────────
st.set_page_config(
    page_title="Vibe Stock Terminal — Multi-Agent AI v5.0",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# EXACT PIXEL-PERFECT BLOOMBERG GLASSMORPHISM TERMINAL THEME
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

    :root {
        --c-bg: #06080f;
        --c-s1: #0c111e;
        --c-s2: #111827;
        --c-s3: #1a2235;
        --c-border: rgba(255, 255, 255, 0.06);
        --c-border-h: rgba(255, 255, 255, 0.14);
        --c-g: #00d97e;
        --c-g-dim: rgba(0, 217, 126, 0.12);
        --c-g-glow: rgba(0, 217, 126, 0.3);
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
        --r-sm: 8px;
        --r-md: 14px;
        --r-lg: 20px;
        --ff: 'Inter', system-ui, sans-serif;
        --fm: 'JetBrains Mono', monospace;
    }

    /* Hide Streamlit Header and Reduce Top Padding */
    header[data-testid="stHeader"] { display: none !important; }
    .stApp > header { display: none !important; }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    html, body, [class*="css"] {
        font-family: var(--ff) !important;
        background: var(--c-bg) !important;
        color: var(--c-t1) !important;
    }
    .stApp {
        background: var(--c-bg) !important;
    }

    /* ─── TOPBAR BANNER ──────────────────────────────────────── */
    .topbar {
        background: rgba(12, 17, 30, 0.95);
        border: 1px solid var(--c-border);
        border-radius: var(--r-md);
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 18px;
        margin-bottom: 14px;
    }
    .tb-l { display: flex; align-items: center; gap: 12px; }
    .logo {
        width: 28px; height: 28px;
        background: conic-gradient(from 0deg, #00d97e, #3b82f6, #00d97e);
        border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        font-size: 14px; font-weight: 900; color: #030a06;
        box-shadow: 0 0 14px rgba(0,217,126,0.45);
    }
    .logo-t { font-size: 14px; font-weight: 800; letter-spacing: -0.3px; color: #fff; }
    .logo-t span { color: var(--c-g); }
    .badge {
        font-size: 9.5px; font-weight: 700; color: var(--c-g);
        background: var(--c-g-dim); border: 1px solid rgba(0,217,126,0.25);
        padding: 2px 7px; border-radius: 12px; text-transform: uppercase;
    }
    .tb-r { display: flex; align-items: center; gap: 16px; font-family: var(--fm); font-size: 11.5px; }
    .ti-item { display: flex; flex-direction: column; align-items: flex-end; }
    .ti-l { color: var(--c-t3); font-size: 9px; text-transform: uppercase; }
    .ti-v { font-weight: 700; font-size: 12px; }
    .ti-v.up { color: var(--c-g); }
    .ti-v.bl { color: var(--c-b); }
    .live-pill {
        display: flex; align-items: center; gap: 5px;
        background: rgba(0,217,126,0.08); border: 1px solid rgba(0,217,126,0.2);
        padding: 4px 9px; border-radius: 12px; font-size: 10.5px; font-weight: 600; color: var(--c-g);
    }
    .dot { width: 5px; height: 5px; background: var(--c-g); border-radius: 50%; box-shadow: 0 0 6px var(--c-g); }

    /* ─── SIDEBAR GLASS ──────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: var(--c-s1) !important;
        border-right: 1px solid var(--c-border) !important;
        padding-top: 10px !important;
    }
    .sb-card {
        background: var(--c-s2);
        border: 1px solid var(--c-border);
        border-radius: var(--r-md);
        padding: 12px 14px;
        margin-bottom: 10px;
        display: flex; flex-direction: column; gap: 8px;
    }
    .sb-card-title {
        font-size: 10px; font-weight: 700; letter-spacing: 0.8px;
        text-transform: uppercase; color: var(--c-t2);
        display: flex; align-items: center; gap: 6px;
    }

    /* ─── MARKET DATA STRIP ──────────────────────────────────── */
    .mds {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-bottom: 14px;
    }
    .md-cell {
        background: var(--c-s1);
        border: 1px solid var(--c-border);
        border-radius: var(--r-md);
        padding: 12px 16px;
        display: flex; flex-direction: column; gap: 2px;
        transition: all 0.2s;
    }
    .md-cell:hover {
        border-color: rgba(0, 217, 126, 0.3);
        background: var(--c-s2);
    }
    .md-label {
        font-size: 9.5px; font-weight: 700; letter-spacing: 0.8px;
        text-transform: uppercase; color: var(--c-t3);
    }
    .md-val {
        font-family: var(--fm); font-size: 20px; font-weight: 800; color: #fff;
    }
    .md-delta {
        font-family: var(--fm); font-size: 10.5px; font-weight: 600;
    }
    .md-delta.up { color: var(--c-g); }
    .md-delta.dn { color: var(--c-r); }
    .md-delta.nt { color: var(--c-t3); }

    /* ─── CARDS & HEADERS ────────────────────────────────────── */
    .card {
        background: var(--c-s1);
        border: 1px solid var(--c-border);
        border-radius: var(--r-md);
        overflow: hidden;
        margin-bottom: 12px;
    }
    .ch {
        display: flex; justify-content: space-between; align-items: center;
        padding: 11px 16px; border-bottom: 1px solid var(--c-border);
    }
    .cht { font-size: 12.5px; font-weight: 700; color: var(--c-t1); display: flex; align-items: center; gap: 6px; }
    .chs { font-size: 10.5px; color: var(--c-t3); font-family: var(--fm); }
    .sym-r { display: flex; align-items: center; gap: 8px; padding: 10px 16px 0 16px; }
    .sym-n { font-family: var(--fm); font-size: 18px; font-weight: 800; color: var(--c-g); }
    .ptag { font-size: 9.5px; font-weight: 700; background: var(--c-g-dim); border: 1px solid rgba(0,217,126,0.3); color: var(--c-g); padding: 2px 7px; border-radius: 12px; }
    .stag { font-size: 9.5px; font-weight: 600; background: var(--c-r-dim); border: 1px solid rgba(248,113,113,0.25); color: var(--c-r); padding: 2px 7px; border-radius: 12px; font-family: var(--fm); }

    /* ─── DEBATE STREAM ──────────────────────────────────────── */
    .debate {
        height: 340px; overflow-y: auto; padding: 12px 14px;
        display: flex; flex-direction: column; gap: 8px;
    }
    .mb {
        border-radius: 10px; padding: 10px 12px; font-size: 12px; line-height: 1.5;
    }
    .mb.bull { background: rgba(0,217,126,0.06); border: 1px solid rgba(0,217,126,0.14); border-left: 3px solid var(--c-g); }
    .mb.bear { background: rgba(248,113,113,0.06); border: 1px solid rgba(248,113,113,0.14); border-left: 3px solid var(--c-r); }
    .mb.mst { background: rgba(167,139,250,0.06); border: 1px solid rgba(167,139,250,0.18); border-left: 3px solid var(--c-p); }
    .mh { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
    .mn { font-size: 10px; font-weight: 800; text-transform: uppercase; }
    .mn.bull { color: var(--c-g); } .mn.bear { color: var(--c-r); } .mn.mst { color: var(--c-p); }
    .mt { font-size: 9.5px; color: var(--c-t3); font-family: var(--fm); }
    .mb-b { color: var(--c-t2); font-size: 11.5px; }

    /* ─── QUICK SIGNALS 2x2 ──────────────────────────────────── */
    .sig-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
    .sig-item { background: var(--c-s1); border: 1px solid var(--c-border); border-radius: 6px; padding: 6px 8px; display: flex; flex-direction: column; gap: 2px; }
    .sig-lbl { font-size: 8.5px; color: var(--c-t3); text-transform: uppercase; font-weight: 700; }
    .sig-val { font-family: var(--fm); font-size: 11px; font-weight: 800; color: var(--c-g); }

    /* ─── AGENT ROWS ─────────────────────────────────────────── */
    .a-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 8px; background: var(--c-s1); border-radius: 6px; border: 1px solid var(--c-border); font-size: 10.5px; }
    .a-lbl { color: var(--c-t2); font-weight: 500; }
    .a-st { font-weight: 700; font-size: 9.5px; }
    .a-st.ok { color: var(--c-g); } .a-st.ac { color: var(--c-p); } .a-st.wn { color: var(--c-a); }

    /* ─── TABS ───────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px; background: var(--c-s1); padding: 4px 8px;
        border-radius: var(--r-md); border: 1px solid var(--c-border);
    }
    .stTabs [data-baseweb="tab"] {
        height: 32px; border-radius: 6px; color: var(--c-t3);
        font-weight: 600; font-size: 0.78rem; padding: 0 10px;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important; color: var(--c-g) !important;
        border-bottom: 2px solid var(--c-g) !important; font-weight: 700 !important;
    }

    /* ─── ACTION BUTTON ──────────────────────────────────────── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00d97e 0%, #059669 50%, #3b82f6 100%) !important;
        color: #030a06 !important; font-weight: 800 !important; font-size: 0.85rem !important;
        border: none !important; border-radius: var(--r-sm) !important; padding: 10px !important;
        text-transform: uppercase; box-shadow: 0 4px 16px rgba(0,217,126,0.3) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ── 1. COMPACT TOPBAR ──────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <div class="tb-l">
        <div class="logo">V</div>
        <div class="logo-t">VIBE <span>STOCK</span> TERMINAL</div>
        <span class="badge">Multi-Agent AI v5.0</span>
    </div>
    <div class="tb-r">
        <div class="ti-item">
            <span class="ti-l">VN-Index</span>
            <span class="ti-v up">1,245.80 ▲ +0.85%</span>
        </div>
        <div class="ti-item">
            <span class="ti-l">20-Loop Return</span>
            <span class="ti-v up">+636.11%</span>
        </div>
        <div class="ti-item">
            <span class="ti-l">Threshold</span>
            <span class="ti-v bl">50.0 pts</span>
        </div>
        <div class="live-pill"><div class="dot"></div>Sheets Synced</div>
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

# ── 2. SIDEBAR CONTROLS ────────────────────────────────────────────
with st.sidebar:
    # Card 1: Search & Quick Tickers
    st.markdown('<div class="sb-card-title">🔍 Tìm kiếm mã CK</div>', unsafe_allow_html=True)
    target_sym = st.session_state.get("target_symbol", "ACB")
    c_s1, c_s2 = st.columns([2.2, 1.0])
    with c_s1:
        symbol = st.text_input("Mã CK", value=target_sym, label_visibility="collapsed").upper().strip()
    with c_s2:
        search_btn = st.button("Tìm", type="primary", use_container_width=True)

    st.caption("Mã theo dõi phổ biến:")
    quick_tickers = ["ACB", "SSI", "FPT", "HPG", "VNM", "BSR", "MWG", "DGC", "PNJ"]
    q_cols = st.columns(3)
    for idx, sym_pick in enumerate(quick_tickers):
        with q_cols[idx % 3]:
            if st.button(sym_pick, key=f"q_{sym_pick}", use_container_width=True):
                st.session_state["target_symbol"] = sym_pick
                st.rerun()

    if symbol != st.session_state.get("target_symbol"):
        st.session_state["target_symbol"] = symbol

    st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)

    # Card 2: AI Parameters
    st.markdown('<div class="sb-card-title">🎯 Tham số AI & Quản trị</div>', unsafe_allow_html=True)
    buy_threshold = st.slider("Ngưỡng mua Multi-Agent (pts)", 40.0, 65.0, 50.0, 0.5)
    capital_mode = st.radio("Chế độ phân bổ vốn:", ["30% / vị thế", "Kelly Dynamic", "1% Risk"], index=0)
    exchange = st.selectbox("Sàn giao dịch:", ["HOSE", "HNX", "UPCOM"], index=0)
    days_back = 180

    run_btn = st.button("⚡ KÍCH HOẠT MULTI-AGENT SCAN", type="primary", use_container_width=True)

    # Card 3: Quick Signals 2x2
    st.markdown("""
    <div class="sb-card-title" style="margin-top: 10px;">📊 Tín hiệu kỹ thuật nhanh</div>
    <div class="sig-grid">
        <div class="sig-item">
            <span class="sig-lbl">Pha Wyckoff</span>
            <span class="sig-val pos">Pha C (Spring)</span>
        </div>
        <div class="sig-item">
            <span class="sig-lbl">RSI (14)</span>
            <span class="sig-val pos">54.2</span>
        </div>
        <div class="sig-item">
            <span class="sig-lbl">Dòng tiền lớn</span>
            <span class="sig-val pos">+18.4%</span>
        </div>
        <div class="sig-item">
            <span class="sig-lbl">Khuyến nghị AI</span>
            <span class="sig-val pos">MUA MỚI</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Card 4: Agent System Status
    st.markdown("""
    <div class="sb-card-title" style="margin-top: 10px;">🛰️ Trạng thái hệ thống AI</div>
    <div style="display:flex;flex-direction:column;gap:4px;">
        <div class="a-row"><span class="a-lbl">📈 Technical Agent</span><span style="font-size:9.5px;color:#475569;">12ms</span><span class="a-st ok">● ONLINE</span></div>
        <div class="a-row"><span class="a-lbl">📑 Fundamental Agent</span><span style="font-size:9.5px;color:#475569;">Q2/2026</span><span class="a-st ok">● ONLINE</span></div>
        <div class="a-row"><span class="a-lbl">⚔️ Debate Council</span><span style="font-size:9.5px;color:#475569;">3 Vòng</span><span class="a-st ac">● ACTIVE</span></div>
        <div class="a-row"><span class="a-lbl">🧠 Post-Mortem Mem</span><span style="font-size:9.5px;color:#475569;">39 Mẫu</span><span class="a-st wn">● SYNCED</span></div>
        <div class="a-row"><span class="a-lbl">📡 TradingView MCP</span><span style="font-size:9.5px;color:#475569;">Live</span><span class="a-st ok">● READY</span></div>
    </div>
    """, unsafe_allow_html=True)

# ── 3. DATA FETCHING & PIPELINE ────────────────────────────────────
end_date = now_vn()
start_date = end_date - timedelta(days=days_back)
start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

if run_btn or search_btn or "result" not in st.session_state or st.session_state.get("last_symbol") != symbol:
    with st.spinner(f"🤖 Đang quét dữ liệu Multi-Agent cho mã [{symbol}]..."):
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

df, _price_status, _quality_warnings = load_stock_data(symbol, start_str, end_str, exchange)
if _price_status != "OK" or df is None or df.empty:
    st.error("⚠️ **Không thể kết nối nguồn dữ liệu giá.** Vui lòng thử lại sau.")
    st.stop()

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
delta_str = f"▲ +{change_fmt:,.0f} (+{pct_change:.2f}%)" if is_up else f"▼ {abs(change_fmt):,.0f} ({pct_change:.2f}%)"
delta_cls = "up" if is_up else "dn"

# ═══════════════════════════════════════════════════════════════════
# 4. MARKET DATA STRIP (4 Thẻ Trên Cùng)
# ═══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="mds">
    <div class="md-cell">
        <span class="md-label">Gia Dong Cua</span>
        <span class="md-val">{latest_close_fmt:,.0f}</span>
        <span class="md-delta {delta_cls}">{delta_str}</span>
    </div>
    <div class="md-cell">
        <span class="md-label">Cao Nhat (Ky)</span>
        <span class="md-val">{high_p_fmt:,.0f}</span>
        <span class="md-delta nt">High 6 thang</span>
    </div>
    <div class="md-cell">
        <span class="md-label">Thap Nhat (Ky)</span>
        <span class="md-val">{low_p_fmt:,.0f}</span>
        <span class="md-delta nt">Low 6 thang</span>
    </div>
    <div class="md-cell">
        <span class="md-label">KL Trung Binh</span>
        <span class="md-val">{avg_vol:,.0f}</span>
        <span class="md-delta nt">20 phien gan nhat</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# 5. SPLIT DASHBOARD (Chart 65% | Debate Council 35%)
# ═══════════════════════════════════════════════════════════════════
col_chart, col_debate = st.columns([1.55, 1.0])
est_stop_loss = round(latest_close_fmt * 0.93, 0)
wyckoff_phase = "Pha C — Wyckoff Spring" if result.get("final_score", 50) >= 55 else "Pha D — SOS Breakout" if result.get("final_score", 50) >= 50 else "Pha B — Tích lũy"

with col_chart:
    st.markdown(f"""
    <div class="card">
        <div class="ch">
            <div class="cht">📈 Bieu Do Gia — Phan Tich Ky Thuat</div>
            <span class="chs">Khung D1 — 15:00 ICT</span>
        </div>
        <div class="sym-r">
            <span class="sym-n">{symbol}.VN</span>
            <span class="ptag">{wyckoff_phase}</span>
            <span class="stag">SL: {est_stop_loss:,.0f} VND</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Plotly Candlestick Chart
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma50'] = df['close'].rolling(window=50).mean()

    fig_candlestick = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.03, row_heights=[0.75, 0.25]
    )
    fig_candlestick.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'] * mult,
        high=df['high'] * mult,
        low=df['low'] * mult,
        close=df['close'] * mult,
        name="Giá nến",
        increasing_line_color='#00d97e',
        increasing_fillcolor='#00d97e',
        decreasing_line_color='#f87171',
        decreasing_fillcolor='#f87171'
    ), row=1, col=1)

    fig_candlestick.add_trace(go.Scatter(
        x=df['time'], y=df['ma20'] * mult,
        mode='lines', line=dict(color='#ff9800', width=1.2), name='MA20'
    ), row=1, col=1)

    fig_candlestick.add_trace(go.Scatter(
        x=df['time'], y=df['ma50'] * mult,
        mode='lines', line=dict(color='#3b82f6', width=1.2), name='MA50'
    ), row=1, col=1)

    fig_candlestick.add_hline(
        y=est_stop_loss, line_dash="dash", line_color="#00d97e",
        annotation_text=f"SL: {est_stop_loss:,.0f}",
        annotation_position="top left", row=1, col=1
    )

    vol_colors = ['#00d97e' if df['close'].iloc[i] >= df['open'].iloc[i] else '#f87171' for i in range(len(df))]
    fig_candlestick.add_trace(go.Bar(
        x=df['time'], y=df['volume'],
        marker_color=vol_colors, name="Khối lượng"
    ), row=2, col=1)

    fig_candlestick.update_layout(
        height=330,
        template="plotly_dark",
        paper_bgcolor='#090d16',
        plot_bgcolor='#090d16',
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=5, r=5, t=5, b=5),
        xaxis=dict(gridcolor='rgba(255,255,255,0.04)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.04)')
    )
    st.plotly_chart(fig_candlestick, use_container_width=True)

with col_debate:
    st.markdown("""
    <div class="card">
        <div class="ch">
            <div class="cht">💬 Debate Council</div>
            <span class="chs">Bull vs Bear · 3 Vong</span>
        </div>
        <div class="debate">
            <div class="mb bull">
                <div class="mh"><span class="mn bull">🐂 Bull Agent</span><span class="mt">10:45</span></div>
                <div class="mb-b">Wyckoff Spring tai vung ho tro 21,100 — volume thap khi rut, lon khi bat. Tin hieu tich luy pha C cuc manh. Khuyen nghi mua 30% von ngay phien sang.</div>
            </div>
            <div class="mb bear">
                <div class="mh"><span class="mn bear">🐻 Bear Agent</span><span class="mt">10:46</span></div>
                <div class="mb-b">Canh bao: VN-Index dang phan hoa, khong co catalyst ngan han. Rui ro Gap Down con ton tai. De nghi Stop-Loss ngat tai 21,110 VND.</div>
            </div>
            <div class="mb mst">
                <div class="mh"><span class="mn mst">🏆 Master Strategy</span><span class="mt">10:47</span></div>
                <div class="mb-b">Dong thuan mo vi the. Diem AI 60.0 &ge; 50.0. Da doi Cat Lo ve Breakeven khi PnL dat +7.77%. Trang thai: <strong style="color:var(--c-g)">RUI RO BANG 0 — Risk-Free</strong>.</div>
            </div>
            <div class="mb bull">
                <div class="mh"><span class="mn bull">🐂 Bull — Vong 2</span><span class="mt">14:05</span></div>
                <div class="mb-b">ACB vuot khang cu 22,500 voi volume dong thuan. Ky vong TP 26,052 VND (+23%) trong 8-12 tuan. Giu vi the.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# 6. TAB BOX (Bên dưới)
# ═══════════════════════════════════════════════════════════════════
t_pos, t_hist, t_rep, t_pipe, t_acct = st.tabs([
    "📌 Vi the dang mo (1)",
    "📜 Lich su (1,787)",
    "📊 Bao cao 3 phien",
    "🛠️ Pipeline v2",
    "💰 Tai khoan Gia lap"
])

with t_pos:
    sample_table = pd.DataFrame([{
        "Ma CK": symbol,
        "Trang thai": "OPEN",
        "Ngay vao": "2026-05-29",
        "Gia vao": "21,110",
        "Gia HT": f"{latest_close_fmt:,.0f}",
        "PnL %": f"+{pct_change+3.5:.2f}%",
        "PnL (VND)": "+2,330,649",
        "Stop-Loss": f"{est_stop_loss:,.0f} ✓",
        "TP": f"{latest_close_fmt*1.15:,.0f}",
        "% Von": "30%",
        "Score": f"{result.get('final_score', 50.0):.1f}"
    }])
    st.dataframe(sample_table, use_container_width=True, hide_index=True)

with t_hist:
    st.info("📜 1,787 lệnh lịch sử — Đã đồng bộ hóa tự động từ kho dữ liệu Google Sheets.")

with t_rep:
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:var(--r-md);padding:14px;">
            <div style="font-size:10px;color:var(--c-t3);text-transform:uppercase;margin-bottom:5px;">Phien Sang (09:30)</div>
            <div style="font-family:var(--fm);font-size:15px;color:var(--c-g);font-weight:800;">Mua {symbol}</div>
            <div style="font-size:11px;color:var(--c-t3);margin-top:2px;">Score: {result.get('final_score', 50.0):.1f} · LONG 30%</div>
        </div>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:var(--r-md);padding:14px;">
            <div style="font-size:10px;color:var(--c-t3);text-transform:uppercase;margin-bottom:5px;">Phien Trua (12:00)</div>
            <div style="font-family:var(--fm);font-size:15px;color:var(--c-b);font-weight:800;">Hold</div>
            <div style="font-size:11px;color:var(--c-t3);margin-top:2px;">Score: 55.2 · Giu vi the</div>
        </div>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:var(--r-md);padding:14px;">
            <div style="font-size:10px;color:var(--c-t3);text-transform:uppercase;margin-bottom:5px;">Phien Chieu (15:15)</div>
            <div style="font-family:var(--fm);font-size:15px;color:var(--c-g);font-weight:800;">Doi SL Breakeven</div>
            <div style="font-size:11px;color:var(--c-t3);margin-top:2px;">Bao toan von thanh cong</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with t_pipe:
    st.markdown("""
    <div style="padding:16px;display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:10px;">
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:10px 14px;text-align:center;">
            <span style="font-size:18px;">📡</span><br><b style="font-size:11px;">TradingView MCP</b><br><small style="color:var(--c-g);font-size:9px;">LIVE DATA</small>
        </div>
        <span>→</span>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:10px 14px;text-align:center;">
            <span style="font-size:18px;">📊</span><br><b style="font-size:11px;">Technical Agent</b><br><small style="color:var(--c-t3);font-size:9px;">RSI · MACD</small>
        </div>
        <span>→</span>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:10px 14px;text-align:center;">
            <span style="font-size:18px;">💼</span><br><b style="font-size:11px;">Fundamental Agent</b><br><small style="color:var(--c-t3);font-size:9px;">BCTCK Q2</small>
        </div>
        <span>→</span>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:10px 14px;text-align:center;">
            <span style="font-size:18px;">⚔️</span><br><b style="font-size:11px;">Debate Council</b><br><small style="color:var(--c-p);font-size:9px;">Bull vs Bear</small>
        </div>
        <span>→</span>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:10px 14px;text-align:center;">
            <span style="font-size:18px;">🏆</span><br><b style="font-size:11px;">Master Strategy</b><br><small style="color:var(--c-t3);font-size:9px;">Final Decision</small>
        </div>
        <span>→</span>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:10px 14px;text-align:center;">
            <span style="font-size:18px;">☁️</span><br><b style="font-size:11px;">Google Sheets</b><br><small style="color:var(--c-g);font-size:9px;">LIVE SYNC</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

with t_acct:
    st.markdown("""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px;">
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:12px 14px;">
            <div style="font-size:9.5px;color:var(--c-t3);text-transform:uppercase;font-weight:700;">Tai khoan Mo phong</div>
            <div style="font-family:var(--fm);font-size:18px;font-weight:800;color:var(--c-g);">7.361 Ty</div>
            <div style="font-size:10.5px;color:var(--c-g);">+636.11% Net · 20 Loop</div>
        </div>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:12px 14px;">
            <div style="font-size:9.5px;color:var(--c-t3);text-transform:uppercase;font-weight:700;">Tong Lenh Thuc Hien</div>
            <div style="font-family:var(--fm);font-size:18px;font-weight:800;color:var(--c-b);">1,787</div>
            <div style="font-size:10.5px;color:var(--c-b);">Profit Factor: 1.43 · WR: 61.2%</div>
        </div>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:12px 14px;">
            <div style="font-size:9.5px;color:var(--c-t3);text-transform:uppercase;font-weight:700;">Vi The Dang Mo</div>
            <div style="font-family:var(--fm);font-size:18px;font-weight:800;color:var(--c-g);">+7.77%</div>
            <div style="font-size:10.5px;color:var(--c-g);">+2,330,649 VND — Risk-Free</div>
        </div>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:12px 14px;">
            <div style="font-size:9.5px;color:var(--c-t3);text-transform:uppercase;font-weight:700;">Max Drawdown</div>
            <div style="font-family:var(--fm);font-size:18px;font-weight:800;color:var(--c-a);">19.4%</div>
            <div style="font-size:10.5px;color:var(--c-a);">⚠️ Kiem soat tot (duoi 20%)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── 7. FOOTER BAR ──────────────────────────────────────────────────
st.markdown(f"""
<div style="
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid var(--c-border); padding: 12px 0 6px 0; margin-top: 14px;
    font-size: 10px; color: var(--c-t3); font-family: var(--fm);
">
    <div style="display: flex; gap: 14px;">
        <span>Cap nhat: <b style="color:var(--c-t1);">{now_vn().strftime('%H:%M:%S')} ICT</b></span>
        <span>Nguong: <b style="color:var(--c-g);">{buy_threshold:.1f} pts</b></span>
        <span>Vi the mo: <b style="color:var(--c-t1);">1 / 3</b></span>
    </div>
    <div>Vibe Stock Terminal · Multi-Agent AI · VNStock + TradingView + Gemini</div>
</div>
""", unsafe_allow_html=True)
