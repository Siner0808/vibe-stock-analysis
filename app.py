import json
import streamlit as st
import streamlit.components.v1
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from master_agent import run_full_analysis

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

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Giá đóng cửa", f"{latest_close:,.2f} VNĐ", f"{change:+,.2f} ({pct_change:+.2f}%)")
    c2.metric("Cao nhất (kỳ)", f"{high_p:,.2f} VNĐ")
    c3.metric("Thấp nhất (kỳ)", f"{low_p:,.2f} VNĐ")
    c4.metric("KL Trung bình", f"{avg_vol:,.0f}")
    c5.metric("Chất lượng dữ liệu", result.get("data_quality", "OK"))

st.divider()

# ---- TABS ----
tab_main, tab_debate, tab_detail, tab_news, tab_chart, tab_diagram, tab_raw = st.tabs([
    "🧠 Kết quả Tổng hợp", "⚖️ Debate Council",
    "🔬 Chi tiết từng Agent",
    "📰 Tin tức & Sentiment", "📊 Đồ thị Kỹ thuật",
    "📐 Sơ đồ Pipeline", "📄 Dữ liệu thô"
])

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
            x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="OHLC"
        ))
        fig.add_trace(go.Scatter(x=df['time'], y=df['MA20'], mode='lines', name='MA20', line=dict(color='#ff9800', width=1.5)))
        fig.add_trace(go.Scatter(x=df['time'], y=df['MA50'], mode='lines', name='MA50', line=dict(color='#2196f3', width=1.5)))
        fig.update_layout(
            template="plotly_dark", height=500,
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
    st.subheader("📐 Kiến trúc Pipeline Multi-Agent — 5 Tầng")
    import pathlib, os

    # Load diagram HTML from the dedicated file (built with html-diagram skill)
    _diagram_paths = [
        # Trong thư mục project
        pathlib.Path(__file__).parent / "pipeline_diagram.html",
        # Trong artifact dir
        pathlib.Path(r"C:\Users\cuong\.gemini\antigravity\brain\94db5080-33a8-473d-9aa7-24e6bc20d5a5\pipeline_diagram.html"),
    ]
    _diagram_html = None
    for _p in _diagram_paths:
        if _p.exists():
            _diagram_html = _p.read_text(encoding="utf-8")
            break

    if _diagram_html:
        st.components.v1.html(_diagram_html, height=860, scrolling=True)
    else:
        st.warning("Không tìm thấy file pipeline_diagram.html. Vui lòng kiểm tra lại.")

with tab_raw:
    st.subheader("📄 JSON Output toàn bộ kết quả phân tích")
    raw_output = {k: v for k, v in result.items() if k != "analyses"}
    st.code(json.dumps(raw_output, indent=2, ensure_ascii=False, default=str), language="json")
    if df is not None:
        st.subheader("📋 Bảng dữ liệu OHLCV thô")
        st.dataframe(df.sort_values(by='time', ascending=False), use_container_width=True)
