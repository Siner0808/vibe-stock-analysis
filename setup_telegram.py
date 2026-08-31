import requests
import json
import time

import os

CONFIG_FILE = "notification_config.json"

def get_bot_token():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                token = cfg.get("telegram_bot_token")
                if token:
                    return token
        except Exception:
            pass
    return os.getenv("TELEGRAM_BOT_TOKEN", "")

BOT_TOKEN = get_bot_token()

def check_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if data.get("ok"):
            results = data.get("result", [])
            if results:
                # Lay update moi nhat
                latest_msg = results[-1].get("message", {})
                chat = latest_msg.get("chat", {})
                chat_id = chat.get("id")
                first_name = chat.get("first_name", "Bạn")
                
                if chat_id:
                    print(f"✅ Tim thay Chat ID cua {first_name}: {chat_id}")
                    
                    # Luu vao config
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    
                    cfg["telegram_bot_token"] = BOT_TOKEN
                    cfg["telegram_chat_id"] = str(chat_id)
                    
                    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                        json.dump(cfg, f, ensure_ascii=False, indent=2)
                    
                    # Gui tin nhan chao mung test
                    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    welcome_text = f"🎉 *XÁC THỰC THÀNH CÔNG!*\n\nChào {first_name}, Bot AI Trading Antigravity đã kết nối thành công với tài khoản Telegram của bạn.\n\nTừ bây giờ, mọi sự kiện: Mua mới, Chốt lời (+15%), Cắt lỗ (-6%) và Trailing Stop sẽ được tự động gửi trực tiếp về đây!"
                    requests.post(send_url, json={"chat_id": chat_id, "text": welcome_text, "parse_mode": "Markdown"})
                    return True, chat_id
            else:
                print("Chua co tin nhan nao gui den bot. Xin hay nhan /start cho bot tren Telegram.")
        else:
            print("API Telegram tra ve loi:", data)
    except Exception as e:
        print("Loi ket noi Telegram:", e)
    return False, None

if __name__ == "__main__":
    check_updates()
