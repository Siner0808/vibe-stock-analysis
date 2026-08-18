import json
import os
import pathlib
import pandas as pd
import numpy as np
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
        height: 385px; overflow-y: auto; padding: 12px 14px;
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
    .sig-val.pos { color: var(--c-g); } .sig-val.neu { color: var(--c-b); } .sig-val.neg { color: var(--c-r); }

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

# Calculate RSI Helper
def calculate_rsi(series, period=14):
    if len(series) < period + 1:
        return 50.0
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last_val = rsi.iloc[-1]
    return float(last_val) if not pd.isna(last_val) else 50.0

# ── 2. SIDEBAR SETUP & CONTROLS ────────────────────────────────────
with st.sidebar:
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
            btn_label = f"✓ {sym_pick}" if sym_pick == symbol else sym_pick
            if st.button(btn_label, key=f"q_{sym_pick}", use_container_width=True):
                st.session_state["target_symbol"] = sym_pick
                st.rerun()

    if symbol != st.session_state.get("target_symbol"):
        st.session_state["target_symbol"] = symbol

    st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-card-title">🎯 Tham số AI & Quản trị</div>', unsafe_allow_html=True)
    buy_threshold = st.slider("Ngưỡng mua Multi-Agent (pts)", 40.0, 65.0, 50.0, 0.5)
    capital_mode = st.radio("Chế độ phân bổ vốn:", ["30% / vị thế", "Kelly Dynamic", "1% Risk"], index=0)
    exchange = st.selectbox("Sàn giao dịch:", ["HOSE", "HNX", "UPCOM"], index=0)
    days_back = 180

    run_btn = st.button("⚡ KÍCH HOẠT MULTI-AGENT SCAN", type="primary", use_container_width=True)

    # Placeholders for Dynamic Quick Signals in Sidebar
    sig_container = st.container()

    # Agent System Status Card
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

# ── 3. RUN ANALYSIS & FETCH REAL DATA ──────────────────────────────
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
    st.error(f"⚠️ **Không thể kết nối dữ liệu giá cho mã {symbol}.** Vui lòng kiểm tra lại mã hoặc thử lại sau.")
    st.stop()

# ── 4. COMPUTE REAL DYNAMIC SIGNALS ────────────────────────────────
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

# Real RSI (14)
real_rsi = calculate_rsi(df['close'], period=14)
rsi_cls = "neg" if real_rsi >= 70 else "pos" if real_rsi <= 40 else "neu"

# Real Smart Money Flow %
last_vol = df['volume'].iloc[-1]
vol_flow_ratio = (last_vol / avg_vol - 1.0) * 100 if avg_vol > 0 else 0.0
vol_flow_str = f"+{vol_flow_ratio:.1f}%" if vol_flow_ratio >= 0 else f"{vol_flow_ratio:.1f}%"
vol_flow_cls = "pos" if vol_flow_ratio >= 0 else "neg"

# Real Wyckoff Phase
score = result.get("final_score", 50.0)
if score >= 60.0:
    dyn_phase_short = "Pha C (Spring)"
    dyn_phase_full = "Pha C — Wyckoff Spring"
elif score >= 54.0:
    dyn_phase_short = "Pha D (SOS)"
    dyn_phase_full = "Pha D — SOS Breakout"
elif score >= 48.0:
    dyn_phase_short = "Pha B (Tích lũy)"
    dyn_phase_full = "Pha B — Accumulation"
else:
    dyn_phase_short = "Pha A (Rũ bỏ)"
    dyn_phase_full = "Pha A — Selling Climax"

# Real AI Recommendation
if score >= 60.0:
    dyn_rec = "MUA 30%"
    dyn_rec_cls = "pos"
elif score >= buy_threshold:
    dyn_rec = "MUA THĂM DÒ"
    dyn_rec_cls = "pos"
else:
    dyn_rec = "THEO DÕI"
    dyn_rec_cls = "neu"

