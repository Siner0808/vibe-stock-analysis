"""
optimize_20_loops.py
──────────────────────────────────────────────────────────────────────
Tối ưu hóa 20 Vòng (20-Iteration Optimization Loop) với Vốn giả định 1 TỶ ĐỒNG (1,000,000,000 VNĐ)
quét thang điểm từ 40.0 đến 60.0 để tìm điểm vào mang lại Lợi Nhuận Thực Tế Cao Nhất.
"""
import os
import sys
import gc
from datetime import datetime, timedelta
from argparse import Namespace
import pandas as pd

from backtest.data import load_all
from paper_trading import PaperTradingJournal, guard_not_real_ledger
from paper_metrics import compute
from paper_runner import cmd_seed

sys.stdout.reconfigure(encoding="utf-8")

INITIAL_CAPITAL = 1_000_000_000  # 1 Tỷ VNĐ
symbols = ["FPT", "HPG", "VNM", "MBB", "SSI", "TCB", "VHM", "MWG"]

print("💰 Khởi tạo Danh mục Giả định: 1,000,000,000 VNĐ (1 Tỷ Đồng)")
print("🚀 Bắt đầu Vòng lặp Học hỏi & Tối ưu hóa 20 Iterations (Khung điểm 40.0 - 60.0)...")

# Đảm bảo có cache
dataset = load_all(symbols)
if not dataset:
    print("❌ Chưa có cache. Đang tải...")
    from backtest.data import download
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    download(symbols, start_date, end_date)

iterations = []
# Tạo 20 tham số đa dạng từ 40.0 đến 60.0 với stride khác nhau
thresholds = [40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0, 49.0,
              50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 60.0]

for idx, th in enumerate(thresholds, 1):
    stride = 2 if idx % 2 == 1 else 3
    iterations.append({
        "loop": idx,
        "buy_threshold": th,
        "stride": stride,
        "note": f"Threshold {th:.1f} (Stride={stride})"
    })

results = []

for item in iterations:
    loop_num = item["loop"]
    db_temp = f"paper_20loop_{loop_num}.db"
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
    
    if perf is not None and perf.n_trades > 0:
        closed = perf.n_trades
        win_rate = perf.win_rate * 100
        expectancy = perf.expectancy
        max_dd = perf.max_drawdown_pct
        net_pct = perf.total_net_pct
        final_capital = INITIAL_CAPITAL * (1.0 + net_pct / 100.0)
        net_profit_vnd = final_capital - INITIAL_CAPITAL
    else:
        closed, win_rate, expectancy, max_dd, net_pct = 0, 0, 0, 0, 0
        final_capital = INITIAL_CAPITAL
        net_profit_vnd = 0

    results.append({
        "loop": loop_num,
        "note": item["note"],
        "buy_threshold": item["buy_threshold"],
        "stride": item["stride"],
        "closed_trades": closed,
        "win_rate": win_rate,
        "expectancy": expectancy,
        "max_dd": max_dd,
        "net_pct": net_pct,
        "final_capital": final_capital,
        "net_profit_vnd": net_profit_vnd
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
print("\n" + "="*95)
print("📊 BẢNG KẾT QUẢ QUẢN LÝ VỐN 1 TỶ ĐỒNG QUA 20 VÒNG TỐI ƯU (KHUNG ĐIỂM 40 - 60)")
print("="*95)

for _, r in df_res.iterrows():
    sign = "+" if r['net_profit_vnd'] >= 0 else ""
    print(f"Vòng {r['loop']:02d} | Th={r['buy_threshold']:4.1f} | Lệnh: {r['closed_trades']:03d} | Thắng: {r['win_rate']:4.1f}% | Kỳ vọng: {r['expectancy']:+5.2f}% | MaxDD: {r['max_dd']:4.1f}% | Giá trị tài sản: {r['final_capital']:,.0f} VNĐ ({sign}{r['net_profit_vnd']:,.0f} VNĐ)")

active_df = df_res[df_res["closed_trades"] > 0]
if not active_df.empty:
    best_row = active_df.sort_values(by="final_capital", ascending=False).iloc[0]
else:
    best_row = df_res.iloc[0]

# Bat bien 7: KHONG de cu mot dong nao trong bang tren lam "ket qua".
# Bang o tren la TOAN DAI; lay dong lai cao nhat trong do la do do may
# cua phep tim kiem. Xem dai_ket_qua.py va NGUYEN-TAC-DO-LUONG.md muc 7.
from dai_ket_qua import CANH_BAO
print(CANH_BAO)

# KHÔNG ghi vào paper_trades.db. Vòng thắng ở đây là cực đại của 20 lần thử
# trên CÙNG một bộ dữ liệu — đó là độ may của phép tìm kiếm, không phải lợi
# thế của chiến lược (NGUYEN-TAC-DO-LUONG.md, bất biến 7). Nạp nó vào sổ
# lệnh thật đã xoá 96/113 lệnh thật ngày 12/08/2026.
SCRATCH_DB = "paper_optimize_20loops_insample.db"
guard_not_real_ledger(SCRATCH_DB, caller="optimize_20_loops.py")

print(f"⚡ Ghi kết quả in-sample ra {SCRATCH_DB} (KHÔNG đụng sổ lệnh thật)...")
if os.path.exists(SCRATCH_DB):
    try:
        os.remove(SCRATCH_DB)
    except Exception:
        pass

best_args = Namespace(
    db=SCRATCH_DB,
    symbols=",".join(symbols),
    min_history=30,
    stride=best_row["stride"],
    buy_threshold=best_row["buy_threshold"]
)
cmd_seed(best_args)
print(f"✅ Đã ghi kết quả IN-SAMPLE ra {SCRATCH_DB}. Đây KHÔNG phải sổ lệnh thật.")
print("   Tham số dùng ở đây là cực đại của N lần thử trên CÙNG bộ dữ liệu,")
print("   nên theo bất biến 7 nó chưa dùng được để giao dịch.")
