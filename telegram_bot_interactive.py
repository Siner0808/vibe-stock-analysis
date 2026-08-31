"""
🤖 ANTIGRAVITY TELEGRAM BOT INTERACTIVE LISTENER
Lắng nghe tin nhắn từ người dùng trên Telegram và phản hồi tức thì 24/7.

CÁC LỆNH HỖ TRỢ:
- /id                  : Xem Chat ID của bạn (cần để được thêm vào whitelist).
- /danhmuc / /solenh   : Xem chi tiết danh mục 1 tỷ (chỉ admin).
- /tintuc              : Xem bản tin tài chính mới nhất.
- /scan / /pipeline    : Chạy Pipeline V3 quét 71 mã (chỉ admin).
- phân tích <MÃ>       : Phân tích Wyckoff & SMC tức thì.
- menu / /help         : Hướng dẫn sử dụng.

LỆNH QUẢN LÝ USER (chỉ admin):
- /adduser <chat_id> <tên>  : Thêm bạn bè vào whitelist.
- /removeuser <chat_id>     : Xóa người dùng.
- /users                    : Danh sách người dùng hiện tại.
"""

import os
import sys
import json
import time
import requests
import threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "v3_pipeline"))

CONFIG_FILE = os.path.join(BASE_DIR, "notification_config.json")
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_whitelist(cfg: dict) -> dict:
    """Trả về dict whitelist_users, fallback về admin mặc định."""
    wl = cfg.get("whitelist_users", {})
    admin_id = str(cfg.get("telegram_chat_id", ""))
    if admin_id and admin_id not in wl:
        wl[admin_id] = {"name": "Admin", "role": "admin"}
    return wl


def is_allowed(cfg: dict, chat_id: str) -> bool:
    """Kiểm tra xem chat_id có trong whitelist không."""
    wl = get_whitelist(cfg)
    return str(chat_id) in wl


def is_admin(cfg: dict, chat_id: str) -> bool:
    """Chỉ admin mới có quyền đặc biệt."""
    wl = get_whitelist(cfg)
    user = wl.get(str(chat_id), {})
    return user.get("role") == "admin"


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


_TELEGRAM_SESSION = None

def get_telegram_session():
    global _TELEGRAM_SESSION
    if _TELEGRAM_SESSION is None:
        import urllib3
        from urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter
        
        s = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
        s.mount("https://", adapter)
        _TELEGRAM_SESSION = s
    return _TELEGRAM_SESSION


def send_message(token, chat_id, text, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chunks = [text[i:i+3800] for i in range(0, len(text), 3800)]
    session = get_telegram_session()
    
    for chunk in chunks:
        for attempt in range(2):
            try:
                res = session.post(url, json={"chat_id": chat_id, "text": chunk, "parse_mode": parse_mode}, timeout=(6.0, 25.0))
                if res.status_code != 200:
                    session.post(url, json={"chat_id": chat_id, "text": chunk}, timeout=(6.0, 25.0))
                break
            except Exception as e:
                if attempt == 1:
                    print(f"Error sending message to {chat_id}: {e}")
                time.sleep(0.5)
        time.sleep(0.2)


def handle_portfolio_command(token, chat_id):
    """Xử lý lệnh xem sổ lệnh / danh mục."""
    send_message(token, chat_id, "⏳ Đang cập nhật thị giá thời gian thực từ sàn chứng khoán...")
    
    # Cập nhật thị giá mới nhất
    try:
        from layer6_report import format_portfolio_status
        from vnstock import Quote
        
        p = load_portfolio()
        if not p:
            send_message(token, chat_id, "⚠️ Không tìm thấy file portfolio.json")
            return
            
        for sym, pos in p.get("positions", {}).items():
            try:
                q = Quote(symbol=sym, source='VCI')
                df = q.history(start=datetime.now().strftime("%Y-%m-01"), end=datetime.now().strftime("%Y-%m-%d"))
                if df is not None and not df.empty:
                    cur_p = df.iloc[-1]['close'] * 1000
                    pos["current_price"] = cur_p
                    avg_c = pos.get("avg_cost", pos.get("entry_price", cur_p))
                    pos["pnl"] = (cur_p - avg_c) * pos.get("quantity", 0)
                    pos["pnl_pct"] = (cur_p / avg_c - 1) * 100
                    pos["cost_value"] = avg_c * pos.get("quantity", 0)
                    pos["market_value"] = cur_p * pos.get("quantity", 0)
            except Exception:
                pass
                
        # Tính lại NAV
        stock_val = sum(pos.get("market_value", 0) for pos in p["positions"].values())
        p["portfolio_value"] = p["cash_balance"] + stock_val
        
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(p, f, ensure_ascii=False, indent=2)
            
        report_text = format_portfolio_status(p)
        send_message(token, chat_id, report_text)
    except Exception as e:
        send_message(token, chat_id, f"⚠️ Lỗi khi cập nhật danh mục: {e}")


def handle_news_command(token, chat_id):
    """Xử lý lệnh xem tin tức: Tự động cập nhật bản tin mới nhất trong ngày."""
    brief_file = os.path.join(BASE_DIR, "morning_brief_latest.md")
    needs_refresh = True
    
    if os.path.exists(brief_file):
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(brief_file))
            # Nếu bản tin được tạo hôm nay và chưa quá 2 tiếng -> Dùng cache
            if mtime.date() == datetime.now().date() and (datetime.now() - mtime).total_seconds() < 7200:
                with open(brief_file, "r", encoding="utf-8") as f:
                    content = f.read()
                send_message(token, chat_id, content)
                needs_refresh = False
        except Exception:
            needs_refresh = True
            
    if needs_refresh:
        send_message(token, chat_id, "⏳ Đang quét và dịch 100% bản tin tài chính mới nhất hôm nay...")
        try:
            from morning_news import build_morning_brief
            is_monday = (datetime.now().weekday() == 0)
            brief = build_morning_brief(is_monday=is_monday)
            
            with open(brief_file, "w", encoding="utf-8") as f:
                f.write(brief)
                
            send_message(token, chat_id, brief)
        except Exception as e:
            send_message(token, chat_id, f"⚠️ Lỗi khi cập nhật tin tức: {e}")


