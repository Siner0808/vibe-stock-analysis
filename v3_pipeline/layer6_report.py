"""
TẦNG 6: BÁO CÁO LUẬN ĐIỂM ĐẦU TƯ & GỬI TELEGRAM
- Tổng hợp toàn bộ kết quả Pipeline
- Viết Investment Thesis Report (Báo cáo Luận điểm) cho từng lệnh
- Gửi ngay về Telegram @VideStock_VN_bot
"""
import json
import os
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "notification_config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def send_telegram(message: str):
    """Gửi tin nhắn về Telegram Bot (tất cả whitelist)."""
    cfg = load_config()
    token = cfg.get("telegram_bot_token")
    
    chat_ids = set()
    if cfg.get("telegram_chat_id"):
        chat_ids.add(str(cfg.get("telegram_chat_id")))
    for cid in cfg.get("whitelist_users", {}).keys():
        chat_ids.add(str(cid))
    
    if not token or not chat_ids:
        print("  ⚠️ Chưa cấu hình Telegram. In báo cáo ra màn hình.")
        print(message)
        return False
    
    max_len = 3800
    chunks = [message[i:i+max_len] for i in range(0, len(message), max_len)]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    success = True
    
    for chat_id in chat_ids:
        for chunk in chunks:
            for attempt in range(2):
                try:
                    res = requests.post(url, json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}, timeout=20)
                    if res.status_code != 200:
                        requests.post(url, json={"chat_id": chat_id, "text": chunk}, timeout=20)
                    break
                except Exception as e:
                    if attempt == 1:
                        print(f"  Lỗi Telegram cho chat {chat_id}: {e}")
                        success = False
    return success


