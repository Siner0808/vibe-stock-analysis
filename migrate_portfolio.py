import json

with open('portfolio.json', 'r', encoding='utf-8') as f:
    p = json.load(f)

for sym, pos in p['positions'].items():
    ep = pos.get('entry_price', 0)
    if 'avg_cost' not in pos:
        pos['avg_cost'] = ep
    if 'num_entries' not in pos:
        pos['num_entries'] = 1
    if 'entry_date' not in pos and 'open_date' in pos:
        pos['entry_date'] = pos['open_date']
    elif 'entry_date' not in pos:
        pos['entry_date'] = '2026-08-24'

with open('portfolio.json', 'w', encoding='utf-8') as f:
    json.dump(p, f, ensure_ascii=False, indent=2)

print('OK - Da cap nhat portfolio.json')
for sym, pos in p['positions'].items():
    ep = pos['entry_price']
    ac = pos['avg_cost']
    qty = pos['quantity']
    print(f"  {sym}: Gia mo={ep:,.0f} | Gia von TB={ac:,.0f} | KL={qty:,}")