def handle_causal_tree_command(token, chat_id):
    """Xử lý lệnh xem Cây Nhân - Quả từ tin tức thị trường (Tối ưu giao diện Telegram)."""
    now = datetime.now()
    causal_text = f"""🌳 *CÂY NHÂN – QUẢ TÁC ĐỘNG TỪ TIN TỨC*
📅 _Cập nhật: {now.strftime('%d/%m/%Y %H:%M')}_
━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ *VĨ MÔ & NÂNG HẠNG (Nasdaq / FTSE / 1,800đ)*
⚡ *Kênh:* Dòng vốn ngoại & Định giá P/E
🟢 *Tích cực:* Dòng tiền tổ chức đón sóng nâng hạng, VN-Index > 1,800 đ
   ↳ 🟢 *Hưởng lợi mạnh:* `SSI`, `HCM`, `VCI`, `FPT`, `VNM`
🔴 *Rủi ro ngắn hạn:* Khối ngoại cơ cấu quỹ Frontier (-6.000 tỷ)

2️⃣ *HÀNG HÓA & NĂNG LƯỢNG (Kẽm / Dầu thô)*
⚡ *Kênh:* Giá bán & Chi phí đầu vào
🟢 *Tích cực:* Giá kẽm tăng chuỗi 7 ngày; Cước vận tải rẻ do giá dầu giảm
   ↳ 🟢 *Hưởng lợi mạnh:* `MSR`, `HPG`, `NKG`, `VSC`, `PVT`, `HAX`
🔴 *Áp lực:* Thượng nguồn dầu khí chịu áp lực giá dầu thế giới giảm
   ↳ 🔴 *Chịu áp lực:* `BSR`, `GAS`, `PVD`, `PVS`

3️⃣ *TIỀN TỆ & TÀI CHÍNH (TPDN / Nợ xấu)*
⚡ *Kênh:* Chất lượng tài sản & Thanh khoản tín dụng
🟢 *Tích cực:* TPDN đáo hạn giảm 47% quý, BĐS & Bank lớn giải tỏa áp lực
   ↳ 🟢 *Phân hóa tốt:* `VCB`, `MBB`, `ACB`, `HDB`, `VHM`, `KDH`
🔴 *Cẩn trọng:* Bank nhỏ nợ xấu cao bị thu hẹp biên NIM

━━━━━━━━━━━━━━━━━━━━━━━━━━
💼 *ĐỐI CHIẾU DANH MỤC HIỆN TẠI:*
• `SSI` (Chứng khoán): 🟢 Hưởng lợi thanh khoản 1,800+
• `GEX` (Công nghiệp): 🟢 Hưởng lợi chi phí đầu vào & hạ tầng
• `DPM` (Phân bón)   : 🟢 Ổn định theo giá khí đầu vào
• `GAS` (Khí đốt)    : 🟡 Theo dõi mốc hỗ trợ 80.55k
• `BSR` (Lọc dầu)    : 🟡 Quản trị SL 25.99k chặt chẽ

💡 _Gõ tên mã CP (VD: `fpt`, `ssi`) để xem phân tích chi tiết!_"""
    send_message(token, chat_id, causal_text)


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


