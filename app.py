import base64
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

# ── Animated Brand Logo Generator ─────────────────────────────────
def get_animated_logo_html(size=44, uid="sb"):
    return (
        f'<div class="vibe-logo-wrap" style="width:{size}px;height:{size}px;">'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 184 184" width="{size}" height="{size}" class="vibe-animated-logo">'
        f'<defs><clipPath id="core_{uid}"><circle cx="92" cy="92" r="84"></circle></clipPath></defs>'
        f'<circle cx="92" cy="92" r="84" fill="#131a22"></circle>'
        f'<g clip-path="url(#core_{uid})">'
        f'<rect class="vbar b1" x="33.5" y="86" width="17" height="58" fill="#319cfc" rx="4"></rect>'
        f'<rect class="vbar b2" x="58.5" y="104" width="17" height="40" fill="#e24947" rx="4"></rect>'
        f'<rect class="vbar b3" x="83.5" y="62" width="17" height="82" fill="#fcaa2b" rx="4"></rect>'
        f'<rect class="vbar b4" x="108.5" y="32" width="17" height="112" fill="#61cc69" rx="4"></rect>'
        f'<rect class="vbar b5" x="133.5" y="78" width="17" height="66" fill="#9964e5" rx="4"></rect>'
        f'</g>'
        f'<g class="orbit-group">'
        f'<path d="M 135.250 17.089 A 86.5 86.5 0 0 1 139.111 164.545" fill="none" stroke="#41dca5" stroke-width="6" stroke-linecap="round"></path>'
        f'<path d="M 131.270 169.072 A 86.5 86.5 0 0 1 5.619 96.527" fill="none" stroke="#00ccf9" stroke-width="6" stroke-linecap="round"></path>'
        f'<path d="M 5.619 87.473 A 86.5 86.5 0 0 1 131.270 14.928" fill="none" stroke="#9c93ff" stroke-width="6" stroke-linecap="round"></path>'
        f'</g>'
        f'</svg>'
        f'</div>'
    )

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

    /* Transparent Streamlit Header & Persistent Sidebar Reopen Button */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0px !important;
        min-height: 0px !important;
        z-index: 99999 !important;
    }
    div[data-testid="stSidebarCollapsedControl"],
    button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] button {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        background: #111827 !important;
        border: 1px solid rgba(0, 217, 126, 0.5) !important;
        border-radius: 8px !important;
        color: #00d97e !important;
        box-shadow: 0 0 12px rgba(0, 217, 126, 0.3) !important;
        cursor: pointer !important;
        z-index: 100000 !important;
    }
    div[data-testid="stSidebarCollapsedControl"] svg,
    button[data-testid="stSidebarCollapseButton"] svg {
        fill: #00d97e !important;
        stroke: #00d97e !important;
    }
    div[data-testid="stSidebarCollapsedControl"]:hover,
    button[data-testid="stSidebarCollapseButton"]:hover {
        border-color: #00d97e !important;
        box-shadow: 0 0 16px rgba(0, 217, 126, 0.6) !important;
    }
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

    /* ─── LIVE ANIMATED LOGO ─────────────────────────────────── */
    .vibe-logo-wrap {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        position: relative;
        filter: drop-shadow(0 0 12px rgba(0, 217, 126, 0.45));
        animation: logoBreathing 3.5s ease-in-out infinite alternate;
    }
    .vibe-animated-logo {
        display: block;
    }
    .orbit-group {
        transform-origin: 92px 92px;
        animation: orbitSpin 10s linear infinite;
    }
    @keyframes orbitSpin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes logoBreathing {
        0% { filter: drop-shadow(0 0 10px rgba(0, 217, 126, 0.35)); }
        50% { filter: drop-shadow(0 0 20px rgba(0, 217, 126, 0.85)) drop-shadow(0 0 26px rgba(59, 130, 246, 0.5)); }
        100% { filter: drop-shadow(0 0 10px rgba(0, 217, 126, 0.35)); }
    }
    .vbar {
        transform-origin: center bottom;
        animation: barBounce 1.8s ease-in-out infinite alternate;
    }
    .vbar.b1 { animation-delay: 0.1s; animation-duration: 2.1s; }
    .vbar.b2 { animation-delay: 0.4s; animation-duration: 1.7s; }
    .vbar.b3 { animation-delay: 0.2s; animation-duration: 2.4s; }
    .vbar.b4 { animation-delay: 0.5s; animation-duration: 1.9s; }
    .vbar.b5 { animation-delay: 0.3s; animation-duration: 2.2s; }

    @keyframes barBounce {
        0% { transform: scaleY(0.90); opacity: 0.8; }
        50% { transform: scaleY(1.10); opacity: 1.0; }
        100% { transform: scaleY(0.90); opacity: 0.8; }
    }

    /* ─── SIDEBAR BRAND HEADER ───────────────────────────────── */
    .sb-brand-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0 4px 10px 4px;
        margin-top: -32px !important;
        margin-bottom: 10px;
        border-bottom: 1px solid var(--c-border);
    }
    .sb-brand-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .sb-brand-name {
        font-size: 15px;
        font-weight: 900;
        letter-spacing: -0.3px;
        color: #ffffff;
        font-family: var(--ff);
    }
    .sb-brand-name span {
        color: var(--c-g);
    }
    .sb-brand-tag {
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        color: var(--c-t2);
        font-family: var(--fm);
    }

    /* ─── SEARCH INPUT & PILLS THEME ─────────────────────────── */
    [data-testid="stSidebar"] div[data-baseweb="input"] {
        background: rgba(15, 23, 42, 0.85) !important;
        border: 1px solid rgba(0, 217, 126, 0.3) !important;
        border-radius: 10px !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.4) !important;
        transition: all 0.25s ease !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="input"]:focus-within {
        border-color: #00d97e !important;
        box-shadow: 0 0 14px rgba(0, 217, 126, 0.4), inset 0 2px 4px rgba(0,0,0,0.4) !important;
        background: rgba(15, 23, 42, 0.98) !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="input"] input {
        color: #ffffff !important;
        font-family: var(--fm) !important;
        font-size: 14px !important;
        font-weight: 800 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
    }
    [data-testid="stSidebar"] div[data-testid="column"] button {
        background: rgba(17, 24, 39, 0.65) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: var(--c-t2) !important;
        font-family: var(--fm) !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        padding: 5px 6px !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] div[data-testid="column"] button:hover {
        border-color: rgba(0, 217, 126, 0.5) !important;
        color: #00d97e !important;
        background: rgba(0, 217, 126, 0.1) !important;
        transform: translateY(-1px) !important;
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

    /* ─── SIDEBAR GLASS & ZERO TOP PADDING ─────────────────────── */
    section[data-testid="stSidebar"] {
        background: var(--c-s1) !important;
        border-right: 1px solid var(--c-border) !important;
        padding-top: 0px !important;
    }
    div[data-testid="stSidebarHeader"] {
        padding: 6px 12px 0 12px !important;
        height: auto !important;
        min-height: 0px !important;
        background: transparent !important;
    }
    div[data-testid="stSidebarUserContent"] {
        padding-top: 0px !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
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

# ── SỔ LỆNH GIẤY — nguồn DUY NHẤT cho mọi con số hiệu quả trên giao diện ──
# Trên Streamlit Cloud, `.gitignore` chặn `*.db` nên paper_trades.db KHÔNG
# tồn tại. Bản cũ khi đó rơi vào nhánh dự phòng dựng sẵn một vị thế ACB
# +7,77% và bốn ô KPI bê từ ui_prototype.html — tức nhánh bịa là nhánh LUÔN
# chạy trên cloud. Nay: không đọc được sổ thì nói "chưa có dữ liệu".
# Nguong mua mac dinh cua giao dien. Topbar render TRUOC sidebar nen khong
# doc duoc bien cua thanh truot; truoc day cho do in cung "50.0 pts", nen
# keo truot sang 65 thi topbar van noi 50. Nay ca hai doc chung mot nguon:
# hang so nay cho lan render dau, session_state cho moi lan sau.
NGUONG_MUA_MAC_DINH = 50.0
KHOA_NGUONG_MUA = "nguong_mua_pts"

_db_path = pathlib.Path(__file__).parent / "paper_trades.db"
real_open_trades = []
so_lenh_perf = None
so_lenh_dong = 0
if _db_path.exists():
    try:
        from paper_metrics import compute as _compute
        from paper_trading import PaperTradingJournal as _PJ
        _j = _PJ(str(_db_path), cho_phep_so_that=True)
        _all = _j.all_trades()
        _j.db.close()
        real_open_trades = [t for t in _all
                            if t.status in ("OPEN", "PENDING", "CLOSING")]
        _dong = [t for t in _all if t.status == "CLOSED"]
        so_lenh_dong = len(_dong)
        so_lenh_perf = _compute(_dong)
        so_lenh_loi = None
    except Exception as _e:
        so_lenh_loi = f"lỗi đọc sổ lệnh: {type(_e).__name__}: {_e}"
else:
    so_lenh_loi = "không tìm thấy paper_trades.db (bình thường trên Streamlit Cloud)"


def _so(gia_tri, dinh_dang="{:,.2f}"):
    """Số thật, hoặc dấu gạch. KHÔNG BAO GIỜ là một con số thay thế."""
    return "—" if gia_tri is None else dinh_dang.format(gia_tri)


# ── 1. COMPACT TOPBAR ──────────────────────────────────────────────
topbar_logo_html = get_animated_logo_html(size=28, uid="tb")
st.markdown(
    f'<div class="topbar">'
    f'<div class="tb-l">'
    f'{topbar_logo_html}'
    f'<div class="logo-t">VIBE <span>STOCK</span> TERMINAL</div>'
    f'<span class="badge">Multi-Agent AI v5.0</span>'
    f'</div>'
    f'<div class="tb-r">'
    f'<div class="ti-item"><span class="ti-l">VN-Index</span><span class="ti-v">—</span></div>'
    f'<div class="ti-item"><span class="ti-l">Sổ lệnh (net)</span>'
    f'<span class="ti-v">{_so(so_lenh_perf.total_net_pct if so_lenh_perf else None, "{:+.2f}%")}</span></div>'
    f'<div class="ti-item"><span class="ti-l">Threshold</span><span class="ti-v bl">'
    f'{st.session_state.get(KHOA_NGUONG_MUA, NGUONG_MUA_MAC_DINH):.1f} pts</span></div>'
    # Truoc day pill nay noi "Sheets Synced" kem cham xanh, trong khi
    # app.py khong he import sheets_store va chua bao gio goi trang_thai().
    # Cung ho voi market_filter.status() bao active=True trong khi cong
    # dong cung. Kiem that can mot cu goi mang moi lan render, nen o day
    # chi noi dung thu minh biet: chua kiem.
    f'<div class="live-pill">Sheets: chưa kiểm</div>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True
)

# ── Data Helper Functions ──────────────────────────────────────────
@st.cache_data(ttl=300)
def load_stock_data(ticker, start, end, exch="HOSE"):
    try:
        res = VNStockCollectorAgent().collect(ticker, start, end, exchange=exch)
        quality = res.get("quality")
        warns = [i.message for i in quality.warnings] if quality is not None else []
        # bia-ok: nhanh `except` ngay duoi tra "FAILED", nen thieu khoa
        # `status` ma tra "OK" la khong nhat quan. Thuoc Phase 2C: sua o
        # day truoc khi cong chat luong du lieu duoc bat se lam giao dien
        # va so lenh noi hai chuyen khac nhau ve cung mot phien.
        return res.get("df"), res.get("status", "OK"), warns
    except Exception:
        return None, "FAILED", []

# Calculate RSI Helper
def calculate_rsi(series, period=14):
    # Thiếu dữ liệu thì trả None. Trả 50.0 là bịa một chỉ báo trung tính
    # rồi hiển thị nó như quan sát được.
    if len(series) < period + 1:
        return None
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last_val = rsi.iloc[-1]
    return float(last_val) if not pd.isna(last_val) else None

# ── 2. SIDEBAR SETUP & CONTROLS ────────────────────────────────────
with st.sidebar:
    # Sidebar Brand Header with Live Animated Circular Logo
    sidebar_logo_html = get_animated_logo_html(size=44, uid="sb")
    st.markdown(
        f'<div class="sb-brand-header">'
        f'{sidebar_logo_html}'
        f'<div class="sb-brand-info"><div class="sb-brand-name">VIBE <span>STOCK</span></div><div class="sb-brand-tag">Terminal AI v5.0</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

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
    buy_threshold = st.slider("Ngưỡng mua Multi-Agent (pts)", 40.0, 65.0,
                              NGUONG_MUA_MAC_DINH, 0.5, key=KHOA_NGUONG_MUA)
    capital_mode = st.radio("Chế độ phân bổ vốn:", ["30% / vị thế", "Kelly Dynamic", "1% Risk"], index=0)
    exchange = st.selectbox("Sàn giao dịch:", ["HOSE", "HNX", "UPCOM"], index=0)
    days_back = 180

    run_btn = st.button("⚡ KÍCH HOẠT MULTI-AGENT SCAN", type="primary", use_container_width=True)

    # Placeholders for Dynamic Quick Signals in Sidebar
    sig_container = st.container()

    # Trạng thái hệ thống — chỉ khẳng định thứ ĐO ĐƯỢC tại chỗ.
    # Bản cũ dán cứng "12ms · ONLINE · Q2/2026 · 3 Vòng · 39 Mẫu · SYNCED ·
    # Live · READY", không dòng nào đọc từ đâu. Riêng số mẫu post-mortem
    # lệch thực tế hơn 160 lần — file thật có 6.327 mẫu.
    _pm_path = pathlib.Path(__file__).parent / "sl_pattern_memory.json"
    _pm_n = None
    if _pm_path.exists():
        try:
            _pm_n = len(json.loads(_pm_path.read_text(encoding="utf-8")))
        except Exception:
            _pm_n = None
    _pm_bat = os.environ.get("POST_MORTEM_ENABLED") == "1"
    _pm_chi_tiet = "—" if _pm_n is None else f"{_pm_n:,} mẫu"
    _pm_trang_thai = "● BẬT" if _pm_bat else "● TẮT"

    def _hang(nhan, chi_tiet, trang_thai, lop="wn"):
        return (f'<div class="a-row"><span class="a-lbl">{nhan}</span>'
                f'<span style="font-size:9.5px;color:#475569;">{chi_tiet}</span>'
                f'<span class="a-st {lop}">{trang_thai}</span></div>')

    st.markdown(
        '<div class="sb-card-title" style="margin-top: 10px;">'
        '🛰️ Trạng thái hệ thống AI</div>'
        '<div style="display:flex;flex-direction:column;gap:4px;">'
        + _hang("🧠 Post-Mortem Mem", _pm_chi_tiet, _pm_trang_thai,
                "ac" if _pm_bat else "wn")
        + _hang("📈 Technical Agent", "—", "● chưa đo")
        + _hang("📑 Fundamental Agent", "—", "● chưa đo")
        + _hang("⚔️ Debate Council", "—", "● chưa đo")
        + _hang("📡 TradingView MCP", "—", "● chưa đo")
        + '</div>',
        unsafe_allow_html=True)

# ── 3. RUN ANALYSIS & FETCH REAL DATA ──────────────────────────────
end_date = now_vn()
start_date = end_date - timedelta(days=days_back)
start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

# Cửa sổ dữ liệu cho PHÂN TÍCH tách khỏi cửa sổ cho BIỂU ĐỒ.
#
# `days_back = 180` (~124 phiên) là lựa chọn hiển thị, nhưng SMA200 cần 200
# phiên. Thiếu thì `_compute_local_indicators()` trả None cho SMA200, và
# trước 21/08/2026 giá trị VNĐ của TradingView nằm lại trong gói — agent xu
# hướng so 69,63 với 82.942 rồi trừ 2,0 điểm "Bear Market" cho MỌI mã.
#
# Nay `data_collectors` bỏ chỉ báo lệch đơn vị thay vì để lẫn, nên lỗi đó
# không còn. Nhưng bỏ đi cũng là mất một luật chấm điểm. Kéo dài cửa sổ
# phân tích để local tính nổi SMA200 thì luật đó sống lại, bằng đúng đơn vị
# của OHLCV. 420 ngày lịch ~ 285 phiên, dư so với 200.
NGAY_LICH_SU_PHAN_TICH = 420
start_str_phan_tich = (end_date - timedelta(days=NGAY_LICH_SU_PHAN_TICH)
                       ).strftime("%Y-%m-%d")

if run_btn or search_btn or "result" not in st.session_state or st.session_state.get("last_symbol") != symbol:
    with st.spinner(f"🤖 Đang quét dữ liệu Multi-Agent cho mã [{symbol}]..."):
        try:
            result = run_full_analysis(symbol, start_str_phan_tich, end_str, exchange)
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
rsi_txt = _so(real_rsi, "{:.1f}")
rsi_cls = ("neu" if real_rsi is None
           else "neg" if real_rsi >= 70 else "pos" if real_rsi <= 40 else "neu")

# Real Smart Money Flow %
last_vol = df['volume'].iloc[-1]
vol_flow_ratio = (last_vol / avg_vol - 1.0) * 100 if avg_vol > 0 else 0.0
vol_flow_str = f"+{vol_flow_ratio:.1f}%" if vol_flow_ratio >= 0 else f"{vol_flow_ratio:.1f}%"
vol_flow_cls = "pos" if vol_flow_ratio >= 0 else "neg"

# Bốn nhãn dưới đây CHỈ là điểm cuối chia thành 4 khoảng — không có phân
# tích Wyckoff nào ở đây. Bản cũ gọi chúng là "Pha C — Wyckoff Spring" và
# hiển thị như kết quả nhận diện cấu trúc giá.
score = result["final_score"]
if score >= 60.0:
    dyn_phase_short = "Điểm ≥ 60"
    dyn_phase_full = "Vùng điểm ≥ 60 (điểm cuối, không phải pha Wyckoff)"
elif score >= 54.0:
    dyn_phase_short = "Điểm 54–60"
    dyn_phase_full = "Vùng điểm 54–60 (điểm cuối, không phải pha Wyckoff)"
elif score >= 48.0:
    dyn_phase_short = "Điểm 48–54"
    dyn_phase_full = "Vùng điểm 48–54 (điểm cuối, không phải pha Wyckoff)"
else:
    dyn_phase_short = "Điểm < 48"
    dyn_phase_full = "Vùng điểm < 48 (điểm cuối, không phải pha Wyckoff)"

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
# Thiếu khuyến nghị của risk agent thì để TRỐNG. Bản cũ suy ra
# close×0,93 và close×1,15 rồi hiển thị như mức do agent tính.
est_stop_loss = risk_data.get("stop_loss_price")
if est_stop_loss is not None and est_stop_loss < 1000:
    est_stop_loss = round(est_stop_loss * mult, 0)
est_tp = risk_data.get("take_profit_price")
if est_tp is not None and est_tp < 1000:
    est_tp = round(est_tp * mult, 0)

sl_txt = _so(est_stop_loss, "{:,.0f}")
tp_txt = _so(est_tp, "{:,.0f}")
_pct = lambda muc: (None if muc is None or not latest_close_fmt
                    else (muc / latest_close_fmt - 1.0) * 100.0)
sl_pct_txt = _so(_pct(est_stop_loss), "{:+.1f}%")
tp_pct_txt = _so(_pct(est_tp), "{:+.1f}%")

# Render DYNAMIC Quick Signals in Sidebar
with sig_container:
    st.markdown(f"""
    <div class="sb-card-title" style="margin-top: 10px;">📊 Tín hiệu nhanh [{symbol}]</div>
    <div class="sig-grid">
        <div class="sig-item">
            <span class="sig-lbl">Vùng điểm AI</span>
            <span class="sig-val pos">{dyn_phase_short}</span>
        </div>
        <div class="sig-item">
            <span class="sig-lbl">RSI (14)</span>
            <span class="sig-val {rsi_cls}">{rsi_txt}</span>
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
            <span class="stag">SL: {sl_txt} VND</span>
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

    if est_stop_loss is not None:
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
    bull_msg = f"Tín hiệu dòng tiền và mô hình giá của {symbol} tại vùng hỗ trợ {sl_txt} rất tích cực. Khuyến nghị giải ngân thăm dò."
    bear_msg = f"Cảnh báo: Biên độ dao động của {symbol} và thị trường chung cần theo dõi sát. Thiết lập ngưỡng cắt lỗ ngặt nghèo."
    master_msg = f"Đồng thuận mở vị thế {symbol}. Điểm AI đạt {score:.1f}/100. Kích hoạt quản trị rủi ro đa tầng."
    bull2_msg = f"Kỳ vọng mục tiêu chốt lời ngắn hạn của {symbol} đạt {tp_txt} VNĐ. Duy trì vị thế."

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

# ═══════════════════════════════════════════════════════════════════
# 7. TAB BOX (Bên dưới)
# ═══════════════════════════════════════════════════════════════════
num_open_positions = len(real_open_trades)
t_pos, t_hist, t_rep, t_pipe, t_acct = st.tabs([
    f"📌 Vị thế Danh mục ({num_open_positions})",
    f"📜 Lịch sử giao dịch ({so_lenh_dong:,})" if so_lenh_perf else "📜 Lịch sử giao dịch",
    "📊 Báo cáo 3 phiên",
    "🛠️ Pipeline v2",
    "💰 Tài khoản Giả lập"
])

with t_pos:
    st.markdown(f"##### 💼 Danh mục Vị thế đang nắm giữ ({num_open_positions} mã)")
    if real_open_trades:
        open_rows = []
        for t in real_open_trades:
            # Thiếu trường nào thì để trống trường đó. Bản cũ thay bằng
            # 22.750đ, ngày 2026-05-29, điểm 60.0 và vốn 30 triệu/vị thế —
            # bốn con số không đọc từ đâu cả.
            ent_p = t.entry_price
            curr_p = latest_close_fmt if t.symbol == symbol else None
            pnl_pct = (None if not ent_p or curr_p is None
                       else (curr_p - ent_p) / ent_p * 100.0)
            open_rows.append({
                "Mã CK": t.symbol,
                "Trạng thái": t.status,
                "Ngày vào": t.entry_date or "—",
                "Giá vào": _so(ent_p, "{:,.0f}"),
                "Giá HT": _so(curr_p, "{:,.0f}"),
                "PnL %": _so(pnl_pct, "{:+.2f}%"),
                "Stop-Loss": _so(t.stop_loss, "{:,.0f}"),
                "Take-Profit": _so(t.take_profit, "{:,.0f}"),
                "% Vốn": _so(t.size_pct, "{:.0f}%"),
                "Điểm AI": _so(t.entry_score, "{:.1f}"),
            })
        st.dataframe(pd.DataFrame(open_rows), use_container_width=True, hide_index=True)
    elif so_lenh_loi:
        st.warning(f"⚠️ Chưa đọc được sổ lệnh — {so_lenh_loi}")
    else:
        st.info("Sổ lệnh không có vị thế nào đang mở.")

    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
    
    # Kế hoạch vào lệnh cho mã đang xem
    st.markdown(f"##### 🎯 Kế hoạch vào lệnh đề xuất cho mã [{symbol}]")
    if score >= buy_threshold and dyn_rec != "THEO DÕI":
        plan_table = pd.DataFrame([{
            "Mã CK": symbol,
            "Khuyến nghị": dyn_rec,
            "Vùng giá mua đề xuất": f"{latest_close_fmt:,.0f} VNĐ",
            "Cắt lỗ (SL)": f"{sl_txt} VNĐ ({sl_pct_txt})",
            "Chốt lời (TP)": f"{tp_txt} VNĐ ({tp_pct_txt})",
            "Tỷ trọng vốn": _so(
                result.get("safety", {}).get("safe_position_size"), "{:.0f}%"),
            "Điểm AI": f"{score:.1f} / 100",
            "Trạng thái": "SẴN SÀNG GIẢI NGÂN"
        }])
        st.dataframe(plan_table, use_container_width=True, hide_index=True)
    else:
        st.warning(f"⚠️ Mã **{symbol}** hiện có Điểm AI **{score:.1f}/100** (thấp hơn ngưỡng mua **{buy_threshold:.1f} pts**). Hệ thống khuyến nghị tiếp tục **THEO DÕI** và chưa kích hoạt mở vị thế mua.")

with t_hist:
    if so_lenh_perf:
        st.info(f"📜 {so_lenh_dong:,} lệnh đã đóng trong sổ lệnh giấy "
                f"(`paper_trades.db`). Đây là sổ ghi tiến về phía trước, "
                f"không phải kết quả backtest.")
    else:
        st.warning(f"⚠️ Chưa đọc được sổ lệnh — {so_lenh_loi}")

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
            <div style="font-size:11px;color:var(--c-t3);margin-top:2px;">RSI: {rsi_txt} · Vol flow: {vol_flow_str}</div>
        </div>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:var(--r-md);padding:14px;">
            <div style="font-size:10px;color:var(--c-t3);text-transform:uppercase;margin-bottom:5px;">Phien Chieu (15:15)</div>
            <div style="font-family:var(--fm);font-size:15px;color:var(--c-g);font-weight:800;">Doi SL Breakeven</div>
            <div style="font-size:11px;color:var(--c-t3);margin-top:2px;">Stop-loss bảo toàn: {sl_txt} VNĐ</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with t_pipe:
    st.markdown("""
    <div style="padding:16px;display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:10px;">
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:10px 14px;text-align:center;">
            <span style="font-size:18px;">📡</span><br><b style="font-size:11px;">TradingView MCP</b><br><small style="color:var(--c-t3);font-size:9px;">chưa đo</small>
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
            <span style="font-size:18px;">☁️</span><br><b style="font-size:11px;">Google Sheets</b><br><small style="color:var(--c-t3);font-size:9px;">chưa đo</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

with t_acct:
    # Mọi con số ở đây đi qua paper_metrics.compute(). Bản cũ là HTML tĩnh
    # bê từ ui_prototype.html: 7.361 Tỷ · +636,11% · 1.787 lệnh · PF 1,43 ·
    # WR 61,2% · DD 19,4% — không con số nào tồn tại trong sổ lệnh.
    if so_lenh_perf is None:
        st.warning(f"⚠️ Chưa đọc được sổ lệnh — {so_lenh_loi}. "
                   f"Không hiển thị số liệu hiệu quả.")
    else:
        _p = so_lenh_perf
        try:
            from paper_metrics import expectancy_significant
            _sig = expectancy_significant([t for t in _all if t.status == "CLOSED"])
        except Exception:
            _sig = None

        _o = ('<div style="background:var(--c-s2);border:1px solid var(--c-border);'
              'border-radius:10px;padding:12px 14px;">')
        _nhan = ('<div style="font-size:9.5px;color:var(--c-t3);'
                 'text-transform:uppercase;font-weight:700;">')
        _to = '<div style="font-family:var(--fm);font-size:18px;font-weight:800;color:'
        _nho = '<div style="font-size:10.5px;color:'

        st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px;">
        {_o}{_nhan}Loi nhuan cong don (net)</div>
            {_to}var(--c-t1);">{_p.total_net_pct:+.2f}%</div>
            {_nho}var(--c-t3);">{_p.n_trades} lenh da dong</div></div>
        {_o}{_nhan}Ty le thang · Profit factor</div>
            {_to}var(--c-t1);">{_p.win_rate * 100:.1f}%</div>
            {_nho}var(--c-t3);">PF {_p.profit_factor:.2f} · lai TB {_p.avg_win:+.2f}% · lo TB {_p.avg_loss:+.2f}%</div></div>
        {_o}{_nhan}Ky vong moi lenh</div>
            {_to}var(--c-t1);">{_p.expectancy:+.2f}%</div>
            {_nho}var(--c-a);">{(f"KTC 95%: {_sig['ci'][0]:+.2f}% .. {_sig['ci'][1]:+.2f}%" if _sig else "chua co KTC")}</div></div>
        {_o}{_nhan}Sut giam toi da</div>
            {_to}var(--c-t1);">{_p.max_drawdown_pct:.2f}%</div>
            {_nho}var(--c-t3);">Von trien khai: {_p.avg_capital_deployed_pct:.0f}% TB · {_p.peak_capital_deployed_pct:.0f}% dinh</div></div>
    </div>
    """, unsafe_allow_html=True)

        if _sig and not _sig["significant"]:
            st.warning(f"⚠️ {_sig['verdict']} — kỳ vọng {_p.expectancy:+.2f}% "
                       f"trên {_p.n_trades} lệnh chưa loại được số 0.")
        if _p.peak_capital_deployed_pct > 100.0:
            st.error(
                f"🔴 ĐÒN BẨY ẨN: vốn cam kết cùng lúc chạm "
                f"{_p.peak_capital_deployed_pct:.0f}% (trung bình "
                f"{_p.avg_capital_deployed_pct:.0f}%). Lợi nhuận cộng dồn ở "
                f"trên là của một tài khoản vay được, không phải tài khoản "
                f"thật — xem NGUYEN-TAC-DO-LUONG.md, bất biến 7b.")
        st.caption("Nguồn: paper_trades.db qua paper_metrics.compute(). "
                   "Sổ lệnh giấy — không phải giao dịch thật.")

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
