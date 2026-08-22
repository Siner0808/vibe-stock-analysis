import base64
import json
import os

# Bật bộ nhớ hậu nghiệm cho app, giống `run_daily.py` (21/08/2026).
#
# VÌ SAO. Trước đây app KHÔNG bật, còn phiên quét sinh sổ lệnh thì có. Cùng
# một mã, cùng một ngày, app chấm cao hơn tới 12 điểm (PENALTY = -12,0) so
# với điểm đã ghi vào sổ — nên app có thể hiện MUA đúng mã mà phiên quét bỏ
# qua. Đo trên sổ thật: 437 quyết định trùng một ô bộ nhớ, trong đó 166 nằm
# trong vùng bị lật ở ngưỡng 58.
#
# PHẢI đặt TRƯỚC khi `post_mortem_learning` được nạp lần đầu, vì engine đọc
# biến này lúc khởi tạo.
#
# Lưu ý khi đọc số: bộ nhớ này đã BÃO HOÀ, không phải thiếu mẫu — 44 mẫu chỉ
# gồm 2 bộ ba khác nhau và phủ 3,2% số quyết định. Bật lên là để app KHỚP
# với sổ lệnh, không phải vì nó làm điểm tốt hơn; đo được là nó không.
# Xem docs/ket-qua-bo-nho-rieng-20260821.md.
os.environ.setdefault("POST_MORTEM_ENABLED", "1")
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
from pha_wyckoff import doc_pha
from data_quality import now_vn, price_multiplier
from data_collectors import VNStockCollectorAgent
import mau_bang_gia as _mbg

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

    /* ─── NĂM MÀU BẢNG GIÁ VIỆT NAM ──────────────────────────── */
    /* Lớp do `mau_bang_gia.MauGia.lop_css` chọn — đừng gán tay ở đây.
       Tím và xanh lam chỉ xuất hiện khi ĐỌC ĐƯỢC biên độ thật của đúng
       phiên đó từ bảng giá sở; không đọc được thì chỉ còn ba màu. Lý do
       đầy đủ nằm trong docstring của `mau_bang_gia.py`. */
    .bg-tran { color: var(--c-p) !important; }   /* tím      — giá TRẦN   */
    .bg-tang { color: var(--c-g) !important; }   /* xanh lá  — tăng       */
    .bg-tc   { color: var(--c-a) !important; }   /* vàng cam — tham chiếu */
    .bg-giam { color: var(--c-r) !important; }   /* đỏ       — giảm       */
    .bg-san  { color: var(--c-b) !important; }   /* xanh lam — giá SÀN    */
    .bg-kb   { color: var(--c-t3) !important; }  /* xám      — chưa biết  */

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


def _tip(chuoi) -> str:
    """Chuỗi an toàn để nhét vào thuộc tính `title="..."`.

    Nội dung tooltip có phần bê nguyên thông báo lỗi từ thư viện ngoài, mà
    một dấu nháy kép trong đó là đủ để cắt đứt thẻ HTML và làm hỏng cả
    thanh tiêu đề.
    """
    return (str(chuoi).replace("&", "&amp;").replace('"', "&quot;")
            .replace("<", "&lt;").replace(">", "&gt;"))


# ── VN-INDEX cho topbar ────────────────────────────────────────────
# Ô này viết cứng dấu gạch "—" từ ngày dựng giao diện: nó không đọc gì nên
# không bao giờ có số. `market_filter.chi_so_moi_nhat()` ưu tiên MẠNG (khác
# `get_vni_df()` của bộ lọc, vốn ưu tiên cache trên đĩa) và luôn trả kèm
# NGÀY PHIÊN — nhãn hiện ngày cạnh con số để một phiên cũ không thể giả
# dạng phiên mới. TTL 5 phút: đủ tươi trong phiên, đủ thưa để Streamlit vẽ
# lại không kéo theo một cú gọi mạng.
@st.cache_data(ttl=300, show_spinner=False)
def _vnindex_topbar():
    try:
        from market_filter import chi_so_moi_nhat
        return chi_so_moi_nhat()
    except Exception as e:
        return {"dong_cua": None, "thay_doi": None, "phan_tram": None,
                "ngay": None, "nguon": None,
                "loi": f"{type(e).__name__}: {str(e)[:80]}"}


_vni = _vnindex_topbar()
if _vni.get("dong_cua") is None:
    _vni_nhan, _vni_val, _vni_lop = "VN-Index", "—", "bg-kb"
    _vni_tip = f"Không lấy được VN-INDEX — {_vni.get('loi') or 'không rõ lý do'}"
