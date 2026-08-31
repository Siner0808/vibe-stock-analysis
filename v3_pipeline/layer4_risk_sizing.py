"""
TẦNG 4: RỦI RO & POSITION SIZING ĐỒNG THUẬN
- Tính toán kích thước vị thế dựa trên Consensus Score
- Kiểm tra tập trung ngành (Max 30% mỗi ngành)
- Kelly Criterion điều chỉnh bảo thủ
- Output: Danh sách lệnh xác nhận với KL cụ thể
"""
import json
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist_71.json")
ORDER_BOOK_FILE = os.path.join(BASE_DIR, "order_book.csv")
MAX_POSITIONS = 5
MAX_NAV_PER_STOCK = 0.20        # 20% NAV tối đa
MAX_SECTOR_EXPOSURE = 0.30      # 30% NAV tối đa mỗi ngành
MIN_CONSENSUS_TO_TRADE = 55     # Ngưỡng tối thiểu để vào lệnh


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cash_balance": 1_000_000_000, "positions": {}, "portfolio_value": 1_000_000_000}


def save_portfolio(p):
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)


def get_sector_map():
    """Tra cứu ngành của từng mã CP."""
    with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    sector_map = {}
    for sector, tickers in data.items():
        for t in tickers:
            sector_map[t] = sector
    return sector_map


def confidence_weighted_size(consensus_score: int, nav: float, max_pct: float = MAX_NAV_PER_STOCK) -> float:
    """
    Kích thước vị thế tỷ lệ với mức độ đồng thuận:
    - Consensus >= 80 → Full size (20% NAV)
    - Consensus 60-79 → 60% size (12% NAV)
    - Consensus 55-59 → 40% size (8% NAV)
    """
    if consensus_score >= 80:
        multiplier = 1.0
    elif consensus_score >= 70:
        multiplier = 0.75
    elif consensus_score >= 60:
        multiplier = 0.60
    else:
        multiplier = 0.40
    
    return nav * max_pct * multiplier


def check_sector_concentration(portfolio: dict, sector: str, additional_amount: float, sector_map: dict) -> bool:
    """Kiểm tra xem ngành đó đã chiếm quá 30% NAV chưa."""
    nav = portfolio.get("portfolio_value", 1_000_000_000)
    positions = portfolio.get("positions", {})
    
    current_sector_value = sum(
        pos.get("quantity", 0) * pos.get("current_price", pos.get("entry_price", 0))
        for sym, pos in positions.items()
        if sector_map.get(sym) == sector
    )
    
    new_total = current_sector_value + additional_amount
    new_pct = new_total / nav
    
    return new_pct <= MAX_SECTOR_EXPOSURE


