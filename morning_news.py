"""
📰 BẢN TIN BUỔI SÁNG 9H — ANTIGRAVITY MARKET INTELLIGENCE
- Tối ưu hóa siêu tốc: Tải RSS đa luồng + Dịch song song
- Dịch tự động 100% Tiếng Việt (Google Chrome Engine)
- Tóm tắt trọng tâm ngắn gọn, số liệu chính xác
- Gửi Telegram @VideStock_VN_bot
"""

import os
import json
import requests
import feedparser
import re
import time
import urllib.parse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "notification_config.json")

# ─── NGUỒN TIN RSS ──────────────────────────────────────────────────────────

INTERNATIONAL_FEEDS = [
    {"name": "CNBC Markets",      "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "icon": "📺", "lang": "en"},
    {"name": "MarketWatch",       "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",                          "icon": "📈", "lang": "en"},
    {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss",                                         "icon": "💹", "lang": "en"},
    {"name": "FT Markets",        "url": "https://www.ft.com/markets?format=rss",                                               "icon": "🗞️", "lang": "en"},
]

DOMESTIC_FEEDS = [
    {"name": "VnEconomy",         "url": "https://vneconomy.vn/chung-khoan.rss",                   "icon": "🇻🇳", "lang": "vi"},
    {"name": "CafeF CK",          "url": "https://cafef.vn/chung-khoan.rss",                       "icon": "☕", "lang": "vi"},
    {"name": "Baodautu",          "url": "https://baodautu.vn/chung-khoan/rss",                    "icon": "💼", "lang": "vi"},
]

PRIORITY_KEYWORDS = [
    "fed","lãi suất","interest rate","inflation","lạm phát","gdp","recession","suy thoái",
    "powell","vnindex","vn-index","hose","dow jones","s&p","nasdaq","dầu thô","crude oil",
    "vàng","gold","trump","china","tariff","thuế quan","trade war","ngân hàng nhà nước",
    "chứng khoán","margin","ipo","room ngoại","vingroup","masan","fpt","vcb","bsr","gas",
    "mbb","ssi","dpn","vnm","quantitative","easing","tightening","yield","treasury","bond",
    "rate cut","rate hike","cắt giảm lãi suất","tăng lãi suất","ftse","msci","etf",
]

_TRANSLATE_CACHE = {}


# ─── TIỆN ÍCH ───────────────────────────────────────────────────────────────

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def send_telegram(message: str) -> bool:
    cfg = load_config()
    token = cfg.get("telegram_bot_token")
    if not token:
        print(message)
        return False

    chat_ids = set()
    if cfg.get("telegram_chat_id"):
        chat_ids.add(str(cfg.get("telegram_chat_id")))
    for cid in cfg.get("whitelist_users", {}).keys():
        chat_ids.add(str(cid))

    if not chat_ids:
        print("⚠️ Không có chat_id nào được cấu hình.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    success = True

    for chat_id in chat_ids:
        for chunk in [message[i:i+3800] for i in range(0, len(message), 3800)]:
            for attempt in range(2):
                try:
                    r = requests.post(url, json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}, timeout=25)
                    if r.status_code != 200:
                        requests.post(url, json={"chat_id": chat_id, "text": chunk}, timeout=25)
                    break
                except Exception as e:
                    if attempt == 1:
                        print(f"Telegram error for chat_id {chat_id}: {e}")
                        success = False
                    time.sleep(1)
            time.sleep(0.2)
    return success


def translate_to_vi(text: str) -> str:
    """
    Dịch siêu tốc sang Tiếng Việt 100% bằng Google Chrome Translation API.
    Có bộ nhớ cache tự động.
    """
    if not text or len(text.strip()) < 3:
        return text

    if text in _TRANSLATE_CACHE:
        return _TRANSLATE_CACHE[text]

    vi_chars = "àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
    vi_count = sum(1 for c in text.lower() if c in vi_chars)
    if vi_count > len(text) * 0.02:
        _TRANSLATE_CACHE[text] = text
        return text

    # 1. Thử qua Google Chrome Extension API
    try:
        url = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=vi&q=" + urllib.parse.quote(text[:1000])
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code == 200:
            res = r.json()
            out = None
            if isinstance(res, list) and len(res) > 0:
                if isinstance(res[0], str):
                    out = res[0]
                elif isinstance(res[0], list) and len(res[0]) > 0:
                    out = res[0][0]
            elif isinstance(res, str):
                out = res
            if out and not "error 500" in out.lower():
                _TRANSLATE_CACHE[text] = out
                return out
    except Exception:
        pass

    # 2. Fallback qua MyMemoryTranslator
    try:
        from deep_translator import MyMemoryTranslator
        res = MyMemoryTranslator(source="english", target="vietnamese").translate(text[:400])
        if res and not any(err in res.lower() for err in ["error", "limit exceeded", "mymemory"]):
            _TRANSLATE_CACHE[text] = res
            return res
    except Exception:
        pass

    _TRANSLATE_CACHE[text] = text
    return text


def clean_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text or '').strip()


def extract_key_point_raw(summary: str) -> tuple:
    """Trích xuất câu đầu tiên và các số liệu quan trọng."""
    raw = clean_html(summary or "")
    numbers = re.findall(r'[-+]?\d+\.?\d*\s*(?:%|percent|điểm|tỷ|billion|trillion|bps)', raw, re.IGNORECASE)
    
    sentences = re.split(r'[.!?。]', raw)
    first_sentence = ""
    for s in sentences:
        s = s.strip()
        if len(s) > 25:
            first_sentence = s
            break
    if not first_sentence:
        first_sentence = raw[:160]
        
    return first_sentence, numbers[:3]


def is_priority(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in PRIORITY_KEYWORDS)


def fetch_single_feed(feed_info: dict, since: datetime) -> list:
    """Tải 1 RSS feed với timeout ngắn (4s) và không dịch để tăng tốc tối đa."""
    items = []
    try:
        r = requests.get(feed_info["url"],
                         headers={"User-Agent": "Mozilla/5.0"},
                         timeout=4)
        parsed = feedparser.parse(r.content)

        for entry in parsed.entries[:12]:
            pub_time = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_time = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_time = datetime(*entry.updated_parsed[:6])
            else:
                pub_time = datetime.now()

            if pub_time < since:
                continue

            title_raw = entry.get("title", "").strip()
            summary_raw = clean_html(entry.get("summary", ""))
            lang = feed_info.get("lang", "en")
            priority = is_priority(title_raw, summary_raw)
            first_sentence, numbers = extract_key_point_raw(summary_raw)

            items.append({
                "title_raw": title_raw,
                "summary_raw": summary_raw,
                "first_sentence": first_sentence,
                "numbers": numbers,
                "link": entry.get("link", ""),
                "pub_time": pub_time,
                "source": feed_info["name"],
                "icon": feed_info["icon"],
                "priority": priority,
                "lang": lang,
            })
    except Exception as e:
        print(f"  ⚠️ Lỗi {feed_info['name']}: {type(e).__name__}")

    return items


def enrich_item_translation(item: dict) -> dict:
    """Dịch tiêu đề và trích xuất điểm chính của 1 item được chọn."""
    lang = item["lang"]
    title_raw = item["title_raw"]
    
    if lang != "vi":
        title_vi = translate_to_vi(title_raw)
        sentence_vi = translate_to_vi(item["first_sentence"])
    else:
        title_vi = title_raw
        sentence_vi = item["first_sentence"]

    if item["numbers"]:
        nums_str = " | ".join(item["numbers"])
        key_point = f"{sentence_vi.strip()} _(Số liệu: {nums_str})_"
    else:
        key_point = sentence_vi.strip()[:240]

    item["title_vi"] = title_vi
    item["key_point"] = key_point
    return item


# ─── BUILD BẢN TIN ──────────────────────────────────────────────────────────

def format_item(item: dict, show_time: bool = True) -> str:
    star = "⭐ " if item["priority"] else ""
    time_str = item["pub_time"].strftime("%H:%M")
    time_tag = f"[{time_str}] " if show_time else ""

    lines = []
    lines.append(f"{star}{item['icon']} *{time_tag}{item['title_vi'][:85]}*")

    if item.get("key_point") and item["key_point"].lower() != item["title_vi"].lower()[:len(item["key_point"])].lower():
        lines.append(f"↳ {item['key_point'][:220]}")

    return "\n".join(lines)


def build_morning_brief(is_monday: bool) -> str:
    start_t = time.time()
    now = datetime.now()
    since = (now - timedelta(days=3)) if is_monday else (now - timedelta(hours=25))

    weekday_names = {0:"Thứ Hai",1:"Thứ Ba",2:"Thứ Tư",3:"Thứ Năm",4:"Thứ Sáu"}
    today_name = weekday_names.get(now.weekday(), "")
    period = "Thứ 7 + Chủ Nhật + Sáng nay" if is_monday else "24h qua"

    all_feeds = [(f, since, "intl") for f in INTERNATIONAL_FEEDS] + [(f, since, "vn") for f in DOMESTIC_FEEDS]
    print(f"\n⚡ Tải song song {len(all_feeds)} nguồn tin RSS...")

    intl_raw, vn_raw = [], []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_single_feed, f[0], f[1]): (f[0]["name"], f[0]["icon"], f[2]) for f in all_feeds}
        for fut in as_completed(futures):
            name, icon, ftype = futures[fut]
            try:
                res = fut.result()
                print(f"  {icon} {name}: {len(res)} tin")
                if ftype == "intl":
                    intl_raw.extend(res)
                else:
                    vn_raw.extend(res)
            except Exception as e:
                print(f"  ⚠️ {name} failed: {e}")

    # Sắp xếp: Priority → Mới nhất
    intl_raw.sort(key=lambda x: (-x["priority"], -x["pub_time"].timestamp()))
    vn_raw.sort(key=lambda x: (-x["priority"], -x["pub_time"].timestamp()))

    # Lọc chỉ chọn các tin tốt nhất để dịch (giảm từ 100 tin xuống ~18 tin)
    intl_chosen = [x for x in intl_raw if x["priority"]][:5] + [x for x in intl_raw if not x["priority"]][:4]
    vn_chosen   = [x for x in vn_raw if x["priority"]][:5] + [x for x in vn_raw if not x["priority"]][:4]

    chosen_all = intl_chosen + vn_chosen
    print(f"⚡ Dịch song song {len(chosen_all)} tin trọng tâm...")

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(enrich_item_translation, chosen_all))

    total = len(intl_raw) + len(vn_raw)
    pri_count = len([x for x in intl_raw + vn_raw if x["priority"]])

    # ─── HEADER ──────────────────────────────────────────────────────────────
    msg = f"""🌅 *BẢN TIN BUỔI SÁNG — {today_name} {now.strftime('%d/%m/%Y')} 9:00*
🤖 _Antigravity Market Intelligence | Dịch & Tóm tắt tự động_
📅 Phạm vi: _{period}_
━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    # ─── TIN QUỐC TẾ ─────────────────────────────────────────────────────────
    if intl_chosen:
        msg += "\n\n🌍 *TIN QUỐC TẾ*\n"
        for item in intl_chosen:
            msg += "\n" + format_item(item) + "\n"

    # ─── TIN TRONG NƯỚC ──────────────────────────────────────────────────────
    if vn_chosen:
        msg += "\n\n🇻🇳 *THỊ TRƯỜNG CHỨNG KHOÁN VIỆT NAM*\n"
        for item in vn_chosen:
            msg += "\n" + format_item(item) + "\n"

    # ─── FOOTER ──────────────────────────────────────────────────────────────
    elapsed = time.time() - start_t
    msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 {total} tin tổng hợp | ⭐ {pri_count} tin ưu tiên
🕘 Cập nhật: {now.strftime('%H:%M:%S')} (Xử lý: {elapsed:.1f}s) — _Chúc giao dịch thành công!_ 🚀
_⭐ = Tin tác động trực tiếp đến thị trường_"""

    return msg


# ─── MAIN ────────────────────────────────────────────────────────────────────

def run_morning_news():
    now = datetime.now()
    weekday = now.weekday()

    if weekday > 4:
        print("Cuối tuần — không gửi bản tin.")
        return

    is_monday = (weekday == 0)
    wday_names = ["Thứ Hai","Thứ Ba","Thứ Tư","Thứ Năm","Thứ Sáu"]
    print(f"📅 {wday_names[weekday]} {now.strftime('%d/%m/%Y')} — Bắt đầu xây dựng bản tin...")
    if is_monday:
        print("   → Chế độ Thứ Hai: quét bổ sung Thứ 7 + Chủ Nhật")

    brief = build_morning_brief(is_monday)
    success = send_telegram(brief)

    status = "✅ Đã gửi Telegram" if success else "⚠️ Lỗi Telegram"
    print(f"\n{status}")

    report_path = os.path.join(BASE_DIR, "morning_brief_latest.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(brief)
    print(f"💾 Lưu: {report_path}")


if __name__ == "__main__":
    run_morning_news()