else:
    # Chỉ số không có trần/sàn, nên gọi không kèm bảng giá: hàm tự tụt
    # xuống ba màu. Dung sai theo ĐƠN VỊ CHỈ SỐ, không phải đơn vị giá.
    _vni_mau = _mbg.mau_cho_phien(
        _vni["dong_cua"],
        _vni["dong_cua"] - (_vni.get("thay_doi") or 0.0),
        dung_sai=_mbg.DUNG_SAI_CHI_SO)
    _vni_ngay = _vni["ngay"] or ""
    _vni_nhan = f"VN-Index · {_vni_ngay[8:10]}/{_vni_ngay[5:7]}" if _vni_ngay else "VN-Index"
    _vni_lop = _vni_mau.lop_css
    _vni_val = (f"{_vni['dong_cua']:,.2f} "
                f"<span style=\"font-size:10px;font-weight:600;\">"
                f"{_vni_mau.mui_ten} {_so(_vni.get('phan_tram'), '{:+.2f}%')}"
                f"</span>")
    _vni_tip = (f"VN-INDEX phiên {_vni_ngay} — nguồn: {_vni.get('nguon')}. "
                f"Đây là phiên GẦN NHẤT lấy được; nó không mặc định là "
                f"hôm nay.")

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
    f'<div class="ti-item" title="{_tip(_vni_tip)}">'
    f'<span class="ti-l">{_vni_nhan}</span>'
    f'<span class="ti-v {_vni_lop}">{_vni_val}</span></div>'
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
def nen_noi_phien(ticker: str, ngay: str):
    """Nến 30 phút của ĐÚNG ngày `ngay`. Trả (DataFrame | None, lý do lỗi).

    Trả lý do thay vì nuốt lỗi: giao diện phải phân biệt được "hôm nay chưa
    có nến nào" với "không lấy được nến". Hai thứ đó nhìn giống nhau nếu chỉ
    trả None.

    Lọc lại theo ngày vì nguồn trả dư — xin một ngày mà nhận về 12 nến gồm
    cả phiên hôm trước, trong khi một phiên HOSE chỉ có 9 nến 30 phút.
    """
    try:
        import canh_bao_noi_phien as _cb
        import intraday_data as _idd
        d = _idd.tai(ticker, ngay, ngay, "30m", dung_cache=False)
        return _cb.loc_dung_ngay(d, ngay), None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:90]}"


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

    # MỌI dòng dưới đây ĐỌC trạng thái thật của lượt phân tích gần nhất.
    #
    # Bản cũ viết cứng "● chưa đo" cho bốn dòng — chúng không đọc gì cả, nên
    # nói sai ngay cả khi thành phần đó đang chạy tốt. Đo ngày 21/08/2026:
    # TradingView trả 15 chỉ báo, tin tức về 155 bài, Debate Council chạy đủ
    # vòng — cả ba đều bị bảng gắn nhãn "chưa đo".
    #
    # "Chưa chạy" khác "chưa đo": chưa chạy là chưa bấm nút, đọc được từ
    # session_state. Bảng không được nói gì hơn thế.

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

