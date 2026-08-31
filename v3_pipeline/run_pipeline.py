"""
ENTRY POINT: ANTIGRAVITY QUANT PIPELINE V3
Chạy toàn bộ 7 Tầng theo thứ tự, truyền kết quả giữa các tầng.
"""
import sys
import os
import json
from datetime import datetime

# Thêm v3_pipeline vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from layer0_data_quality import load_watchlist, run_quality_gate
from layer0_5_macro_filter import run_macro_filter
from layer2_wyckoff_engine import run_wyckoff_engine
from layer3_debate_council import run_debate_council
from layer4_risk_sizing import run_risk_sizing, load_portfolio, save_portfolio
from layer6_report import run_report

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")
ORDER_BOOK_FILE = os.path.join(BASE_DIR, "order_book.csv")


def execute_approved_orders(approved_orders: list):
    """Thực thi các lệnh mua đã được phê duyệt: cập nhật portfolio.json và order_book.csv."""
    if not approved_orders:
        return
    
    portfolio = load_portfolio()
    
    import csv
    order_book_path = ORDER_BOOK_FILE
    file_exists = os.path.exists(order_book_path)
    
    with open(order_book_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "action", "symbol", "sector", "quantity",
                             "entry_price", "amount", "stop_loss", "take_profit",
                             "consensus_score", "rr_ratio", "reason"])
        
        for order in approved_orders:
            sym = order["symbol"]
            
            # Ghi vào portfolio
            portfolio["positions"][sym] = {
                "quantity": order["quantity"],
                "entry_price": order["entry_price"],
                "current_price": order["entry_price"],
                "stop_loss": order["stop_loss"],
                "take_profit": order["take_profit"],
                "sector": order["sector"],
                "consensus_score": order["consensus_score"],
                "open_date": datetime.now().strftime("%Y-%m-%d"),
                "pnl": 0,
                "pnl_pct": 0.0
            }
            portfolio["cash_balance"] -= order["amount"]
            
            # Ghi vào order_book.csv
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "BUY_ENTRY_V3",
                sym,
                order["sector"],
                order["quantity"],
                order["entry_price"],
                order["amount"],
                order["stop_loss"],
                order["take_profit"],
                order["consensus_score"],
                order.get("rr_ratio", 0),
                f"Pipeline V3 | Consensus {order['consensus_score']}/100"
            ])
        
        # Cập nhật NAV
        total_position_value = sum(
            pos["quantity"] * pos["current_price"]
            for pos in portfolio["positions"].values()
        )
        portfolio["portfolio_value"] = portfolio["cash_balance"] + total_position_value
    
    save_portfolio(portfolio)
    print(f"\n  💾 Đã cập nhật {len(approved_orders)} lệnh vào portfolio.json và order_book.csv")


def run_full_pipeline():
    """Chạy toàn bộ Pipeline V3 từ đầu đến cuối."""
    start_time = datetime.now()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║   🤖 ANTIGRAVITY QUANT TRADING PIPELINE V3                  ║
║   Khởi chạy: {start_time.strftime('%d/%m/%Y %H:%M:%S')}                       ║
║   Vốn quản lý: 1.000.000.000 VNĐ | 71 Mã | 16 Ngành       ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # ─── TẦNG 0: DATA QUALITY GATE ─────────────────────────────
    symbols = load_watchlist()
    quality_results = run_quality_gate(symbols)
    passed_symbols = [s for s, r in quality_results.items() if r["passed"]]
    
    # ─── TẦNG 0.5: LỌC VĨ MÔ & RS RANKING ─────────────────────
    macro_result = run_macro_filter(quality_results)
    top_symbols = macro_result.get("top_symbols", [])
    
    if not top_symbols:
        print("\n🔴 RISK-OFF: Pipeline dừng tại Tầng 0.5 — Không phân tích tiếp")
        portfolio = load_portfolio()
        run_report(macro_result, {}, {}, [], portfolio)
        return
    
    # ─── TẦNG 2: WYCKOFF ENGINE ─────────────────────────────────
    wyckoff_results = run_wyckoff_engine(top_symbols, quality_results)
    
    # ─── TẦNG 3: HỘI ĐỒNG PHẢN BIỆN ────────────────────────────
    debate_results = run_debate_council(wyckoff_results, quality_results)
    
    # ─── TẦNG 4: RỦI RO & SIZING ────────────────────────────────
    approved_orders = run_risk_sizing(debate_results, macro_result)
    
    # ─── THỰC THI LỆNH ──────────────────────────────────────────
    if approved_orders:
        execute_approved_orders(approved_orders)
    
    # ─── TẦNG 6: BÁO CÁO & TELEGRAM ────────────────────────────
    portfolio = load_portfolio()
    run_report(macro_result, wyckoff_results, debate_results, approved_orders, portfolio)
    
    elapsed = (datetime.now() - start_time).seconds
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║   ✅ PIPELINE V3 HOÀN TẤT — {elapsed}s                          ║
║   Lệnh phê duyệt: {len(approved_orders)} | Đã gửi Telegram                  ║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_full_pipeline()