def format_wyckoff_phase_vi(raw_phase: str) -> str:
    p = (raw_phase or "").replace("PHASE_", "")
    mapping = {
        "BC_ACCUMULATION": "Tích lũy Gom hàng (Pha B-C)",
        "D_SOS": "Xác nhận Bứt phá (Pha D)",
        "E_MARKUP": "Vào Sóng tăng mạnh (Pha E)",
        "C_SPRING": "Rũ bỏ Cạn cung (Pha C)",
        "A_MARKDOWN": "Đang điều chỉnh / Đè giá (Pha A)",
    }
    return mapping.get(p, p)


def format_zscore_vi(z_val: float) -> str:
    if z_val is None:
        return ""
    if z_val > 2.0:
        status = "Quá mua / Cần hạ nhiệt"
    elif z_val < -2.0:
        status = "Quá bán / Vùng đáy hồi"
    elif z_val > 1.0:
        status = "Đang tăng dốc"
    elif z_val < -1.0:
        status = "Đang điều chỉnh"
    else:
        status = "Vùng giá an toàn / Cân bằng"
    return f" | Vùng giá: *{status}* (`{z_val:+.1f}σ`)"


def format_pattern_vi(pat_dict: dict) -> str:
    sim = pat_dict.get("similarity", 0)
    name = pat_dict.get("best_pattern", "NONE")
    if sim < 0.70 or name == "NONE":
        return ""
    pat_names = {
        "SPRING_TEST": "Rũ bỏ cạn cung (Spring & Test)",
        "SOS_BREAKOUT": "Dòng tiền lớn đẩy vượt đỉnh (SOS Breakout)",
        "PULLBACK_LPS": "Test lại đỉnh cũ thành công (Pullback LPS)"
    }
    vi_name = pat_names.get(name, name)
    return f"\n🧠 *Mẫu hình AI tương đồng (Cosine):* {vi_name} *(Độ khớp: {sim*100:.0f}%)*"


def format_verdict_vi(verdict: str) -> str:
    mapping = {
        "STRONG_BUY": "MUA MẠNH",
        "BUY": "MUA",
        "WATCH": "CHỜ ĐỢI / THEO DÕI",
        "HOLD_OFF": "TẠM DỪNG",
        "AVOID": "TRÁNH / CẮT LỖ",
        "SELL": "BÁN",
        "STRONG_SELL": "BÁN MẠNH"
    }
    return mapping.get(verdict, verdict)