# ── Bảng trạng thái hệ thống: vẽ SAU khi đã có kết quả ────────────
#
# Streamlit chạy kịch bản từ trên xuống. Đặt bảng này trong khối
# `with st.sidebar:` ở đầu file thì nó vẽ TRƯỚC khi `run_full_analysis`
# chạy, nên ở đúng lượt vừa quét xong nó vẫn hiện "chưa chạy" — người
# dùng bấm quét, thấy kết quả hiện ra, mà bảng bên cạnh vẫn nói chưa
# chạy gì. `st.sidebar` dùng được ở bất cứ đâu, nên chỗ đúng của nó là
# sau khi `result` có giá trị.
with st.sidebar:
        _kq = st.session_state.get("result") or {}
        _nguon = " ".join(_kq.get("data_sources") or [])
        _bd = _kq.get("score_breakdown") or {}
        _da_chay = bool(_kq)

        def _chua_chay(dong):
            return _hang(dong, "—", "● chưa chạy", "wn")

        # ── Technical: sáu agent phân tích, đọc điểm thành phần thật ──
        if not _da_chay:
            _row_tech = _chua_chay("📈 Technical Agent")
        else:
            # Trừ "fundamental": nó có dòng riêng bên dưới, và đếm một
            # agent đọc báo cáo tài chính vào ô "Technical" là nói sai.
            _n_ind = len([k for k in (_kq.get("analyses") or {})
                          if k != "fundamental"])
            _row_tech = _hang(
                "📈 Technical Agent",
                f"trend {_bd.get('trend_score', '—')} · "
                f"vol {_bd.get('volume_score', '—')}",
                f"● {_n_ind} agent", "ac" if _n_ind else "wn")

        # ── Debate Council: đọc số vòng thật và mức điều chỉnh thật ──
        if not _da_chay:
            _row_debate = _chua_chay("⚔️ Debate Council")
        else:
            _dbt = _kq.get("debate") or {}
            _vong = len(_dbt.get("rounds") or [])
            _dc = _bd.get("debate_adjustment", 0) or 0
            _row_debate = _hang(
                "⚔️ Debate Council",
                f"{_vong} vòng · {_dc:+.1f} điểm" if _vong else "không chạy",
                "● BẬT" if _vong else "● TẮT", "ac" if _vong else "wn")

        # ── Agent Cơ Bản: đọc báo cáo tài chính thật ──
        #
        # Dòng này từng bị GỠ (21/08/2026) vì trong repo không có lớp nào
        # như vậy. Nay có `fundamental_agent.FundamentalAgent`, và mọi con
        # số dưới đây đọc từ kết quả chạy thật — kỳ báo cáo lấy từ nguồn
        # chứ không dán cứng "Q2/2026" như bản mockup.
        _fa = (_kq.get("analyses") or {}).get("fundamental") or {}
        if not _da_chay:
            _row_fa = _chua_chay("📑 Fundamental Agent")
        elif not _fa.get("available"):
            _row_fa = _hang(
                "📑 Fundamental Agent",
                (_fa.get("signals") or ["không đọc được"])[0]
                .lstrip("⚠️🟡 ")[:40],
                "● TẮT", "wn")
        else:
            _row_fa = _hang(
                "📑 Fundamental Agent",
                f"{_fa['xep_hang']} {_fa['diem']:.0f}/100 · BCTC {_fa['nam']}",
                "● BẬT", "ac")

        # ── Gói vnstock: hạng ĐANG CÓ HIỆU LỰC, không phải hạng đã mua ──
        #
        # Dòng này tồn tại vì ngày 22/08/2026 tài khoản đã lên Silver mà app
        # vẫn chạy như gói miễn phí: BCTC bị cắt còn 8/34 kỳ, hạn mức 60 thay
        # vì 300 req/phút. Không có lỗi nào, không cảnh báo nào — `vnai` nuốt
        # ImportError của package `vnii` rồi trả "free".
        #
        # Không dùng `_da_chay` làm điều kiện: hạng gói không phụ thuộc lượt
        # quét, và nó sai NGAY CẢ KHI chưa quét gì.
        try:
            import vnstock_goi as _vg
            _goi = _vg.kiem_goi()
            _row_goi = _hang(
                "🎫 Gói vnstock",
                (f"{_goi.hang_may_chu} · hết hạn {_goi.het_han}"
                 if _goi.dat else
                 f"mua {_goi.hang_may_chu} · chạy như {_goi.hang_cuc_bo}"
                 if _goi.tinh_trang == _vg.LECH else _goi.ly_do[:38]),
                "● ĐÚNG" if _goi.dat
                else "● LỆCH" if _goi.tinh_trang == _vg.LECH else "● ?",
                "ac" if _goi.dat else "wn")
        except Exception as _e:
            _goi = None
            _row_goi = _hang("🎫 Gói vnstock",
                             f"không kiểm được ({type(_e).__name__})",
                             "● ?", "wn")

        # ── TradingView: đọc từ ghi chú nguồn thật ──
        if not _da_chay:
            _row_tv = _chua_chay("📡 TradingView")
        else:
            _tv_ok = "[TradingView] Lấy dữ liệu" in _nguon
            _row_tv = _hang(
                "📡 TradingView",
                f"khuyến nghị {_kq.get('score_breakdown', {}).get('tv_bonus', 0):+d} đ"
                if _tv_ok else "không lấy được",
                "● BẬT" if _tv_ok else "● TẮT", "ac" if _tv_ok else "wn")

        st.markdown(
            '<div class="sb-card-title" style="margin-top: 10px;">'
            '🛰️ Trạng thái hệ thống AI</div>'
            '<div style="display:flex;flex-direction:column;gap:4px;">'
            + _hang("🧠 Post-Mortem Mem", _pm_chi_tiet, _pm_trang_thai,
                    "ac" if _pm_bat else "wn")
            + _row_tech
            + _row_fa
            + _row_debate
            + _row_tv
            + _row_goi
            + '</div>'
            + (f'<div style="font-size:9px;color:#f59e0b;margin-top:6px;'
               f'line-height:1.45;">⚠️ {_goi.dong_log()}</div>'
               if _goi is not None and not _goi.dat else '')
            # Ảnh hưởng bằng 0 phải được NÓI RA ngay cạnh dòng "● BẬT".
            # Một thành phần bật mà không tác động, nếu không ghi chú, đọc
            # y hệt một thành phần đang tham gia quyết định.
            + '<div style="font-size:9px;color:#475569;margin-top:6px;'
            'line-height:1.45;">Agent Cơ Bản đọc BCTC năm gần nhất (vnstock). '
            '<b>Ảnh hưởng lên điểm giao dịch: 0</b> — chưa CHẠY phép đo, '
            'không phải không đo được. Xem <code>fundamental_agent.py</code> '
            'và <code>experiment_fundamentals.py</code>.</div>',
            unsafe_allow_html=True)
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
# ── NĂM MÀU BẢNG GIÁ ───────────────────────────────────────────────
#
# Bản cũ có hai màu và `is_up = change >= 0`, nên một phiên đứng giá được tô
# xanh và ghi "▲ +0 (+0.00%)" — đứng giá không phải tăng. Nó cũng không có
# cách nào nói TRẦN hay SÀN, hai trạng thái mà người xem bảng giá Việt Nam
# đọc trước tiên.
#
# Không tự suy ra trần bằng ngưỡng phần trăm. Đo 21/08/2026: SSI trần ở
# +6,96% còn SHS tăng +8,16% mà KHÔNG trần (HNX biên 10%, trần 16.100, đóng
# 15.900). Mọi ngưỡng cứng đều tô sai ít nhất một trong hai mã đó.
#
# Tham chiếu lấy từ bảng giá khi có, vì `close.iloc[-2]` KHÔNG phải giá
# tham chiếu vào ngày giao dịch không hưởng quyền.
@st.cache_data(ttl=180, show_spinner=False)
def _bang_gia(ma: str):
    return _mbg.doc_bang_gia(ma)


