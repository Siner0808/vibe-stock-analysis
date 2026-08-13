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
    session_name = "SÁNG (09:30)" if now_time.hour < 11 else ("TRƯA (12:00)" if now_time.hour < 14 else "CHIỀU ATC (15:15)")
    print("=" * 80)
    print(f"🚀 KÍCH HOẠT QUÉT THỊ TRƯỜNG DỰ BÁO VIBE CODING - PHIÊN {session_name}")
    print(f"⏰ Thời gian: {now_time:%Y-%m-%d %H:%M:%S}")
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

    scan_details = []
    collector = VNStockCollectorAgent()

    import time
    for idx, sym in enumerate(CUSTOM_WATCHLIST_SYMBOLS, 1):
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

                # Thu thập thông tin phân tích cho báo cáo
                last_score = s.get("score", 50.0)
                raw_close = float(row["close"])
                close_vnd = raw_close * (1000.0 if raw_close < 500.0 else 1.0)
                scan_details.append({
                    "symbol": sym,
                    "close": close_vnd,
                    "score": last_score,
                    "opened": s["opened"] > 0,
                    "filled": s["filled_in"] > 0
                })
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

        time.sleep(1.0) # Tạm dừng 1.0s giữa các request

    trades = journal.all_trades()
    rep = report(trades)

    # ── TẠO BÁO CÁO PHÂN TÍCH CHUYÊN SÂU KHI HOÀN THÀNH ──────────────
    scan_details.sort(key=lambda x: -x["score"])
    top_candidates = [x for x in scan_details if x["score"] >= 50.0]

    open_trades = [t for t in trades if t.status in ("OPEN", "PENDING", "CLOSING")]

    # Phân loại theo Ngành
    sector_summary = {}
    for sec_name, sec_syms in SECTOR_WATCHLIST.items():
        matched = [x for x in scan_details if x["symbol"] in sec_syms]
        if matched:
            avg_score = sum(x["score"] for x in matched) / len(matched)
            sector_summary[sec_name] = {
                "count": len(matched),
                "avg_score": avg_score,
                "top_stock": sorted(matched, key=lambda x: -x["score"])[0]
            }

    sorted_sectors = sorted(sector_summary.items(), key=lambda x: -x[1]["avg_score"])

    # Dựng báo cáo dạng Markdown
    report_md = f"""# 📊 BÁO CÁO PHÂN TÍCH THỊ TRƯỜNG DỰ BÁO VIBE CODING
**Khung giờ thực thi:** Phiên {session_name} lúc {now_time:%d/%m/%Y %H:%M:%S}  
**Rổ chứng khoán theo dõi:** {len(CUSTOM_WATCHLIST_SYMBOLS)} mã thuộc 16 Ngành Tùy chỉnh  
**Ngưỡng điểm mua (Buy Threshold):** {BUY_THRESHOLD:.1f} điểm | **Chế độ:** Self-Improving Post-Mortem AI

---

### 🚀 1. TỔNG QUAN PHIÊN QUÉT MULTI-AGENT
- **Số lệnh mới phát hiện mở mua:** `{opened_count}` lệnh
- **Số lệnh chờ đã khớp mua:** `{pending_count}` lệnh
- **Số lệnh đã chốt lời / cắt lỗ:** `{closed_count}` lệnh
- **Số cổ phiếu đạt ngưỡng theo dõi (Score ≥ 50.0):** `{len(top_candidates)}/{len(scan_details)}` mã

---

### ⭐ 2. TOP CỔ PHIẾU CÓ TÍN HIỆU TÍCH CỰC NHẤT THỊ TRƯỜNG (SCORE ≥ 50.0)

"""
    if top_candidates:
        report_md += "| STT | Mã CK | Giá Đóng Cửa (VNĐ) | Điểm Multi-Agent | Trạng Thái Lệnh |\n"
        report_md += "| :---: | :---: | :---: | :---: | :---: |\n"
        for i, item in enumerate(top_candidates[:10], 1):
            stt_str = "🟢 MUA MỚI" if item["opened"] else ("🔵 ĐÃ KHỚP" if item["filled"] else "👀 THEO DÕI")
            report_md += f"| {i} | **{item['symbol']}** | {item['close']:,.0f} | **{item['score']:.1f}/100** | {stt_str} |\n"
    else:
        report_md += "ℹ️ *Phiên này không có cổ phiếu nào vượt ngưỡng mua 50.0 điểm. Hệ thống duy trì trạng thái kiên nhẫn đứng ngoài an toàn.*\n"

    report_md += """
---

### 🏗️ 3. XẾP HẠNG TÍN HIỆU THEO 16 NGÀNH HÀNG (SECTOR RANKING)

| Xếp hạng | Tên Ngành Hàng | Số Mã Quét | Điểm Trung Bình | Mã Dẫn Đầu Ngành (Top Stock) |
| :---: | :--- | :---: | :---: | :--- |\n"""
    for i, (sec_name, sec_info) in enumerate(sorted_sectors, 1):
        top_s = sec_info['top_stock']
        report_md += f"| {i} | **{sec_name}** | {sec_info['count']} mã | **{sec_info['avg_score']:.1f}đ** | {top_s['symbol']} ({top_s['score']:.1f}đ) |\n"

    report_md += """
---

### 📌 4. DANH SÁCH VỊ THẾ ĐANG MỞ & QUẢN TRỊ RỦI RO (ACTIVE POSITIONS)

"""
    if open_trades:
        report_md += "| Mã CK | Trạng Thái | Ngày Vào | Giá Vào (VNĐ) | Cắt Lỗ (SL) | Chốt Lời (TP) | Tỷ Trọng Vốn |\n"
        report_md += "| :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        for t in open_trades:
            sl_str = f"{t.stop_loss:,.0f} VNĐ" if t.stop_loss else "—"
            tp_str = f"{t.take_profit:,.0f} VNĐ" if t.take_profit else "—"
            entry_p = f"{t.entry_price:,.0f} VNĐ" if t.entry_price else "Chờ khớp phiên tới"
            size_pct = f"{t.size_pct:.0f}%"
            report_md += f"| **{t.symbol}** | `{t.status}` | {t.entry_date or t.signal_date} | {entry_p} | {sl_str} | {tp_str} | {size_pct} |\n"
    else:
        report_md += "ℹ️ **Hiện tại không có lệnh nào đang mở.** Tất cả vị thế đã được chốt lời / cắt lỗ an toàn.\n"

    report_md += f"""
---

### 📈 5. KẾT QUẢ TỔNG THỂ SỔ LỆNH GIẤY (PAPER JOURNAL SUMMARY)

```text
{rep}
```
"""

    print("\n" + "=" * 80)
    print("📊 BÁO CÁO PHÂN TÍCH CHUYÊN SÂU PHIÊN " + session_name)
    print("=" * 80)
    print(report_md)

    # ── Đẩy sổ lệnh ra kho ngoài ─────────────────────────────────────
    # PHẢI làm trước khi đóng kết nối. Trên Streamlit Cloud ổ đĩa là tạm,
    # nên nếu không đẩy ra ngoài thì mọi lệnh vừa ghi sẽ mất khi app ngủ
    # hoặc redeploy.
    #
    # Lỗi đẩy KHÔNG được làm hỏng phiên quét — dữ liệu đã nằm an toàn
    # trong .db local rồi. Nhưng phải kêu to: "tưởng đã sao lưu mà thật
    # ra không" là trạng thái tệ nhất.
    try:
        import sheets_store as _ss
        _backend = _ss.open_from_secrets()
        if _backend is None:
            print("\nℹ️ Kho ngoài chưa cấu hình — sổ lệnh chỉ nằm trên ổ đĩa này.")
        else:
            _bc = _ss.push(journal.db, _backend)
            print(f"\n☁️ Đã đẩy sổ lệnh ra Google Sheets: "
                  f"{_bc['trades']} lệnh · thêm {_bc['decisions_moi']} quyết định mới")
    except Exception as _e:
        print(f"\n🚨 ĐẨY KHO NGOÀI THẤT BẠI: {type(_e).__name__}: {_e}")
        print("   Sổ lệnh local vẫn nguyên. Nhưng trên cloud, dữ liệu phiên "
              "này SẼ MẤT nếu không đẩy lại được.")

    journal.db.close()

    # 1. Ghi log ngắn ra daily_execution_log.txt
    log_file = "daily_execution_log.txt"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n==================== [ {now_time:%Y-%m-%d %H:%M:%S} - PHIÊN {session_name} ] ====================\n")
        f.write(rep)

    # 2. Ghi báo cáo phân tích chi tiết ra latest_daily_report.md
    with open("latest_daily_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    # 3. Lưu lịch sử báo cáo vào thư mục reports/
    os.makedirs("reports", exist_ok=True)
    report_hist_file = f"reports/daily_report_{now_time:%Y%m%d_%H%M}.md"
    with open(report_hist_file, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\n✅ Đã lưu Báo cáo Phân tích Chuyên sâu vào file 'latest_daily_report.md' và '{report_hist_file}'")

if __name__ == "__main__":
    execute_daily_scan()
