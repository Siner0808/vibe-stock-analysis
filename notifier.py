import os
import json
import requests
import subprocess
from datetime import datetime

# Doc cau hinh tu file config.json neu co
CONFIG_FILE = "notification_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "zalo_webhook_url": "",
        "zalo_oa_access_token": "",
        "zalo_user_id": "",
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        "windows_toast_enabled": True
    }

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def send_windows_toast(title, message):
    """Bắn thông báo trực tiếp lên góc phải màn hình Windows (Windows Notification)"""
    try:
        # Su dung PowerShell de hien Toast Notification tren Windows ma khong can thu vien ngoai
        ps_cmd = f"""
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $textNodes = $template.GetElementsByTagName("text")
        $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null
        $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Antigravity AI Trading").Show($toast)
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=5)
        return True
    except Exception as e:
        print(f"Windows Toast error: {e}")
        return False

def send_zalo_webhook(message, webhook_url=None):
    """Gửi thông báo qua Zalo Webhook / Zalo Chatbot"""
    cfg = load_config()
    url = webhook_url or cfg.get("zalo_webhook_url")
    if not url:
        return False, "Chưa cấu hình Zalo Webhook URL"
    
    payload = {
        "text": message,
        "content": message
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200, res.text
    except Exception as e:
        return False, str(e)

def send_zalo_oa(message, user_id=None, access_token=None):
    """Gửi qua Zalo Official Account (OA) API"""
    cfg = load_config()
    token = access_token or cfg.get("zalo_oa_access_token")
    uid = user_id or cfg.get("zalo_user_id")
    
    if not token or not uid:
        return False, "Chưa có Access Token hoặc User ID Zalo OA"
    
    url = "https://openapi.zalo.me/v3.0/oa/message/cs"
    headers = {"access_token": token, "Content-Type": "application/json"}
    payload = {
        "recipient": {"user_id": uid},
        "message": {"text": message}
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        return res.status_code == 200, res.json()
    except Exception as e:
        return False, str(e)

def send_telegram(message, bot_token=None, chat_id=None):
    """Gửi qua Telegram Bot (Cực kỳ tiện lợi & miễn phí 100%)"""
    cfg = load_config()
    token = bot_token or cfg.get("telegram_bot_token")
    cid = chat_id or cfg.get("telegram_chat_id")
    if not token or not cid:
        return False, "Chưa cấu hình Telegram Bot Token hoặc Chat ID"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": cid, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200, res.text
    except Exception as e:
        return False, str(e)

def broadcast_alert(title, message):
    """Phát thông báo đồng thời qua tất cả các kênh đã bật"""
    cfg = load_config()
    full_msg = f"🚨 {title}\n\n{message}\n\n⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    
    # 1. Windows Toast
    if cfg.get("windows_toast_enabled", True):
        send_windows_toast(title, message)
    
    # 2. Zalo Webhook / OA
    if cfg.get("zalo_webhook_url"):
        send_zalo_webhook(full_msg)
    elif cfg.get("zalo_oa_access_token") and cfg.get("zalo_user_id"):
        send_zalo_oa(full_msg)
        
    # 3. Telegram (nếu có)
    if cfg.get("telegram_bot_token") and cfg.get("telegram_chat_id"):
        send_telegram(full_msg)

if __name__ == "__main__":
    print("Testing Notification System...")
    broadcast_alert("ANTIGRAVITY AI TRADING", "Thử nghiệm gửi thông báo cảnh báo thành công!")
    print("Test finished.")