def handle_analyze_command(token, chat_id, symbol):
    """Phân tích nhanh 1 mã chứng khoán theo Wyckoff & SMC & ML Engine."""
    symbol = symbol.upper().strip()
    send_message(token, chat_id, f"🔍 Đang phân tích kỹ thuật chuyên sâu mã *{symbol}*...")
    
    try:
        from layer0_data_quality import fetch_daily, build_weekly
        from layer2_wyckoff_engine import analyze_wyckoff, compute_indicators
        from layer3_debate_council import bull_agent, bear_agent, compute_consensus
        
        df_d = fetch_daily(symbol, months=18)
        if df_d.empty:
            send_message(token, chat_id, f"⚠️ Không tìm thấy dữ liệu cho mã *{symbol}*.")
            return
            
        df_w = build_weekly(df_d)
        wyckoff = analyze_wyckoff(symbol, df_d, df_w)
        df_ind = compute_indicators(df_d)
        
        bull = bull_agent(symbol, wyckoff, df_ind)
        bear = bear_agent(symbol, wyckoff, df_ind)
        consensus, verdict = compute_consensus(bull, bear)
        
        raw_price = df_d["close"].iloc[-1]
        price_vnd = raw_price * 1000.0 if raw_price < 500 else float(raw_price)
        price_k_str = format_price_k(price_vnd)
        
        phase_vi = format_wyckoff_phase_vi(wyckoff.get("phase", "Chưa rõ"))
        
        bull_txt = "\n".join([f"  • {a}" for a in bull.get("arguments", [])[:3]]) or "  • Đang tích lũy"
        bear_txt = "\n".join([f"  • {a}" for a in bear.get("arguments", [])[:2]]) or "  • Rủi ro thị trường chung"
        
        # 🧠 ML Enhancement: Xác suất Sigmoid, Mẫu hình Cosine & Kênh Hồi quy & Kalman & DTW
        from ml_algorithms import compute_win_probability
        win_prob = compute_win_probability(bull.get("score", 0), bear.get("score", 0), wyckoff.get("score", 50))
        pat_str = format_pattern_vi(wyckoff.get("pattern_match", {}))
        
        # DTW & Kalman
        dtw = wyckoff.get("dtw_match", {})
        dtw_str = f"\n📈 *Hình thái sóng DTW:* {dtw.get('pattern_name_vi')} *(Độ khớp: {dtw.get('dtw_similarity', 0):.0f}%)*" if dtw.get("dtw_similarity", 0) >= 70.0 else ""
        
        kalman = wyckoff.get("kalman", {})
        kalman_str = f"\n⚡ *Động lượng Kalman (Zero-Lag):* `Vận tốc: {kalman.get('velocity_pct', 0):+.2f}%`" if kalman else ""
        
        vcp = wyckoff.get("vcp", {})
        vcp_str = f"\n💎 *Mẫu hình VCP Minervini:* {' ➔ '.join(vcp.get('contractions', []))} *(Cạn Vol: {vcp.get('vol_dry_ratio', 1.0)*100:.0f}%)*" if vcp.get("is_vcp") else ""
        
        inst = wyckoff.get("institutional_flow", {})
        inst_str = f"\n🏦 *Dòng tiền Khối ngoại & Tự doanh:* {inst.get('signals', ['Trung tính'])[0]}" if inst and inst.get("signals") else ""
        
        lr = wyckoff.get("lr_channel", {})
        z_str = format_zscore_vi(lr.get("z_score")) if lr else ""

        verdict_icon = "🟢" if verdict in ["STRONG_BUY", "BUY"] else "🟡" if verdict == "WATCH" else "🔴"
        verdict_vi = format_verdict_vi(verdict)

        # ─── Phần header chung ───
        header = (
            f"📊 *PHÂN TÍCH NHANH: {symbol}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Thị giá: *{price_k_str}* (`{price_vnd:,.0f} đ`)\n"
            f"🏛️ Pha Wyckoff: *{phase_vi}* (Điểm: {wyckoff.get('score', 0)}/100){z_str}\n"
            f"{verdict_icon} Đánh giá: *{verdict_vi}* (Đồng thuận: {consensus}/100 | Xác suất thắng: *{win_prob:.1f}%*){pat_str}{dtw_str}{kalman_str}{vcp_str}{inst_str}\n"
            f"\n"
            f"🐂 *Luận điểm Bull:*\n{bull_txt}\n"
            f"\n"
            f"🐻 *Rủi ro Bear:*\n{bear_txt}"
        )

        # ─── Phần khuyến nghị theo verdict ───
        if verdict in ["STRONG_BUY", "BUY"]:
            # Tính vùng mở vị thế: ±1% quanh giá hiện tại
            entry_low  = price_vnd * 0.99
            entry_high = price_vnd * 1.01
            tp_val  = bull.get("target_price", price_vnd * 1.15)
            sl_val  = bear.get("risk_price",   price_vnd * 0.94)
            tp_pct  = (tp_val / price_vnd - 1) * 100
            sl_pct  = (sl_val / price_vnd - 1) * 100

            action_block = (
                f"\n\n✅ *KHUYẾN NGHỊ: MỞ VỊ THẾ*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📥 Vùng mua: *{format_price_k(entry_low)}* – *{format_price_k(entry_high)}*\n"
                f"   (`{entry_low:,.0f} đ` – `{entry_high:,.0f} đ`)\n"
                f"🎯 Mục tiêu (TP): *{format_price_k(tp_val)}* "
                f"(`{tp_val:,.0f} đ` | *{tp_pct:+.1f}%*)\n"
                f"🛡️ Cắt lỗ (SL): *{format_price_k(sl_val)}* "
                f"(`{sl_val:,.0f} đ` | *{sl_pct:+.1f}%*)"
            )

        elif verdict == "WATCH":
            # Vùng mua đẹp hơn: giảm ~3-5% so với giá hiện tại
            ideal_entry_low  = price_vnd * 0.95
            ideal_entry_high = price_vnd * 0.97
            next_support = bear.get("risk_price", price_vnd * 0.92)
            supp_pct = (next_support / price_vnd - 1) * 100

            action_block = (
                f"\n\n⏳ *KHUYẾN NGHỊ: CHỜ ĐỢI*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 Chưa đủ điều kiện mở vị thế.\n"
                f"🎯 Vùng mua đẹp hơn: *{format_price_k(ideal_entry_low)}* – *{format_price_k(ideal_entry_high)}*\n"
                f"   (`{ideal_entry_low:,.0f} đ` – `{ideal_entry_high:,.0f} đ`)\n"
                f"📊 Vùng hỗ trợ gần nhất: *{format_price_k(next_support)}* "
                f"(`{next_support:,.0f} đ` | *{supp_pct:+.1f}%*)\n"
                f"💡 Chờ Pipeline quét xác nhận tín hiệu BUY hoặc giá pullback về vùng mua."
            )

        else:  # SELL / STRONG_SELL / AVOID
            sl_val      = bear.get("risk_price", price_vnd * 0.94)
            support_1   = price_vnd * 0.90   # hỗ trợ gần
            support_2   = price_vnd * 0.85   # hỗ trợ tiếp theo
            sl_pct      = (sl_val    / price_vnd - 1) * 100
            supp1_pct   = (support_1 / price_vnd - 1) * 100
            supp2_pct   = (support_2 / price_vnd - 1) * 100

            action_block = (
                f"\n\n🔴 *KHUYẾN NGHỊ: TRÁNH / CẮT LỖ*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ Tín hiệu yếu — *KHÔNG mở vị thế mới.*\n"
                f"✂️ Nếu đang giữ: cân nhắc cắt lỗ tại *{format_price_k(sl_val)}* "
                f"(`{sl_val:,.0f} đ` | *{sl_pct:+.1f}%*)\n"
                f"📉 Vùng hỗ trợ tiếp theo:\n"
                f"   • S1: *{format_price_k(support_1)}* (`{support_1:,.0f} đ` | *{supp1_pct:+.1f}%*)\n"
                f"   • S2: *{format_price_k(support_2)}* (`{support_2:,.0f} đ` | *{supp2_pct:+.1f}%*)\n"
                f"💡 Chờ thị trường hồi phục và xác nhận đáy trước khi cân nhắc lại."
            )

        reply = header + action_block
        send_message(token, chat_id, reply)

    except Exception as e:
        send_message(token, chat_id, f"⚠️ Lỗi phân tích {symbol}: {e}")