_ngay_nen = str(df["time"].iloc[-1])[:10] if "time" in df.columns else None
_mau = _mbg.mau_cho_phien(latest_close_fmt, prev_close * mult,
                          _ngay_nen, _bang_gia(symbol))
delta_cls = _mau.lop_css

# Từ đây trở đi phần trăm hiển thị là phần trăm SO VỚI THAM CHIẾU đang dùng,
# không phải so với `close.iloc[-2]`. Hai con số bằng nhau ở phiên thường và
# khác nhau ở phiên không hưởng quyền — dùng lẫn thì màu và số nói hai
# chuyện khác nhau về cùng một phiên.
if _mau.thay_doi is not None:
    change_fmt, pct_change = _mau.thay_doi, _mau.phan_tram

_hau_to = (f" · {_mau.nhan}"
           if _mau.ma in (_mbg.TRAN, _mbg.SAN, _mbg.THAM_CHIEU,
                          _mbg.KHONG_BIET) else "")
if _mau.thay_doi is None:
    delta_str = f"— chưa có tham chiếu{_hau_to}"
else:
    delta_str = (f"{_mau.mui_ten} {change_fmt:+,.0f} "
                 f"({pct_change:+.2f}%){_hau_to}")

# Tooltip là chỗ KIỂM lại màu. Một màu không nói được nó dựa trên số nào thì
# không ai bắt được lúc nó sai.
_mau_tip = f"Tham chiếu: {_so(_mau.tham_chieu, '{:,.0f}')} đ"
if _mau.biet_bien_do:
    _mau_tip += (f" · trần {_mau.tran:,.0f} · sàn {_mau.san:,.0f}")
else:
    _mau_tip += " · KHÔNG biết biên độ, nên không kết luận trần/sàn"
_mau_tip += f" · nguồn: {_mau.nguon}"
if _mau.ghi_chu:
    _mau_tip += f" · {_mau.ghi_chu}"

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

score = result["final_score"]

