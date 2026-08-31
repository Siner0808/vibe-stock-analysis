import os
import json
import csv
from datetime import datetime
import pandas as pd
import numpy as np
from vnstock import Quote

PORTFOLIO_FILE = "portfolio.json"
ORDER_BOOK_FILE = "order_book.csv"
REPORT_FILE = "daily_trading_report.md"

MAX_POSITIONS = 5
MAX_ALLOCATION_PER_STOCK = 0.20  # Toi da 20% von (200 trieu/ma)
MAX_PORTFOLIO_HEAT = 0.02       # Max 2% risk tren moi deal

def load_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        init_data = {
            "initial_capital": 1000000000.0,
            "cash_balance": 1000000000.0,
            "portfolio_value": 1000000000.0,
            "total_profit_loss": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "positions": {},
            "closed_trades": [],
            "daily_snapshots": []
        }
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(init_data, f, ensure_ascii=False, indent=2)
        return init_data
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_portfolio(data):
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_order_book(order_type, symbol, sector, qty, price, total_value, sl, tp, reason):
    file_exists = os.path.exists(ORDER_BOOK_FILE)
    with open(ORDER_BOOK_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Order_Type", "Symbol", "Sector", "Quantity", "Price", "Total_Value", "Stop_Loss", "Take_Profit", "Reason"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            order_type,
            symbol,
            sector,
            qty,
            f"{price:,.0f}",
            f"{total_value:,.0f}",
            f"{sl:,.0f}" if sl else "-",
            f"{tp:,.0f}" if tp else "-",
            reason
        ])

def get_realtime_price(symbol):
    try:
        q = Quote(symbol=symbol, source='VCI')
        df = q.history(start=datetime.now().strftime("%Y-%m-01"), end=datetime.now().strftime("%Y-%m-%d"))
        if df is not None and not df.empty:
            return df.iloc[-1]['close'] * 1000
    except Exception:
        pass
    # Fallback to cache if any
    cache_path = os.path.join("data_cache", f"{symbol}.csv")
    if os.path.exists(cache_path):
        df = pd.read_csv(cache_path)
        return df.iloc[-1]['close'] * 1000
    return None

