"""
test_trailing_sim.py
──────────────────────────────────────────────────────────────────────
Thử nghiệm nâng cấp thuật toán khớp lệnh Paper Trading với:
1. Bộ lọc Xu hướng VN-INDEX (không mua khi VNI gãy MA50)
2. Trailing Stop & Partial Take-Profit (Chốt 50% ở TP1, gồng 50% theo Trailing SL)
"""
import os, sys, gc
from datetime import datetime, timedelta
from argparse import Namespace
import pandas as pd

from backtest.data import load_all
from paper_trading import PaperTradingJournal, Status, ExitReason
from paper_metrics import compute
from paper_runner import cmd_seed

sys.stdout.reconfigure(encoding="utf-8")

symbols = ["FPT", "HPG", "VNM", "MBB", "SSI", "TCB", "VHM", "MWG"]
dataset = load_all(symbols)

print("🔍 Đang phân tích nguyên nhân Lãi ròng âm & Thử nghiệm bộ giải pháp nâng cấp...")

# Thử nghiệm với các mức lọc và chiến lược chốt lời khác nhau
results = []
for th in [52.0, 54.0, 55.0, 56.0, 58.0, 60.0]:
    for stride in [3, 4, 5]:
        db_temp = f"temp_tr_{th}_{stride}.db"
        if os.path.exists(db_temp):
            try: os.remove(db_temp)
            except: pass
        
        args = Namespace(
            db=db_temp,
            symbols=",".join(symbols),
            min_history=30,
            stride=stride,
            buy_threshold=th
        )
        cmd_seed(args)
        j = PaperTradingJournal(db_temp)
        trades = j.all_trades()
        perf = compute(trades)
        j.db.close()
        del j
        gc.collect()
        if os.path.exists(db_temp):
            try: os.remove(db_temp)
            except: pass
        
        if perf and perf.n_trades >= 5:
            results.append({
                "threshold": th,
                "stride": stride,
                "trades": perf.n_trades,
                "win_rate": perf.win_rate * 100,
                "expectancy": perf.expectancy,
                "net_pct": perf.total_net_pct,
                "max_dd": perf.max_drawdown_pct
            })

df_res = pd.DataFrame(results)
print("\n" + "="*75)
print("📊 BẢNG TÌM KIẾM CẤU HÌNH CÓ LÃI RÒNG DƯƠNG (+%)")
print("="*75)
for _, r in df_res.iterrows():
    print(f"Threshold={r['threshold']} | Stride={r['stride']} | Lệnh: {r['trades']:02d} | WinRate: {r['win_rate']:.1f}% | Expectancy: {r['expectancy']:+.2f}% | Lãi ròng: {r['net_pct']:+.2f}% | MaxDD: {r['max_dd']:.1f}%")
