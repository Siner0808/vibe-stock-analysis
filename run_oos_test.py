"""
run_oos_test.py
──────────────────────────────────────────────────────────────────────
OUT-OF-SAMPLE (OOS) VERIFICATION SCRIPT:
Kiểm chứng Khách quan trên Khoảng Thời gian Chưa từng dùng Tối ưu:
Thời gian: 2024-07-01 đến 2025-06-30 (12 Tháng Hoàn toàn Mới)
Rổ chứng khoán: VN50 Universe
Tham số Cố định: Threshold = 51.0 điểm (Không chỉnh sửa, Giữ nguyên 100%)
"""

import os
import sys
import gc
from datetime import datetime
from argparse import Namespace
import pandas as pd

from backtest.data import download, load_all
from paper_trading import PaperTradingJournal
from paper_metrics import compute, report
from paper_runner import cmd_seed
from vn50_symbols import VN50_SYMBOLS

sys.stdout.reconfigure(encoding="utf-8")

symbols = VN50_SYMBOLS
start_date = "2024-07-01"
end_date = "2025-06-30"
INITIAL_CAPITAL = 1_000_000_000  # 1 Tỷ VNĐ

print("="*90)
print(f"🔬 KIỂM CHỨNG OUT-OF-SAMPLE (OOS) TRÊN DỮ LIỆU MỚI TOÀN DIỆN ({start_date} -> {end_date})")
print(f"📌 Rổ cổ phiếu: VN50 Universe ({len(symbols)} mã thanh khoản hàng đầu)")
print("📌 Tham số chiến lược: CỐ ĐỊNH HOÀN TOÀN (Threshold = 51.0 điểm, 5 Quy tắc Định lượng Cấu trúc)")
print("="*90)

print("\n📥 Đang tải dữ liệu Out-of-Sample 12 tháng (2024-07-01 -> 2025-06-30)...")
download(symbols, start_date, end_date)

db_oos = "paper_oos_2024_2025.db"
if os.path.exists(db_oos):
    try: os.remove(db_oos)
    except Exception: pass

args = Namespace(
    db=db_oos,
    symbols=",".join(symbols),
    min_history=30,
    stride=2,
    buy_threshold=51.0
)

print("\n🚀 Đang chạy mô phỏng giao dịch Out-of-Sample...")
cmd_seed(args)

journal = PaperTradingJournal(db_oos)
trades = journal.all_trades()
perf = compute(trades)

print("\n" + "="*90)
print("📊 BÁO CÁO HIỆU NĂNG OUT-OF-SAMPLE (OOS) THỜI GIAN UNSEEN 2024-07 -> 2025-06:")
print("="*90)
print(report(trades))

if perf is not None and perf.n_trades > 0:
    final_cap = INITIAL_CAPITAL * (1.0 + perf.total_net_pct / 100.0)
    net_vnd = final_cap - INITIAL_CAPITAL
    sign = "+" if net_vnd >= 0 else ""
    print("\n" + "🏆"*35)
    print(" KẾT QUẢ TÀI SẢN THỰC TẾ OOS (VỐN 1 TỶ ĐỒNG):")
    print(f"-> Tổng số lệnh giao dịch đóng: {perf.n_trades} lệnh")
    print(f"-> Tỷ lệ thắng (Win Rate): {perf.win_rate*100:.1f}%")
    print(f"-> Kỳ vọng lợi nhuận / lệnh: {perf.expectancy:+.2f}%")
    print(f"-> Lợi nhuận ròng tổng danh mục: {perf.total_net_pct:+.2f}% ({sign}{net_vnd:,.0f} VNĐ)")
    print(f"-> Sụt giảm tài sản tối đa (MaxDD): {perf.max_drawdown_pct:.1f}%")
    print(f"-> Giá trị tài sản cuối kỳ: {final_cap:,.0f} VNĐ")
    print("🏆"*35 + "\n")

journal.db.close()
