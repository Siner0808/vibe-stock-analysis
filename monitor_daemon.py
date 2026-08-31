import os
import sys
import json
import time
from datetime import datetime
import pandas as pd
from vnstock import Quote
from notifier import broadcast_alert

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "v3_pipeline"))
from ml_algorithms import kalman_filter_trend

PORTFOLIO_FILE = "portfolio.json"
ORDER_BOOK_FILE = "order_book.csv"
ALERTS_FILE = "active_alerts.json"
SCAN_RESULTS_FILE = "scan_results_71_stocks.csv"

def format_price_k(price):
    if price is None: return "N/A"
    price_k = price / 1000.0 if price > 500 else float(price)
    return f"{price_k:.2f}k"

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_portfolio(p):
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

def save_alert(alert_type, symbol, price, message):
    alerts = []
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                alerts = json.load(f)
        except Exception:
            alerts = []
    
    new_alert = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": alert_type,
        "symbol": symbol,
        "price": price,
        "message": message,
        "read": False
    }
    alerts.append(new_alert)
    alerts = alerts[-50:]
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)
    
    print(f"\n🚨 [{new_alert['timestamp']}] {alert_type}: {message}")
    # Phát thông báo ra Telegram & Notifier
    broadcast_alert(f"🚨 CẢNH BÁO QUAN TRỌNG: {symbol} - {alert_type}", message)

def check_monitoring_cycle():
    portfolio = load_portfolio()
    if not portfolio:
        return []

    event_notifications = []
    open_positions = portfolio.get("positions", {})
    
    # 1. Kiểm tra vị thế đang nắm giữ (TP / SL / Trailing Stop & Kalman Velocity)
    for sym, pos in list(open_positions.items()):
        try:
            q = Quote(symbol=sym, source='VCI')
            df = q.history(start=datetime.now().strftime("%Y-%m-01"), end=datetime.now().strftime("%Y-%m-%d"))
            if df is None or df.empty:
                continue
            cur_p = df.iloc[-1]['close'] * 1000.0 if df.iloc[-1]['close'] < 500 else float(df.iloc[-1]['close'])
        except Exception:
            continue

        pos["current_price"] = cur_p
        pnl_pct = (cur_p / pos["entry_price"] - 1) * 100
        pos["pnl"] = (cur_p - pos["entry_price"]) * pos["quantity"]
        pos["pnl_pct"] = pnl_pct
        
        # Kalman Zero-Lag check
        if len(df) >= 10:
            kalman_res = kalman_filter_trend(df['close'].values)
            if kalman_res.get("signal") == "BEARISH_REVERSAL" and pnl_pct > 3.0:
                msg = f"⚡ *ĐẢO CHIỀU GIẢM (KALMAN ZERO-LAG):* {sym} vận tốc giảm `{kalman_res.get('velocity_pct', 0):+.2f}%`. Cân nhắc hạ tỷ trọng tại {format_price_k(cur_p)} (`{cur_p:,.0f} đ`) để bảo toàn lợi nhuận!"
                save_alert("KALMAN_WARNING", sym, cur_p, msg)
                event_notifications.append(msg)
        
        # Trailing Stop: Nếu lãi > 8% và SL chưa nâng lên hòa vốn
        if pnl_pct >= 8.0 and pos["stop_loss"] < pos["entry_price"]:
            pos["stop_loss"] = pos["entry_price"] * 1.02
            msg = f"🛡️ *TRAILING STOP:* {sym} đạt lãi *{pnl_pct:+.2f}%*. Tự động dời Stop Loss lên *{format_price_k(pos['stop_loss'])}* (`{pos['stop_loss']:,.0f} đ`) để khóa lợi nhuận!"
            save_alert("TRAILING_STOP", sym, cur_p, msg)
            event_notifications.append(msg)

        # Chốt lời
        if cur_p >= pos["take_profit"]:
            msg = f"🎯 *TARGET CHỐT LỜI ĐẠT ĐỈNH:* {sym} chạm *{format_price_k(cur_p)}* (`{cur_p:,.0f} đ`) — Lãi *{pnl_pct:+.2f}%* (`{pos['pnl']:+,.0f} đ`). Khớp lệnh bán chốt lời!"
            save_alert("TAKE_PROFIT", sym, cur_p, msg)
            event_notifications.append(msg)
            portfolio["cash_balance"] += pos["quantity"] * cur_p
            del open_positions[sym]

        # Cắt lỗ kỷ luật
        elif cur_p <= pos["stop_loss"]:
            msg = f"⚠️ *CẮT LỖ KỶ LUẬT:* {sym} chạm ngưỡng *{format_price_k(cur_p)}* (`{cur_p:,.0f} đ`) — Lỗ *{pnl_pct:+.2f}%* (`{pos['pnl']:+,.0f} đ`). Kích hoạt bán bảo vệ vốn!"
            save_alert("STOP_LOSS", sym, cur_p, msg)
            event_notifications.append(msg)
            portfolio["cash_balance"] += pos["quantity"] * cur_p
            del open_positions[sym]

    # 2. Nếu danh mục còn trống, kiểm tra các mã tiềm năng đạt ngưỡng mua
    if len(open_positions) < 5 and os.path.exists(SCAN_RESULTS_FILE):
        scan_df = pd.read_csv(SCAN_RESULTS_FILE)
        top_candidates = scan_df[(scan_df['total_score'] >= 80) & (~scan_df['symbol'].isin(open_positions.keys()))].head(3)
        for _, c in top_candidates.iterrows():
            sym = c['symbol']
            score = c['total_score']
            price = c['price']
            msg = f"⚡ *CỔ PHIẾU VÀO NGƯỠNG MUA:* {sym} ({c.get('sector', 'N/A')}) giá *{format_price_k(price)}* (`{price:,.0f} đ`), Điểm định lượng *{score:.0f}/100* đạt chuẩn Wyckoff Pha D/E."
            save_alert("BUY_SIGNAL", sym, price, msg)
            event_notifications.append(msg)

    save_portfolio(portfolio)
    return event_notifications

if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Kiểm tra hệ thống giám sát tự động 15 phút...")
    events = check_monitoring_cycle()
    if events:
        print(f"Phát hiện {len(events)} sự kiện cần báo cáo:")
        for ev in events:
            print(f"- {ev}")
    else:
        print("Trạng thái danh mục ổn định, không có vi phạm ngưỡng.")