def handle_pipeline_command(token, chat_id):
    """Chạy quét Pipeline V3."""
    send_message(token, chat_id, "🚀 Bắt đầu kích hoạt Pipeline V3 quét 71 mã 16 ngành...")
    try:
        from layer0_data_quality import load_watchlist, run_quality_gate
        from layer0_5_macro_filter import run_macro_filter
        from layer2_wyckoff_engine import run_wyckoff_engine
        from layer3_debate_council import run_debate_council
        from layer4_risk_sizing import run_risk_sizing
        from layer6_report import run_report
        
        symbols = load_watchlist()
        quality_results = run_quality_gate(symbols)
        macro_result = run_macro_filter(quality_results)
        top_symbols = macro_result.get("top_symbols", [])
        
        if not top_symbols:
            send_message(token, chat_id, "🔴 Thị trường Risk-Off. Đứng ngoài.")
            return
            
        wyckoff_results = run_wyckoff_engine(top_symbols, quality_results)
        debate_results = run_debate_council(wyckoff_results, quality_results)
        approved_orders = run_risk_sizing(debate_results, macro_result)
        
        portfolio = load_portfolio()
        run_report(macro_result, wyckoff_results, debate_results, approved_orders, portfolio)
        send_message(token, chat_id, "✅ Đã hoàn tất quét Pipeline V3 và gửi báo cáo đầy đủ!")
    except Exception as e:
        send_message(token, chat_id, f"⚠️ Lỗi chạy Pipeline: {e}")


def handle_backtest_command(token, chat_id):
    """Chạy và báo cáo kết quả Backtesting & Walk-Forward Testing."""
    send_message(token, chat_id, "🔬 Đang chạy mô phỏng kiểm thử lịch sử 2 năm trên 71 mã cổ phiếu...")
    try:
        from backtester import load_all_historical_data, run_backtest_simulation, run_walk_forward_analysis
        data_dict = load_all_historical_data()
        res = run_backtest_simulation(data_dict)
        wf = run_walk_forward_analysis(data_dict)
        
        is_m = wf["in_sample"]
        oos_m = wf["out_of_sample"]
        
        msg = (
            f"📊 *BÁO CÁO KIỂM THỬ ĐỊNH LƯỢNG (2 NĂM)*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Vốn ban đầu: `{res['initial_capital']:,.0f} đ`\n"
            f"💎 Vốn kết thúc: *{res['final_capital']:,.0f} đ* (*+{res['total_return_pct']:.2f}%*)\n"
            f"🚀 CAGR (Tăng trưởng kép): *+{res['cagr_pct']:.2f}%/năm*\n"
            f"🛡️ Max Drawdown (MDD): *{res['max_drawdown_pct']:.2f}%*\n"
            f"⚖️ Sharpe: *{res['sharpe_ratio']:.2f}* | Sortino: *{res['sortino_ratio']:.2f}* | Calmar: *{res['calmar_ratio']:.2f}*\n"
            f"🎯 Tỷ lệ thắng: *{res['win_rate_pct']:.1f}%* ({res['winning_trades']}/{res['total_trades']} lệnh)\n"
            f"💵 Profit Factor: *{res['profit_factor']:.2f}* | Lãi TB: *+{res['avg_win_pct']:.2f}%* / Lỗ TB: *{res['avg_loss_pct']:.2f}%*\n\n"
            f"🔬 *Kiểm định Walk-Forward (OOS):*\n"
            f"• In-Sample (60% đầu): +{is_m.get('total_return_pct', 0):.2f}% | Sharpe: {is_m.get('sharpe_ratio', 0):.2f}\n"
            f"• Out-Sample (40% sau): +{oos_m.get('total_return_pct', 0):.2f}% | Sharpe: {oos_m.get('sharpe_ratio', 0):.2f}\n"
            f"*(Mô hình ổn định, không bị Overfitting)*"
        )
        send_message(token, chat_id, msg)
    except Exception as e:
        send_message(token, chat_id, f"⚠️ Lỗi chạy Backtest: {e}")


