"""
optimize_custom_71stocks_18m.py
──────────────────────────────────────────────────────────────────────
Tối ưu hóa 10 Vòng lặp trên Danh mục Tùy chỉnh 16 Ngành (71 Mã Cổ phiếu)
Thời gian: 18 Tháng Gần Nhất (547 Ngày)
Vốn khởi điểm: 1,000,000,000 VNĐ (1 Tỷ VNĐ)
Chế độ: Đa tiến trình/Đa luồng song song (Parallel Multi-Processing)
"""

import os
import sys
import gc
from datetime import datetime, timedelta
from argparse import Namespace
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["POST_MORTEM_ENABLED"] = "1"
sys.stdout.reconfigure(encoding="utf-8")

from backtest.data import download, load_all
from paper_trading import PaperTradingJournal
from paper_metrics import compute
from paper_runner import cmd_seed
from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS, SECTOR_WATCHLIST

INITIAL_CAPITAL = 1_000_000_000  # 1 Tỷ VNĐ
symbols = CUSTOM_WATCHLIST_SYMBOLS
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=547)).strftime("%Y-%m-%d")

print("=" * 80)
print(f"💰 KHỞI TẠO TỐI ƯU HÓA 10 VÒNG LẶP DỰ BÁO - 16 NGÀNH ({len(symbols)} MÃ CỔ PHIẾU)")
print(f"📅 Khoảng thời gian: {start_date} đến {end_date} (18 Tháng gần nhất)")
print(f"⚙️ Tải dữ liệu & Bật Chế độ Đa luồng/Đa tiến trình song song (Parallel Acceleration)...")
print("=" * 80)

# Tải dữ liệu OHLCV cho 71 mã
download(symbols, start_date, end_date)

# 10 Vòng lặp với các ngưỡng mua từ 42.0 đến 60.0
thresholds = [42.0, 44.0, 46.0, 48.0, 50.0, 52.0, 54.0, 56.0, 58.0, 60.0]
STRIDE = 2

iterations = []
for idx, th in enumerate(thresholds, 1):
    iterations.append({
        "loop": idx,
        "buy_threshold": th,
        "stride": STRIDE,
        "note": f"Ngưỡng {th:.1f} điểm (Stride={STRIDE})"
    })

def run_single_loop(item):
    loop_num = item["loop"]
    th = item["buy_threshold"]
    db_temp = f"paper_custom71_18m_loop_{loop_num}.db"
    
    if os.path.exists(db_temp):
        try: os.remove(db_temp)
        except Exception: pass

    try:
        args = Namespace(
            symbols=",".join(symbols),
            start=start_date,
            end=end_date,
            stride=item["stride"],
            min_history=60,
            initial_capital=INITIAL_CAPITAL,
            buy_threshold=th,
            db=db_temp,
            no_summary=True
        )
        cmd_seed(args)

        journal = PaperTradingJournal(db_temp)
        trades = journal.all_trades()
        m = compute(trades)

        if m is None:
            return {"loop": loop_num, "threshold": th, "status": "NO_TRADES"}

        closed = len([t for t in trades if t.status == "CLOSED"])
        pnl = m.total_net_pct
        pf = m.profit_factor
        wr = m.win_rate
        mdd = m.max_drawdown
        final_eq = m.final_equity

        res = {
            "loop": loop_num,
            "threshold": th,
            "closed": closed,
            "pnl": pnl,
            "win_rate": wr,
            "profit_factor": pf,
            "max_dd": mdd,
            "final_equity": final_eq,
            "status": "SUCCESS"
        }
        print(f"  [Loop {loop_num:02d}/10] Ngưỡng {th:.1f}đ -> {closed:3d} lệnh | PnL: {pnl:+7.2f}% | WinRate: {wr:5.1f}% | PF: {pf:4.2f} | MaxDD: {mdd:4.1f}%")
        return res
    except Exception as e:
        print(f"  [Loop {loop_num:02d}/10] FAILED: {e}")
        return {"loop": loop_num, "threshold": th, "status": "FAILED", "error": str(e)}

def main():
    print(f"\n🚀 BẮT ĐẦU CHẠY SONG SONG 10 VÒNG LẶP TRÊN 71 MÃ CỔ PHIẾU...")
    start_time = datetime.now()

    results = []
    # Chạy song song với ThreadPoolExecutor 8 workers
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(run_single_loop, item): item for item in iterations}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)

    results.sort(key=lambda x: x["loop"])
    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 90)
    print(f"📊 BÁO CÁO KẾT QUẢ TỐI ƯU HÓA 10 VÒNG LẶP (DANH MỤC 71 MÃ - 18 THÁNG)")
    print(f"⏱️ Tổng thời gian thực thi đa luồng: {elapsed:.2f} giây")
    print("=" * 90)
    print(f"{'Vòng':<6}{'Ngưỡng Mua':<12}{'Số Lệnh':<10}{'Lợi Nhuận (%)':<16}{'Thắng (%)':<12}{'ProfitFactor':<14}{'MaxDD (%)':<10}")
    print("-" * 90)

    best_pnl = -999.0
    best_item = None

    for r in results:
        if r.get("status") == "SUCCESS":
            pnl_val = r['pnl']
            if pnl_val > best_pnl:
                best_pnl = pnl_val
                best_item = r

            pnl_str = f"{r['pnl']:+.2f}%"
            final_val_vnd = r['final_equity'] / 1e9
            print(f"Vòng {r['loop']:<2d}   {r['threshold']:<10.1f}  {r['closed']:<8d}  {pnl_str:<14} ({final_val_vnd:.2f}B VNĐ)  {r['win_rate']:<10.1f}  {r['profit_factor']:<12.2f}  {r['max_dd']:<8.1f}")
        else:
            print(f"Vòng {r['loop']:<2d}   THẤT BẠI: {r.get('error')}")

    print("=" * 90)

    if best_item:
        print(f"\n🏆 VÒNG LẶP XUẤT SẮC NHẤT:")
        print(f"   - Ngưỡng mua tối ưu: {best_item['threshold']:.1f} điểm")
        print(f"   - Tổng lợi nhuận: {best_item['pnl']:+.2f}% ({best_item['final_equity']/1e9:.2f} Tỷ VNĐ)")
        print(f"   - Win Rate: {best_item['win_rate']:.1f}% | Profit Factor: {best_item['profit_factor']:.2f}")
        print(f"   - Sức chịu đựng rủi ro (Max Drawdown): {best_item['max_dd']:.1f}%")
        print("=" * 90)

    # Dọn dẹp các file temp db
    for i in range(1, 11):
        tmp_db = f"paper_custom71_18m_loop_{i}.db"
        if os.path.exists(tmp_db):
            try: os.remove(tmp_db)
            except Exception: pass

if __name__ == "__main__":
    main()
