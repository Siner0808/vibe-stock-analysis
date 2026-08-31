import json
import os
import time
import pandas as pd
import numpy as np
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

SYMBOL_TO_SECTOR = {}
for sec, syms in SECTOR_MAP.items():
    for s in syms:
        if s not in SYMBOL_TO_SECTOR:
            SYMBOL_TO_SECTOR[s] = sec

all_symbols = list(SYMBOL_TO_SECTOR.keys())
os.makedirs("data_cache", exist_ok=True)

start_date = "2025-02-01"
end_date = "2026-08-24"

stock_data = {}
print(f"Bat dau kiem tra / thu thap du lieu 18 thang cho {len(all_symbols)} ma...")

for idx, sym in enumerate(all_symbols, 1):
    cache_path = os.path.join("data_cache", f"{sym}.csv")
    
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 500:
        try:
            df = pd.read_csv(cache_path)
            df['time'] = pd.to_datetime(df['time'])
            df = df.sort_values('time').reset_index(drop=True)
            if len(df) >= 30:
                stock_data[sym] = df
                print(f"[{idx:02d}/{len(all_symbols)}] {sym} ({SYMBOL_TO_SECTOR[sym]}): Loaded tu Cache ({len(df)} bars)")
                continue
        except Exception:
            pass

    # Neu chua co cache thi fetch tu API voi sleep 1.5s
    success = False
    for attempt in range(3):
        try:
            time.sleep(1.5)
            q = Quote(symbol=sym, source='VCI')
            df = q.history(start=start_date, end=end_date)
            if df is not None and not df.empty and len(df) >= 30:
                df['time'] = pd.to_datetime(df['time'])
                df = df.sort_values('time').reset_index(drop=True)
                df.to_csv(cache_path, index=False)
                stock_data[sym] = df
                print(f"[{idx:02d}/{len(all_symbols)}] {sym} ({SYMBOL_TO_SECTOR[sym]}): API Success ({len(df)} bars)")
                success = True
                break
            else:
                print(f"[{idx:02d}/{len(all_symbols)}] {sym}: Du lieu rong hoac < 30 bars")
                break
        except Exception as e:
            print(f"[{idx:02d}/{len(all_symbols)}] {sym} Thu lai {attempt+1}: {e}")
            time.sleep(10)

print(f"\nDa san sang du lieu cho {len(stock_data)} / {len(all_symbols)} ma co phieu.")

# Tinh toan chi so ky thuat
metrics_list = []

for sym, df in stock_data.items():
    close = df['close'] * 1000
    high = df['high'] * 1000
    low = df['low'] * 1000
    volume = df['volume']
    
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(min(200, len(close))).mean()
    vol_ma20 = volume.rolling(20).mean()
    
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss.replace(0, 1e-6))
    rsi = 100 - (100 / (1 + rs))
    
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - signal
    
    cur_p = close.iloc[-1]
    cur_ma20 = ma20.iloc[-1]
    cur_ma50 = ma50.iloc[-1]
    cur_ma200 = ma200.iloc[-1]
    cur_rsi = rsi.iloc[-1]
    cur_vol = volume.iloc[-1]
    cur_vol_ma20 = vol_ma20.iloc[-1]
    vol_ratio = cur_vol / max(1, cur_vol_ma20)
    
    ret_1w = (cur_p / close.iloc[-5] - 1) * 100 if len(close) >= 5 else 0
    ret_1m = (cur_p / close.iloc[-20] - 1) * 100 if len(close) >= 20 else 0
    ret_3m = (cur_p / close.iloc[-60] - 1) * 100 if len(close) >= 60 else 0
    ret_6m = (cur_p / close.iloc[-120] - 1) * 100 if len(close) >= 120 else 0
    
    high_18m = high.max()
    low_18m = low.min()
    pos_18m = (cur_p - low_18m) / max(1, high_18m - low_18m) * 100
    
    is_above_ma20 = cur_p > cur_ma20
    is_above_ma50 = cur_p > cur_ma50
    is_golden_cross = cur_ma20 > cur_ma50
    is_vol_breakout = vol_ratio >= 1.3
    
    low_20d = low.tail(20).min()
    bounce_from_low = (cur_p / low_20d - 1) * 100
    
    has_fvg = False
    for i in range(len(df)-10, len(df)-1):
        if i >= 1 and i+1 < len(df):
            if df.iloc[i+1]['low']*1000 > df.iloc[i-1]['high']*1000:
                has_fvg = True
                break
    
    has_displacement = False
    for i in range(len(df)-5, len(df)):
        body_pct = abs(df.iloc[i]['close'] - df.iloc[i]['open']) / df.iloc[i]['open'] * 100
        v_rat = df.iloc[i]['volume'] / max(1, vol_ma20.iloc[i])
        if body_pct >= 3.5 and v_rat >= 1.4:
            has_displacement = True
            break
            
    metrics_list.append({
        'symbol': sym,
        'sector': SYMBOL_TO_SECTOR[sym],
        'price': cur_p,
        'ma20': cur_ma20,
        'ma50': cur_ma50,
        'ma200': cur_ma200,
        'rsi': cur_rsi,
        'vol_ratio': vol_ratio,
        'cur_vol': cur_vol,
        'vol_ma20': cur_vol_ma20,
        'ret_1w': ret_1w,
        'ret_1m': ret_1m,
        'ret_3m': ret_3m,
        'ret_6m': ret_6m,
        'high_18m': high_18m,
        'low_18m': low_18m,
        'pos_18m': pos_18m,
        'is_above_ma20': is_above_ma20,
        'is_above_ma50': is_above_ma50,
        'is_golden_cross': is_golden_cross,
        'is_vol_breakout': is_vol_breakout,
        'bounce_from_low': bounce_from_low,
        'has_fvg': has_fvg,
        'has_displacement': has_displacement,
        'macd_hist': macd_hist.iloc[-1]
    })

