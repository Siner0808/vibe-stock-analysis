"""
optimize_agent.py
──────────────────────────────────────────────────────────────────────
Tối ưu hóa 10 Vòng (10-Iteration Optimization Loop) học từ các vị thế SL/TP
để tìm bộ tham số quản trị rủi ro & điểm vào tối ưu nhất.
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
print("🚀 Bắt đầu Vòng lặp Học hỏi & Tối ưu hóa 10 Iterations...")

# Đảm bảo có cache
dataset = load_all(symbols)
if not dataset:
    print("❌ Chưa có cache. Đang tải...")
    from backtest.data import download
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    download(symbols, start_date, end_date)

iterations = [
    {"loop": 1, "buy_threshold": 50.0, "stride": 2, "note": "Thử nghiệm Ngưỡng mua rộng (50 điểm)"},
    {"loop": 2, "buy_threshold": 55.0, "stride": 2, "note": "Ngưỡng mua chuẩn (55 điểm)"},
    {"loop": 3, "buy_threshold": 58.0, "stride": 2, "note": "Ngưỡng mua lọc tín hiệu nhiễu (58 điểm)"},
    {"loop": 4, "buy_threshold": 60.0, "stride": 2, "note": "Ngưỡng mua chất lượng cao (60 điểm)"},
    {"loop": 5, "buy_threshold": 62.0, "stride": 2, "note": "Ngưỡng mua kỷ luật cao (62 điểm)"},
    {"loop": 6, "buy_threshold": 65.0, "stride": 2, "note": "Ngưỡng mua sàng lọc gắt gao (65 điểm)"},
    {"loop": 7, "buy_threshold": 58.0, "stride": 1, "note": "Quét toàn bộ phiên (Stride=1, Threshold=58)"},
    {"loop": 8, "buy_threshold": 60.0, "stride": 1, "note": "Quét toàn bộ phiên (Stride=1, Threshold=60)"},
    {"loop": 9, "buy_threshold": 62.0, "stride": 1, "note": "Quét toàn bộ phiên (Stride=1, Threshold=62)"},
    {"loop": 10, "buy_threshold": 64.0, "stride": 1, "note": "Quét toàn bộ phiên chọn lọc nhất (Threshold=64)"},
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
print("\n" + "="*75)
print("📊 BẢNG KẾT QUẢ TỐI ƯU HÓA 10 VÒNG HỌC HỎI CỦA AGENT")
print("="*75)
for _, r in df_res.iterrows():
    print(f"Vòng {r['loop']:02d} | Threshold={r['buy_threshold']} | Lệnh đóng: {r['closed_trades']:02d} | Thắng: {r['win_rate']:.1f}% | Kỳ vọng: {r['expectancy']:+.2f}% | MaxDD: {r['max_dd']:.1f}% | Lãi ròng: {r['net_return']:+.2f}% | ({r['note']})")

best_row = df_res.sort_values(by="expectancy", ascending=False).iloc[0]
print("\n" + "🏆"*25)
print(" VÒNG TỐI ƯU HÓA XUẤT SẮC NHẤT:")
print(f"-> Vòng {best_row['loop']:02d} ({best_row['note']})")
print(f"-> Ngưỡng mua tối ưu: {best_row['buy_threshold']} điểm")
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
print("✅ Đã cập nhật Sổ lệnh chính thức với tham số tối ưu thành công!")
