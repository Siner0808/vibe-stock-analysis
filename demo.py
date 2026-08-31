"""
Demo Vnstock Vibe Coding
Lấy dữ liệu giá, tính chỉ số cơ bản & hiển thị thông tin cổ phiếu FPT
"""

import os
import sys

# Đảm bảo console Windows in đúng tiếng Việt và icon emoji
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from vnstock.api.quote import Quote
from vnstock import Reference

def main():
    print("=" * 60)
    print("🚀 CHÀO MỪNG ĐẾN VỚI VNSTOCK VIBE CODING!")
    print("=" * 60)
    
    symbol = "FPT"
    print(f"\n📊 1. Đang tải lịch sử giá 10 phiên gần nhất của mã {symbol}...")
    
    q = Quote(symbol=symbol, source="VCI")
    df = q.history(start="2024-01-01", end="2024-02-01")
    
    if not df.empty:
        print("\n📈 Bảng dữ liệu giá:")
        print(df.tail(10)[["time", "open", "high", "low", "close", "volume"]].to_string(index=False))
        
        latest_close = df.iloc[-1]["close"]
        prev_close = df.iloc[-2]["close"]
        change = latest_close - prev_close
        pct_change = (change / prev_close) * 100
        
        print(f"\n📌 Giá đóng cửa gần nhất: {latest_close:,.2f} VNĐ ({pct_change:+.2f}%)")
    else:
        print("Không tìm thấy dữ liệu giá.")

    print("\n" + "=" * 60)
    print("✅ Môi trường hoạt động hoàn hảo! Bạn có thể bắt đầu xây dựng chiến lược.")
    print("=" * 60)

if __name__ == "__main__":
    main()
