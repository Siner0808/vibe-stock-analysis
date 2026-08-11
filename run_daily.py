"""
run_daily.py
─────────────
Script tự động quét danh mục VN100 và cập nhật Sổ Lệnh Giấy paper_trades.db.
Được lên lịch chạy tự động tại các khung giờ: 09:30, 12:00, 15:15 (Thứ 2 đến Thứ 6).
"""
import os
import sys
import pandas as pd
from datetime import datetime

os.environ["POST_MORTEM_ENABLED"] = "1"
sys.stdout.reconfigure(encoding="utf-8")

from vn100_symbols import CUSTOM_WATCHLIST_SYMBOLS, SECTOR_WATCHLIST
from paper_trading import PaperTradingJournal
from paper_metrics import compute, report
from paper_runner import run_session
from data_collectors import VNStockCollectorAgent
from data_quality import now_vn

DB_PATH = "paper_trades.db"
BUY_THRESHOLD = 50.0

def execute_daily_scan():
    now_time = now_vn()
    print("=" * 80)
    print(f"🚀 KÍCH HOẠT QUÉT THỊ TRƯỜNG DỰ BÁO VIBE CODING: {now_time:%Y-%m-%d %H:%M:%S}")
    print(f"📌 Rổ chứng khoán Theo dõi: Danh mục Tùy chỉnh 16 Ngành ({len(CUSTOM_WATCHLIST_SYMBOLS)} mã)")
    print(f"📌 Ngưỡng điểm mua: {BUY_THRESHOLD} điểm (Tối ưu từ 20 Vòng lặp)")
    print(f"📌 Chế độ: Self-Improving AI (Post-Mortem Memory Loop ACTIVE)")
    print("=" * 80)

    journal = PaperTradingJournal(DB_PATH)
    start_date = (now_time - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
    end_date = now_time.strftime("%Y-%m-%d")

    opened_count = 0
    closed_count = 0
    pending_count = 0

    collector = VNStockCollectorAgent()

    import time
    for idx, sym in enumerate(VN100_SYMBOLS, 1):
        retry = 0
        while retry < 3:
            try:
                res = collector.collect(sym, start_date, end_date, exchange="HOSE")
                if res.get("status") != "OK":
                    note = str(res.get("note", ""))
                    if "Rate limit" in note or "GIỚI HẠN API" in note:
                        print(f"  ⏳ {sym}: Dính Rate Limit API (60 req/min). Tự động chờ 40 giây...")
                        time.sleep(40)
                        retry += 1
                        continue
                    break
                
                df = res["df"]
                if df is None or df.empty or len(df) < 20:
                    break
                
                row = df.iloc[-1]
                bar = {
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"])
                }
                s = run_session(journal, sym, df, bar, str(row["time"]), "HOSE", BUY_THRESHOLD)
                opened_count += s["opened"]
                closed_count += s["closed"]
                pending_count += s["filled_in"]
                break
            except Exception as e:
                err_msg = str(e)
                if "Rate limit" in err_msg or "429" in err_msg:
                    print(f"  ⏳ {sym}: Dính Rate Limit API. Tự động chờ 40 giây...")
                    time.sleep(40)
                    retry += 1
                else:
                    print(f"⚠️ Lỗi xử lý {sym}: {e}")
                    break

        time.sleep(1.0) # Tạm dừng 1.0 giây giữa các request để tuân thủ 60 requests/phút

    trades = journal.all_trades()
    rep = report(trades)

    print("\n" + "=" * 80)
    print("📊 BÁO CÁO CẬP NHẬT SỔ LỆNH GIẤY THỰC TẾ:")
    print("=" * 80)
    print(rep)

    journal.db.close()
    
    # Ghi log ra file daily_execution_log.txt
    log_file = "daily_execution_log.txt"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n==================== [ {now_time:%Y-%m-%d %H:%M:%S} ] ====================\n")
        f.write(rep)
    
    print(f"\n✅ Đã ghi log thành công vào {log_file} và {DB_PATH}")

if __name__ == "__main__":
    execute_daily_scan()
