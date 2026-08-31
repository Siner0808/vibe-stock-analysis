import json
from notifier import broadcast_alert

with open('portfolio.json', 'r', encoding='utf-8') as f:
    p = json.load(f)

nav = p["portfolio_value"]
cash = p["cash_balance"]

msg = f"""📊 TỔNG QUAN SỔ LỆNH AI (VỐN 1 TỶ VNĐ)
━━━━━━━━━━━━━━━━━━━━
💰 Tổng tài sản NAV: {nav:,.0f} VNĐ
💵 Tiền mặt dự phòng: {cash:,.0f} VNĐ

📋 5 Vị thế giải ngân đợt 1 (Đã khớp):
1. ⛽ BSR: 7,200 CP @ 27.65k (199.1 tr) | SL: 26.0k | TP: 31.8k
2. 📈 SSI: 9,400 CP @ 21.25k (199.8 tr) | SL: 20.0k | TP: 24.4k
3. 🧪 DPM: 8,800 CP @ 22.65k (199.3 tr) | SL: 21.3k | TP: 26.0k
4. ⚡ GAS: 2,300 CP @ 85.70k (197.1 tr) | SL: 80.6k | TP: 98.6k
5. 🏭 GEX: 7,500 CP @ 26.60k (199.5 tr) | SL: 25.0k | TP: 30.6k

🛡️ Kỷ luật giao dịch định lượng:
• Chốt lời (Take Profit): +15%
• Cắt lỗ (Stop Loss): -6%
• Trailing Stop: Tự động bảo vệ lãi khi đạt > +8%

🤖 Hệ thống đang giám sát liên tục theo thời gian thực và sẽ tự động gửi tin nhắn cho bạn khi có biến động!"""

broadcast_alert("KẾT NỐI HỆ THỐNG THÀNH CÔNG", msg)
print("Welcome report sent successfully!")
