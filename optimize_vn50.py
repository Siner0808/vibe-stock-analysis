"""
optimize_vn50.py
──────────────────────────────────────────────────────────────────────
Tối ưu hóa 20 Vòng trên Rổ VN50 (50 Cổ phiếu hàng đầu) với Vốn 1 TỶ ĐỒNG:
1. Tự động nâng SL về 0% (Hòa vốn Break-Even) khi lãi đạt +5%
2. Mở rộng TP gồng sóng +20% đến +30% cho tới khi đảo chiều mạnh
3. Tải và phân tích 50 cổ phiếu thanh khoản hàng đầu VN50
"""
import os
import sys
import gc
from datetime import datetime, timedelta
from argparse import Namespace
import pandas as pd

from backtest.data import load_all, download
from paper_trading import PaperTradingJournal, guard_not_real_ledger
from paper_metrics import compute
from paper_runner import cmd_seed
from vn50_symbols import VN50_SYMBOLS

sys.stdout.reconfigure(encoding="utf-8")

INITIAL_CAPITAL = 1_000_000_000  # 1 Tỷ VNĐ
symbols = VN50_SYMBOLS

print(f"💰 Khởi tạo Danh mục VN50 Giả định: 1,000,000,000 VNĐ ({len(symbols)} cổ phiếu hàng đầu)")
print("🚀 Bắt đầu Vòng lặp Học hỏi & Tối ưu hóa 20 Iterations trên Rổ VN50...")

# Đảm bảo có cache cho 50 mã VN50
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
download(symbols, start_date, end_date)

thresholds = [40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0, 49.0,
              50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 60.0]

iterations = []
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
    db_temp = f"paper_vn50_loop_{loop_num}.db"
    if os.path.exists(db_temp):
        try: os.remove(db_temp)
        except Exception: pass
    
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
        try: os.remove(db_temp)
        except Exception: pass

df_res = pd.DataFrame(results)
print("\n" + "="*98)
print("📊 BẢNG KẾT QUẢ RỔ VN50 - QUẢN LÝ VỐN 1 TỶ ĐỒNG QUA 20 VÒNG TỐI ƯU")
print("="*98)

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

# KHÔNG ghi vào paper_trades.db — xem NGUYEN-TAC-DO-LUONG.md, bất biến 7.
# Vòng thắng là cực đại của N lần thử trên cùng dữ liệu, không phải kết quả.
SCRATCH_DB = "paper_optimize_vn50_insample.db"
guard_not_real_ledger(SCRATCH_DB, caller="optimize_vn50.py")

print(f"⚡ Ghi kết quả in-sample ra {SCRATCH_DB} (KHÔNG đụng sổ lệnh thật)...")
if os.path.exists(SCRATCH_DB):
    try: os.remove(SCRATCH_DB)
    except Exception: pass

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
