"""
run_vn100_18m_test.py
──────────────────────────────────────────────────────────────────────
MÔ PHỎNG 18 THÁNG GẦN NHẤT TRÊN RỔ VN100 UNIVERSE (547 NGÀY LỊCH SỬ)
Vốn khởi điểm: 1,000,000,000 VNĐ
Tham số: Threshold = 51.0 điểm, 5 Quy tắc Định lượng Cấu trúc
"""

import os
import sys
import gc
from datetime import datetime, timedelta
from argparse import Namespace
import pandas as pd

from backtest.data import download, load_all
from paper_trading import PaperTradingJournal
from paper_metrics import compute, report
from paper_runner import cmd_seed
from vn100_symbols import VN100_SYMBOLS

sys.stdout.reconfigure(encoding="utf-8")

symbols = VN100_SYMBOLS
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=547)).strftime("%Y-%m-%d") # 18 tháng
INITIAL_CAPITAL = 1_000_000_000  # 1 Tỷ VNĐ

print("="*90)
print(f"🔥 KIỂM CHỨNG BẮT BỘ 18 THÁNG GẦN NHẤT ({start_date} -> {end_date}) TRÊN RỔ VN100")
print(f"📌 Rổ cổ phiếu: VN100 Universe ({len(symbols)} mã thanh khoản hàng đầu)")
print("📌 Tham số chiến lược: FROZEN (Buy Threshold = 51.0 điểm, 5 Quy tắc Định lượng Cấu trúc)")
print("="*90)

print(f"\n📥 Kiểm tra/Tải dữ liệu 18 tháng lịch sử cho {len(symbols)} cổ phiếu VN100...")
download(symbols, start_date, end_date)

db_vn100 = "paper_vn100_18m.db"
if os.path.exists(db_vn100):
    try: os.remove(db_vn100)
    except Exception: pass

args = Namespace(
    db=db_vn100,
    symbols=",".join(symbols),
    min_history=30,
    stride=2,
    buy_threshold=51.0
)

print("\n🚀 Đang chạy mô phỏng 18 tháng VN100...")
cmd_seed(args)

journal = PaperTradingJournal(db_vn100)
trades = journal.all_trades()
perf = compute(trades)

print("\n" + "="*90)
print("📊 BÁO CÁO HIỆU NĂNG 18 THÁNG RỔ VN100:")
print("="*90)
print(report(trades))

if perf is not None and perf.n_trades > 0:
    final_cap = INITIAL_CAPITAL * (1.0 + perf.total_net_pct / 100.0)
    net_vnd = final_cap - INITIAL_CAPITAL
    sign = "+" if net_vnd >= 0 else ""
    print("\n" + "🏆"*35)
    print(" KẾT QUẢ TÀI SẢN MÔ PHỎNG 18 THÁNG VN100 (VỐN 1 TỶ ĐỒNG):")
    print(f"-> Tổng số lệnh giao dịch đóng: {perf.n_trades} lệnh")
    print(f"-> Tỷ lệ thắng (Win Rate): {perf.win_rate*100:.1f}%")
    print(f"-> Mức Lãi TB / Lệnh Thắng: {perf.avg_win:+.2f}%")
    print(f"-> Mức Lỗ TB / Lệnh Lỗ: {perf.avg_loss:+.2f}%")
    print(f"-> Kỳ vọng lợi nhuận / lệnh: {perf.expectancy:+.2f}%")
    print(f"-> Profit Factor (Hệ số sinh lời): {perf.profit_factor:.2f}")
    print(f"-> Lợi nhuận ròng tổng danh mục: {perf.total_net_pct:+.2f}% ({sign}{net_vnd:,.0f} VNĐ)")
    print(f"-> Sụt giảm tài sản tối đa (MaxDD): {perf.max_drawdown_pct:.1f}%")
    print(f"-> Giá trị tài sản cuối kỳ: {final_cap:,.0f} VNĐ")
    print("🏆"*35 + "\n")

journal.db.close()
