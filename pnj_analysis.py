import pandas as pd
import numpy as np
from vnstock import Quote, Company, Reference, Fundamental

sym = 'PNJ'
q = Quote(symbol=sym, source='VCI')
df = q.history(start='2025-01-01', end='2026-08-24')
c = Company(symbol=sym, source='VCI')
overview = c.overview()

df['time'] = pd.to_datetime(df['time'])
df = df.sort_values('time').reset_index(drop=True)

df['MA20'] = df['close'].rolling(20).mean()
df['MA50'] = df['close'].rolling(50).mean()
df['MA200'] = df['close'].rolling(200).mean()
df['vol_ma20'] = df['volume'].rolling(20).mean()
df['vol_ratio'] = df['volume'] / df['vol_ma20']

delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

latest = df.iloc[-1]
p_now = latest['close'] * 1000
p_high_1y = df['high'].max() * 1000
p_low_1y = df['low'].min() * 1000
p_high_6m = df.tail(130)['high'].max() * 1000
p_low_6m = df.tail(130)['low'].min() * 1000

print('=== THONG TIN CO BAN PNJ ===')
if not overview.empty:
    print('Gia hien tai:', overview['current_price'].values[0])
    cap = overview['market_cap'].values[0]
    print(f'Von hoa: {cap:,.0f} d')
    if 'pe' in overview.columns:
        print('P/E:', overview['pe'].values[0])
    if 'pb' in overview.columns:
        print('P/B:', overview['pb'].values[0])

print(f'Gia dong cua gan nhat: {p_now:,.0f} d')
ma20 = latest['MA20']*1000
ma50 = latest['MA50']*1000
ma200 = latest['MA200']*1000 if not np.isnan(latest['MA200']) else 0
print(f'MA20: {ma20:,.0f} d | MA50: {ma50:,.0f} d | MA200: {ma200:,.0f} d')
print(f'RSI(14): {latest["RSI"]:.1f}')
print(f'Bien do 1 nam qua: {p_low_1y:,.0f} d - {p_high_1y:,.0f} d')
print(f'Bien do 6 thang qua: {p_low_6m:,.0f} d - {p_high_6m:,.0f} d')

print('\nTop 5 cay nen Volume dot bien nhat (1.5 nam qua):')
top_vol = df.sort_values('volume', ascending=False).head(5)
for _, r in top_vol.iterrows():
    t = r['time'].strftime('%Y-%m-%d')
    o, h, l, cl, v = r['open']*1000, r['high']*1000, r['low']*1000, r['close']*1000, r['volume']
    vr = r['vol_ratio']
    print(f'Ngay {t}: O={o:,.0f} | H={h:,.0f} | L={l:,.0f} | C={cl:,.0f} | Vol={v:,.0f} ({vr:.1f}x MA20)')

print('\nFVG (Fair Value Gap) 20 phien gan day:')
for i in range(len(df)-20, len(df)-1):
    c1 = df.iloc[i-1]
    c2 = df.iloc[i]
    c3 = df.iloc[i+1]
    t2 = c2['time'].strftime('%Y-%m-%d')
    if c3['low'] > c1['high']:
        fvg_bot = c1['high'] * 1000
        fvg_top = c3['low'] * 1000
        print(f'  [BULLISH FVG] Ngay {t2}: {fvg_bot:,.0f} - {fvg_top:,.0f} d (Range: {fvg_top-fvg_bot:,.0f} d)')
    elif c3['high'] < c1['low']:
        fvg_top = c1['low'] * 1000
        fvg_bot = c3['high'] * 1000
        print(f'  [BEARISH FVG] Ngay {t2}: {fvg_bot:,.0f} - {fvg_top:,.0f} d')

print('\n15 phien giao dich gan nhat:')
for _, r in df.tail(15).iterrows():
    t = r['time'].strftime('%Y-%m-%d')
    o, h, l, cl, v = r['open']*1000, r['high']*1000, r['low']*1000, r['close']*1000, r['volume']
    print(f'{t}: Open={o:,.0f}, High={h:,.0f}, Low={l:,.0f}, Close={cl:,.0f}, Vol={v:,.0f}')