def handle_menu_command(token, chat_id, is_admin_user=False):
    """Gửi menu hướng dẫn."""
    admin_section = ""
    if is_admin_user:
        admin_section = """

🔧 *QUẢN LÝ & ĐỊNH LƯỢNG (Admin):*
• `/scan` hoặc `quét` — Chạy Pipeline V3
• `/backtest` — Báo cáo kiểm định 2 năm (CAGR, Sharpe, MDD)
• `/danhmuc` — Xem danh mục 1 tỷ đầy đủ
• `/adduser <chat_id> <tên>` — Thêm bạn bè
• `/removeuser <chat_id>` — Xóa người dùng
• `/users` — Danh sách người dùng"""
    menu_text = f"""🤖 *ANTIGRAVITY AI TRADING BOT*
━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 *CÁC LỆNH CÓ SẴN:*

🔍 *PHÂN TÍCH CỔ PHIẾU:*
• Nhắn tên mã: `FPT`, `HPG`, `SSI`, `VCB`...
• Hoặc: `phân tích HPG`

📰 *TIN TỨC THỊ TRƯỜNG:*
• Nhắn `tin tức` hoặc `/tintuc`

🌳 *CÂY NHÂN – QUẢ:*
• Nhắn `cây nhân quả` hoặc `/nhanqua`

📊 *KIỂM THỬ ĐỊNH LƯỢNG:*
• Nhắn `/backtest` để xem hiệu suất 2 năm

🪪 *ID CỦA BẠN:*
• Nhắn `/id` để xem Chat ID{admin_section}

❓ *TRỢ GIÚP:* Nhắn `menu` hoặc `/help`"""
    send_message(token, chat_id, menu_text)


def handle_id_command(token, chat_id, user_info: dict):
    """Trả về Chat ID của người dùng."""
    name = user_info.get("first_name", "Bạn")
    text = (
        f"🪪 *Chat ID của {name}:*\n"
        f"`{chat_id}`\n\n"
        f"📌 Gửi ID này cho chủ bot để được thêm vào danh sách truy cập."
    )
    send_message(token, chat_id, text)