# ── PHA WYCKOFF — đọc cấu trúc giá thật ──────────────────────────────
#
# Ô này từng hiện "Pha C — Wyckoff Spring" cho MỌI mã có điểm ≥ 60; ngày
# 21/08/2026 nhãn bị gỡ vì không có phân tích nào đứng sau, và thay bằng
# "Vùng điểm ≥ 60 (điểm cuối, không phải pha Wyckoff)". Nay nó đọc từ
# `pha_wyckoff.doc_pha()`, tức là từ tương quan giá–khối lượng.
#
# `doc_pha` trả "Chưa đủ bằng chứng" khá thường xuyên, và đó KHÔNG phải
# lỗi: pha B của tích luỹ và pha B của phân phối trông giống hệt nhau,
# nên gán hướng ở đó là bịa. Đừng "sửa" bằng cách nới ngưỡng cho ra nhãn
# đẹp hơn — đó đúng là cách cái nhãn cũ ra đời.
wy = doc_pha(df, mult)
dyn_phase_short = wy.nhan_ngan
dyn_phase_full = wy.nhan_day
phase_cls = {"tang": "pos", "giam": "neg"}.get(wy.huong, "neu")

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
            <span class="sig-lbl">Pha Wyckoff</span>
            <span class="sig-val {phase_cls}">{dyn_phase_short}</span>
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
    <div class="md-cell" title="{_tip(_mau_tip)}">
        <span class="md-label">Gia Dong Cua ({symbol})</span>
        <span class="md-val {delta_cls}">{latest_close_fmt:,.0f}</span>
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

    # ── Bằng chứng của phép đọc Wyckoff ──────────────────────────────
    #
    # Một nhãn pha không kèm bằng chứng thì không ai kiểm được, và thứ
    # không kiểm được thì không đo được. Ba mục dưới đây là bắt buộc theo
    # đúng phương pháp: bằng chứng ủng hộ, bằng chứng PHẢN BIỆN, và điều
    # kiện phủ định — "cần nhìn thấy gì để biết mình đã đọc sai".
    with st.expander(f"🔍 Bằng chứng Wyckoff — {wy.nhan_ngan} "
                     f"({wy.do_tin})", expanded=False):
        if wy.san is not None:
            st.markdown(
                f"**Hai biên vùng:** sàn `{wy.san:,.0f}` — trần "
                f"`{wy.tran:,.0f}` · nền `{wy.so_phien_nen}` phiên")
        if wy.bang_chung:
            st.markdown("**Bằng chứng ủng hộ**")
            st.markdown("\n".join(f"- {b}" for b in wy.bang_chung))
        st.markdown("**Bằng chứng phản biện**")
        st.markdown("\n".join(f"- {p}" for p in wy.phan_bien))
        st.markdown(f"**Điều kiện phủ định** — {wy.phu_dinh}")
        st.caption("Phân tích cấu trúc phục vụ việc đọc bối cảnh, không "
                   "phải khuyến nghị mua bán. Chỉ đọc khung ngày và không "
                   "đối chiếu VN-INDEX; cổ phiếu Việt Nam đồng pha với chỉ "
                   "số rất cao nên phần lớn mã chỉ đang phản chiếu thị "
                   "trường. Kết quả này KHÔNG tham gia chấm điểm.")

