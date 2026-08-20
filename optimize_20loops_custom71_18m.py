"""
optimize_20loops_custom71_18m.py
──────────────────────────────────────────────────────────────────────
Tối ưu hóa 20 Vòng lặp trên Danh mục Tùy chỉnh 16 Ngành (71 Mã Cổ phiếu)
Thời gian: 18 Tháng Gần Nhất (547 Ngày) đến hôm nay
Vốn khởi điểm: 1,000,000,000 VNĐ (1 Tỷ VNĐ)
Chế độ: Đa tiến trình / Đa luồng song song (Parallel Acceleration)
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

from backtest.data import download
from paper_trading import PaperTradingJournal
from paper_metrics import compute
from paper_runner import cmd_seed
from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS, SECTOR_WATCHLIST

INITIAL_CAPITAL = 1_000_000_000  # 1 Tỷ VNĐ
symbols = CUSTOM_WATCHLIST_SYMBOLS
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=547)).strftime("%Y-%m-%d")

print("=" * 90)
print(f"💰 KHỞI TẠO TỐI ƯU HÓA 20 VÒNG LẶP DỰ BÁO VIBE CODING - 16 NGÀNH ({len(symbols)} MÃ CỔ PHIẾU)")
print(f"📅 Khoảng thời gian: {start_date} đến {end_date} (18 Tháng gần nhất)")
print(f"⚙️ Chế độ: Self-Improving AI (Post-Mortem Loop) | 8 Tiến trình song song (Parallel Worker Threads)")
print("=" * 90)

# 1. Tải và đồng bộ dữ liệu OHLCV 18 tháng cho 71 mã
print("📥 Đang tải và kiểm tra dữ liệu 71 cổ phiếu...")
download(symbols, start_date, end_date)

# 2. Thiết lập 20 Vòng lặp từ ngưỡng 40.0 đến 59.0 điểm (bước nhảy 1.0 điểm)
thresholds = [round(40.0 + i * 1.0, 1) for i in range(20)]
STRIDE = 2

iterations = []
for idx, th in enumerate(thresholds, 1):
    iterations.append({
        "loop": idx,
        "buy_threshold": th,
        "stride": STRIDE,
        "note": f"Ngưỡng {th:.1f} điểm"
    })

def run_single_loop(item):
    loop_num = item["loop"]
    th = item["buy_threshold"]
    db_temp = f"paper_custom20loop_18m_loop_{loop_num}.db"
    
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
        mdd = m.max_drawdown_pct
        final_eq = INITIAL_CAPITAL * (1.0 + pnl / 100.0)

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
        print(f"  [Loop {loop_num:02d}/20] Ngưỡng {th:.1f}đ -> {closed:3d} lệnh | PnL: {pnl:+7.2f}% | WinRate: {wr:5.1f}% | PF: {pf:4.2f} | MaxDD: {mdd:4.1f}%")
        return res
    except Exception as e:
        print(f"  [Loop {loop_num:02d}/20] FAILED: {e}")
        return {"loop": loop_num, "threshold": th, "status": "FAILED", "error": str(e)}

def main():
    print(f"\n🚀 THỰC THI THÍ NGHIỆM 20 VÒNG LẶP SONG SONG TRÊN 71 MÃ CỔ PHIẾU...")
    start_time = datetime.now()

    results = []
    # Kích hoạt 8 luồng chạy song song để đạt tốc độ cao nhất
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(run_single_loop, item): item for item in iterations}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)

    results.sort(key=lambda x: x["loop"])
    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 100)
    print(f"📊 BÁO CÁO TỔNG HỢP KẾT QUẢ TỐI ƯU HÓA 20 VÒNG LẶP (DANH MỤC 71 MÃ - 18 THÁNG)")
    print(f"⏱️ Tổng thời gian chạy đa luồng: {elapsed:.2f} giây")
    print("=" * 100)
    print(f"{'Vòng':<6}{'Ngưỡng Mua':<14}{'Số Lệnh':<10}{'Lợi Nhuận (%)':<18}{'Vốn Cuối (VNĐ)':<18}{'Thắng (%)':<12}{'Profit Factor':<15}{'MaxDD (%)':<10}")
    print("-" * 100)


    for r in results:
        if r.get("status") == "SUCCESS":
            pnl_val = r['pnl']

            pnl_str = f"{r['pnl']:+.2f}%"
            final_val_vnd = r['final_equity'] / 1e9
            print(f"Vòng {r['loop']:<2d}   {r['threshold']:<12.1f}  {r['closed']:<8d}  {pnl_str:<16}  {final_val_vnd:6.3f} Tỷ VNĐ    {r['win_rate']:<10.1f}  {r['profit_factor']:<13.2f}  {r['max_dd']:<8.1f}")
        else:
            print(f"Vòng {r['loop']:<2d}   THẤT BẠI: {r.get('error')}")

    print("=" * 100)

    # Bat bien 7: KHONG de cu mot dong nao trong bang tren lam "ket qua".
    # Bang o tren la TOAN DAI; lay dong lai cao nhat trong do la do do may
    # cua phep tim kiem. Xem dai_ket_qua.py va NGUYEN-TAC-DO-LUONG.md muc 7.
    from dai_ket_qua import CANH_BAO
    print(CANH_BAO)

    # KHONG xoa cac .db moi vong. Chung la bang chung cua TOAN DAI:
    # bo chung di thi chi con lai con so trong bao cao, ma bao cao nam
    # ngoai repo thi nam ngoai moi bat bien (NGUYEN-TAC-DO-LUONG.md).
    # Sau su co 12/08, 12/20 so cua lan chay do da bi xoa mat.
    print("ℹ️  Giu lai cac .db moi vong lam bang chung — xoa tay khi khong can.")

if __name__ == "__main__":
    main()