def format_order_thesis(order: dict, debate: dict) -> str:
    """Tạo Investment Thesis Report cho một lệnh mua."""
    sym = order["symbol"]
    sector = order["sector"]
    consensus = order["consensus_score"]
    rr = order.get("rr_ratio", 0)
    
    bull_args = "\n".join([f"   • {a}" for a in order.get("bull_args", [])])
    bear_args = "\n".join([f"   • {a}" for a in order.get("bear_args", [])])
    
    verdict_bar = "🟢" * (consensus // 20) + "⬜" * (5 - consensus // 20)
    
    report = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 LỆNH MUA MỚI: *{sym}*
━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 Ngành: {sector}
💡 Consensus: {verdict_bar} {consensus}/100
📐 Risk:Reward = {rr:.1f} : 1

💰 Chi tiết lệnh:
• Giá vào: {order['entry_price']:,.0f} đ
• Khối lượng: {order['quantity']:,} CP
• Giải ngân: {order['amount']/1e6:.1f} triệu ({order['size_pct']}% NAV)
• Stop Loss: {order['stop_loss']:,.0f} đ (-6%)
• Take Profit: {order['take_profit']:,.0f} đ (+15%)

🐂 Luận điểm TĂNG:
{bull_args}

🐻 Rủi ro GIẢM:
{bear_args}

😈 Cảnh báo Phản biện:
   • Kịch bản xấu nhất nếu sai: -{6:.0f}% = {order['entry_price'] * order['quantity'] * 0.06 / 1e6:.1f}tr
   • Kịch bản tốt nhất nếu đúng: +{15:.0f}% = {order['entry_price'] * order['quantity'] * 0.15 / 1e6:.1f}tr"""
    
    return report


def format_regime_header(macro_result: dict) -> str:
    """Header báo cáo tổng quan thị trường."""
    regime = macro_result.get("regime", {})
    emoji = regime.get("emoji", "⚪")
    name = regime.get("regime", "UNKNOWN")
    ret_1m = regime.get("ret_1m", 0)
    ret_3m = regime.get("ret_3m", 0)
    vnindex = regime.get("vnindex_latest", 0)
    
    return f"""🤖 *BÁO CÁO AI TRADING PIPELINE V3*
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━
{emoji} *Chế độ thị trường: {name}*
📊 VN-Index: {vnindex:,.1f} | 1T: {ret_1m:+.1f}% | 3T: {ret_3m:+.1f}%"""


def format_no_signal_report(macro_result: dict, wyckoff_count: int, debate_count: int) -> str:
    """Báo cáo khi không có tín hiệu."""
    regime = macro_result.get("regime", {})
    return f"""{format_regime_header(macro_result)}

📋 *KẾT QUẢ PIPELINE:*
• Tầng 2 (Wyckoff): {wyckoff_count} mã đạt chuẩn
• Tầng 3 (Debate): {debate_count} mã đủ đồng thuận
• Tầng 4 (Sizing): Không có lệnh nào đủ R:R ≥ 2.0

✅ *TRẠNG THÁI: ĐỨNG NGOÀI CHỜ ĐỢI*
Không có vị thế mới được phê duyệt. Hệ thống tiếp tục giám sát.

_Pipeline sẽ tự động thông báo khi xuất hiện tín hiệu hội tụ đủ điều kiện._"""


def format_portfolio_status(portfolio: dict) -> str:
    """Báo cáo danh mục dạng BẢNG cô đọng, hiển thị rõ Chỉ số Thị trường & Giá Hiện Tại."""
    nav = portfolio.get("portfolio_value", 0)
    cash = portfolio.get("cash_balance", 0)
    positions = portfolio.get("positions", {})
    initial = portfolio.get("initial_capital", 1_000_000_000)
    
    stock_value = sum(pos.get("quantity", 0) * pos.get("current_price", pos.get("entry_price", 0)) for pos in positions.values())
    total_pnl = sum(pos.get("pnl", 0) for pos in positions.values())
    total_pnl_pct = (total_pnl / initial * 100) if initial else 0
    
    # Lấy chỉ số VN-Index nếu có
    vnindex_str = ""
    try:
        from vnstock import Quote
        q = Quote(symbol="VNINDEX", source="VCI")
        df_vn = q.history(start=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"), end=datetime.now().strftime("%Y-%m-%d"))
        if df_vn is not None and len(df_vn) >= 2:
            latest_idx = df_vn.iloc[-1]['close']
            prev_idx = df_vn.iloc[-2]['close']
            diff_idx = latest_idx - prev_idx
            diff_pct = (latest_idx / prev_idx - 1) * 100
            idx_icon = "🟢" if diff_idx >= 0 else "🔴"
            vnindex_str = f"🏛️ *VN-INDEX:* `{latest_idx:,.2f}` ({idx_icon} `{diff_pct:+.2f}%` | `{diff_idx:+.2f}đ`)\n"
    except Exception:
        pass
    
    # Tạo bảng Monospace thẳng hàng
    table_rows = []
    table_rows.append(f"{'MÃ':<5} {'KL':>5} {'GIÁ VỐN':>8} {'GIÁ HT':>8} {'LÃI/LỖ':>7}")
    table_rows.append("─" * 36)
    
    sl_tp_lines = []
    
    for sym, pos in positions.items():
        qty = pos.get("quantity", 0)
        qty_str = f"{qty/1000:.1f}k" if qty >= 1000 else str(qty)
        
        avg_cost = pos.get("avg_cost", pos.get("entry_price", 0))
        cur_p = pos.get("current_price", avg_cost)
        pnl_pct = pos.get("pnl_pct", 0)
        pnl_val = pos.get("pnl", 0)
        
        cost_str = f"{avg_cost/1000:.2f}k"
        cur_str = f"{cur_p/1000:.2f}k"
        pnl_str = f"{pnl_pct:+.2f}%"
        
        table_rows.append(f"{sym:<5} {qty_str:>5} {cost_str:>8} {cur_str:>8} {pnl_str:>7}")
        
        sl = pos.get("stop_loss", 0)
        tp = pos.get("take_profit", 0)
        pnl_icon = "🟢" if pnl_pct >= 0 else "🔴"
        sl_tp_lines.append(f"{pnl_icon} *{sym}* (HT: `{cur_p:,.0f}đ` | Vốn: `{avg_cost:,.0f}đ`)\n   ↳ SL: `{sl:,.0f}đ` | TP: `{tp:,.0f}đ` | L/L: `{pnl_val/1e6:+.2f}tr`")
    
    table_body = "\n".join(table_rows)
    targets_body = "\n".join(sl_tp_lines)
    pnl_nav_emoji = "📈" if total_pnl >= 0 else "📉"
    
    # Monte Carlo Metrics
    mc_section = ""
    try:
        from ml_algorithms import run_monte_carlo_portfolio
        mc = run_monte_carlo_portfolio(portfolio, {})
        if "var_95_vnd" in mc:
            mc_section = (
                f"\n🎲 *ĐỊNH LƯỢNG RỦI RO MONTE CARLO (5,000 kịch bản):*\n"
                f"   • VaR 95% (Tổn thất tối đa 10 ngày): `-{mc['var_95_pct']:.2f}%` (`-{mc['var_95_vnd']/1e6:.1f}tr`)\n"
                f"   • Xác suất sinh lời danh mục: *{mc['portfolio_win_prob']:.1f}%* | Tỷ lệ Kelly: `{mc['optimal_kelly_fraction']:.1f}%`\n"
            )
    except Exception:
        pass
        
    return f"""📊 *DANH MỤC VỊ THẾ ({len(positions)}/5 MÃ)*
{vnindex_str}```text
{table_body}
```
🎯 *CHI TIẾT GIÁ & MỤC TIÊU:*
{targets_body}
{mc_section}━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 Tiền mặt: `{cash/1e6:.1f}tr` | 📦 Cổ phiếu: `{stock_value/1e6:.1f}tr`
💼 NAV: *{nav/1e6:.1f} triệu* ({pnl_nav_emoji} *{total_pnl_pct:+.2f}%* | `{total_pnl/1e6:+.2f}tr`)"""




def run_report(macro_result: dict, wyckoff_results: dict, debate_results: dict, 
               approved_orders: list, portfolio: dict):
    """Entry point Tầng 6: Tổng hợp và gửi báo cáo."""
    print(f"\n{'='*60}")
    print(f"📄 TẦNG 6: PHÁT HÀNH BÁO CÁO LUẬN ĐIỂM ĐẦU TƯ")
    print(f"{'='*60}")
    
    wyckoff_count = len([r for r in wyckoff_results.values() if r.get("valid")])
    debate_count = len([r for r in debate_results.values() if r.get("verdict") in ["STRONG_BUY", "BUY"]])
    
    if not approved_orders:
        # Không có lệnh mới
        report = format_no_signal_report(macro_result, wyckoff_count, debate_count)
        report += format_portfolio_status(portfolio)
        print("  ℹ️ Không có lệnh mới — Gửi báo cáo trạng thái...")
        send_telegram(report)
    else:
        # Có lệnh mới
        header = format_regime_header(macro_result)
        header += f"\n\n🎯 *{len(approved_orders)} LỆNH MUA MỚI ĐƯỢC PHÊ DUYỆT*"
        header += format_portfolio_status(portfolio)
        send_telegram(header)
        
        for order in approved_orders:
            sym = order["symbol"]
            debate = debate_results.get(sym, {})
            thesis = format_order_thesis(order, debate)
            success = send_telegram(thesis)
            status = "✅ Đã gửi Telegram" if success else "📝 Đã in ra màn hình"
            print(f"  {status}: Báo cáo luận điểm {sym}")
    
    # Lưu báo cáo ra file
    report_path = "../daily_trading_report_v3.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# BÁO CÁO PIPELINE V3 — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        f.write(f"## Chế độ thị trường: {macro_result.get('regime', {}).get('regime')}\n")
        f.write(f"## Số lệnh phê duyệt: {len(approved_orders)}\n\n")
        for order in approved_orders:
            f.write(f"### {order['symbol']}: {order['quantity']:,} CP @ {order['entry_price']:,.0f}đ\n")
            f.write(f"- SL: {order['stop_loss']:,.0f}đ | TP: {order['take_profit']:,.0f}đ | R:R {order.get('rr_ratio', 0):.1f}\n")
            f.write(f"- Consensus: {order['consensus_score']}/100\n\n")
    
    print(f"\n  💾 Báo cáo đã lưu: {report_path}")
    return True
