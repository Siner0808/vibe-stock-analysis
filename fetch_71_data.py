import json
import time
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from vnstock import Quote, Company

SECTOR_MAP = {
    "Dầu khí": ["BSR", "PVD", "PVS", "PLX", "OIL"],
    "Tài nguyên cơ bản": ["HPG", "HHP", "HSG", "NKG", "MSR"],
    "Hàng & Dịch vụ công nghiệp": ["VSC", "GEX", "PVT", "VTP"],
    "Thực phẩm & Đồ uống": ["VNM", "HAG", "MSN", "BAF", "NAF"],
    "Y tế": ["DHG", "DCL"],
    "Ngân hàng": ["STB", "VCB", "LPB", "BID", "CTG", "TCB", "HDB", "SHB", "MBB", "ACB"],
    "Bất động sản": ["NVL", "VHM", "KDH", "PDR", "DIG", "VRE", "VIC", "DXG", "NLG", "BCM"],
    "Công nghệ thông tin": ["FPT"],
    "Hóa chất": ["AAA", "DPM", "DCM", "GVR"],
    "Xây dựng & Vật liệu": ["CII", "HHV", "VCG", "GEL", "PC1"],
    "Ô tô": ["HAX", "HUT"],
    "Hàng cá nhân & Gia dụng": ["PNJ", "GIL"],
    "Bán lẻ": ["FRT", "MWG"],
    "Dịch vụ & Giải trí": ["VJC", "VPL", "HVN", "ACV"],
    "Điện, Nước & Khí đốt": ["POW", "GAS", "PLX"],
    "Dịch vụ tài chính": ["VIX", "SSI", "VCI", "HCM", "SHS", "VND", "MBS", "VCK"]
}

# Save Watchlist JSON
all_symbols = []
for sector, symbols in SECTOR_MAP.items():
    for s in symbols:
        if s not in all_symbols:
            all_symbols.append(s)

watchlist_data = {
    "sectors": SECTOR_MAP,
    "total_sectors": len(SECTOR_MAP),
    "unique_symbols": all_symbols,
    "total_symbols": len(all_symbols)
}

with open("watchlist_71.json", "w", encoding="utf-8") as f:
    json.dump(watchlist_data, f, ensure_ascii=False, indent=2)

print(f"Loaded {len(all_symbols)} unique symbols across {len(SECTOR_MAP)} sectors.")

# Fetch 18 months data (from 2025-02-01 to 2026-08-24)
start_date = "2025-02-01"
end_date = "2026-08-24"

results = []
data_store = {}

for idx, sym in enumerate(all_symbols, 1):
    print(f"[{idx}/{len(all_symbols)}] Fetching {sym}...", end=" ", flush=True)
    try:
        q = Quote(symbol=sym, source='VCI')
        df = q.history(start=start_date, end=end_date)
        if df is None or df.empty or len(df) < 30:
            print("No data / Insufficient data")
            continue
        
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)
        data_store[sym] = df
        print(f"OK ({len(df)} bars)")
    except Exception as e:
        print(f"Error: {e}")

print(f"\nSuccessfully downloaded data for {len(data_store)} / {len(all_symbols)} symbols.")
