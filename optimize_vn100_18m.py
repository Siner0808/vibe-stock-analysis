"""
optimize_vn100_18m.py
──────────────────────────────────────────────────────────────────────
Tối ưu hóa 20 Vòng lặp trên Rổ VN100 với Dữ liệu 18 Tháng Gần Nhất (547 Ngày)
Vốn khởi điểm: 1,000,000,000 VNĐ
Thang điểm Mua: 40.0 -> 60.0 điểm
Tích hợp 5 Nguyên lý Định lượng Đột phá
"""

import os
import sys
import gc
from datetime import datetime, timedelta
from argparse import Namespace
import pandas as pd

from backtest.data import download, load_all
from paper_trading import PaperTradingJournal
from paper_metrics import compute
from paper_runner import cmd_seed
from vn100_symbols import VN100_SYMBOLS

sys.stdout.reconfigure(encoding="utf-8")

INITIAL_CAPITAL = 1_000_000_000  # 1 Tỷ VNĐ
symbols = VN100_SYMBOLS
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=547)).strftime("%Y-%m-%d")

print(f"💰 Khởi tạo Danh mục VN100 (18 Tháng Lịch sử): 1,000,000,000 VNĐ ({len(symbols)} mã cổ phiếu)")
print("🚀 Bắt đầu Vòng lặp 20 Iterations Tối ưu hóa trên Rổ VN100...")

download(symbols, start_date, end_date)

thresholds = [40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0, 49.0,
              50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 60.0]

# stride PHẢI cố định. Bản trước để `2 if idx % 2 == 1 else 3`, nên so vòng 1
# với vòng 2 là so cả ngưỡng LẪN stride — hai biến trộn nhau, không kết luận
# được biến nào gây ra chênh lệch. Tệ hơn: stride=3 nghĩa là chỉ kiểm tra vị
# thế 3 phiên một lần, giá có thể xuyên sâu qua cắt lỗ rồi mới bị phát hiện.
# Đó là thay đổi bản chất mô phỏng, không liên quan gì tới ngưỡng mua.
STRIDE = 2

iterations = []
for idx, th in enumerate(thresholds, 1):
    iterations.append({
        "loop": idx,
        "buy_threshold": th,
        "stride": STRIDE,
        "note": f"Threshold {th:.1f} (Stride={STRIDE})"
    })

results = []

for item in iterations:
    loop_num = item["loop"]
    db_temp = f"paper_vn100_18m_loop_{loop_num}.db"
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
print("\n" + "="*100)
print("📊 BẢNG KẾT QUẢ RỔ VN100 (18 THÁNG GẦN NHẤT) - QUẢN LÝ VỐN 1 TỶ ĐỒNG QUA 20 VÒNG TỐI ƯU")
print("="*100)

for _, r in df_res.iterrows():
    sign = "+" if r['net_profit_vnd'] >= 0 else ""
    print(f"Vòng {r['loop']:02d} | Th={r['buy_threshold']:4.1f} | Lệnh: {r['closed_trades']:03d} | Thắng: {r['win_rate']:4.1f}% | Kỳ vọng: {r['expectancy']:+5.2f}% | MaxDD: {r['max_dd']:4.1f}% | Giá trị tài sản: {r['final_capital']:,.0f} VNĐ ({sign}{r['net_profit_vnd']:,.0f} VNĐ)")

active_df = df_res[df_res["closed_trades"] > 0]
if not active_df.empty:
    best_row = active_df.sort_values(by="final_capital", ascending=False).iloc[0]
else:
    best_row = df_res.iloc[0]

print("\n" + "🏆"*35)
print(" VÒNG TỐI ƯU HÓA VN100 18 THÁNG XUẤT SẮC NHẤT (VỐN 1 TỶ ĐỒNG):")
print(f"-> Vòng {best_row['loop']:02d} ({best_row['note']})")
print(f"-> Ngưỡng mua tối ưu: {best_row['buy_threshold']} điểm")
print(f"-> Tổng số lệnh đóng: {best_row['closed_trades']} lệnh")
print(f"-> Tỷ lệ thắng: {best_row['win_rate']:.1f}%")
print(f"-> Kỳ vọng lợi nhuận / lệnh: {best_row['expectancy']:+.2f}%")
print(f"-> Mức sụt giảm tài sản tối đa (MaxDD): {best_row['max_dd']:.1f}%")
print(f"-> GIÁ TRỊ TÀI SẢN CUỐI KỲ: {best_row['final_capital']:,.0f} VNĐ")
sign = "+" if best_row['net_profit_vnd'] >= 0 else ""
print(f"-> LỢI NHUẬN RÒNG THỰC TẾ: {sign}{best_row['net_profit_vnd']:,.0f} VNĐ ({best_row['net_pct']:+.2f}%)")
print("🏆"*35 + "\n")

print("""
⚠️  ĐỌC TRƯỚC KHI DÙNG CON SỐ Ở TRÊN

Bảng này là 20 lần chạy trên CÙNG một bộ dữ liệu, rồi lấy vòng lãi cao nhất.
Cực đại của 20 phép thử trên cùng dữ liệu luôn bị thổi phồng — nó đo độ may
của phép tìm kiếm, không đo lợi thế của chiến lược. Không có tập kiểm định
nào ở đây, nên KHÔNG con số nào trong bảng là kết quả ngoài mẫu.

Dòng đáng tin nhất là dòng có NHIỀU LỆNH NHẤT, không phải dòng lãi cao nhất:
mẫu càng lớn thì sai số càng nhỏ. Ngưỡng càng cao thì lệnh càng ít, nhiễu
càng lớn, và "chiến thắng" xuất hiện đúng ở chỗ nhiễu lớn nhất.

Dùng walkforward_vn100.py để có con số ngoài mẫu thật sự.

Script này KHÔNG ghi vào paper_trades.db. Sổ lệnh đó là nhật ký tiến bước,
ghi đè nó bằng kết quả in-sample là xoá mất bằng chứng duy nhất chưa bị
tối ưu chạm vào.
""")