mdf = pd.DataFrame(metrics_list)

# 20-Round Scoring Loop
scores = {sym: 0.0 for sym in mdf['symbol']}

for _, r in mdf.iterrows():
    # VONG 1: Gia tren MA20
    if r['is_above_ma20']: scores[r['symbol']] += 5.0
    # VONG 2: Gia tren MA50
    if r['is_above_ma50']: scores[r['symbol']] += 5.0
    # VONG 3: Golden Cross MA20 > MA50
    if r['is_golden_cross']: scores[r['symbol']] += 5.0
    # VONG 4: Gia tren MA200 (Uptrend dai han)
    if r['price'] > r['ma200']: scores[r['symbol']] += 5.0
    # VONG 5: Dong tien dot bien Vol > 1.4x MA20
    if r['vol_ratio'] >= 1.4: scores[r['symbol']] += 6.0
    elif r['vol_ratio'] >= 1.1: scores[r['symbol']] += 3.0
    # VONG 6: Thanh khoan doi dao > 400k CP
    if r['vol_ma20'] >= 400000: scores[r['symbol']] += 4.0
    # VONG 7: RSI xung luc dep 50 - 72
    if 50 <= r['rsi'] <= 72: scores[r['symbol']] += 6.0
    elif 45 <= r['rsi'] < 50: scores[r['symbol']] += 3.0
    # VONG 8: MACD Histogram > 0
    if r['macd_hist'] > 0: scores[r['symbol']] += 5.0
    # VONG 9: Suc manh 1W > 2%
    if r['ret_1w'] > 4.0: scores[r['symbol']] += 6.0
    elif r['ret_1w'] > 1.5: scores[r['symbol']] += 4.0
    # VONG 10: Suc manh 1M > 4%
    if r['ret_1m'] > 6.0: scores[r['symbol']] += 6.0
    elif r['ret_1m'] > 2.0: scores[r['symbol']] += 3.0
    # VONG 11: Wyckoff Pha D/E
    if r['is_above_ma20'] and r['is_above_ma50'] and r['bounce_from_low'] > 6.0: scores[r['symbol']] += 7.0
    # VONG 12: Wyckoff Spring recovery > 4%
    if r['bounce_from_low'] >= 4.0: scores[r['symbol']] += 5.0
    # VONG 13: SMC Displacement
    if r['has_displacement']: scores[r['symbol']] += 7.0
    # VONG 14: SMC Bullish FVG
    if r['has_fvg']: scores[r['symbol']] += 6.0
    # VONG 15: SMC Discount/OTE (20% - 75% bien do)
    if 20 <= r['pos_18m'] <= 75: scores[r['symbol']] += 5.0
    # VONG 16: Du dia tang >= 15%
    upside = (r['high_18m'] / r['price'] - 1) * 100
    if upside >= 20.0: scores[r['symbol']] += 5.0
    elif upside >= 10.0: scores[r['symbol']] += 3.0
    # VONG 17: R:R >= 2:1
    downside = (r['price'] - r['ma50']) / r['price'] * 100
    if downside > 0 and (upside / max(1, downside)) >= 1.8: scores[r['symbol']] += 5.0
    # VONG 18: Nganh dan song
    if r['sector'] in ["Ngân hàng", "Dịch vụ tài chính", "Bán lẻ", "Hàng cá nhân & Gia dụng", "Bất động sản", "Hóa chất"]: scores[r['symbol']] += 4.0
    # VONG 19: An toan thanh khoan
    if r['price'] >= 10000 and r['vol_ma20'] >= 250000: scores[r['symbol']] += 3.0
    # VONG 20: Dong pha Uptrend
    if r['ret_1w'] > 0 and r['ret_1m'] > 0: scores[r['symbol']] += 4.0

mdf['total_score'] = mdf['symbol'].map(scores)
mdf = mdf.sort_values('total_score', ascending=False).reset_index(drop=True)
mdf.to_csv("scan_results_71_stocks.csv", index=False, encoding="utf-8-sig")

print("\n" + "="*85)
print(f"📊 KET QUA HOAN TAT 20 VONG LOOP DANH GIA 16 NGANH ({len(mdf)} MA CO PHIEU)")
print("="*85)

print("\n🏆 TOP 15 CO PHIEU CO DIEM MUA CAO NHAT:")
top15 = mdf.head(15)
for idx, r in top15.iterrows():
    print(f"Top {idx+1:02d}: {r['symbol']:<5} | Nganh: {r['sector']:<25} | Gia: {r['price']:>7,.0f} d | 1W: {r['ret_1w']:>+5.1f}% | 1M: {r['ret_1m']:>+5.1f}% | RSI: {r['rsi']:>4.1f} | Diem: {r['total_score']:.0f}/100")

print("\n📌 TOP 1 MOI NGANH (16 NGANH HANG):")
for sec in SECTOR_MAP.keys():
    sec_df = mdf[mdf['sector'] == sec].sort_values('total_score', ascending=False)
    if not sec_df.empty:
        best = sec_df.iloc[0]
        print(f"• {sec:<28}: {best['symbol']:<5} (Diem: {best['total_score']:>2.0f}/100 | Gia: {best['price']:>7,.0f} d | 1M: {best['ret_1m']:>+5.1f}%)")
