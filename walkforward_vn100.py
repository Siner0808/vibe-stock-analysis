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

print(f"💰 Khởi tạo Danh mục VN100 (18 Tháng Lịch sử): 1,000,000,000 VNĐ ({len(symbols)} mã)")
print(f"📅 IN-SAMPLE (Train): {start_date} -> {split_date} (12 tháng)")
print(f"📅 OUT-OF-SAMPLE (Test): {split_date} -> {end_date} (6 tháng)")
print("🚀 Bắt đầu Walk-Forward Testing...")

# Tải dữ liệu toàn bộ 18 tháng một lần
download(symbols, start_date, end_date)
dataset = load_all(symbols)
if not dataset:
    print("❌ Lỗi: Không thể tải dữ liệu")
    sys.exit(1)

STRIDE = 2
MIN_HISTORY = 30
thresholds = [45.0, 48.0, 50.0, 52.0, 55.0, 58.0, 60.0]

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
print("PHASE 1: IN-SAMPLE OPTIMIZATION (Tìm ngưỡng tối ưu)")
print("="*80)

results_is = []
best_perf = None
best_th = None
best_final_cap = -1

for th in thresholds:
    print(f"🔄 Đang chạy In-Sample với ngưỡng {th}...")
    db_temp = f"temp_is_{th}.db"
    perf, _ = run_simulation(start_date, split_date, th, db_temp)
    
    if os.path.exists(db_temp):
        try: os.remove(db_temp)
        except Exception: pass
        
    if perf is not None and perf.n_trades > 0:
        win_rate = perf.win_rate * 100
        final_capital = INITIAL_CAPITAL * (1.0 + perf.total_net_pct / 100.0)
        net_profit = final_capital - INITIAL_CAPITAL
        
        print(f"   => Th={th} | Lệnh={perf.n_trades} | Thắng={win_rate:.1f}% | Lãi={net_profit:,.0f} VNĐ")
        
        if final_capital > best_final_cap:
            best_final_cap = final_capital
            best_th = th
            best_perf = perf
            
    else:
        print(f"   => Th={th} | Không có lệnh giao dịch")

if best_th is None:
    print("❌ In-Sample không tìm thấy ngưỡng nào có lợi nhuận/lệnh.")
    sys.exit(1)

print("\n" + "🏆"*25)
print(f"🔥 KẾT QUẢ IN-SAMPLE: CHỌN NGƯỠNG MUA TỐI ƯU LÀ {best_th}")
print(f"   Lợi nhuận ròng in-sample: {best_final_cap - INITIAL_CAPITAL:,.0f} VNĐ")
print("🏆"*25 + "\n")

print("="*80)
print("PHASE 2: OUT-OF-SAMPLE TESTING (Kiểm định thực tế mù)")
print("="*80)
print(f"🔄 Đang chạy Out-Of-Sample với ngưỡng tối ưu {best_th} trên tập dữ liệu hoàn toàn mới...")

db_oos = "paper_oos_vn100.db"
perf_oos, trades_oos = run_simulation(split_date, end_date, best_th, db_oos)

if perf_oos is not None and perf_oos.n_trades > 0:
    win_rate = perf_oos.win_rate * 100
    final_capital = INITIAL_CAPITAL * (1.0 + perf_oos.total_net_pct / 100.0)
    net_profit = final_capital - INITIAL_CAPITAL
    
    print("\n" + "📊"*25)
    print(" KẾT QUẢ NGOÀI MẪU (OUT-OF-SAMPLE) - CHỈ SỐ SỰ THẬT:")
    print(f"-> Ngưỡng áp dụng: {best_th} điểm (Bê nguyên từ In-Sample)")
    print(f"-> Tổng số lệnh đóng: {perf_oos.n_trades} lệnh")
    print(f"-> Tỷ lệ thắng: {win_rate:.1f}%")
    print(f"-> Kỳ vọng lợi nhuận / lệnh: {perf_oos.expectancy:+.2f}%")
    print(f"-> Mức sụt giảm tối đa (MaxDD): {perf_oos.max_drawdown_pct:.1f}%")
    print(f"-> GIÁ TRỊ TÀI SẢN CUỐI KỲ: {final_capital:,.0f} VNĐ")
    sign = "+" if net_profit >= 0 else ""
    print(f"-> LỢI NHUẬN RÒNG THỰC TẾ: {sign}{net_profit:,.0f} VNĐ ({perf_oos.total_net_pct:+.2f}%)")
    print("📊"*25 + "\n")
    
    # Benchmarking OOS
    from paper_runner import build_benchmark
    from paper_metrics import report as build_report
    bench = build_benchmark(trades_oos, dataset)
    print("\nBÁO CÁO CHI TIẾT OOS:")
    print(build_report(trades_oos, bench))
else:
    print("❌ Out-Of-Sample không có lệnh nào được thực thi. Chiến lược quá khắt khe.")
    
print(f"\n✅ Đã lưu kết quả Out-Of-Sample vào {db_oos}")