def run_trading_cycle():
    print("="*80)
    print(f"🤖 KHOI DONG AI TRADING ENGINE - SO LENH TU DONG (1 TY VND)")
    print(f"⏰ Thoi gian he thong: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*80)

    portfolio = load_portfolio()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Cap nhat thi gia va quan tri vi the dang mo (Check StopLoss, TakeProfit, TrailingStop)
    print("\n🔍 1. Kiem tra va cap nhat vi the mo...")
    open_positions = portfolio["positions"]
    total_stock_value = 0.0
    closed_this_round = []

    for sym, pos in list(open_positions.items()):
        cur_p = get_realtime_price(sym)
        if cur_p is None:
            cur_p = pos["entry_price"]
        
        pos["current_price"] = cur_p
        pos["market_value"] = pos["quantity"] * cur_p
        avg_cost = pos.get("avg_cost", pos["entry_price"])  # Dung gia von TB neu co
        pnl = (cur_p - avg_cost) * pos["quantity"]
        pnl_pct = (cur_p / avg_cost - 1) * 100
        pos["pnl"] = pnl
        pos["pnl_pct"] = pnl_pct
        pos["cost_value"] = pos["quantity"] * avg_cost  # Cap nhat gia von thuc te
        
        # Trailing stop: Neu da lai > 8% (tinh tren avg_cost), nang SL
        if pnl_pct >= 8.0 and pos["stop_loss"] < avg_cost:
            pos["stop_loss"] = avg_cost * 1.02
            print(f"🛡️ {sym}: Kich hoat Trailing Stop! Nang SL len {pos['stop_loss']:,.0f} d (Bao toan von)")

        # Kiem tra Take Profit
        if cur_p >= pos["take_profit"]:
            print(f"🎯 {sym}: DAT MUC TIEU CHOT LOI! Gia {cur_p:,.0f} d >= TP {pos['take_profit']:,.0f} d (Lai {pnl_pct:+.1f}%)")
            portfolio["cash_balance"] += pos["market_value"]
            log_order_book("SELL_TP", sym, pos["sector"], pos["quantity"], cur_p, pos["market_value"], pos["stop_loss"], pos["take_profit"], f"Chot loi dat target ({pnl_pct:+.1f}%)")
            portfolio["closed_trades"].append({
                "symbol": sym,
                "sector": pos["sector"],
                "entry_date": pos["entry_date"],
                "exit_date": today_str,
                "entry_price": pos["entry_price"],
                "exit_price": cur_p,
                "quantity": pos["quantity"],
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "reason": "Take Profit Target Reached"
            })
            del open_positions[sym]
            closed_this_round.append(sym)
            continue

        # Kiem tra Stop Loss
        elif cur_p <= pos["stop_loss"]:
            print(f"⚠️ {sym}: VI PHAM MUC CAT LO! Gia {cur_p:,.0f} d <= SL {pos['stop_loss']:,.0f} d (Lo {pnl_pct:+.1f}%)")
            portfolio["cash_balance"] += pos["market_value"]
            log_order_book("SELL_SL", sym, pos["sector"], pos["quantity"], cur_p, pos["market_value"], pos["stop_loss"], pos["take_profit"], f"Cat lo ky luat ({pnl_pct:+.1f}%)")
            portfolio["closed_trades"].append({
                "symbol": sym,
                "sector": pos["sector"],
                "entry_date": pos["entry_date"],
                "exit_date": today_str,
                "entry_price": pos["entry_price"],
                "exit_price": cur_p,
                "quantity": pos["quantity"],
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "reason": "Stop Loss Hit"
            })
            del open_positions[sym]
            closed_this_round.append(sym)
            continue
        
        total_stock_value += pos["market_value"]
        print(f"• {sym} ({pos['sector']}): KL {pos['quantity']:,} | Gia von: {avg_cost:,.0f} d | Gia hien tai: {cur_p:,.0f} d | PnL: {pnl:+,.0f} d ({pnl_pct:+.2f}%)")

    # 2. Quet co hoi vao lenh moi neu danh muc con cho (Max 5 ma)
    available_slots = MAX_POSITIONS - len(open_positions)
    print(f"\n⚡ 2. Kiem tra co hoi mua moi (So luong vi the trong: {available_slots}/{MAX_POSITIONS})...")

    if available_slots > 0 and os.path.exists("scan_results_71_stocks.csv"):
        scan_df = pd.read_csv("scan_results_71_stocks.csv")
        # Loc cac ma co diem >= 80, chua co trong danh muc va volume tot
        candidates = scan_df[(scan_df['total_score'] >= 80) & (~scan_df['symbol'].isin(open_positions.keys()))].head(available_slots)
        
        for _, c in candidates.iterrows():
            sym = c['symbol']
            sector = c['sector']
            price = c['price']
            score = c['total_score']
            
            # Tinh toan tien giai ngan toi da cho 1 ma (20% NAV = 200 Trieu)
            nav = portfolio["cash_balance"] + total_stock_value
            max_pos_value = min(nav * MAX_ALLOCATION_PER_STOCK, portfolio["cash_balance"])
            
            if max_pos_value >= 50000000: # Toi thieu 50 trieu moi mo lenh
                # Tinh khoang Stop Loss va Take Profit theo Wyckoff / SMC
                sl_price = price * 0.94  # SL 6% (duoi vung LPS/FVG)
                tp_price = price * 1.15  # TP 15% (R:R ~ 2.5:1)
                
                # Tinh so luong CP tron lo 100
                qty = int(max_pos_value // (price * 100)) * 100
                actual_val = qty * price
                
                if qty > 0 and actual_val <= portfolio["cash_balance"]:
                    portfolio["cash_balance"] -= actual_val
                    open_positions[sym] = {
                        "symbol": sym,
                        "sector": sector,
                        "entry_date": today_str,
                        "entry_price": price,       # Gia mo vi the lan dau
                        "avg_cost": price,           # Gia von trung binh (= entry khi moi mo)
                        "current_price": price,
                        "quantity": qty,
                        "cost_value": actual_val,
                        "market_value": actual_val,
                        "stop_loss": sl_price,
                        "take_profit": tp_price,
                        "pnl": 0.0,
                        "pnl_pct": 0.0,
                        "score": score,
                        "num_entries": 1             # So lan mua (de tinh avg_cost sau)
                    }
                    total_stock_value += actual_val
                    log_order_book("BUY_ENTRY", sym, sector, qty, price, actual_val, sl_price, tp_price, f"Diem manh {score:.0f}/100 - Wyckoff Pha D/E & SMC MSS")
                    print(f"🚀 [AUTO BUY] Da khop lenh MUA: {sym} ({sector}) | KL: {qty:,} | Gia: {price:,.0f} d | GVon TB: {price:,.0f} | Tong: {actual_val:,.0f} d | SL: {sl_price:,.0f} | TP: {tp_price:,.0f}")

    # 3. Cap nhat thong so tong the tai khoan
    total_nav = portfolio["cash_balance"] + total_stock_value
    portfolio["portfolio_value"] = total_nav
    total_pnl = total_nav - portfolio["initial_capital"]
    portfolio["total_profit_loss"] = total_pnl
    
    # Cap nhat thong ke trade
    closed = portfolio["closed_trades"]
    portfolio["total_trades"] = len(closed)
    portfolio["winning_trades"] = len([t for t in closed if t["pnl"] > 0])
    portfolio["losing_trades"] = len([t for t in closed if t["pnl"] <= 0])
    portfolio["win_rate"] = (portfolio["winning_trades"] / max(1, portfolio["total_trades"])) * 100
    
    # Ghi snapshot hang ngay
    portfolio["daily_snapshots"].append({
        "date": today_str,
        "cash": portfolio["cash_balance"],
        "stock_value": total_stock_value,
        "total_nav": total_nav,
        "daily_pnl": total_pnl,
        "daily_return_pct": (total_nav / portfolio["initial_capital"] - 1) * 100
    })
    
    save_portfolio(portfolio)

    # 4. Xuat Bao Cao Ngay
    generate_daily_report(portfolio)
    print("\n" + "="*80)
    print("✅ HOAN TAT PHIEN GD TU DONG! DA XUAT BAO CAO VA GHI SO LENH.")
    print("="*80)

def generate_daily_report(portfolio):
    today_str = datetime.now().strftime("%d/%m/%Y")
    total_nav = portfolio["portfolio_value"]
    cash = portfolio["cash_balance"]
    init_cap = portfolio["initial_capital"]
    total_pnl = portfolio["total_profit_loss"]
    total_ret = (total_nav / init_cap - 1) * 100
    
    positions = portfolio["positions"]
    
    md = []
    md.append(f"# 📊 BÁO CÁO SỔ LỆNH VÀ DANH MỤC ĐẦU TƯ AI TRADING (VỐN 1 TỶ VNĐ)")
    md.append(f"**Ngày báo cáo:** {today_str} | **Hệ thống AI:** Antigravity Quant Engine (Wyckoff & SMC)\n")
    
    md.append(f"## 💰 1. TỔNG QUAN TÀI SẢN (NAV)")
    md.append(f"- **Vốn ban đầu:** `{init_cap:,.0f} VNĐ`")
    md.append(f"- **Tổng tài sản ròng (NAV hiện tại):** `{total_nav:,.0f} VNĐ`")
    md.append(f"- **Tiền mặt khả dụng:** `{cash:,.0f} VNĐ` ({cash/total_nav*100:.1f}%)")
    md.append(f"- **Giá trị cổ phiếu:** `{total_nav - cash:,.0f} VNĐ` ({(total_nav-cash)/total_nav*100:.1f}%)")
    md.append(f"- **Tổng Lãi / Lỗ ròng:** `{total_pnl:+,.0f} VNĐ` (**{total_ret:+.2f}%**)\n")
    
    md.append(f"## 📈 2. SỔ VỊ THẾ ĐANG NẮM GIỮ ({len(positions)}/{MAX_POSITIONS} VỊ THẾ)")
    if positions:
        md.append("| STT | Mã | Nhóm ngành | Khối lượng | Giá vốn mua | Giá thị trường | Tổng giá trị | Cắt lỗ (SL) | Chốt lời (TP) | Lãi/Lỗ (VNĐ) | % Lãi/Lỗ |")
        md.append("|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        for idx, (sym, p) in enumerate(positions.items(), 1):
            pnl_color = "🟢" if p["pnl"] >= 0 else "🔴"
            md.append(f"| {idx:02d} | **{sym}** | {p['sector']} | {p['quantity']:,} | {p['entry_price']:,.0f} đ | {p['current_price']:,.0f} đ | {p['market_value']:,.0f} đ | {p['stop_loss']:,.0f} đ | {p['take_profit']:,.0f} đ | {p['pnl']:+,.0f} đ | {pnl_color} **{p['pnl_pct']:+.2f}%** |")
    else:
        md.append("*Hiện tại danh mục chưa có vị thế nào mở. Đang chờ tín hiệu xác nhận.*")
    
    md.append(f"\n## 📜 3. LỊCH SỬ KHỚP LỆNH MỚI NHẤT")
    if os.path.exists(ORDER_BOOK_FILE):
        odf = pd.read_csv(ORDER_BOOK_FILE).tail(10)
        md.append("| Thời gian | Loại lệnh | Mã CP | Khối lượng | Giá khớp | Tổng giá trị | Lý do vào lệnh / Chiến lược |")
        md.append("|:---|:---:|:---:|:---:|:---:|:---:|:---|")
        for _, r in odf.iterrows():
            md.append(f"| {r['Timestamp']} | `{r['Order_Type']}` | **{r['Symbol']}** | {r['Quantity']:,} | {r['Price']} đ | {r['Total_Value']} đ | {r['Reason']} |")
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

if __name__ == "__main__":
    run_trading_cycle()