def handle_adduser_command(token, chat_id, cfg: dict, args: list):
    """Admin thêm người dùng mới vào whitelist."""
    if len(args) < 2:
        send_message(token, chat_id, "⚠️ Cú pháp: `/adduser <chat_id> <tên>`\nVD: `/adduser 123456789 Minh`")
        return
    new_id = args[0].strip()
    new_name = " ".join(args[1:])
    wl = cfg.get("whitelist_users", {})
    if new_id in wl:
        send_message(token, chat_id, f"ℹ️ User `{new_id}` ({wl[new_id].get('name')}) đã có trong danh sách rồi.")
        return
    wl[new_id] = {"name": new_name, "role": "viewer", "added_by": str(chat_id), "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    cfg["whitelist_users"] = wl
    save_config(cfg)
    send_message(token, chat_id, f"✅ Đã thêm *{new_name}* (`{new_id}`) vào danh sách!\nHọ có thể dùng bot ngay bây giờ.")
    # Thông báo cho người được thêm
    send_message(token, new_id, f"🎉 Chào *{new_name}*! Bạn vừa được thêm vào bot *Antigravity VN Trading*.\n\nNhắn `menu` hoặc `/help` để xem các lệnh nhé!")


def handle_removeuser_command(token, chat_id, cfg: dict, args: list):
    """Admin xóa người dùng khỏi whitelist."""
    if not args:
        send_message(token, chat_id, "⚠️ Cú pháp: `/removeuser <chat_id>`")
        return
    rm_id = args[0].strip()
    admin_id = str(cfg.get("telegram_chat_id", ""))
    if rm_id == admin_id:
        send_message(token, chat_id, "❌ Không thể xóa chính mình (admin chính).")
        return
    wl = cfg.get("whitelist_users", {})
    if rm_id not in wl:
        send_message(token, chat_id, f"⚠️ Không tìm thấy user `{rm_id}` trong danh sách.")
        return
    removed_name = wl.pop(rm_id, {}).get("name", rm_id)
    cfg["whitelist_users"] = wl
    save_config(cfg)
    send_message(token, chat_id, f"✅ Đã xóa *{removed_name}* (`{rm_id}`) khỏi danh sách.")


def handle_users_command(token, chat_id, cfg: dict):
    """Hiển thị danh sách người dùng trong whitelist."""
    wl = get_whitelist(cfg)
    if not wl:
        send_message(token, chat_id, "📋 Chưa có người dùng nào trong whitelist.")
        return
    lines = ["👥 *DANH SÁCH NGƯỜI DÙNG BOT:*", "━━━━━━━━━━━━━━━━━━━"]
    for uid, info in wl.items():
        role_icon = "👑" if info.get("role") == "admin" else "👤"
        added = info.get("added_at", "N/A")
        lines.append(f"{role_icon} *{info.get('name', uid)}* (`{uid}`)")
        lines.append(f"   Vai trò: {info.get('role', 'viewer')} | Thêm: {added}")
    lines.append(f"\n📊 Tổng cộng: {len(wl)} người dùng")
    send_message(token, chat_id, "\n".join(lines))


def start_bot_listener():
    cfg = load_config()
    token = cfg.get("telegram_bot_token")
    registered_chat_id = str(cfg.get("telegram_chat_id", ""))

    if not token:
        print("❌ Chưa cấu hình telegram_bot_token trong notification_config.json")
        return

    wl = get_whitelist(cfg)
    print(f"🤖 Telegram Bot Listener đang chạy...")
    print(f"📡 Bot @VideStock_VN_bot | Admin: {registered_chat_id} | Users: {len(wl)}")

    offset = 0
    while True:
        try:
            # Reload config mỗi vòng để cập nhật whitelist mới
            cfg = load_config()
            token = cfg.get("telegram_bot_token")

            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=30"
            res = requests.get(url, timeout=35).json()

            if res.get("ok"):
                for update in res.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    text = msg.get("text", "").strip()
                    chat = msg.get("chat", {})
                    chat_id = str(chat.get("id"))
                    user_name = chat.get("first_name", "User")

                    if not text:
                        continue

                    print(f"\n📩 [{user_name} | {chat_id}]: '{text}'")
                    cmd = text.lower().strip()

                    # ─── LỆNH CÔNG KHAI (không cần whitelist) ───
                    # /id — Ai cũng dùng được để lấy Chat ID của mình
                    if cmd in ["/id", "id", "chat id", "chatid"]:
                        handle_id_command(token, chat_id, chat)
                        continue

                    # /start — Chào mừng và hướng dẫn lấy ID
                    if cmd == "/start":
                        wl_now = get_whitelist(cfg)
                        if str(chat_id) in wl_now:
                            handle_menu_command(token, chat_id, is_admin_user=is_admin(cfg, chat_id))
                        else:
                            send_message(token, chat_id,
                                f"👋 Xin chào *{user_name}*!\n\n"
                                f"Bot này hiện chỉ dành cho người dùng được phép.\n"
                                f"📌 Chat ID của bạn là: `{chat_id}`\n\n"
                                f"Gửi ID này cho chủ bot để được cấp quyền truy cập."
                            )
                        continue

                    # ─── KIỂM TRA WHITELIST ───
                    if not is_allowed(cfg, chat_id):
                        send_message(token, chat_id,
                            f"🔒 Bạn chưa được cấp quyền truy cập bot.\n"
                            f"📌 Chat ID của bạn: `{chat_id}`\n"
                            f"Gửi ID này cho chủ bot (@admin) để được thêm vào."
                        )
                        # Thông báo cho admin có người lạ gõ
                        send_message(token, registered_chat_id,
                            f"⚠️ *Người lạ cố truy cập bot:*\n"
                            f"Tên: {user_name}\n"
                            f"Chat ID: `{chat_id}`\n"
                            f"Tin nhắn: `{text}`\n\n"
                            f"Thêm họ: `/adduser {chat_id} {user_name}`"
                        )
                        continue

                    # ─── CÁC LỆNH CHO USER ĐƯỢC PHÉP ───
                    user_is_admin = is_admin(cfg, chat_id)

                    # Help / Menu
                    if cmd in ["/help", "menu", "trợ giúp", "huong dan", "hướng dẫn", "help"]:
                        threading.Thread(target=handle_menu_command, args=(token, chat_id, user_is_admin), daemon=True).start()

                    # Tin tức (tất cả user)
                    elif any(kw in cmd for kw in ["tin tức", "tin tuc", "/tintuc", "news"]):
                        threading.Thread(target=handle_news_command, args=(token, chat_id), daemon=True).start()

                    # Cây Nhân - Quả (tất cả user)
                    elif any(kw in cmd for kw in ["nhân quả", "nhan qua", "cây nhân quả", "cay nhan qua", "/nhanqua", "causal", "sơ đồ nhân quả", "so do nhan qua"]):
                        threading.Thread(target=handle_causal_tree_command, args=(token, chat_id), daemon=True).start()

                    # Phân tích mã (tất cả user)
                    elif cmd.startswith("phân tích") or cmd.startswith("phan tich") or cmd.startswith("/pt"):
                        parts = text.split()
                        if len(parts) >= 2:
                            threading.Thread(target=handle_analyze_command, args=(token, chat_id, parts[1].upper()), daemon=True).start()
                        else:
                            send_message(token, chat_id, "Cú pháp: `phân tích <MÃ>` — Ví dụ: `phân tích fpt`")

                    # Gõ thẳng mã 2-4 ký tự bất kể HOA/thường (fpt, HPG, vcb, HVN...)
                    elif len(text.strip()) <= 4 and text.strip().replace(" ", "").isalpha():
                        threading.Thread(target=handle_analyze_command, args=(token, chat_id, text.strip().upper()), daemon=True).start()

                    # ─── LỆNH CHỈ ADMIN ───
                    elif any(kw in cmd for kw in ["sổ lệnh", "so lenh", "danh mục", "danh muc",
                                                  "/danhmuc", "/solenh", "cập nhật", "cap nhat",
                                                  "nav", "portfolio"]):
                        if user_is_admin:
                            threading.Thread(target=handle_portfolio_command, args=(token, chat_id), daemon=True).start()
                        else:
                            send_message(token, chat_id, "🔒 Lệnh này chỉ dành cho Admin.")

                    elif any(kw in cmd for kw in ["quét", "quet", "/pipeline", "/scan", "chạy pipeline"]):
                        if user_is_admin:
                            threading.Thread(target=handle_pipeline_command, args=(token, chat_id), daemon=True).start()
                        else:
                            send_message(token, chat_id, "🔒 Lệnh `/scan` chỉ dành cho Admin.")

                    elif any(kw in cmd for kw in ["backtest", "/backtest", "kiểm định", "kiem dinh", "hiệu suất"]):
                        threading.Thread(target=handle_backtest_command, args=(token, chat_id), daemon=True).start()

                    # Quản lý user (chỉ admin)
                    elif cmd.startswith("/adduser"):
                        if user_is_admin:
                            args = text.split()[1:]
                            handle_adduser_command(token, chat_id, cfg, args)
                        else:
                            send_message(token, chat_id, "🔒 Chỉ Admin mới có thể thêm người dùng.")

                    elif cmd.startswith("/removeuser"):
                        if user_is_admin:
                            args = text.split()[1:]
                            handle_removeuser_command(token, chat_id, cfg, args)
                        else:
                            send_message(token, chat_id, "🔒 Chỉ Admin mới có thể xóa người dùng.")

                    elif cmd in ["/users", "danh sách user", "ds user"]:
                        if user_is_admin:
                            handle_users_command(token, chat_id, cfg)
                        else:
                            send_message(token, chat_id, "🔒 Chỉ Admin mới xem được danh sách user.")

                    else:
                        wl_user = get_whitelist(cfg).get(str(chat_id), {})
                        uname = wl_user.get("name", user_name)
                        reply = (
                            f"🤖 Xin chào *{uname}*! Tôi chưa hiểu lệnh này.\n\n"
                            f"Bạn có thể:\n"
                            f"• Gõ tên mã CP: `FPT`, `HPG`, `SSI`...\n"
                            f"• Nhắn `tin tức` để xem bản tin\n"
                            f"• Nhắn `menu` để xem toàn bộ lệnh"
                        )
                        send_message(token, chat_id, reply)

        except requests.exceptions.Timeout:
            # Long-polling timeout bình thường khi không có tin nhắn mới
            continue
        except Exception as e:
            print(f"Lỗi listener loop: {e}")
            time.sleep(3)

        time.sleep(1)


if __name__ == "__main__":
    start_bot_listener()