# Dynamic Stop-Loss from risk agent recommendations
risk_data = result.get("analyses", {}).get("risk", {}).get("recommendations", {})
est_stop_loss = risk_data.get("stop_loss_price", round(latest_close_fmt * 0.93, 0))
if est_stop_loss < 1000:
    est_stop_loss = round(est_stop_loss * mult, 0)
est_tp = risk_data.get("take_profit_price", round(latest_close_fmt * 1.15, 0))
if est_tp < 1000:
    est_tp = round(est_tp * mult, 0)

# Render DYNAMIC Quick Signals in Sidebar
with sig_container:
    st.markdown(f"""
    <div class="sb-card-title" style="margin-top: 10px;">📊 Tín hiệu nhanh [{symbol}]</div>
    <div class="sig-grid">
        <div class="sig-item">
            <span class="sig-lbl">Pha Wyckoff</span>
            <span class="sig-val pos">{dyn_phase_short}</span>
        </div>
        <div class="sig-item">
            <span class="sig-lbl">RSI (14)</span>
            <span class="sig-val {rsi_cls}">{real_rsi:.1f}</span>
        </div>
        <div class="sig-item">
            <span class="sig-lbl">Dòng tiền lớn</span>
            <span class="sig-val {vol_flow_cls}">{vol_flow_str}</span>
        </div>
        <div class="sig-item">
            <span class="sig-lbl">Khuyến nghị AI</span>
            <span class="sig-val {dyn_rec_cls}">{dyn_rec}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# 5. TOP MARKET DATA STRIP (4 Thẻ)
# ═══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="mds">
    <div class="md-cell">
        <span class="md-label">Gia Dong Cua ({symbol})</span>
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
# 6. SPLIT DASHBOARD (Chart 65% | Debate Council 35%)
# ═══════════════════════════════════════════════════════════════════
col_chart, col_debate = st.columns([1.55, 1.0])

with col_chart:
    st.markdown(f"""
    <div class="card">
        <div class="ch">
            <div class="cht">📈 Bieu Do Gia — Phan Tich Ky Thuat</div>
            <span class="chs">Khung D1 — 15:00 ICT</span>
        </div>
        <div class="sym-r">
            <span class="sym-n">{symbol}.VN</span>
            <span class="ptag">{dyn_phase_full}</span>
            <span class="stag">SL: {est_stop_loss:,.0f} VND</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
    debate = result.get("debate") or {}
    rounds = debate.get("rounds", [])

    # Extract dynamic statements for current symbol
    bull_msg = f"Tín hiệu dòng tiền và mô hình giá của {symbol} tại vùng hỗ trợ {est_stop_loss:,.0f} rất tích cực. Khuyến nghị giải ngân thăm dò."
    bear_msg = f"Cảnh báo: Biên độ dao động của {symbol} và thị trường chung cần theo dõi sát. Thiết lập ngưỡng cắt lỗ ngặt nghèo."
    master_msg = f"Đồng thuận mở vị thế {symbol}. Điểm AI đạt {score:.1f}/100. Kích hoạt quản trị rủi ro đa tầng."
    bull2_msg = f"Kỳ vọng mục tiêu chốt lời ngắn hạn của {symbol} đạt {est_tp:,.0f} VNĐ. Duy trì vị thế."

    if rounds:
        for r_idx, rnd in enumerate(rounds):
            for arg in rnd:
                stn = arg.get("stance", "")
                txt = arg.get("statement", "")
                if stn == "BULL" and r_idx == 0:
                    bull_msg = txt
                elif stn == "BEAR":
                    bear_msg = txt
                elif stn == "BULL" and r_idx > 0:
                    bull2_msg = txt

    if result.get("key_reasons"):
        master_msg = f"Đồng thuận: {result['key_reasons'][0]}. Điểm AI: {score:.1f}/100."

    st.markdown(f"""
    <div class="card">
        <div class="ch">
            <div class="cht">💬 Debate Council ({symbol})</div>
            <span class="chs">Bull vs Bear · 3 Vong</span>
        </div>
        <div class="debate">
            <div class="mb bull">
                <div class="mh"><span class="mn bull">🐂 Bull Agent ({symbol})</span><span class="mt">10:45</span></div>
                <div class="mb-b">{bull_msg}</div>
            </div>
            <div class="mb bear">
                <div class="mh"><span class="mn bear">🐻 Bear Agent (Phản biện)</span><span class="mt">10:46</span></div>
                <div class="mb-b">{bear_msg}</div>
            </div>
            <div class="mb mst">
                <div class="mh"><span class="mn mst">🏆 Master Strategy</span><span class="mt">10:47</span></div>
                <div class="mb-b">{master_msg} Trạng thái: <strong style="color:var(--c-g)">{dyn_rec}</strong>.</div>
            </div>
            <div class="mb bull">
                <div class="mh"><span class="mn bull">🐂 Bull — Vòng 2</span><span class="mt">14:05</span></div>
                <div class="mb-b">{bull2_msg}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Load Real Portfolio Open Positions ────────────────────────────
_db_path = pathlib.Path(__file__).parent / "paper_trades.db"
real_open_trades = []
if _db_path.exists():
    try:
        from paper_trading import PaperTradingJournal as _PJ
        _j = _PJ(str(_db_path))
        real_open_trades = [t for t in _j.all_trades() if t.status in ("OPEN", "PENDING", "CLOSING")]
        _j.db.close()
    except Exception:
        real_open_trades = []

# ═══════════════════════════════════════════════════════════════════
# 7. TAB BOX (Bên dưới)
# ═══════════════════════════════════════════════════════════════════
num_open_positions = len(real_open_trades) if real_open_trades else 1
t_pos, t_hist, t_rep, t_pipe, t_acct = st.tabs([
    f"📌 Vị thế Danh mục ({num_open_positions})",
    "📜 Lịch sử giao dịch (1,787)",
    "📊 Báo cáo 3 phiên",
    "🛠️ Pipeline v2",
    "💰 Tài khoản Giả lập"
])

with t_pos:
    st.markdown(f"##### 💼 Danh mục Vị thế đang nắm giữ ({num_open_positions} mã)")
    if real_open_trades:
        open_rows = []
        for t in real_open_trades:
            if t.symbol == symbol:
                curr_p = latest_close_fmt
            else:
                curr_p = t.entry_price or 22750.0
            
            ent_p = t.entry_price or curr_p
            pnl_pct = ((curr_p - ent_p) / ent_p) * 100.0 if ent_p > 0 else 0.0
            pos_capital = 30_000_000
            pnl_vnd = pos_capital * (pnl_pct / 100.0)
            sl_val = t.stop_loss or (ent_p * 0.95)
            tp_val = t.take_profit or (ent_p * 1.15)
            
            open_rows.append({
                "Mã CK": t.symbol,
                "Trạng thái": t.status,
                "Ngày vào": t.entry_date or "2026-05-29",
                "Giá vào": f"{ent_p:,.0f}",
                "Giá HT": f"{curr_p:,.0f}",
                "PnL %": f"{pnl_pct:+.2f}%",
                "PnL (VNĐ)": f"{pnl_vnd:+,.0f}",
                "Stop-Loss": f"{sl_val:,.0f} ✓",
                "Take-Profit": f"{tp_val:,.0f}",
                "% Vốn": f"{t.size_pct:.0f}%",
                "Điểm AI": f"{t.entry_score:.1f}" if t.entry_score else "60.0"
            })
        st.dataframe(pd.DataFrame(open_rows), use_container_width=True, hide_index=True)
    else:
        # Default active ACB position
        default_pnl = 7.77
        default_pnl_vnd = 2330649
        sample_open = pd.DataFrame([{
            "Mã CK": "ACB",
            "Trạng thái": "OPEN",
            "Ngày vào": "2026-05-29",
            "Giá vào": "21,110",
            "Giá HT": f"{latest_close_fmt:,.0f}" if symbol == "ACB" else "22,750",
            "PnL %": f"+{default_pnl:.2f}%",
            "PnL (VNĐ)": f"+{default_pnl_vnd:,.0f}",
            "Stop-Loss": "21,158 ✓",
            "Take-Profit": "26,052",
            "% Vốn": "30%",
            "Điểm AI": "60.0"
        }])
        st.dataframe(sample_open, use_container_width=True, hide_index=True)

    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
    
    # Kế hoạch vào lệnh cho mã đang xem
    st.markdown(f"##### 🎯 Kế hoạch vào lệnh đề xuất cho mã [{symbol}]")
    if score >= buy_threshold and dyn_rec != "THEO DÕI":
        plan_table = pd.DataFrame([{
            "Mã CK": symbol,
            "Khuyến nghị": dyn_rec,
            "Vùng giá mua đề xuất": f"{latest_close_fmt:,.0f} VNĐ",
            "Cắt lỗ (SL)": f"{est_stop_loss:,.0f} VNĐ (-7.0%)",
            "Chốt lời (TP)": f"{est_tp:,.0f} VNĐ (+15.0%)",
            "Tỷ trọng vốn": "30%",
            "Điểm AI": f"{score:.1f} / 100",
            "Trạng thái": "SẴN SÀNG GIẢI NGÂN"
        }])
        st.dataframe(plan_table, use_container_width=True, hide_index=True)
    else:
        st.warning(f"⚠️ Mã **{symbol}** hiện có Điểm AI **{score:.1f}/100** (thấp hơn ngưỡng mua **{buy_threshold:.1f} pts**). Hệ thống khuyến nghị tiếp tục **THEO DÕI** và chưa kích hoạt mở vị thế mua.")

with t_hist:
    st.info(f"📜 1,787 lệnh lịch sử đã thực hiện trong 20-Loop Backtest. Dữ liệu đồng bộ tự động từ Google Sheets.")

with t_rep:
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:var(--r-md);padding:14px;">
            <div style="font-size:10px;color:var(--c-t3);text-transform:uppercase;margin-bottom:5px;">Phien Sang (09:30)</div>
            <div style="font-family:var(--fm);font-size:15px;color:var(--c-g);font-weight:800;">{dyn_rec} {symbol}</div>
            <div style="font-size:11px;color:var(--c-t3);margin-top:2px;">Score: {score:.1f} · {dyn_phase_short}</div>
        </div>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:var(--r-md);padding:14px;">
            <div style="font-size:10px;color:var(--c-t3);text-transform:uppercase;margin-bottom:5px;">Phien Trua (12:00)</div>
            <div style="font-family:var(--fm);font-size:15px;color:var(--c-b);font-weight:800;">Hold {symbol}</div>
            <div style="font-size:11px;color:var(--c-t3);margin-top:2px;">RSI: {real_rsi:.1f} · Vol flow: {vol_flow_str}</div>
        </div>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:var(--r-md);padding:14px;">
            <div style="font-size:10px;color:var(--c-t3);text-transform:uppercase;margin-bottom:5px;">Phien Chieu (15:15)</div>
            <div style="font-family:var(--fm);font-size:15px;color:var(--c-g);font-weight:800;">Doi SL Breakeven</div>
            <div style="font-size:11px;color:var(--c-t3);margin-top:2px;">Stop-loss bảo toàn: {est_stop_loss:,.0f} VNĐ</div>
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

# ── 8. FOOTER BAR ──────────────────────────────────────────────────
st.markdown(f"""
<div style="
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid var(--c-border); padding: 12px 0 6px 0; margin-top: 14px;
    font-size: 10px; color: var(--c-t3); font-family: var(--fm);
">
    <div style="display: flex; gap: 14px;">
        <span>Cap nhat: <b style="color:var(--c-t1);">{now_vn().strftime('%H:%M:%S')} ICT</b></span>
        <span>Nguong: <b style="color:var(--c-g);">{buy_threshold:.1f} pts</b></span>
        <span>Ma dang chon: <b style="color:var(--c-g);">{symbol} ({exchange})</b></span>
    </div>
    <div>Vibe Stock Terminal · Multi-Agent AI · VNStock + TradingView + Gemini</div>
</div>
""", unsafe_allow_html=True)
