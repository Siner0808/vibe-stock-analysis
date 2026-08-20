"""
paper_runner.py
──────────────────────────────────────────────────────────────────────
Vòng chạy cho sổ lệnh giấy.

    # Nạp sổ bằng dữ liệu lịch sử (dùng cache của backtest)
    python3 paper_runner.py seed --stride 1

    # Chạy một phiên trên dữ liệu mới nhất
    python3 paper_runner.py daily --symbols FPT,HPG,VNM

    # Xem báo cáo
    python3 paper_runner.py report

THỨ TỰ TRONG MỘT PHIÊN — KHÔNG ĐƯỢC ĐỔI
────────────────────────────────────────
    1. fill_pending  (khớp lệnh VÀO ở giá mở cửa hôm nay)
    2. fill_closing  (khớp lệnh RA ở giá mở cửa hôm nay)
    3. evaluate_open (xét SL/TP bằng nến hôm nay)
    4. consider_entry(tín hiệu hôm nay -> chờ khớp phiên sau)

Bước 4 phải ở CUỐI. Nếu tính tín hiệu rồi khớp luôn trong cùng phiên thì
đã nhìn trộm: điểm số dựa trên giá đóng cửa hôm nay, không thể mua ở giá
mở cửa hôm nay bằng thông tin đó.
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from data_quality import now_vn
from paper_metrics import report as build_report
from paper_trading import PaperTradingJournal, Status


class DaLuongVoiBoNhoError(RuntimeError):
    """Chấm điểm đa luồng trong khi post-mortem BẬT — kết quả không tái lập."""


_LUONG_DA_GOI: set = set()


def _reset_gac_da_luong() -> None:
    """Xoá dấu vết luồng đã gọi. Dành cho test và cho tiến trình con."""
    _LUONG_DA_GOI.clear()


def _gac_da_luong() -> None:
    """Nổ nếu chấm điểm chạy trên nhiều luồng trong khi post-mortem BẬT.

    Bất biến 7. `post_mortem_learning._ENGINE_CACHE` giữ MỘT engine cho cả
    tiến trình, và `record_sl_trade()` nối thêm vào `sl_patterns` dùng chung.
    Nên khi 20 vòng tối ưu chạy qua `ThreadPoolExecutor(max_workers=8)`,
    vòng 3 đóng một lệnh bằng cắt lỗ và làm lệch điểm của vòng 11 — vòng nào
    chạy trước là do lịch luồng, nên chạy lại ra bảng khác. "Quán quân của
    20 vòng" khi đó không tái lập được.

    Luồng KHÔNG sửa được chuyện này: đặt lại cache giữa vòng sẽ đè lên các
    vòng đang chạy song song, còn thread-local thì rò rỉ vì 20 vòng dùng
    chung 8 luồng. Chỉ tiến trình riêng mới cho độc lập thật.

    Hai lối đi hợp lệ, cả hai đều được nêu trong thông báo lỗi:
      • mỗi vòng một TIẾN TRÌNH (ProcessPoolExecutor)
      • hoặc TẮT post-mortem — khi đó `sl_penalty` luôn 0, `_analyze` trở
        lại là hàm thuần, và các vòng chỉ khác nhau ở ngưỡng. Đa luồng khi
        đó hợp lệ.

    Không có cửa thoát bằng biến môi trường: cấu hình bị chặn ở đây không
    cho ra kết quả dùng được, nên "cho phép tạm" chỉ là cách viết khác của
    "cho ra số sai nhưng đừng báo".
    """
    import threading

    from post_mortem_learning import get_learning_engine
    if not get_learning_engine().enabled:
        return

    _LUONG_DA_GOI.add(threading.get_ident())
    if len(_LUONG_DA_GOI) > 1:
        raise DaLuongVoiBoNhoError(
            "Chấm điểm đang chạy trên "
            + str(len(_LUONG_DA_GOI))
            + " luồng trong CÙNG một tiến trình, trong khi post-mortem BẬT. "
              "Các vòng dùng chung sl_patterns nên KHÔNG vòng nào độc lập — "
              "bảng kết quả không tái lập được, và lấy vòng lãi cao nhất "
              "trong đó là vi phạm bất biến 7. "
              "Sửa bằng MỘT trong hai cách: cho mỗi vòng một tiến trình "
              "riêng (ProcessPoolExecutor, nhớ dời phần dựng dữ liệu ở mức "
              "module vào main() trước), hoặc đặt POST_MORTEM_ENABLED=0.")


_ANALYZE_CACHE: dict[tuple, dict] = {}


def _dau_van_bo_nho() -> tuple:
    """Dấu vân trạng thái bộ nhớ post-mortem, để đưa vào khoá cache.

    Bất biến 7. Điểm của một lát cắt KHÔNG chỉ phụ thuộc lát cắt: nó còn
    cộng `sl_penalty` lấy từ `post_mortem_learning`, mà bộ nhớ ở đó phình
    ra trong lúc chạy. Bản cũ khoá cache bằng
    `(symbol, len(history), last_time)` — tức ghi nhớ một giá trị KHÔNG
    phải hàm thuần của khoá.

    Hậu quả trong `optimize_20loops_custom71_18m.py`: 20 vòng chạy trong
    MỘT tiến trình qua `ThreadPoolExecutor(max_workers=8)`, dùng chung cả
    `_ANALYZE_CACHE` lẫn `_ENGINE_CACHE`. Vòng 3 đóng một lệnh bằng cắt lỗ
    làm bộ nhớ phình thêm; vòng 11 gọi `_analyze` cho cùng lát cắt và nhận
    lại điểm mà vòng 3 đã tính TRƯỚC khi bộ nhớ đổi. Vòng nào tính trước
    là do luồng nào chạy trước — nên chạy lại ra bảng khác, và "quán quân
    của 20 vòng" không tái lập được.

    Dùng ĐỘ DÀI làm dấu vân được vì `record_sl_trade()` chỉ nối thêm, không
    bao giờ sửa hay xoá. Ngày nào có đường xoá/sửa mẫu hình thì dấu vân này
    phải đổi thành hash nội dung.
    """
    from post_mortem_learning import get_learning_engine
    may = get_learning_engine()
    return (bool(may.enabled), len(may.sl_patterns))


def _analyze(symbol: str, history: pd.DataFrame, exchange: str = "HOSE") -> dict:
    """Chạy pipeline thật trên lịch sử đã cắt tới ngày T."""
    global _ANALYZE_CACHE
    _gac_da_luong()
    last_time = str(history["time"].iloc[-1]) if "time" in history.columns and len(history) else ""
    cache_key = (symbol, len(history), last_time) + _dau_van_bo_nho()
    if cache_key in _ANALYZE_CACHE:
        return _ANALYZE_CACHE[cache_key]

    from data_collectors import MarketDataPacket, DataOrchestrator
    from master_agent import MasterConsensusAgent

    packet = MarketDataPacket(
        symbol=symbol, exchange=exchange,
        ohlcv_df=history.reset_index(drop=True),
        tv_recommendation="NEUTRAL",   # không có TradingView lịch sử
        news_packet=None,
        data_quality="OK",
    )
    
    # BẮT BUỘC: Tính toán indicator cho backtest (vì TradingView MCP không hỗ trợ quá khứ)
    if packet.ohlcv_df is not None and len(packet.ohlcv_df) >= 20:
        orchestrator = DataOrchestrator(symbol, "", "")
        local_inds = orchestrator._compute_local_indicators(packet.ohlcv_df)
        packet.tv_indicators.update({k: v for k, v in local_inds.items() if v is not None})
        packet.source_notes.append("[Local] Đã tự tính RSI, MACD, BB, MAs... từ OHLCV lịch sử")

    res = MasterConsensusAgent().run(packet)
    _ANALYZE_CACHE[cache_key] = res
    return res


def run_session(journal: PaperTradingJournal, symbol: str,
                history: pd.DataFrame, bar: dict, session_date: str,
                exchange: str = "HOSE",
                buy_threshold: float | None = None) -> dict:
    """Xử lý MỘT phiên cho MỘT mã. `history` chỉ chứa dữ liệu tới hết phiên này.

    ĐƠN VỊ: mọi giá đưa vào sổ đều quy về VNĐ.
    Nguồn vnstock trả giá theo nghìn đồng (FPT = 71.2), trong khi
    RiskManagementAgent trả stop_loss/take_profit theo VNĐ (66.000).
    So thẳng hai thứ đó thì `low <= stop_loss` luôn đúng — mọi lệnh đóng
    ngay phiên sau với lợi nhuận vô nghĩa hàng chục nghìn phần trăm.
    """
    from data_quality import price_multiplier

    mult = price_multiplier(history)
    bar = {k: (float(v) * mult if v is not None else v) for k, v in bar.items()}

    stats = {"filled_in": 0, "filled_out": 0, "closed": 0, "opened": 0}

    stats["filled_in"] = journal.fill_pending(symbol, session_date, bar["open"])
    stats["filled_out"] = journal.fill_closing(symbol, session_date, bar["open"])

    result = None
    if journal.open_position(symbol) is not None:
        result = _analyze(symbol, history, exchange)
        closed = journal.evaluate_open(symbol, session_date, bar,
                                       current_score=int(result["final_score"]))
        stats["closed"] = len(closed)

    if journal.open_position(symbol) is None:
        result = result or _analyze(symbol, history, exchange)
        if journal.consider_entry(symbol, session_date, result, exchange,
                                  buy_threshold) is not None:
            stats["opened"] = 1

    # Điểm THẬT của phiên này. Bên dựng báo cáo cần nó; trước đây nó được
    # tính ở đây rồi vứt đi, nên báo cáo phải bịa một hằng số thay thế.
    stats["final_score"] = float(result["final_score"])
    return stats


# ─────────────────────────────── seed ────────────────────────────────
def _cat_khoang(df, bat_dau, ket_thuc):
    """Cắt DataFrame về khoảng [bat_dau, ket_thuc] theo cột `time`.

    Không truyền thì giữ nguyên — im lặng cắt bớt còn tệ hơn không cắt.

    So sánh trên 10 ký tự đầu vì `backtest/cache/` có HAI định dạng cột
    `time` trong cùng một thư mục: 40/125 file dạng '2025-02-10 07:00:00',
    85/125 dạng '2021-10-14'. So chuỗi nguyên vẹn sẽ bỏ sót cả nhóm kia.
    """
    if df is None or "time" not in getattr(df, "columns", []):
        return df
    ngay = df["time"].astype(str).str.slice(0, 10)
    loc = None
    if bat_dau:
        loc = ngay >= str(bat_dau)[:10]
    if ket_thuc:
        v = ngay <= str(ket_thuc)[:10]
        loc = v if loc is None else (loc & v)
    return df if loc is None else df[loc]


def cmd_seed(args) -> int:
    from backtest import data as bt_data

    journal = PaperTradingJournal(args.db)
    symbols = args.symbols.split(",") if args.symbols else None
    dataset = bt_data.load_all(symbols)
    if not dataset:
        print("❌ Chưa có cache. Chạy `python3 backtest/run.py fetch` trước.")
        return 1

    # Bản cũ BỎ QUA args.start/args.end: nó gọi load_all() rồi duyệt trọn
    # file cache. Các script tối ưu vẫn dựng Namespace(start=..., end=...)
    # và in "18 Tháng gần nhất", nên nhãn đó là trang trí — độ phủ thật lên
    # tới ~4,8 năm với 34 mã. Nay tôn trọng nếu có, và LUÔN nói ra độ phủ
    # thật để nhãn không thể sai một lần nữa.
    bat_dau = getattr(args, "start", None)
    ket_thuc = getattr(args, "end", None)
    if bat_dau or ket_thuc:
        dataset = {k: _cat_khoang(v, bat_dau, ket_thuc) for k, v in dataset.items()}
        dataset = {k: v for k, v in dataset.items() if v is not None and len(v)}
        if not dataset:
            print(f"❌ Không mã nào có dữ liệu trong khoảng {bat_dau} → {ket_thuc}.")
            return 1

    _ngay = [str(v["time"].iloc[i])[:10] for v in dataset.values()
             for i in (0, -1) if "time" in v.columns and len(v)]
    if _ngay:
        _phien = [len(v) for v in dataset.values()]
        print(f"📅 ĐỘ PHỦ THẬT: {min(_ngay)} → {max(_ngay)} · {len(dataset)} mã · "
              f"{min(_phien)}–{max(_phien)} phiên mỗi mã"
              + (f" · đã cắt theo {bat_dau or '…'} → {ket_thuc or '…'}"
                 if (bat_dau or ket_thuc) else " · KHÔNG cắt khoảng"))

    total = {"opened": 0, "closed": 0}
    for i, (sym, df) in enumerate(sorted(dataset.items()), 1):
        n = len(df)
        for t in range(args.min_history, n, args.stride):
            row = df.iloc[t]
            # Lịch sử CHỈ tới hết phiên t — đây là dòng chống nhìn trộm
            history = df.iloc[: t + 1]
            s = run_session(journal, sym, history,
                            {"open": float(row["open"]), "high": float(row["high"]),
                             "low": float(row["low"]), "close": float(row["close"])},
                            str(row["time"]), buy_threshold=args.buy_threshold)
            total["opened"] += s["opened"]
            total["closed"] += s["closed"]
        if not getattr(args, 'no_summary', False):
            print(f"  [{i}/{len(dataset)}] {sym}: xong {n - args.min_history} phiên")

    if not getattr(args, 'no_summary', False):
        print(f"\nĐã nạp: {total['opened']} lệnh mở, {total['closed']} lệnh đóng")
        print(f"Sổ: {args.db}")
    return 0


# ─────────────────────────────── daily ───────────────────────────────
def cmd_daily(args) -> int:
    from data_collectors import VNStockCollectorAgent

    journal = PaperTradingJournal(args.db, cho_phep_so_that=True)
    if isinstance(args.symbols, list):
        symbols = [s.strip().upper() for s in args.symbols]
    else:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
    end = now_vn()
    start = end - pd.Timedelta(days=args.days)

    for sym in symbols:
        res = VNStockCollectorAgent().collect(
            sym, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"),
            exchange=args.exchange)
        if res.get("status") != "OK":
            print(f"  {sym}: bỏ qua — {res.get('note', 'không lấy được dữ liệu')}")
            continue
        df = res["df"]
        row = df.iloc[-1]
        s = run_session(journal, sym, df,
                        {"open": float(row["open"]), "high": float(row["high"]),
                         "low": float(row["low"]), "close": float(row["close"])},
                        str(row["time"]), args.exchange, args.buy_threshold)
        print(f"  {sym}: khớp vào {s['filled_in']} · khớp ra {s['filled_out']} "
              f"· đóng {s['closed']} · mở {s['opened']}")

    print(f"\nPhiên {now_vn():%Y-%m-%d %H:%M} (giờ VN) — đã ghi vào {args.db}")
    return 0


def build_benchmark(trades, dataset: dict) -> dict:
    """Lợi nhuận của rổ ĐỀU TRỌNG SỐ trong đúng khoảng thời gian mỗi lệnh.

    Vì sao dùng rổ thay vì VN-INDEX: câu hỏi cần trả lời là "chọn ĐÚNG mã,
    ĐÚNG lúc có hơn việc cầm đều tất cả không?". Rổ đều trọng số cô lập
    được kỹ năng chọn mã; VN-INDEX còn lẫn cả khác biệt về thành phần và
    tỷ trọng vốn hoá. Rổ cũng tính được offline từ cache sẵn có.
    """
    if not dataset:
        return {}
    closes = {}
    for sym, df in dataset.items():
        s = df.set_index(df["time"].astype(str))["close"].astype(float)
        closes[sym] = s[~s.index.duplicated(keep="last")]

    bench: dict[tuple[str, str], float] = {}
    for t in trades:
        if t.status != "CLOSED" or not t.entry_date or not t.exit_date:
            continue
        key = (t.entry_date, t.exit_date)
        if key in bench:
            continue
        rets = []
        for s in closes.values():
            if key[0] in s.index and key[1] in s.index:
                a, b = float(s[key[0]]), float(s[key[1]])
                if a > 0:
                    rets.append((b - a) / a * 100)
        if rets:
            bench[key] = sum(rets) / len(rets)
    return bench


# ─────────────────────────────── report ──────────────────────────────
def cmd_report(args) -> int:
    journal = PaperTradingJournal(args.db, cho_phep_so_that=True)
    trades = journal.all_trades()
    if not trades:
        print("Sổ trống. Chạy `seed` hoặc `daily` trước.")
        return 1

    bench = None
    if not args.no_benchmark:
        try:
            from backtest import data as bt_data
            syms = args.symbols.split(",") if args.symbols else None
            bench = build_benchmark(trades, bt_data.load_all(syms)) or None
        except Exception:
            bench = None

    print(build_report(trades, bench))

    decisions = journal.decisions()
    skipped = journal.decisions(acted=False)
    print("")
    print("─" * 64)
    print(f"Tổng quyết định đã ghi: {len(decisions)}  "
          f"(vào lệnh {len(decisions) - len(skipped)}, bỏ qua {len(skipped)})")
    reasons: dict[str, int] = {}
    for d in skipped:
        key = (d["skip_reason"] or "?").split("(")[0][:40]
        reasons[key] = reasons.get(key, 0) + 1
    for k, v in sorted(reasons.items(), key=lambda x: -x[1])[:5]:
        print(f"  bỏ qua vì {k}: {v}")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Sổ lệnh giấy của agent")
    p.add_argument("--db", default="paper_trades.db")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("seed", help="Nạp sổ từ cache lịch sử của backtest")
    s.add_argument("--stride", type=int, default=1)
    s.add_argument("--min-history", type=int, default=60, dest="min_history")
    s.add_argument("--symbols")
    s.add_argument("--buy-threshold", type=float, default=None,
                   dest="buy_threshold",
                   help="Ngưỡng điểm mở lệnh. Mặc định 62 — nhưng khi chạy "
                        "không có TradingView, điểm hiếm khi vượt 61 nên "
                        "hầu như không có lệnh nào. Thử 55 để có mẫu.")
    s.set_defaults(func=cmd_seed)

    d = sub.add_parser("daily", help="Chạy một phiên trên dữ liệu mới nhất")
    d.add_argument("--symbols", required=True)
    d.add_argument("--exchange", default="HOSE")
    d.add_argument("--days", type=int, default=180)
    d.add_argument("--buy-threshold", type=float, default=None,
                   dest="buy_threshold")
    d.set_defaults(func=cmd_daily)

    r = sub.add_parser("report", help="Báo cáo hiệu quả")
    r.add_argument("--symbols", help="Rổ dùng làm chuẩn đối chiếu")
    r.add_argument("--no-benchmark", action="store_true", dest="no_benchmark",
                   help="Bỏ đối chiếu chuẩn (không khuyến khích)")
    r.set_defaults(func=cmd_report)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
