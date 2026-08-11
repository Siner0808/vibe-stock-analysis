"""
evaluate_custom71_results.py
──────────────────────────────────────────────────────────────────────
Đọc và tính toán ngay kết quả 10 Vòng lặp từ 10 file SQLite đã chạy xong.
"""
import os
import sys
from paper_trading import PaperTradingJournal
from paper_metrics import compute

sys.stdout.reconfigure(encoding="utf-8")

thresholds = [42.0, 44.0, 46.0, 48.0, 50.0, 52.0, 54.0, 56.0, 58.0, 60.0]

print("=" * 95)
print(f"📊 BÁO CÁO KẾT QUẢ TỐI ƯU HÓA 10 VÒNG LẶP (DANH MỤC 16 NGÀNH - 71 MÃ - 18 THÁNG)")
print("=" * 95)
print(f"{'Vòng':<6}{'Ngưỡng Mua':<12}{'Số Lệnh':<10}{'Lợi Nhuận (%)':<18}{'Giá Trị Cuối (Tỷ)':<20}{'Thắng (%)':<12}{'ProfitFactor':<14}{'MaxDD (%)':<10}")
print("-" * 95)

best_pnl = -999.0
best_item = None

for loop_num, th in enumerate(thresholds, 1):
    db_file = f"paper_custom71_18m_loop_{loop_num}.db"
    if not os.path.exists(db_file):
        print(f"Vòng {loop_num:<2d}   Không tìm thấy file {db_file}")
        continue

    journal = PaperTradingJournal(db_file)
    trades = journal.all_trades()
    m = compute(trades)

    if m is None:
        print(f"Vòng {loop_num:<2d}   {th:<10.1f}  0 lệnh")
        continue

    closed = len([t for t in trades if t.status == "CLOSED"])
    pnl = m.total_net_pct
    initial_cap = 1_000_000_000
    final_eq = initial_cap * (1.0 + pnl / 100.0)
    wr = m.win_rate * 100.0
    pf = m.profit_factor
    mdd = m.max_drawdown_pct

    if pnl > best_pnl:
        best_pnl = pnl
        best_item = {
            "loop": loop_num,
            "threshold": th,
            "closed": closed,
            "pnl": pnl,
            "final_equity": final_eq,
            "win_rate": wr,
            "profit_factor": pf,
            "max_dd": mdd
        }

    pnl_str = f"{pnl:+.2f}%"
    eq_str = f"{final_eq / 1e9:.3f} Tỷ VNĐ"
    print(f"Vòng {loop_num:<2d}   {th:<10.1f}  {closed:<8d}  {pnl_str:<16}  {eq_str:<18}  {wr:<10.1f}  {pf:<12.2f}  {mdd:<8.1f}")

print("=" * 95)

if best_item:
    print(f"\n🏆 VÒNG LẶP XUẤT SẮC NHẤT TRÊN DANH MỤC 71 MÃ:")
    print(f"   - Ngưỡng mua tối ưu: {best_item['threshold']:.1f} điểm")
    print(f"   - Tổng lợi nhuận: {best_item['pnl']:+.2f}% ({best_item['final_equity']/1e9:.3f} Tỷ VNĐ từ 1 Tỷ ban đầu)")
    print(f"   - Tỷ lệ thắng (Win Rate): {best_item['win_rate']:.1f}%")
    print(f"   - Chỉ số Profit Factor: {best_item['profit_factor']:.2f}")
    print(f"   - Sức chịu đựng rủi ro (Max Drawdown): {best_item['max_dd']:.1f}%")
    print("=" * 95)
