"""
optimize_agent.py
──────────────────────────────────────────────────────────────────────
Tối ưu hóa 10 Vòng (10-Iteration Optimization Loop) trong khung điểm từ 40.0 đến 50.0
để đánh giá hiệu năng khi mở rộng tần suất vào lệnh.
"""
import os
import sys
import gc
from datetime import datetime, timedelta
from argparse import Namespace
import pandas as pd

from backtest.data import load_all
from paper_trading import PaperTradingJournal
from paper_metrics import compute
from paper_runner import cmd_seed

sys.stdout.reconfigure(encoding="utf-8")

symbols = ["FPT", "HPG", "VNM", "MBB", "SSI", "TCB", "VHM", "MWG"]
print("🚀 Bắt đầu Vòng lặp Học hỏi & Tối ưu hóa 10 Iterations (Khung điểm 40 - 50)...")

# Đảm bảo có cache
dataset = load_all(symbols)
if not dataset:
    print("❌ Chưa có cache. Đang tải...")
    from backtest.data import download
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    download(symbols, start_date, end_date)

iterations = [
    {"loop": 1, "buy_threshold": 40.0, "stride": 2, "note": "Ngưỡng điểm vào lệnh 40.0"},
    {"loop": 2, "buy_threshold": 41.0, "stride": 2, "note": "Ngưỡng điểm vào lệnh 41.0"},
    {"loop": 3, "buy_threshold": 42.0, "stride": 2, "note": "Ngưỡng điểm vào lệnh 42.0"},
    {"loop": 4, "buy_threshold": 43.0, "stride": 2, "note": "Ngưỡng điểm vào lệnh 43.0"},
    {"loop": 5, "buy_threshold": 44.0, "stride": 2, "note": "Ngưỡng điểm vào lệnh 44.0"},
    {"loop": 6, "buy_threshold": 45.0, "stride": 2, "note": "Ngưỡng điểm vào lệnh 45.0"},
    {"loop": 7, "buy_threshold": 46.0, "stride": 2, "note": "Ngưỡng điểm vào lệnh 46.0"},
    {"loop": 8, "buy_threshold": 47.0, "stride": 2, "note": "Ngưỡng điểm vào lệnh 47.0"},
    {"loop": 9, "buy_threshold": 48.0, "stride": 2, "note": "Ngưỡng điểm vào lệnh 48.0"},
    {"loop": 10, "buy_threshold": 50.0, "stride": 2, "note": "Ngưỡng điểm vào lệnh 50.0"},
]

results = []

for item in iterations:
    loop_num = item["loop"]
    db_temp = f"paper_temp_loop_{loop_num}.db"
    if os.path.exists(db_temp):
        try:
            os.remove(db_temp)
        except Exception:
            pass
    
    args = Namespace(
        db=db_temp,
        symbols=",".join(symbols),
        min_history=30,
        stride=item["stride"],
        buy_threshold=item["buy_threshold"]
    )
    
    cmd_seed(args)
    
    journal = PaperTradingJournal(db_temp)
    trades = journal.all_trades()
    perf = compute(trades)
    
    if perf is not None:
        closed = perf.n_trades
        win_rate = perf.win_rate * 100
        expectancy = perf.expectancy
        max_dd = perf.max_drawdown_pct
        net_ret = perf.total_net_pct
    else:
        closed, win_rate, expectancy, max_dd, net_ret = 0, 0, 0, 0, 0

    results.append({
        "loop": loop_num,
        "note": item["note"],
        "buy_threshold": item["buy_threshold"],
        "stride": item["stride"],
        "closed_trades": closed,
        "win_rate": win_rate,
        "expectancy": expectancy,
        "max_dd": max_dd,
        "net_return": net_ret
    })
    
    journal.db.close()
    del journal
    gc.collect()
    if os.path.exists(db_temp):
        try:
            os.remove(db_temp)
        except Exception:
            pass

df_res = pd.DataFrame(results)
print("\n" + "="*80)
print("📊 BẢNG KẾT QUẢ TỐI ƯU HÓA 10 VÒNG HỌC HỎI CỦA AGENT (KHUNG ĐIỂM 40 - 50)")
print("="*80)
for _, r in df_res.iterrows():
    print(f"Vòng {r['loop']:02d} | Threshold={r['buy_threshold']} | Lệnh đóng: {r['closed_trades']:03d} | Thắng: {r['win_rate']:.1f}% | Kỳ vọng: {r['expectancy']:+.2f}% | MaxDD: {r['max_dd']:.1f}% | Lãi ròng: {r['net_return']:+.2f}% | ({r['note']})")

# Lọc chỉ các vòng có lệnh đóng phát sinh thực tế
active_df = df_res[df_res["closed_trades"] > 0]
if not active_df.empty:
    best_row = active_df.sort_values(by="expectancy", ascending=False).iloc[0]
else:
    best_row = df_res.iloc[0]

print("\n" + "🏆"*25)
print(" VÒNG TỐI ƯU HÓA XUẤT SẮC NHẤT KHUNG ĐIỂM 40 - 50:")
print(f"-> Vòng {best_row['loop']:02d} ({best_row['note']})")
print(f"-> Ngưỡng mua tối ưu: {best_row['buy_threshold']} điểm")
print(f"-> Tổng lệnh đóng thực hiện: {best_row['closed_trades']} lệnh")
print(f"-> Tỷ lệ thắng: {best_row['win_rate']:.1f}%")
print(f"-> Kỳ vọng/lệnh: {best_row['expectancy']:+.2f}%")
print(f"-> Lợi nhuận cộng dồn: {best_row['net_return']:+.2f}%")
print("🏆"*25 + "\n")

# Áp dụng bộ tham số tốt nhất vào paper_trades.db chính thức!
print("⚡ Nạp bộ tham số tối ưu chiến thắng vào sổ lệnh chính thức paper_trades.db...")
if os.path.exists("paper_trades.db"):
    try:
        os.remove("paper_trades.db")
    except Exception:
        pass

best_args = Namespace(
    db="paper_trades.db",
    symbols=",".join(symbols),
    min_history=30,
    stride=best_row["stride"],
    buy_threshold=best_row["buy_threshold"]
)
cmd_seed(best_args)
print("✅ Đã cập nhật Sổ lệnh chính thức với tham số tối ưu khung điểm 40 - 50 thành công!")