def run_risk_sizing(debate_results: dict, macro_result: dict) -> list:
    """Entry point Tầng 4: Sinh danh sách lệnh thực thi."""
    print(f"\n{'='*60}")
    print(f"📐 TẦNG 4: RỦI RO & POSITION SIZING")
    print(f"{'='*60}")
    
    portfolio = load_portfolio()
    nav = portfolio.get("portfolio_value", 1_000_000_000)
    cash = portfolio.get("cash_balance", nav)
    current_positions = portfolio.get("positions", {})
    sector_map = get_sector_map()
    
    open_slots = MAX_POSITIONS - len(current_positions)
    print(f"  💰 NAV: {nav:,.0f} đ | Cash: {cash:,.0f} đ | Vị thế trống: {open_slots}")
    
    # 🧠 ML Enhancement: Chạy mô phỏng Monte Carlo 5,000 kịch bản & HRP Allocator
    from ml_algorithms import run_monte_carlo_portfolio, hierarchical_risk_parity
    mc_results = run_monte_carlo_portfolio(portfolio, {})
    if "var_95_vnd" in mc_results:
        print(f"  🎲 Monte Carlo (5,000 kịch bản 10 ngày):")
        print(f"     • VaR 95%  : {mc_results['var_95_vnd']:,.0f} đ (Tổn thất tối đa: {mc_results['var_95_pct']:.2f}%)")
        print(f"     • CVaR 95% : {mc_results['cvar_95_vnd']:,.0f} đ (Kịch bản xấu nhất 5%: {mc_results['cvar_95_pct']:.2f}%)")
        print(f"     • Xác suất sinh lời: {mc_results['portfolio_win_prob']:.1f}% | Rủi ro Drawdown >5%: {mc_results['drawdown_5pct_risk']:.1f}%")
        print(f"     • Tỷ lệ Kelly tối ưu: {mc_results['optimal_kelly_fraction']:.1f}% vốn")
        
    # 🛡️ Phân bổ rủi ro phân cấp HRP cho danh mục hiện tại
    if current_positions:
        sym_list = list(current_positions.keys())
        dummy_cov = np.eye(len(sym_list)) * 0.04 + np.ones((len(sym_list), len(sym_list))) * 0.01
        hrp_weights = hierarchical_risk_parity(dummy_cov, sym_list)
        hrp_str = ", ".join([f"{s}: {w:.1f}%" for s, w in hrp_weights.items()])
        print(f"  🛡️ Tỷ trọng HRP tối ưu rủi ro: {hrp_str}")
    
    if open_slots <= 0:
        print("  ⚠️ Danh mục đầy (5/5 vị thế). Không mở thêm lệnh mới.")
        return []
    
    # Lọc và sắp xếp theo consensus_score
    candidates = [
        r for sym, r in debate_results.items()
        if r["verdict"] in ["STRONG_BUY", "BUY"]
        and r["consensus_score"] >= MIN_CONSENSUS_TO_TRADE
        and sym not in current_positions
    ]
    candidates.sort(key=lambda x: x["consensus_score"], reverse=True)
    
    approved_orders = []
    
    for c in candidates[:open_slots]:
        sym = c["symbol"]
        sector = sector_map.get(sym, "Unknown")
        consensus = c["consensus_score"]
        entry_price = c.get("entry_price", 0)
        
        if entry_price <= 0:
            continue
        
        # Tính kích thước vị thế theo confidence
        alloc_amount = confidence_weighted_size(consensus, nav)
        alloc_amount = min(alloc_amount, cash)  # Không vượt tiền mặt
        
        if alloc_amount < 10_000_000:  # Tối thiểu 10 triệu
            print(f"  ⚠️ {sym}: Không đủ tiền mặt dự phòng (Cần 10tr+)")
            continue
        
        # Kiểm tra tập trung ngành
        if not check_sector_concentration(portfolio, sector, alloc_amount, sector_map):
            print(f"  ⚠️ {sym}: Ngành {sector} đã đạt ngưỡng 30% NAV, bỏ qua")
            continue
        
        # Làm tròn xuống theo lô 100 CP
        quantity = int(alloc_amount / entry_price / 100) * 100
        if quantity <= 0:
            continue
        
        actual_amount = quantity * entry_price
        
        # Stop Loss và Take Profit từ Debate Council
        stop_loss = c.get("stop_loss") or entry_price * 0.94
        take_profit = c.get("target_price") or entry_price * 1.15
        rr = c.get("rr_ratio", 0)
        
        # Chỉ chấp nhận R:R >= 2.0
        if rr and rr < 2.0:
            print(f"  ⚠️ {sym}: R:R {rr:.1f} < 2.0, bỏ qua")
            continue
        
        order = {
            "symbol": sym,
            "sector": sector,
            "action": "BUY",
            "quantity": quantity,
            "entry_price": entry_price,
            "amount": actual_amount,
            "stop_loss": round(stop_loss, -2),
            "take_profit": round(take_profit, -2),
            "rr_ratio": rr,
            "consensus_score": consensus,
            "size_pct": round(actual_amount / nav * 100, 1),
            "bull_args": c["bull"]["arguments"][:2],
            "bear_args": c["bear"]["arguments"][:1],
        }
        
        approved_orders.append(order)
        cash -= actual_amount
        
        print(f"  ✅ APPROVED: {sym} ({sector})")
        print(f"     Consensus {consensus}/100 | KL: {quantity:,} CP | Giá: {entry_price:,.0f}đ")
        print(f"     Giải ngân: {actual_amount/1e6:.1f}tr ({order['size_pct']}% NAV) | R:R: {rr:.1f}")
        print(f"     SL: {order['stop_loss']:,.0f}đ | TP: {order['take_profit']:,.0f}đ")
    
    print(f"\n  📋 Tổng lệnh phê duyệt: {len(approved_orders)}")
    return approved_orders