with col_debate:
    debate = result.get("debate") or {}
    rounds = debate.get("rounds", [])

    # GIÁ TRỊ DỰ PHÒNG KHI TẦNG TRANH LUẬN KHÔNG TRẢ VỀ GÌ.
    #
    # Bản cũ đặt sẵn bốn câu như "Khuyến nghị giải ngân thăm dò" và "Đồng
    # thuận mở vị thế" rồi mới ghi đè bằng phát biểu thật. Bình thường thì
    # debate có vòng nên chúng bị thay — nhưng đúng lúc tầng đó hỏng, giao
    # diện lại hiện một khuyến nghị MUA tự tin mà không agent nào nói ra.
    # Chỗ dự phòng là chỗ dễ bịa nhất, vì nó chỉ lộ ra khi có sự cố.
    _chua = "— tầng tranh luận không trả về phát biểu nào cho lượt này."
    bull_msg = _chua
    bear_msg = _chua
    master_msg = _chua
    bull2_msg = _chua

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
t_pos, t_hist, t_rep, t_fund, t_pipe, t_acct = st.tabs([
    f"📌 Vị thế Danh mục ({num_open_positions})",
    f"📜 Lịch sử giao dịch ({so_lenh_dong:,})" if so_lenh_perf else "📜 Lịch sử giao dịch",
    # Đổi tên 21/08/2026: ba thẻ bên trong không còn là ba phiên trong ngày.
    # Hai trong ba từng là chuỗi viết cứng ("Hold {mã}", "Doi SL Breakeven")
    # nên cái tên "3 phiên" mô tả một kế hoạch không tồn tại. Nay chúng đọc
    # thật: phân tích hôm nay · diễn biến trong phiên · vị thế trong sổ.
    "📊 Hôm nay",
    "📑 Cơ bản",
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
    # BA THẺ NÀY TỪNG LÀ HAI CHUỖI VIẾT CỨNG (21/08/2026).
    #
    # Thẻ giữa in "Hold {symbol}", thẻ phải in "Doi SL Breakeven" — không
    # phụ thuộc mã, không phụ thuộc điểm, không phụ thuộc gì cả. Chúng hiện
    # ra như kế hoạch giao dịch theo phiên do hệ thống sinh ra, trong khi
    # không thành phần nào sinh ra chúng.
    #
    # Nay cả ba đọc dữ liệu thật, và quan trọng hơn: chúng nói SỰ KIỆN chứ
    # không nói LỜI KHUYÊN. Hệ thống chấm trên nến ngày và không đặt lệnh —
    # nó biết "giá đang ở đâu" và "vị thế đã chạm mốc chưa", nó không biết
    # "nên Hold" hay "nên dời stop-loss".
    _ngay_nay = end_date.strftime("%Y-%m-%d")
    _nen_np, _loi_np = nen_noi_phien(symbol, _ngay_nay)

    # ── Thẻ 2: trong phiên hôm nay ──
    if _nen_np is not None and len(_nen_np):
        _gia_cuoi = float(_nen_np["close"].iloc[-1])
        _mo = float(_nen_np["open"].iloc[0])
        _bien = (_gia_cuoi - _mo) / _mo * 100 if _mo else 0.0
        _np_chinh = f"{_gia_cuoi:,.0f} VNĐ"
        _np_phu = (f"{len(_nen_np)} nến 30' · thấp {_nen_np['low'].min():,.0f}"
                   f" · cao {_nen_np['high'].max():,.0f} · {_bien:+.2f}% từ mở cửa")
        _np_mau = "var(--c-g)" if _bien >= 0 else "var(--c-r)"
    elif _loi_np:
        _np_chinh = "chưa lấy được"
        _np_phu = f"nến nội phiên: {_loi_np}"
        _np_mau = "var(--c-t3)"
    else:
        _np_chinh = "chưa có nến"
        _np_phu = f"phiên {_ngay_nay} chưa có nến 30 phút nào"
        _np_mau = "var(--c-t3)"

    # ── Thẻ 3: vị thế THẬT của mã này trong sổ lệnh ──
    _vt = next((t for t in real_open_trades if t.symbol == symbol), None)
    if _vt is None:
        _vt_chinh = "không có vị thế"
        _vt_phu = f"{symbol} không nằm trong sổ lệnh đang mở"
        _vt_mau = "var(--c-t3)"
    else:
        _cham = None
        if _nen_np is not None and len(_nen_np):
            try:
                import canh_bao_noi_phien as _cbm
                from datetime import timezone as _tz
                _cham = _cbm.kiem_mot(
                    {"symbol": symbol, "stop_loss": _vt.stop_loss,
                     "take_profit": _vt.take_profit},
                    _nen_np, end_date if end_date.tzinfo else
                    end_date.replace(tzinfo=_cbm.MUI_GIO_VN))
            except Exception:
                _cham = None
        if _cham is not None:
            _vt_chinh = f"chạm {_cham.loai} lúc {_cham.luc_nen[11:]}"
            _vt_phu = (f"mức {_cham.muc:,.0f} · giá {_cham.gia_cham:,.0f}"
                       f" — sổ lệnh vẫn chấm theo nến NGÀY")
            _vt_mau = "var(--c-r)" if _cham.loai == "SL" else "var(--c-g)"
        else:
            _vt_chinh = "đang mở, chưa chạm mốc"
            _vt_phu = (f"SL {_vt.stop_loss:,.0f} · TP {_vt.take_profit:,.0f}"
                       f" · vào {_vt.entry_date or '—'}")
            _vt_mau = "var(--c-b)"

    _o = ('background:var(--c-s2);border:1px solid var(--c-border);'
          'border-radius:var(--r-md);padding:14px;')
    _nhan = ('font-size:10px;color:var(--c-t3);text-transform:uppercase;'
             'margin-bottom:5px;')
    _phu = 'font-size:11px;color:var(--c-t3);margin-top:2px;'

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
        <div style="{_o}">
            <div style="{_nhan}">Phân tích hôm nay</div>
            <div style="font-family:var(--fm);font-size:15px;color:var(--c-g);font-weight:800;">{dyn_rec} {symbol}</div>
            <div style="{_phu}">Điểm {score:.1f} · {dyn_phase_short}</div>
        </div>
        <div style="{_o}">
            <div style="{_nhan}">Trong phiên {_ngay_nay}</div>
            <div style="font-family:var(--fm);font-size:15px;color:{_np_mau};font-weight:800;">{_np_chinh}</div>
            <div style="{_phu}">{_np_phu}</div>
        </div>
        <div style="{_o}">
            <div style="{_nhan}">Vị thế {symbol}</div>
            <div style="font-family:var(--fm);font-size:15px;color:{_vt_mau};font-weight:800;">{_vt_chinh}</div>
            <div style="{_phu}">{_vt_phu}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with t_fund:
    # Mọi con số ở tab này đọc từ `fundamental_agent.FundamentalAgent`.
    # Không đọc được thì hiện lý do và DỪNG — không có nhánh nào điền số
    # thay thế. Bản cũ của `financial_collector.py` từng sinh P/E từ
    # `hash(symbol)`, và vì hash chuỗi được ngẫu nhiên hoá theo tiến
    # trình, cùng một mã cho ra P/E khác nhau sau mỗi lần khởi động.
    _fu = (result.get("analyses") or {}).get("fundamental") or {}
    st.markdown(f"##### 📑 Sức khoẻ tài chính — {symbol}")

    if not _fu.get("available"):
        st.warning((_fu.get("signals") or ["Không đọc được báo cáo tài chính."])[0])
    else:
        _cs = _fu["chi_so"]
        _c1, _c2, _c3, _c4 = st.columns(4)
        _c1.metric("Xếp hạng", _fu["xep_hang"], f"{_fu['diem']:.0f}/100")
        _c2.metric("ROE", "—" if _cs.roe_pct is None else f"{_cs.roe_pct:.1f}%")
        _c3.metric("P/E", "—" if _cs.pe is None else f"{_cs.pe:.1f}")
        _c4.metric("P/B", "—" if _cs.pb is None else f"{_cs.pb:.2f}")

        # Hai nhóm ngành, hai bộ chỉ tiêu. Ngân hàng vay tiền là nghiệp vụ
        # chứ không phải rủi ro, nên chấm họ bằng Nợ vay/VCSH là chấm sai
        # bản chất — xem `fundamental_agent._cham_an_toan`.
        _rieng = ([("NIM", _cs.nim_pct, "{:.2f}%"),
                   ("Vốn chủ / Tổng tài sản", _cs.vcsh_tren_tts_pct, "{:.1f}%")]
                  if _cs.nhom == "ngân hàng" else
                  [("Biên lợi nhuận", _cs.bien_ln_pct, "{:.1f}%"),
                   ("Nợ vay / Vốn chủ", _cs.no_vay_tren_vcsh_pct, "{:.0f}%"),
                   ("Khả năng trả lãi", _cs.kha_nang_tra_lai, "{:.1f} lần")])
        _bang = [{"Chỉ tiêu": t,
                  "Giá trị": "—" if v is None else f.format(v)}
                 for t, v, f in _rieng + [
                     ("ROA", _cs.roa_pct, "{:.2f}%"),
                     ("EPS", _cs.eps, "{:,.0f} đ"),
                     ("Tỷ suất cổ tức", _cs.co_tuc_pct, "{:.2f}%"),
                     # Hậu tố "tăng trưởng" trong nhãn là bắt buộc: nguồn
                     # đặt tên ba dòng này y hệt số dư (`total_assets`,
                     # `owners_equity`), mà giá trị lại là phần trăm.
                     ("Tăng trưởng LNST", _cs.ln_tang_pct, "{:+.1f}%"),
                     ("Tăng trưởng vốn chủ", _cs.vcsh_tang_pct, "{:+.1f}%"),
                     ("Tăng trưởng tổng tài sản", _cs.tts_tang_pct, "{:+.1f}%")]]
        st.dataframe(pd.DataFrame(_bang), use_container_width=True,
                     hide_index=True)

        if _fu.get("canh_bao"):
            st.error("🔴 Cảnh báo: " + " · ".join(_fu["canh_bao"]))
        st.markdown("**Diễn giải**")
        st.markdown("\n".join(f"- {s}" for s in _fu["signals"]))
        st.caption(f"Nhóm: {_cs.nhom} · kỳ báo cáo: năm {_fu['nam']} · "
                   f"nguồn: {_fu['nguon']}")

    st.info(
        "**Ảnh hưởng lên điểm giao dịch: 0.** Agent này chạy đủ và trả số "
        "thật, nhưng `master_agent.TRONG_SO_CO_BAN = 0.0` nên nó không làm "
        "dịch điểm một ly nào.\n\n"
        "Cho tới 22/08/2026 lý do là **không đo được**: gói cộng đồng chỉ "
        "trả 8 quý, mà yếu tố cơ bản có IC ≈ 0,03–0,05 nên lực phát hiện "
        "chỉ ~10%. Gói tài trợ đã mở giới hạn đó — nay lấy được ~34 quý, "
        "lực phát hiện lên khoảng 46% ở IC 0,05. Lý do nay là **chưa chạy "
        "phép đo**, một chuyện khác hẳn.\n\n"
        "Ba thiên lệch còn nguyên: số liệu đã điều chỉnh hồi tố, rổ chỉ "
        "gồm mã còn sống, cửa sổ nằm trong vùng đã tối ưu — cả ba đều đẩy "
        "kết quả ĐẸP lên. Bật trọng số vẫn là một quyết định ĐO LƯỜNG; "
        "xem `experiment_fundamentals.py`.")

with t_pipe:
    # Sơ đồ này VẼ LUỒNG DỮ LIỆU, nên mỗi ô phải là một chặng có thật.
    #
    # Ô "Fundamental Agent" bị gỡ ngày 21/08/2026 vì lúc đó không lớp nào
    # như vậy tồn tại. Nay `fundamental_agent.FundamentalAgent` có thật và
    # `master_agent` gọi nó, nên ô được vẽ lại — kèm nhãn nói rõ nó KHÔNG
    # nằm trên đường chấm điểm (trọng số 0), vì vẽ nó vào giữa luồng mà
    # không ghi chú sẽ khẳng định điểm số chảy qua đó.
    #
    # Hai ô ghi "chưa đo" cũng đã thay bằng nhãn thật: TradingView đang trả
    # 15 chỉ báo mỗi lượt, Google Sheets đang là kho sổ lệnh. "Chưa đo" ở
    # đây không phải khiêm tốn mà là sai.
    st.markdown("""
    <div style="padding:16px;display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:10px;">
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:10px 14px;text-align:center;">
            <span style="font-size:18px;">📡</span><br><b style="font-size:11px;">TradingView</b><br><small style="color:var(--c-t3);font-size:9px;">RSI·MACD·ADX</small>
        </div>
        <span>→</span>
        <div style="background:var(--c-s2);border:1px solid var(--c-border);border-radius:10px;padding:10px 14px;text-align:center;">
            <span style="font-size:18px;">📊</span><br><b style="font-size:11px;">Technical Agent</b><br><small style="color:var(--c-t3);font-size:9px;">RSI · MACD</small>
        </div>
        <span>→</span>
        <div style="background:var(--c-s2);border:1px dashed var(--c-border);border-radius:10px;padding:10px 14px;text-align:center;opacity:.75;">
            <span style="font-size:18px;">📑</span><br><b style="font-size:11px;">Fundamental Agent</b><br><small style="color:var(--c-t3);font-size:9px;">BCTC năm · trọng số 0</small>
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
            <span style="font-size:18px;">☁️</span><br><b style="font-size:11px;">Google Sheets</b><br><small style="color:var(--c-t3);font-size:9px;">kho sổ lệnh</small>
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
    <!-- Đã bỏ "Gemini" (21/08/2026): chữ đó xuất hiện ĐÚNG MỘT LẦN trong
         toàn bộ app, và là ở chính dòng này. `chatbot_agent.py` không được
         app import lần nào. Ghi tên một thành phần vào chân trang là khẳng
         định nó đang chạy. VNStock và TradingView thì có thật — đã kiểm,
         TradingView trả 15 chỉ báo mỗi lượt phân tích. -->
    <div>Vibe Stock Terminal · Multi-Agent AI · VNStock + TradingView</div>
</div>
""", unsafe_allow_html=True)
