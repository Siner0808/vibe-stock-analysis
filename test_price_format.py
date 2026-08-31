"""
Test và kiểm tra logic chuẩn hóa giá
"""
def format_price_k(price):
    if price is None:
        return "N/A"
    price_k = price / 1000.0 if price > 500 else float(price)
    return f"{price_k:.2f}k"

def format_price_vnd(price):
    if price is None:
        return "N/A"
    price_vnd = price if price > 500 else price * 1000.0
    return f"{price_vnd:,.0f} đ"

# Test với các trường hợp:
tests = [73.0, 72.95, 72.6, 73000, 72950, 21.25, 21250, 85.7, 85700]
for t in tests:
    print(f"Input: {t:8} -> k: {format_price_k(t):>8} | vnd: {format_price_vnd(t):>12}")
