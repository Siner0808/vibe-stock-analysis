"""
trade_review.py
──────────────────────────────────────────────────────────────────────
Vẽ lại biểu đồ tại thời điểm agent ra quyết định, để kiểm tra trực quan.

Ý TƯỞNG TRUNG TÂM: TÁCH "AGENT BIẾT GÌ" KHỎI "SAU ĐÓ XẢY RA GÌ"
────────────────────────────────────────────────────────────────
Biểu đồ chia làm hai vùng có màu nền khác nhau:
  · Vùng SÁNG  — dữ liệu agent nhìn thấy khi ra quyết định
  · Vùng MỜ    — những gì xảy ra sau đó, agent KHÔNG hề biết

Vì sao quan trọng: nhìn cả biểu đồ liền mạch thì bộ não luôn thấy quyết
định là "hiển nhiên" — thiên lệch nhận thức muộn (hindsight bias). Che
phần tương lai đi mới đánh giá được: với thông tin có lúc đó, quyết định
này có hợp lý không?

Đó là câu hỏi khác hẳn với "lệnh này lãi hay lỗ". Một quyết định đúng vẫn
có thể lỗ, và ngược lại. Muốn cải thiện hệ thống thì phải phân biệt được.

Không phụ thuộc Streamlit — trả về Figure của Plotly nên test được offline.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
import plotly.graph_objects as go

from data_quality import price_multiplier

COLOR_UP = "#00e676"
COLOR_DOWN = "#ef5350"
COLOR_ENTRY = "#29b6f6"
COLOR_EXIT = "#ab47bc"
COLOR_SL = "#ef5350"
COLOR_TP = "#00e676"


def slice_around(df: pd.DataFrame, signal_date: str, exit_date: str | None,
                 before: int = 60, after: int = 20) -> pd.DataFrame:
    """Cắt đoạn dữ liệu quanh lệnh: `before` phiên trước tín hiệu, `after`
    phiên sau khi đóng (hoặc sau tín hiệu nếu lệnh chưa đóng)."""
    times = df["time"].astype(str)
    if signal_date not in set(times):
        return pd.DataFrame()
    i0 = int(times[times == signal_date].index[0])
    i1 = i0
    if exit_date and exit_date in set(times):
        i1 = int(times[times == exit_date].index[0])
    lo = max(0, i0 - before)
    hi = min(len(df), i1 + after + 1)
    return df.iloc[lo:hi].reset_index(drop=True)


def build_figure(df: pd.DataFrame, trade: Any, height: int = 520) -> go.Figure:
    """Biểu đồ nến kèm mốc quyết định, tách vùng đã biết và vùng tương lai."""
    window = slice_around(df, trade.signal_date, trade.exit_date)
    fig = go.Figure()
    if window.empty:
        fig.add_annotation(text="Không tìm thấy dữ liệu giá cho lệnh này",
                           showarrow=False, font=dict(color="#b0bec5"))
        fig.update_layout(height=height, template="plotly_dark",
                          paper_bgcolor="#0e1420", plot_bgcolor="#0e1420")
        return fig

    mult = price_multiplier(window)      # quy về VNĐ, khớp đơn vị của SL/TP
    t = window["time"].astype(str)

    fig.add_trace(go.Candlestick(
        x=t, open=window["open"] * mult, high=window["high"] * mult,
        low=window["low"] * mult, close=window["close"] * mult,
        name="Giá", increasing_line_color=COLOR_UP, increasing_fillcolor=COLOR_UP,
        decreasing_line_color=COLOR_DOWN, decreasing_fillcolor=COLOR_DOWN))

    # ── Vùng MỜ: những gì agent không thể biết khi quyết định ────────
    if trade.signal_date in set(t):
        fig.add_vrect(
            x0=trade.signal_date, x1=t.iloc[-1],
            fillcolor="#ffffff", opacity=0.05, line_width=0, layer="below",
            annotation_text="agent chưa biết vùng này khi quyết định",
            annotation_position="top right",
            annotation_font=dict(size=10, color="#78909c"))
        fig.add_vline(x=trade.signal_date, line_width=1, line_dash="dot",
                      line_color="#78909c")

    # ── Ngưỡng cắt lỗ / chốt lời ──────────────────────────────────────
    for price, color, label in ((trade.stop_loss, COLOR_SL, "Cắt lỗ"),
                                (trade.take_profit, COLOR_TP, "Chốt lời")):
        if price:
            fig.add_hline(y=float(price), line_dash="dash", line_color=color,
                          line_width=1,
                          annotation_text=f"{label} {float(price):,.0f}",
                          annotation_position="right",
                          annotation_font=dict(size=10, color=color))

    # ── Điểm vào / ra ─────────────────────────────────────────────────
    marks = []
    if trade.entry_date and trade.entry_price:
        marks.append((trade.entry_date, float(trade.entry_price),
                      "triangle-up", COLOR_ENTRY, "Vào lệnh"))
    if trade.exit_date and trade.exit_price:
        marks.append((trade.exit_date, float(trade.exit_price),
                      "triangle-down", COLOR_EXIT, "Đóng lệnh"))
    for date, price, sym, color, label in marks:
        fig.add_trace(go.Scatter(
            x=[date], y=[price], mode="markers+text", name=label,
            marker=dict(symbol=sym, size=15, color=color,
                        line=dict(width=1, color="#ffffff")),
            text=[f" {label} {price:,.0f}"], textposition="middle right",
            textfont=dict(size=10, color=color)))

    fig.update_layout(
        height=height, template="plotly_dark",
        paper_bgcolor="#0e1420", plot_bgcolor="#0e1420",
        margin=dict(l=10, r=90, t=30, b=10),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.08),
        hovermode="x unified")
    return fig


def decision_context(journal: Any, trade: Any) -> dict:
    """Lấy lại NGUYÊN TRẠNG bối cảnh lúc ra quyết định, từ sổ.

    Đọc từ bảng quyết định chỉ-thêm, không tính lại — tính lại bằng code
    hôm nay sẽ cho ra con số khác nếu logic đã thay đổi, và như vậy thì
    không còn kiểm tra được quyết định GỐC nữa.
    """
    row = journal.db.execute(
        "SELECT * FROM decisions WHERE symbol=? AND signal_date=? AND acted=1"
        " ORDER BY seq LIMIT 1", (trade.symbol, trade.signal_date)).fetchone()
    if row is None:
        return {}
    def _load(x):
        try:
            return json.loads(x) if x else {}
        except Exception:
            return {}
    return {
        "score": row["score"],
        "recommendation": row["recommendation"],
        "components": _load(row["components"]),
        "reasons": _load(row["reasons"]),
        "data_quality": row["data_quality"],
    }


def outcome_summary(trade: Any) -> str:
    """Một dòng mô tả kết cục, nói rõ đây là kết quả chứ không phải đánh giá
    chất lượng quyết định."""
    labels = {"STOP_LOSS": "chạm cắt lỗ", "TAKE_PROFIT": "chạm chốt lời",
              "SIGNAL_REVERSED": "tín hiệu đảo chiều", "MAX_HOLD": "hết hạn nắm giữ"}
    if trade.status != "CLOSED":
        return f"Đang {trade.status.lower()} — chưa có kết cục."
    net = trade.net_return_pct()
    return (f"{labels.get(trade.exit_reason, trade.exit_reason)} · "
            f"{net:+.2f}% sau phí · giữ {trade.entry_date} → {trade.exit_date}")
