"""
walkforward_vn100.py
──────────────────────────────────────────────────────────────────────
Tối ưu hóa chiến lược bằng phương pháp Walk-Forward (12 tháng In-Sample / 6 tháng Out-Of-Sample)
Dữ liệu: 18 tháng (1 năm In-Sample, 6 tháng Out-Of-Sample)
Vốn khởi điểm: 1,000,000,000 VNĐ
Mục tiêu: Ngăn chặn Look-Ahead Bias, tìm kiếm tham số thực sự robust.
"""

import os
import sys
import gc
from datetime import datetime, timedelta
import pandas as pd

from backtest.data import download, load_all
from paper_trading import PaperTradingJournal
from paper_metrics import compute
from paper_runner import run_session
from vn100_symbols import VN100_SYMBOLS

sys.stdout.reconfigure(encoding="utf-8")

INITIAL_CAPITAL = 1_000_000_000  # 1 Tỷ VNĐ
symbols = VN100_SYMBOLS

# Time ranges
now = datetime.now()
end_date = now.strftime("%Y-%m-%d")
split_date = (now - timedelta(days=182)).strftime("%Y-%m-%d") # 6 tháng OOS
start_date = (now - timedelta(days=547)).strftime("%Y-%m-%d") # Tổng 18 tháng

os.environ["POST_MORTEM_ENABLED"] = "1"
MEMORY_FILE = "sl_pattern_memory.json"
if os.path.exists(MEMORY_FILE):
    try: os.remove(MEMORY_FILE)
    except Exception: pass

print(f"💰 Khởi tạo Danh mục VN100 (18 Tháng Continuous Learning): 1,000,000,000 VNĐ ({len(symbols)} mã)")
print(f"📅 GIAI ĐOẠN HỌC MẪU HÌNH (Train): {start_date} -> {split_date} (12 tháng)")
print(f"📅 GIAI ĐOẠN KIỂM ĐỊNH THỰC TẾ (OOS): {split_date} -> {end_date} (6 tháng)")
print("🚀 Bắt đầu Continuous Learning & Testing với Post-Mortem Memory Agent...")

# Tải dữ liệu toàn bộ 18 tháng một lần
download(symbols, start_date, end_date)
dataset = load_all(symbols)
if not dataset:
    print("❌ Lỗi: Không thể tải dữ liệu")
    sys.exit(1)

STRIDE = 2
MIN_HISTORY = 30
BUY_THRESHOLD = 50.0

def run_simulation(sim_start, sim_end, threshold, db_name):
    if os.path.exists(db_name):
        try: os.remove(db_name)
        except Exception: pass
    
    journal = PaperTradingJournal(db_name)
    total = {"opened": 0, "closed": 0}
    
    for i, (sym, df) in enumerate(sorted(dataset.items()), 1):
        df_time = df['time'].astype(str)
        n = len(df)
        for t in range(MIN_HISTORY, n, STRIDE):
            t_date = df_time.iloc[t]
            if t_date < sim_start:
                continue
            if t_date > sim_end:
                break
                
            row = df.iloc[t]
            history = df.iloc[: t + 1]
            s = run_session(journal, sym, history,
                            {"open": float(row["open"]), "high": float(row["high"]),
                             "low": float(row["low"]), "close": float(row["close"])},
                            str(row["time"]), buy_threshold=threshold)
            total["opened"] += s["opened"]
            total["closed"] += s["closed"]
            
    trades = journal.all_trades()
    perf = compute(trades)
    journal.db.close()
    del journal
    gc.collect()
    
    return perf, trades

print("\n" + "="*80)
print("PHASE 1: CONTINUOUS LEARNING (Chạy 18 tháng liền mạch với Memory Loop)")
print("="*80)

db_full = "paper_full_learning.db"
perf_full, trades_full = run_simulation(start_date, end_date, BUY_THRESHOLD, db_full)

# Đọc lại memory để xem học được bao nhiêu mẫu hình
memory_count = 0
if os.path.exists(MEMORY_FILE):
    try:
        import json
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            memory_count = len(data)
    except Exception: pass

print(f"\n🧠 AI đã ghi nhớ thành công {memory_count} mẫu hình dính Cắt lỗ (SL Patterns) trong quá trình giao dịch!")

# Phân tách kết quả cho giai đoạn Out-Of-Sample (6 tháng cuối)
print("\n" + "="*80)
print("PHASE 2: KẾT QUẢ KIỂM ĐỊNH OUT-OF-SAMPLE (6 Tháng Cuối)")
print("="*80)

# Lọc các lệnh đã đóng trong khoảng 6 tháng cuối (split_date -> end_date)
oos_trades = [t for t in trades_full if t.status == "CLOSED" and t.exit_date and t.exit_date >= split_date]
perf_oos = compute(oos_trades)

if perf_oos is not None and perf_oos.n_trades > 0:
    win_rate = perf_oos.win_rate * 100
    final_capital = INITIAL_CAPITAL * (1.0 + perf_oos.total_net_pct / 100.0)
    net_profit = final_capital - INITIAL_CAPITAL
    
    print("\n" + "📊"*25)
    print(" KẾT QUẢ NGOÀI MẪU (OUT-OF-SAMPLE) VỚI MEMORY LOOP:")
    print(f"-> Ngưỡng áp dụng: {BUY_THRESHOLD} điểm (Cố định)")
    print(f"-> Tổng số lệnh đóng trong OOS: {perf_oos.n_trades} lệnh")
    print(f"-> Tỷ lệ thắng: {win_rate:.1f}%")
    print(f"-> Kỳ vọng lợi nhuận / lệnh: {perf_oos.expectancy:+.2f}%")
    print(f"-> Mức sụt giảm tối đa (MaxDD): {perf_oos.max_drawdown_pct:.1f}%")
    print(f"-> GIÁ TRỊ TÀI SẢN CUỐI KỲ (OOS): {final_capital:,.0f} VNĐ")
    sign = "+" if net_profit >= 0 else ""
    print(f"-> LỢI NHUẬN RÒNG THỰC TẾ (OOS): {sign}{net_profit:,.0f} VNĐ ({perf_oos.total_net_pct:+.2f}%)")
    print("📊"*25 + "\n")
    
    # Benchmarking OOS
    from paper_runner import build_benchmark
    from paper_metrics import report as build_report
    bench = build_benchmark(oos_trades, dataset)
    print("\nBÁO CÁO CHI TIẾT OOS (6 THÁNG CUỐI):")
    print(build_report(oos_trades, bench))
else:
    print("❌ Out-Of-Sample không có lệnh nào được đóng trong khoảng thời gian này.")
    
print(f"\n✅ Đã lưu toàn bộ sổ lệnh vào {db_full}")
