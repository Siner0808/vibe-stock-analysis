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


def _analyze(symbol: str, history: pd.DataFrame, exchange: str = "HOSE") -> dict:
    """Chạy pipeline thật trên lịch sử đã cắt tới ngày T."""
    from data_collectors import MarketDataPacket
    from master_agent import MasterConsensusAgent

    packet = MarketDataPacket(
        symbol=symbol, exchange=exchange,
        ohlcv_df=history.reset_index(drop=True),
        tv_recommendation="NEUTRAL",   # không có TradingView lịch sử
        news_packet=None,
        data_quality="OK",
    )
    return MasterConsensusAgent().run(packet)


def run_session(journal: PaperTradingJournal, symbol: str,
                history: pd.DataFrame, bar: dict, session_date: str,
                exchange: str = "HOSE",
                buy_threshold: float | None = None) -> dict:
    """Xử lý MỘT phiên cho MỘT mã. `history` chỉ chứa dữ liệu tới hết phiên này."""
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
    return stats


# ─────────────────────────────── seed ────────────────────────────────
def cmd_seed(args) -> int:
    from backtest import data as bt_data

    journal = PaperTradingJournal(args.db)
    symbols = args.symbols.split(",") if args.symbols else None
    dataset = bt_data.load_all(symbols)
    if not dataset:
        print("❌ Chưa có cache. Chạy `python3 backtest/run.py fetch` trước.")
        return 1

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
        print(f"  [{i}/{len(dataset)}] {sym}: xong {n - args.min_history} phiên")

    print(f"\nĐã nạp: {total['opened']} lệnh mở, {total['closed']} lệnh đóng")
    print(f"Sổ: {args.db}")
    return 0


# ─────────────────────────────── daily ───────────────────────────────
def cmd_daily(args) -> int:
    from data_collectors import VNStockCollectorAgent

    journal = PaperTradingJournal(args.db)
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
    journal = PaperTradingJournal(args.db)
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
